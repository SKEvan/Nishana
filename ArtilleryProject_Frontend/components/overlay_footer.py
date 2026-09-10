"""
Footer Bar Overlay for Tactical Fire Direction Dashboard.
Provides real-time system diagnostics and telemetry status readout.
"""

from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel
from PySide6.QtCore import QTimer, Qt
import random

class OverlayFooter(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(28)
        self.setStyleSheet("background-color: #0e0e0e; border-top: 1px solid #353534; padding: 0 16px;")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(20)

        # Status Metrics
        self.log_ticker = QLabel("SYSTEM_INIT: Tactical Fire Direction Engine Active")
        self.log_ticker.setStyleSheet("color: #00e639; font-size: 10px; font-weight: bold;")

        self.lbl_load = QLabel("SYSTEM_LOAD: 12%")
        self.lbl_load.setStyleSheet("color: #b9ccb2; font-size: 10px; opacity: 0.7;")

        self.lbl_latency = QLabel("UI_LATENCY: 0.003ms")
        self.lbl_latency.setStyleSheet("color: #b9ccb2; font-size: 10px; opacity: 0.7;")

        self.lbl_crypto = QLabel("ENCRYPTION: AES-256-GCM")
        self.lbl_crypto.setStyleSheet("color: #b9ccb2; font-size: 10px; opacity: 0.7;")

        layout.addWidget(self.log_ticker)
        layout.addStretch()
        layout.addWidget(self.lbl_load)
        layout.addWidget(self.lbl_latency)
        layout.addWidget(self.lbl_crypto)

        # Live metric simulation
        self.diag_timer = QTimer(self)
        self.diag_timer.timeout.connect(self.update_diagnostics)
        self.diag_timer.start(2000)

    def update_diagnostics(self):
        load = random.randint(10, 18)
        lat = round(random.uniform(0.002, 0.005), 3)
        self.lbl_load.setText(f"SYSTEM_LOAD: {load}%")
        self.lbl_latency.setText(f"UI_LATENCY: {lat:.3f}ms")

    def set_ticker_message(self, msg):
        self.log_ticker.setText(f"EVENT_LOG: {msg}")
