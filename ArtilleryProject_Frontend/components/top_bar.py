"""
Top Navigation Header Bar for Tactical Fire Direction Dashboard.
Includes title, pulsating LED connection indicator, IP address, system clock, settings, terminal, and power options.
"""

from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QMessageBox, QDialog, QVBoxLayout, QTextEdit
from PySide6.QtCore import Qt, QTimer, QTime
from PySide6.QtGui import QColor

class TopBar(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("HeaderBar")
        self.setFixedHeight(64)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 0, 20, 0)
        layout.setSpacing(16)

        # Left Section: Title & Connection Status
        title_label = QLabel("IOE TACTICAL HUD v4.2")
        title_label.setObjectName("HeaderTitle")
        
        divider1 = QFrame()
        divider1.setFrameShape(QFrame.VLine)
        divider1.setFixedSize(1, 24)
        divider1.setStyleSheet("background-color: #353534;")

        # Pulsating LED indicator
        self.led_dot = QLabel("●")
        self.led_dot.setStyleSheet("color: #00e639; font-size: 16px;")

        self.conn_label = QLabel("CONNECTING...")
        self.conn_label.setObjectName("ConnectedBadge")

        self.ip_label = QLabel("")
        self.ip_label.setObjectName("HeaderIp")

        layout.addWidget(title_label)
        layout.addWidget(divider1)
        layout.addWidget(self.led_dot)
        layout.addWidget(self.conn_label)
        layout.addWidget(self.ip_label)

        self._connected = False

        layout.addStretch()

        # Center Section: Real-time System Clock
        self.clock_label = QLabel()
        self.clock_label.setStyleSheet("color: #00e639; font-size: 16px; font-weight: bold; letter-spacing: 2px;")
        layout.addWidget(self.clock_label)

        layout.addStretch()

        # Right Section: Action Buttons
        self.btn_settings = QPushButton("⚙ SETTINGS")
        self.btn_settings.setProperty("class", "btn-icon")
        self.btn_settings.setStyleSheet("color: #b9ccb2; border: 1px solid #353534; padding: 6px 12px; border-radius: 4px;")
        self.btn_settings.clicked.connect(self.show_settings_dialog)

        self.btn_terminal = QPushButton("💻 TERMINAL")
        self.btn_terminal.setStyleSheet("color: #b9ccb2; border: 1px solid #353534; padding: 6px 12px; border-radius: 4px;")
        self.btn_terminal.clicked.connect(self.show_terminal_dialog)

        self.btn_power = QPushButton("⏻ SHUTDOWN")
        self.btn_power.setStyleSheet("color: #ffb4ab; border: 1px solid #93000a; background: #351313; padding: 6px 12px; border-radius: 4px; font-weight: bold;")
        self.btn_power.clicked.connect(self.confirm_exit)

        layout.addWidget(self.btn_settings)
        layout.addWidget(self.btn_terminal)
        layout.addWidget(self.btn_power)

        # LED Flicker Animation Timer
        self.flicker_timer = QTimer(self)
        self.flicker_timer.timeout.connect(self.flicker_led)
        self.flicker_timer.start(200)

        # Clock Timer
        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self.update_clock)
        self.clock_timer.start(1000)
        self.update_clock()

        self.led_state = True

    def update_clock(self):
        self.clock_label.setText(QTime.currentTime().toString("HH:mm:ss t"))

    def flicker_led(self):
        import random
        if not self._connected:
            self.led_dot.setStyleSheet("color: #ffb4ab; font-size: 16px;")
            return
        if random.random() > 0.92:
            self.led_dot.setStyleSheet("color: #007117; font-size: 16px;")
        else:
            self.led_dot.setStyleSheet("color: #00e639; font-size: 16px;")

    def set_connection_status(self, connected: bool, ip: str = ""):
        """Reflect the real BackendClient socket connection state instead of the
        previously-hardcoded 'CONNECTED' label."""
        self._connected = connected
        if connected:
            self.conn_label.setText("CONNECTED")
            self.conn_label.setStyleSheet("color: #00e639; font-weight: bold; font-size: 12px; font-family: 'JetBrains Mono', monospace; letter-spacing: 1px; background-color: transparent;")
        else:
            self.conn_label.setText("DISCONNECTED")
            self.conn_label.setStyleSheet("color: #ffb4ab; font-weight: bold; font-size: 12px; font-family: 'JetBrains Mono', monospace; letter-spacing: 1px; background-color: transparent;")
        self.ip_label.setText(ip)

    def show_settings_dialog(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("HUD System Settings")
        dlg.setMinimumSize(400, 300)
        dlg.setStyleSheet("background-color: #1c1b1b; color: #e5e2e1;")
        l = QVBoxLayout(dlg)
        lbl = QLabel("⚙ OPERATIONAL CONFIGURATION\n\n- Stream Encryption: AES-256-GCM Enabled\n- Telemetry Frequency: 60Hz\n- Target Coordinate System: MGRS / WGS-84\n- Laser Rangefinder Calibration: Active")
        lbl.setStyleSheet("font-size: 14px; line-height: 1.5; color: #00e639;")
        l.addWidget(lbl)
        btn = QPushButton("CLOSE", dlg)
        btn.setStyleSheet("background-color: #00e639; color: #002203; font-weight: bold; padding: 8px;")
        btn.clicked.connect(dlg.accept)
        l.addWidget(btn)
        dlg.exec()

    def show_terminal_dialog(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("IOE Tactical Terminal v4.2")
        dlg.setMinimumSize(500, 350)
        dlg.setStyleSheet("background-color: #0e0e0e; color: #00e639;")
        l = QVBoxLayout(dlg)
        txt = QTextEdit(dlg)
        txt.setReadOnly(True)
        txt.setText("[SYS_INIT] Tactical Fire Direction Command Initialized...\n[NET_LINK] Connected to 192.168.1.15 via SECURE_LINK_04\n[GPS_ACQ] Lock acquired: 45.1234N / -122.5678W\n[RADAR_DISP] Scan frequency calibrated at 4.0s per revolution\n[BALLISTICS_ENGINE] Ready for target grid assignment.\n>")
        txt.setStyleSheet("background-color: #0e0e0e; color: #00e639; font-family: monospace; font-size: 12px;")
        l.addWidget(txt)
        btn = QPushButton("DISMISS", dlg)
        btn.setStyleSheet("background-color: #353534; color: #00e639; padding: 6px;")
        btn.clicked.connect(dlg.accept)
        l.addWidget(btn)
        dlg.exec()

    def confirm_exit(self):
        reply = QMessageBox.question(self, 'Power Off Confirmation', 
                                     'Are you sure you want to terminate the Tactical HUD session?',
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.window().close()
