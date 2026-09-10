"""
lrf_reader.py

Reads live rangefinder distance from a serial laser rangefinder module and
reports it via plain callbacks on a background thread -- same headless
threading.Thread pattern as sensors/gps_reader.py (no Qt dependency; this
runs inside the backend daemon, not the GUI process).

Wire protocol (continuous-ranging mode):
    Frame:    [0x55, 0xAA, <5 payload bytes>, <checksum>]
    Checksum: sum(payload bytes) & 0xFF

    Start continuous ranging: payload = [freq_byte, 0xFF, 0xFF, 0xFF, 0xFF]
        freq_byte: 0x89 = 1Hz, 0xA9 = 2Hz, 0xB9 = 5Hz
    Stop continuous ranging:  payload = [0x8E, 0xFF, 0xFF, 0xFF, 0xFF]

    Response frame (8 bytes): [0x55, 0xAA, _, status, _, dist_hi, dist_lo, _]
        status == 1  -> valid reading, distance_m = ((dist_hi << 8) | dist_lo) / 10.0
        status != 1  -> no return / out of range

Requires the `pyserial` package: pip install pyserial
"""

import threading
import time

FRAME_HEADER = (0x55, 0xAA)
STOP_PAYLOAD = [0x8E, 0xFF, 0xFF, 0xFF, 0xFF]


def checksum(payload_bytes) -> int:
    return sum(payload_bytes) & 0xFF


def build_frame(payload_bytes) -> bytearray:
    return bytearray([FRAME_HEADER[0], FRAME_HEADER[1]] + list(payload_bytes) + [checksum(payload_bytes)])


def parse_response(resp: bytes):
    """Parse one 8-byte response frame. Returns a ("valid", distance_m),
    ("invalid", None), or ("skip", None) tuple -- "skip" covers both a read
    timeout (empty bytes) and a malformed/unrecognized frame."""
    if len(resp) != 8 or resp[0] != FRAME_HEADER[0] or resp[1] != FRAME_HEADER[1]:
        return ("skip", None)
    status = resp[3]
    if status == 1:
        dist_raw = (resp[5] << 8) | resp[6]
        return ("valid", dist_raw / 10.0)
    return ("invalid", None)


class LRFReader(threading.Thread):
    """
    Background thread that opens the LRF's serial port, starts continuous
    ranging, and invokes callbacks whenever a new reading arrives.

    Callbacks:
        on_reading(distance_m: float)  -- called on a valid ranging reading.
        on_invalid()                   -- called on "no return / out of range".
        on_error(message: str)         -- called on serial/connection errors.
    """

    def __init__(self, port="/dev/ttyAMA2", baudrate=115200, freq_byte=0x89,
                 on_reading=None, on_invalid=None, on_error=None,
                 retry_interval=2.0):
        super().__init__(daemon=True)
        self._port = port
        self._baudrate = baudrate
        self._freq_byte = freq_byte
        self._on_reading = on_reading
        self._on_invalid = on_invalid
        self._on_error = on_error
        self._retry_interval = retry_interval
        self._running = True

    def run(self):
        while self._running:
            try:
                self._read_loop()
            except Exception as e:
                self._emit_error(f"LRF read error: {e}")
            if self._running:
                time.sleep(self._retry_interval)

    def _read_loop(self):
        import serial

        try:
            ser = serial.Serial(self._port, baudrate=self._baudrate, bytesize=8,
                                 parity="N", stopbits=1, timeout=1)
        except Exception as e:
            self._emit_error(f"Could not open LRF serial port {self._port}: {e}")
            return

        try:
            ser.write(build_frame([self._freq_byte, 0xFF, 0xFF, 0xFF, 0xFF]))
            while self._running:
                resp = ser.read(8)
                kind, distance_m = parse_response(resp)
                if kind == "valid":
                    if self._on_reading:
                        self._on_reading(distance_m)
                elif kind == "invalid":
                    if self._on_invalid:
                        self._on_invalid()
        finally:
            try:
                ser.write(build_frame(STOP_PAYLOAD))
                time.sleep(0.1)
                ser.read(8)  # drain the stop acknowledgement, if any
            except Exception:
                pass
            ser.close()

    def _emit_error(self, message):
        if self._on_error:
            self._on_error(message)

    def stop(self):
        self._running = False
        self.join(timeout=3.0)
