"""
BackendClient: connects the PySide6 frontend to the ArtilleryProject_Backend socket
daemon, parses incoming JSON-line messages, and re-emits them as Qt signals so GUI
updates happen safely on the main thread.

Message shapes must stay in sync with ArtilleryProject_Backend/protocol.py.
"""

import json
import socket
import threading
import time

from PySide6.QtCore import QThread, Signal

MSG_HELLO = "hello"
MSG_TELEMETRY = "telemetry"
MSG_SNAPSHOT = "snapshot"
MSG_DEFLECTION_RESULT = "deflection_result"
MSG_DEFLECTION_ERROR = "deflection_error"
MSG_SET_TARGET = "set_target"

_RECONNECT_DELAY_SECS = 2.0


class BackendClient(QThread):
    telemetry_received = Signal(dict)
    snapshot_latched = Signal(dict)
    deflection_received = Signal(dict)
    deflection_failed = Signal(str)
    connection_changed = Signal(bool)

    def __init__(self, host: str = "127.0.0.1", port: int = 5555, parent=None):
        super().__init__(parent)
        self._host = host
        self._port = port
        self._stop_event = threading.Event()
        self._socket_lock = threading.Lock()
        self._socket: socket.socket | None = None

    def stop(self) -> None:
        self._stop_event.set()
        with self._socket_lock:
            if self._socket is not None:
                self._socket.close()
        self.wait(2000)

    def send_target(self, target: dict) -> bool:
        """Send the operator-entered target grid reference to the backend. Returns False
        if there's currently no live connection (caller should surface this to the operator)."""
        message = {
            "type": MSG_SET_TARGET,
            "northing": target.get("northing"),
            "easting": target.get("easting"),
            "altitude": target.get("altitude"),
        }
        payload = (json.dumps(message) + "\n").encode("utf-8")
        with self._socket_lock:
            if self._socket is None:
                return False
            try:
                self._socket.sendall(payload)
                return True
            except OSError:
                return False

    def run(self) -> None:
        while not self._stop_event.is_set():
            try:
                self._connect_and_read()
            except OSError:
                pass
            self.connection_changed.emit(False)
            if self._stop_event.is_set():
                return
            time.sleep(_RECONNECT_DELAY_SECS)

    def _connect_and_read(self) -> None:
        sock = socket.create_connection((self._host, self._port), timeout=5)
        sock.settimeout(1.0)
        with self._socket_lock:
            self._socket = sock
        self.connection_changed.emit(True)

        buffer = b""
        try:
            while not self._stop_event.is_set():
                try:
                    chunk = sock.recv(4096)
                except socket.timeout:
                    continue
                if not chunk:
                    break
                buffer += chunk
                while b"\n" in buffer:
                    line, buffer = buffer.split(b"\n", 1)
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        message = json.loads(line.decode("utf-8"))
                    except json.JSONDecodeError:
                        continue
                    self._dispatch(message)
        finally:
            with self._socket_lock:
                self._socket = None
            sock.close()

    def _dispatch(self, message: dict) -> None:
        msg_type = message.get("type")
        if msg_type == MSG_TELEMETRY:
            self.telemetry_received.emit(message)
        elif msg_type == MSG_SNAPSHOT:
            self.snapshot_latched.emit(message)
        elif msg_type == MSG_DEFLECTION_RESULT:
            self.deflection_received.emit(message)
        elif msg_type == MSG_DEFLECTION_ERROR:
            self.deflection_failed.emit(message.get("message", "Unknown error"))
        # MSG_HELLO needs no further action beyond connection_changed already firing.
