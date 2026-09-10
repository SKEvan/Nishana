"""
IOE Tactical Fire Direction Dashboard v4.2
Main Application Entry Point using PySide6 (Qt for Python).
"""

import sys
import os
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QStackedWidget, QLabel, QFrame
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QFont, QFontDatabase

from styles import HUD_STYLESHEET
from components.top_bar import TopBar
from components.telemetry_panel import TelemetryPanel
from components.target_panel import TargetPanel
from components.fire_correction_panel import FireCorrectionPanel
from components.overlay_footer import OverlayFooter
from net.backend_client import BackendClient

BACKEND_HOST = "127.0.0.1"
BACKEND_PORT = 5555


class TacticalHUDWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("IOE TACTICAL HUD v4.2 - Fire Direction Command System")
        self.resize(1600, 950)
        self.setMinimumSize(1280, 800)

        # Apply Global QSS Stylesheet
        self.setStyleSheet(HUD_STYLESHEET)

        # Main Central Widget Layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        root_layout = QVBoxLayout(central_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # 1. Top Header Bar
        self.top_bar = TopBar(self)
        root_layout.addWidget(self.top_bar)

        # 2. Main Content Body Area (Sidebar + Grid Content)
        body_layout = QHBoxLayout()
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        # Main 3-Column Dashboard Content Layout
        self.main_content = QWidget()
        content_layout = QHBoxLayout(self.main_content)
        content_layout.setContentsMargins(16, 16, 16, 16)
        content_layout.setSpacing(16)

        # Column 1: Observation Post Telemetry (Equal Width)
        self.telemetry_panel = TelemetryPanel(self)
        content_layout.addWidget(self.telemetry_panel, 1)

        # Column 2: Target Grid Reference (Equal Width)
        self.target_panel = TargetPanel(self)
        content_layout.addWidget(self.target_panel, 1)

        # Column 3: Fire Correction Commands (Equal Width)
        self.fire_panel = FireCorrectionPanel(self)
        content_layout.addWidget(self.fire_panel, 1)

        # Connect Signals between Panels
        self.target_panel.target_acquired.connect(self.on_target_acquired)
        self.fire_panel.reset_requested.connect(self.on_reset_requested)

        body_layout.addWidget(self.main_content)
        root_layout.addLayout(body_layout, 1)

        # 3. Footer Overlay
        self.footer = OverlayFooter(self)
        root_layout.addWidget(self.footer)

        # Backend socket client (ArtilleryProject_Backend daemon)
        self.client = BackendClient(host=BACKEND_HOST, port=BACKEND_PORT)
        self.client.telemetry_received.connect(self.telemetry_panel.update_from_backend)
        self.client.deflection_received.connect(self.fire_panel.update_deflection_result)
        self.client.deflection_failed.connect(self.on_deflection_failed)
        self.client.snapshot_latched.connect(self.on_snapshot_latched)
        self.client.connection_changed.connect(self.on_connection_changed)
        self.client.start()

    def on_target_acquired(self, target_data):
        sent = self.client.send_target(target_data)
        northing = target_data.get('northing')
        easting = target_data.get('easting')
        if sent:
            self.footer.set_ticker_message(f"TARGET SENT: Northing {northing} | Easting {easting}")
        else:
            self.footer.set_ticker_message("TARGET NOT SENT: backend not connected.")

    def on_deflection_failed(self, reason):
        self.fire_panel.show_deflection_unavailable(reason)
        self.footer.set_ticker_message(f"DEFLECTION UNAVAILABLE: {reason}")

    def on_snapshot_latched(self, snapshot_data):
        heading = snapshot_data.get('heading_deg')
        distance = snapshot_data.get('distance_m')
        self.footer.set_ticker_message(f"TRIGGER LATCHED: bearing {heading} | distance {distance}")

    def on_connection_changed(self, connected):
        self.top_bar.set_connection_status(connected, BACKEND_HOST if connected else "")
        if connected:
            self.footer.set_ticker_message("BACKEND LINK ESTABLISHED.")
        else:
            self.footer.set_ticker_message("BACKEND LINK LOST. Retrying...")

    def on_reset_requested(self):
        self.target_panel.reset_target()
        self.footer.set_ticker_message("SYSTEM RESET: Target grid reference & fire corrections cleared.")

    def closeEvent(self, event):
        self.client.stop()
        super().closeEvent(event)


def load_fonts():
    """Register downloaded Inter and JetBrains Mono fonts into Qt Font Database."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    inter_path = os.path.join(base_dir, "fonts", "Inter.ttf")
    jb_path = os.path.join(base_dir, "fonts", "JetBrainsMono.ttf")

    if os.path.exists(inter_path):
        res1 = QFontDatabase.addApplicationFont(inter_path)
        print(f"[FONT LOAD] Inter font registered (ID: {res1})")
    if os.path.exists(jb_path):
        res2 = QFontDatabase.addApplicationFont(jb_path)
        print(f"[FONT LOAD] JetBrains Mono font registered (ID: {res2})")


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("IOE Tactical HUD")

    # Load custom application fonts before applying stylesheet
    load_fonts()

    window = TacticalHUDWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()

