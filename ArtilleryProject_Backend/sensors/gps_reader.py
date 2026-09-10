"""
gps_reader.py

Reads live GPS data (latitude, longitude, altitude in meters, fix quality)
from gpsd and reports it via plain callbacks on a background thread.

This is the backend daemon's sensor module -- it has no Qt/GUI dependency
(the backend runs headless on the Raspberry Pi 5), so it uses a plain
threading.Thread instead of QThread/Signal. The frontend's own
net/backend_client.py is what turns this data into Qt signals, on the
GUI side, once it arrives over the socket as a MSG_TELEMETRY message.

Requirements (on the Raspberry Pi 5):
    sudo apt install gpsd gpsd-clients python3-gps

Assumes gpsd is already running and pointed at your GPS's serial device
(e.g. /dev/serial0 or /dev/ttyAMA2). Start it once, e.g.:
    sudo gpsd /dev/serial0 -F /var/run/gpsd.sock
or enable it as a systemd service so it comes up automatically on boot,
which is what lets this reader "just work" as soon as the Pi powers on
with the sensor plugged in.
"""

import threading
import time


class GPSReader(threading.Thread):
    """
    Background thread that continuously polls gpsd and invokes callbacks
    whenever a new fix (lat, lon, alt, fix_quality) is available.

    Callbacks:
        on_fix(lat: float, lon: float, alt_m: float, fix_quality: int)
            fix_quality mirrors gpsd's TPV "mode" field: 2 = 2D fix, 3 = 3D fix.
        on_no_fix()
            called when gpsd is reporting but has no current 2D/3D fix.
        on_error(message: str)
            called on connection/read errors (e.g. gpsd not running).
    """

    def __init__(self, on_fix=None, on_no_fix=None, on_error=None,
                 retry_interval=2.0, parent=None):
        super().__init__(daemon=True)
        self._on_fix = on_fix
        self._on_no_fix = on_no_fix
        self._on_error = on_error
        self._retry_interval = retry_interval
        self._running = True
        self._session = None

    def run(self):
        while self._running:
            try:
                self._read_loop()
            except Exception as e:
                self._emit_error(f"GPS read error: {e}")
            if self._running:
                time.sleep(self._retry_interval)

    def _read_loop(self):
        from gps import gps, WATCH_ENABLE

        try:
            self._session = gps(mode=WATCH_ENABLE)
        except Exception as e:
            self._emit_error(f"Could not connect to gpsd: {e}")
            return

        while self._running:
            try:
                report = self._session.next()
            except StopIteration:
                self._emit_error("gpsd has terminated the session.")
                return

            if report.get("class") != "TPV":
                continue

            mode = getattr(report, "mode", 0)
            lat = getattr(report, "lat", None)
            lon = getattr(report, "lon", None)
            # altHAE = height above ellipsoid, altMSL = height above sea level.
            # altMSL is usually what you want for real-world "altitude".
            alt = getattr(report, "altMSL", None)
            if alt is None:
                alt = getattr(report, "alt", None)  # older gpsd fallback

            has_fix = mode >= 2 and lat is not None and lon is not None and alt is not None
            if has_fix:
                if self._on_fix:
                    self._on_fix(float(lat), float(lon), float(alt), mode)
            else:
                if self._on_no_fix:
                    self._on_no_fix()

    def _emit_error(self, message):
        if self._on_error:
            self._on_error(message)

    def stop(self):
        self._running = False
        if self._session is not None:
            try:
                self._session.close()
            except Exception:
                pass
        self.join(timeout=3.0)
