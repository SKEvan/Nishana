"""
compass_reader.py

CMPS12 Tilt-Compensated Compass driver (I2C mode) for Raspberry Pi 5, plus a
background polling thread that reports heading/pitch/roll via callbacks --
same headless threading.Thread pattern as sensors/gps_reader.py and
sensors/lrf_reader.py.

Wiring (per CMPS12 datasheet pin order):
    Pin 1 (3.3v-5v)   -> Pi 3.3V (physical pin 1)
    Pin 2 (SDA/TX)    -> Pi GPIO2 / SDA1 (physical pin 3)
    Pin 3 (SCL/RX)    -> Pi GPIO3 / SCL1 (physical pin 5)
    Pin 4 (Mode)      -> leave open (I2C mode). Tie to GND only for serial mode.
    Pin 5 (Factory)   -> leave open
    Pin 6 (0v ground) -> Pi GND (physical pin 6)

Default I2C address: 0xC0 (8-bit) = 0x60 (7-bit, what smbus2 uses)

--- Fixing "Remote I/O error" ---
This error comes from the Linux I2C layer (a NACK / failed transaction), not
from this script's logic. The CMPS12 is built around a Bosch BNO055, which
uses I2C clock stretching, and Raspberry Pi's I2C controller has a known
limited clock-stretch timeout that trips over this at the default 100kHz bus
speed. Before relying on the retry logic below to paper over it, fix it at
the source:
    1. `sudo i2cdetect -y 1` -- confirm the device actually appears at 0x60.
       If it doesn't, this is wiring/power, not software.
    2. Lower the I2C bus speed in /boot/firmware/config.txt:
           dtparam=i2c_arm=on,i2c_arm_baudrate=50000
       then reboot.
    3. If it still misbehaves, add external 4.7k ohm pull-ups from SDA and
       SCL to 3.3V (some CMPS12 batches have weak/no onboard pull-ups).

This script retries transient I2C errors with backoff so a single stretch
timeout doesn't crash your backend, but it cannot fix a bus that is
mis-wired or has no pull-ups.

Requires the `smbus2` package: pip install smbus2
"""

import threading
import time
import logging

logger = logging.getLogger(__name__)

I2C_BUS = 1
CMPS12_ADDR = 0x60  # 7-bit form of the default 0xC0 shipped address

# --- Accuracy configuration ---
# Magnetic declination for your location, in degrees (East positive, West
# negative). Look this up for your exact coordinates and date at:
# https://www.ngdc.noaa.gov/geomag/calculators/magcalc.shtml#declination
# Leave at 0.0 if you only need magnetic bearing, not true-north bearing.
MAGNETIC_DECLINATION_DEG = 0.0

# Fixed offset between the PCB's silkscreen "Heading" arrow and your rig's
# actual forward axis, in degrees. Measure this once: point your rig at a
# known landmark, read get_bearing(), and the difference from the landmark's
# true bearing is your offset. Add it here so every reading is corrected.
MOUNTING_OFFSET_DEG = 0.0

# Minimum calibration level (0-3) required on each sub-sensor before a
# bearing reading is trusted. 3 = fully calibrated. Lower this only if you
# understand the accuracy trade-off.
MIN_CALIBRATION_LEVEL = 3

# --- Register map (from CMPS12 datasheet) ---
REG_COMMAND_OR_VERSION = 0x00
REG_BEARING_8BIT = 0x01
REG_BEARING_16BIT_HIGH = 0x02   # + 0x03 low byte -> 0-3599 (calculated, /10 for degrees)
REG_PITCH_90 = 0x04             # signed byte, +/-90
REG_ROLL_90 = 0x05              # signed byte, +/-90
REG_MAG_X_HIGH = 0x06           # 6 raw registers each for mag/accel/gyro follow
REG_ACCEL_X_HIGH = 0x0C
REG_GYRO_X_HIGH = 0x12
REG_TEMP_HIGH = 0x18            # + 0x19 low byte, degrees C
REG_BEARING_BOSCH_HIGH = 0x1A   # + 0x1B low byte -> 0-5759, /16 for degrees
REG_PITCH_180_HIGH = 0x1C       # + 0x1D low byte, signed, +/-180
REG_CALIBRATION_STATE = 0x1E

