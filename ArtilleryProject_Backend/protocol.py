"""
Shared JSON socket protocol for the ArtilleryProject backend daemon.

Message shapes must stay in sync with
ArtilleryProject_Frontend/net/backend_client.py, which is the sole consumer
of these messages. Every message is a single JSON object encoded as one
line (newline-delimited) over the TCP socket.
"""

import json

MSG_HELLO = "hello"
MSG_TELEMETRY = "telemetry"
MSG_SNAPSHOT = "snapshot"
MSG_DEFLECTION_RESULT = "deflection_result"
MSG_DEFLECTION_ERROR = "deflection_error"
MSG_SET_TARGET = "set_target"


def encode(message: dict) -> bytes:
    """Serialize a message dict to a newline-terminated JSON line."""
    return (json.dumps(message) + "\n").encode("utf-8")


def hello_message(server_name: str = "IOE Tactical Backend") -> dict:
    return {"type": MSG_HELLO, "server": server_name}


def telemetry_message(gps: dict = None, compass: dict = None, lrf: dict = None) -> dict:
    """Build a MSG_TELEMETRY message. Any sensor not yet wired up can be left
    as None/omitted -- the frontend's TelemetryPanel renders "--" placeholders
    for missing fields."""
    return {
        "type": MSG_TELEMETRY,
        "gps": gps or {},
        "compass": compass or {},
        "lrf": lrf or {},
    }


def deflection_result_message(impact_northing: float, impact_easting: float,
                               lr_meters: float, fb_meters: float) -> dict:
    return {
        "type": MSG_DEFLECTION_RESULT,
        "impact_northing": impact_northing,
        "impact_easting": impact_easting,
        "lr_meters": lr_meters,
        "fb_meters": fb_meters,
    }


def deflection_error_message(reason: str) -> dict:
    return {"type": MSG_DEFLECTION_ERROR, "message": reason}
