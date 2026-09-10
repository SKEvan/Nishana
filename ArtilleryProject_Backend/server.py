"""
server.py

TCP socket server for the ArtilleryProject backend daemon. Accepts
connections from the PySide6 frontend (see
ArtilleryProject_Frontend/net/backend_client.py), sends it a MSG_HELLO,
then streams newline-delimited JSON messages (telemetry, deflection
results, etc.) to every connected frontend.

Runs on the same Raspberry Pi 5 as the sensors, bound to 0.0.0.0 so it
also accepts connections from a frontend running on a different machine
on the same network -- the frontend just needs BACKEND_HOST pointed at
the Pi's IP in that case.
"""

import json
import socket
import threading

from protocol import encode, hello_message, MSG_SET_TARGET


class BackendServer:
    def __init__(self, host: str = "0.0.0.0", port: int = 5555):
        self._host = host
        self._port = port
        self._server_socket = None
        self._clients = []
        self._clients_lock = threading.Lock()
        self._running = False

    def start(self) -> None:
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server_socket.bind((self._host, self._port))
        self._server_socket.listen(5)
        self._running = True
        threading.Thread(target=self._accept_loop, daemon=True).start()
        print(f"[BACKEND] Listening on {self._host}:{self._port}")

    def _accept_loop(self) -> None:
        while self._running:
            try:
                conn, addr = self._server_socket.accept()
            except OSError:
                break
            print(f"[BACKEND] Frontend connected from {addr}")
            with self._clients_lock:
                self._clients.append(conn)
            try:
                conn.sendall(encode(hello_message()))
            except OSError:
                continue
            threading.Thread(target=self._client_read_loop, args=(conn,), daemon=True).start()

    def _client_read_loop(self, conn: socket.socket) -> None:
        buffer = b""
        try:
            while self._running:
                chunk = conn.recv(4096)
                if not chunk:
                    break
                buffer += chunk
                while b"\n" in buffer:
                    line, buffer = buffer.split(b"\n", 1)
                    line = line.strip()
                    if line:
                        self._handle_incoming(line)
        except OSError:
            pass
        finally:
            with self._clients_lock:
                if conn in self._clients:
                    self._clients.remove(conn)
            conn.close()
            print("[BACKEND] Frontend disconnected")

    def _handle_incoming(self, raw_line: bytes) -> None:
        try:
            message = json.loads(raw_line.decode("utf-8"))
        except json.JSONDecodeError:
            return
        if message.get("type") == MSG_SET_TARGET:
            # Ballistics/deflection engine isn't built yet -- log for now.
            print(f"[BACKEND] Target received (not yet processed): {message}")

    def broadcast(self, message: dict) -> None:
        """Send a message to every currently-connected frontend."""
        payload = encode(message)
        with self._clients_lock:
            dead = []
            for conn in self._clients:
                try:
                    conn.sendall(payload)
                except OSError:
                    dead.append(conn)
            for conn in dead:
                self._clients.remove(conn)

    def stop(self) -> None:
        self._running = False
        if self._server_socket is not None:
            try:
                self._server_socket.close()
            except OSError:
                pass
        with self._clients_lock:
            for conn in self._clients:
                try:
                    conn.close()
                except OSError:
                    pass
            self._clients.clear()