# Command sequences (20ms delay required between each byte per datasheet)
STORE_CALIBRATION_SEQ = [0xF0, 0xF5, 0xF6]
DELETE_CALIBRATION_SEQ = [0xE0, 0xE5, 0xE2]

CMD_DELAY = 0.02   # 20ms, as specified in the datasheet
I2C_RETRIES = 4    # attempts per transaction before giving up
I2C_RETRY_DELAY = 0.01  # base delay between retries, doubled each attempt


def to_signed_byte(val):
    return val - 256 if val > 127 else val


def to_signed_16(high, low):
    val = (high << 8) | low
    return val - 65536 if val > 32767 else val


class CMPS12ConnectionError(Exception):
    """Raised when the CMPS12 cannot be reached on the I2C bus after retries."""
    pass


class CMPS12:
    def __init__(self, bus=I2C_BUS, addr=CMPS12_ADDR, verify_on_connect=True):
        from smbus2 import SMBus
        self.bus = SMBus(bus)
        self.addr = addr

        if verify_on_connect:
            # Fail fast and clearly, instead of the first real read throwing
            # a bare OSError deep inside your backend. Note: _read_byte/
            # _read_block already retry and wrap any OSError into
            # CMPS12ConnectionError themselves, so that's what actually
            # propagates here -- not a raw OSError.
            try:
                self.get_software_version()
            except CMPS12ConnectionError as e:
                self.bus.close()
                raise CMPS12ConnectionError(
                    f"CMPS12 not responding at address {hex(addr)} on I2C bus {bus}. "
                    f"Run 'sudo i2cdetect -y {bus}' to confirm the device is visible, "
                    f"and check wiring/pull-ups/I2C clock speed. Original error: {e}"
                ) from e

    def close(self):
        self.bus.close()

    # --- low-level I2C helpers with retry/backoff ---

    def _read_byte(self, reg):
        delay = I2C_RETRY_DELAY
        last_err = None
        for attempt in range(I2C_RETRIES):
            try:
                return self.bus.read_byte_data(self.addr, reg)
            except OSError as e:
                last_err = e
                logger.debug(
                    "CMPS12 read_byte(reg=%s) attempt %d/%d failed: %s",
                    hex(reg), attempt + 1, I2C_RETRIES, e,
                )
                time.sleep(delay)
                delay *= 2
        raise CMPS12ConnectionError(
            f"CMPS12 read failed at register {hex(reg)} after {I2C_RETRIES} attempts: {last_err}"
        )

    def _read_block(self, reg, length):
        """Single I2C transaction for multi-byte reads (fewer transactions
        than separate byte reads = fewer chances to hit a clock-stretch
        timeout, and no risk of the value changing mid-read)."""
        delay = I2C_RETRY_DELAY
        last_err = None
        for attempt in range(I2C_RETRIES):
            try:
                return self.bus.read_i2c_block_data(self.addr, reg, length)
            except OSError as e:
                last_err = e
                logger.debug(
                    "CMPS12 read_block(reg=%s, len=%d) attempt %d/%d failed: %s",
                    hex(reg), length, attempt + 1, I2C_RETRIES, e,
                )
                time.sleep(delay)
                delay *= 2
        raise CMPS12ConnectionError(
            f"CMPS12 block read failed at register {hex(reg)} after {I2C_RETRIES} attempts: {last_err}"
        )

    def _write_byte(self, reg, value):
        delay = I2C_RETRY_DELAY
        last_err = None
        for attempt in range(I2C_RETRIES):
            try:
                self.bus.write_byte_data(self.addr, reg, value)
                return
            except OSError as e:
                last_err = e
                time.sleep(delay)
                delay *= 2
        raise CMPS12ConnectionError(
            f"CMPS12 write failed at register {hex(reg)} after {I2C_RETRIES} attempts: {last_err}"
        )

    # --- public readings ---

    def get_software_version(self):
        return self._read_byte(REG_COMMAND_OR_VERSION)

    def get_bearing_8bit(self):
        """0-255 representing a full circle."""
        return self._read_byte(REG_BEARING_8BIT)

    def get_bearing(self):
        """Calculated bearing, degrees (0.0 - 359.9)."""
        high, low = self._read_block(REG_BEARING_16BIT_HIGH, 2)
        return ((high << 8) | low) / 10.0

    def get_bearing_bosch(self):
        """BNO055-native bearing, degrees (0.0 - 359.9), from registers 0x1A/0x1B."""
        high, low = self._read_block(REG_BEARING_BOSCH_HIGH, 2)
        return ((high << 8) | low) / 16.0

    def get_pitch(self):
        """+/-90 degrees."""
        return to_signed_byte(self._read_byte(REG_PITCH_90))

    def get_roll(self):
        """+/-90 degrees."""
        return to_signed_byte(self._read_byte(REG_ROLL_90))

    def get_pitch_180(self):
        """Extended-range pitch, +/-180 degrees, from registers 0x1C/0x1D."""
        high, low = self._read_block(REG_PITCH_180_HIGH, 2)
        return to_signed_16(high, low)

    def get_temperature_c(self):
        high, low = self._read_block(REG_TEMP_HIGH, 2)
        return to_signed_16(high, low)

    def get_raw_vector(self, reg_high):
        """Read 3x signed 16-bit values (X,Y,Z) starting at reg_high, in one transaction."""
        data = self._read_block(reg_high, 6)
        x = to_signed_16(data[0], data[1])
        y = to_signed_16(data[2], data[3])
        z = to_signed_16(data[4], data[5])
        return x, y, z

    def get_magnetometer_raw(self):
        return self.get_raw_vector(REG_MAG_X_HIGH)

    def get_accelerometer_raw(self):
        return self.get_raw_vector(REG_ACCEL_X_HIGH)

    def get_gyro_raw(self):
        return self.get_raw_vector(REG_GYRO_X_HIGH)

    def get_calibration_state(self):
        """
        Returns a dict decoding register 0x1E:
        bits 0-1: magnetometer, bits 2-3: accelerometer,
        bits 4-5: gyro, bits 6-7: overall system.
        Each value 0 (uncalibrated) - 3 (fully calibrated).
        """
        val = self._read_byte(REG_CALIBRATION_STATE)
        return {
            "magnetometer": val & 0x03,
            "accelerometer": (val >> 2) & 0x03,
            "gyro": (val >> 4) & 0x03,
            "system": (val >> 6) & 0x03,
        }

    def read_all(self):
        return {
            "bearing": self.get_bearing(),
            "pitch": self.get_pitch(),
            "roll": self.get_roll(),
        }

    def is_calibrated(self, min_level=MIN_CALIBRATION_LEVEL):
        """True only if magnetometer AND system calibration both meet min_level.
        Accelerometer/gyro affect tilt compensation but magnetometer is the
        one that directly determines bearing accuracy."""
        cal = self.get_calibration_state()
        return cal["magnetometer"] >= min_level and cal["system"] >= min_level

    def get_true_bearing(self, samples=5, sample_delay=0.02,
                          declination_deg=MAGNETIC_DECLINATION_DEG,
                          mounting_offset_deg=MOUNTING_OFFSET_DEG,
                          require_calibration=True):
        """
        Best-effort accurate bearing: averages several raw readings to cut
        sensor jitter, then applies your mounting offset and magnetic
        declination to produce a true-north bearing.

        Raises CMPS12ConnectionError if require_calibration is True and the
        sensor hasn't reached MIN_CALIBRATION_LEVEL yet -- call
        is_calibrated() yourself first if you'd rather handle that case
        without an exception.
        """
        if require_calibration and not self.is_calibrated():
            cal = self.get_calibration_state()
            raise CMPS12ConnectionError(
                f"CMPS12 not fully calibrated yet (mag={cal['magnetometer']}, "
                f"system={cal['system']}, need {MIN_CALIBRATION_LEVEL}). "
                f"Rotate/tilt the sensor to complete calibration before "
                f"trusting bearing readings."
            )

        # Average on the unit circle (not the raw degrees) so readings near
        # the 0/360 wraparound don't cancel out incorrectly.
        import math
        sin_sum = 0.0
        cos_sum = 0.0
        for _ in range(samples):
            raw = self.get_bearing()
            rad = math.radians(raw)
            sin_sum += math.sin(rad)
            cos_sum += math.cos(rad)
            if sample_delay:
                time.sleep(sample_delay)

        averaged = math.degrees(math.atan2(sin_sum, cos_sum)) % 360.0
        corrected = (averaged + mounting_offset_deg + declination_deg) % 360.0
        return corrected

    def store_calibration_profile(self):
        """Saves current auto-calibration so it reloads automatically on power-up."""
        for byte in STORE_CALIBRATION_SEQ:
            self._write_byte(REG_COMMAND_OR_VERSION, byte)
            time.sleep(CMD_DELAY)

    def delete_calibration_profile(self):
        """Erases stored calibration profile, module powers into default state."""
        for byte in DELETE_CALIBRATION_SEQ:
            self._write_byte(REG_COMMAND_OR_VERSION, byte)
            time.sleep(CMD_DELAY)


