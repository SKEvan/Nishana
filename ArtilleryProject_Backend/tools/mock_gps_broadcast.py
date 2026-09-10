"""
mock_gps_broadcast.py

Dev-only helper: runs the real BackendServer and broadcasts a slowly-walking
fake GPS fix once a second, so you can visually confirm the frontend <-> backend
wiring works before ever touching real GPS hardware on the Raspberry Pi.

Usage:
    Terminal 1 (from ArtilleryProject_Backend/tools):
        python3 mock_gps_broadcast.py
    Terminal 2 (from ArtilleryProject_Frontend, the real GUI, not offscreen):
        python3 main.py

Watch the frontend's Observation Post Telemetry panel: the top-bar CONNECTED
badge should go green, and LAT/LON/ALT should tick slightly every second.
"""

import os
import sys
import time
import random

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from server import BackendServer
from protocol import telemetry_message


def main():
    server = BackendServer(host="127.0.0.1", port=5555)
    server.start()
    print("[MOCK] Broadcasting fake GPS fixes on 127.0.0.1:5555. Ctrl+C to stop.")

    lat, lon, alt = 45.1234, -122.5678, 450.0
    try:
        while True:
            lat += random.uniform(-0.0002, 0.0002)
            lon += random.uniform(-0.0002, 0.0002)
            alt += random.uniform(-0.5, 0.5)
            server.broadcast(telemetry_message(gps={
                "fix_quality": 3,
                "latitude": lat,
                "longitude": lon,
                "altitude_m": alt,
            }))
            time.sleep(1.0)
    except KeyboardInterrupt:
        print("\n[MOCK] Stopping.")
    finally:
        server.stop()


if __name__ == "__main__":
    main()
