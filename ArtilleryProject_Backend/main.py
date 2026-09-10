"""
ArtilleryProject Backend Daemon -- entry point.

Runs headless on the Raspberry Pi 5. Starts the socket server that the
PySide6 frontend connects to, and starts each sensor reader, wiring its
live data into MSG_TELEMETRY broadcasts.

Currently wired sensors:
    - GPS (via gpsd) -- latitude, longitude, altitude, fix quality.
    - Laser rangefinder (serial) -- distance_m, valid.
    - Compass (CMPS12 via I2C) -- heading_deg, pitch_deg, roll_deg.

Each sensor reader runs on its own thread and reports independently, so
we keep the latest known reading from every sensor here and broadcast a
full merged snapshot on every update -- otherwise, e.g., an LRF-only
update would blank the GPS labels back to "NO FIX" on the frontend (and
vice versa), since TelemetryPanel.update_from_backend() re-renders every
field on each message it receives.
"""

import threading
import time

from server import BackendServer
from protocol import telemetry_message
from sensors.gps_reader import GPSReader
from sensors.lrf_reader import LRFReader
from sensors.compass_reader import CompassReader

BIND_HOST = "0.0.0.0"
BIND_PORT = 5555

LRF_PORT = "/dev/ttyAMA2"
LRF_BAUDRATE = 115200
LRF_FREQ_BYTE = 0x89  # 1Hz continuous ranging

COMPASS_I2C_BUS = 1
COMPASS_ADDR = 0x60
COMPASS_POLL_INTERVAL = 0.1  # 10Hz


def main():
    server = BackendServer(host=BIND_HOST, port=BIND_PORT)
    server.start()

    state_lock = threading.Lock()
    latest_gps = {}
    latest_lrf = {}
    latest_compass = {}

    def broadcast_telemetry():
        with state_lock:
            server.broadcast(telemetry_message(gps=latest_gps, compass=latest_compass, lrf=latest_lrf))

    def on_gps_fix(lat, lon, alt, fix_quality):
        nonlocal latest_gps
        with state_lock:
            latest_gps = {
                "fix_quality": fix_quality,
                "latitude": lat,
                "longitude": lon,
                "altitude_m": alt,
            }
        broadcast_telemetry()

    def on_gps_no_fix():
        nonlocal latest_gps
        with state_lock:
            latest_gps = {"fix_quality": 0}
        broadcast_telemetry()

    def on_gps_error(message):
        print(f"[GPS] {message}")

    def on_lrf_reading(distance_m):
        nonlocal latest_lrf
        with state_lock:
            latest_lrf = {"valid": True, "distance_m": distance_m}
        broadcast_telemetry()

    def on_lrf_invalid():
        nonlocal latest_lrf
        with state_lock:
            latest_lrf = {"valid": False}
        broadcast_telemetry()

    def on_lrf_error(message):
        print(f"[LRF] {message}")

    def on_compass_reading(heading_deg, pitch_deg, roll_deg):
        nonlocal latest_compass
        with state_lock:
            latest_compass = {
                "heading_deg": heading_deg,
                "pitch_deg": pitch_deg,
                "roll_deg": roll_deg,
            }
        broadcast_telemetry()

    def on_compass_error(message):
        print(f"[COMPASS] {message}")

    gps_reader = GPSReader(on_fix=on_gps_fix, on_no_fix=on_gps_no_fix, on_error=on_gps_error)
    gps_reader.start()

    lrf_reader = LRFReader(port=LRF_PORT, baudrate=LRF_BAUDRATE, freq_byte=LRF_FREQ_BYTE,
                            on_reading=on_lrf_reading, on_invalid=on_lrf_invalid,
                            on_error=on_lrf_error)
    lrf_reader.start()

    compass_reader = CompassReader(i2c_bus=COMPASS_I2C_BUS, addr=COMPASS_ADDR,
                                    poll_interval=COMPASS_POLL_INTERVAL,
                                    on_reading=on_compass_reading, on_error=on_compass_error)
    compass_reader.start()

    print("[BACKEND] ArtilleryProject backend daemon running. Press Ctrl+C to stop.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[BACKEND] Shutting down...")
    finally:
        gps_reader.stop()
        lrf_reader.stop()
        compass_reader.stop()
        server.stop()


if __name__ == "__main__":
    main()