class CompassReader(threading.Thread):
    """
    Background thread that polls the CMPS12 over I2C and invokes a callback
    with each new heading/pitch/roll reading.

    Callbacks:
        on_reading(heading_deg: float, pitch_deg: float, roll_deg: float)
        on_error(message: str)
    """

    def __init__(self, i2c_bus=I2C_BUS, addr=CMPS12_ADDR, poll_interval=0.1,
                 on_reading=None, on_error=None, retry_interval=2.0):
        super().__init__(daemon=True)
        self._i2c_bus = i2c_bus
        self._addr = addr
        self._poll_interval = poll_interval
        self._on_reading = on_reading
        self._on_error = on_error
        self._retry_interval = retry_interval
        self._running = True

    def run(self):
        while self._running:
            try:
                self._poll_loop()
            except Exception as e:
                self._emit_error(f"Compass read error: {e}")
            if self._running:
                time.sleep(self._retry_interval)

    def _poll_loop(self):
        try:
            compass = CMPS12(bus=self._i2c_bus, addr=self._addr)
        except Exception as e:
            self._emit_error(f"Could not connect to CMPS12 on I2C bus {self._i2c_bus}: {e}")
            return

        try:
            while self._running:
                try:
                    heading = compass.get_bearing()
                    pitch = compass.get_pitch()
                    roll = compass.get_roll()
                except CMPS12ConnectionError as e:
                    # Transient bus error survived the internal retries too --
                    # report it and let the outer loop reconnect after
                    # retry_interval rather than killing the thread.
                    self._emit_error(str(e))
                    return
                if self._on_reading:
                    self._on_reading(heading, pitch, roll)
                time.sleep(self._poll_interval)
        finally:
            compass.close()

    def _emit_error(self, message):
        if self._on_error:
            self._on_error(message)

    def stop(self):
        self._running = False
        self.join(timeout=3.0)


if __name__ == "__main__":
    # Standalone hardware sanity check -- run this directly on the Pi to
    # confirm I2C wiring/address before wiring it into the full backend.
    logging.basicConfig(level=logging.INFO)
    try:
        compass = CMPS12()
    except CMPS12ConnectionError as e:
        print(f"Connection failed: {e}")
        raise SystemExit(1)

    try:
        print(f"CMPS12 software version: {compass.get_software_version()}")
        print("Reading compass (Ctrl+C to stop):")
        while True:
            data = compass.read_all()
            cal = compass.get_calibration_state()
            print(
                f"Bearing: {data['bearing']:.1f}°  "
                f"Pitch: {data['pitch']}°  "
                f"Roll: {data['roll']}°  "
                f"Cal[sys={cal['system']} gyro={cal['gyro']} "
                f"accel={cal['accelerometer']} mag={cal['magnetometer']}]"
            )
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    finally:
        compass.close()
