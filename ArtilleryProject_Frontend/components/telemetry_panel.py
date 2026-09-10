"""
Observation Post Telemetry Panel for Tactical Fire Direction Dashboard.
Provides real-time GPS, Azimuth compass, pitch/roll, laser rangefinder, and hardware lock indicators.
"""

from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar, QPushButton, QWidget
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QPainter, QPen, QColor

class AzimuthDial(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(54, 54)
        self.azimuth_angle = 185.4

    def set_azimuth(self, angle):
        self.azimuth_angle = angle
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Dial Circle
        painter.setPen(QPen(QColor(53, 53, 52), 2))
        painter.setBrush(QColor(28, 27, 27))
        painter.drawEllipse(3, 3, 48, 48)

        # Needle
        painter.translate(27, 27)
        painter.rotate(self.azimuth_angle)
        painter.setPen(QPen(QColor(0, 230, 57), 2))
        painter.drawLine(QPointF(0, 0), QPointF(0, -18))

        # South Indicator Label
        painter.rotate(-self.azimuth_angle)
        painter.setPen(QPen(QColor(185, 204, 178)))
        font = painter.font()
        font.setPointSize(8)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(self.rect().adjusted(-27, -27, -27, -27), Qt.AlignCenter, "S")

class TelemetryPanel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setProperty("class", "industrial-panel")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Top-left accent bar
        accent_bar = QFrame()
        accent_bar.setFixedSize(16, 4)
        accent_bar.setStyleSheet("background-color: #00e639; border: none;")
        layout.addWidget(accent_bar)

        # Title
        header_layout = QHBoxLayout()
        title = QLabel("OBSERVATION POST TELEMETRY")
        title.setProperty("class", "label-caps")
        title.setStyleSheet("color: #b9ccb2; font-size: 11px; font-weight: bold; font-family: 'JetBrains Mono', monospace; letter-spacing: 1px;")
        header_layout.addWidget(title)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # 1. GPS Coordinates
        gps_title = QLabel("GPS COORDINATES")
        gps_title.setProperty("class", "label-sub")
        layout.addWidget(gps_title)

        self.lat_label = QLabel("LAT: 45.1234")
        self.lat_label.setProperty("class", "data-medium")
        self.lon_label = QLabel("LON: -122.5678")
        self.lon_label.setProperty("class", "data-medium")
        self.alt_label = QLabel("ALT: 450m")
        self.alt_label.setStyleSheet("color: #b9ccb2; font-size: 14px; font-weight: bold;")

        layout.addWidget(self.lat_label)
        layout.addWidget(self.lon_label)
        layout.addWidget(self.alt_label)

        # Separator Line
        sep1 = QFrame()
        sep1.setFrameShape(QFrame.HLine)
        sep1.setStyleSheet("background-color: #353534;")
        layout.addWidget(sep1)

        # 2. Azimuth Compass
        azimuth_layout = QHBoxLayout()
        az_info_layout = QVBoxLayout()
        az_title = QLabel("AZIMUTH")
        az_title.setProperty("class", "label-sub")
        self.az_val = QLabel("185.4°")
        self.az_val.setProperty("class", "data-medium")
        az_info_layout.addWidget(az_title)
        az_info_layout.addWidget(self.az_val)

        self.dial = AzimuthDial()
        azimuth_layout.addLayout(az_info_layout)
        azimuth_layout.addStretch()
        azimuth_layout.addWidget(self.dial)
        layout.addLayout(azimuth_layout)

        # 3. Pitch & Roll Readouts
        pitch_roll_layout = QHBoxLayout()
        
        pitch_box = QVBoxLayout()
        p_title = QLabel("PITCH")
        p_title.setProperty("class", "label-sub")
        self.p_val = QLabel("2.1°")
        self.p_val.setProperty("class", "data-medium")
        pitch_box.addWidget(p_title)
        pitch_box.addWidget(self.p_val)

        roll_box = QVBoxLayout()
        r_title = QLabel("ROLL")
        r_title.setProperty("class", "label-sub")
        self.r_val = QLabel("-0.5°")
        self.r_val.setProperty("class", "data-medium")
        roll_box.addWidget(r_title)
        roll_box.addWidget(self.r_val)

        pitch_roll_layout.addLayout(pitch_box)
        pitch_roll_layout.addLayout(roll_box)
        layout.addLayout(pitch_roll_layout)

        # Separator Line
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.HLine)
        sep2.setStyleSheet("background-color: #353534;")
        layout.addWidget(sep2)

        # 4. Laser Distance
        laser_box = QFrame()
        laser_box.setStyleSheet("background-color: #2a2a2a; border: 1px solid #00e639; border-radius: 4px; padding: 8px;")
        l_layout = QVBoxLayout(laser_box)
        l_title = QLabel("LASER DISTANCE")
        l_title.setStyleSheet("color: #00e639; font-size: 10px; font-weight: bold; letter-spacing: 1px;")
        self.l_val = QLabel("1450.5 m")
        self.l_val.setProperty("class", "data-large")
        l_layout.addWidget(l_title)
        l_layout.addWidget(self.l_val)
        layout.addWidget(laser_box)

        # 5. Hardware Lock Status
        self.lock_btn = QPushButton("🔒 HARDWARE LOCK: ACTIVE")
        self.lock_btn.setStyleSheet("background-color: #201f1f; color: #00e639; border: 2px solid #00e639; padding: 10px; font-weight: bold; text-align: center; border-radius: 4px;")
        self.lock_btn.setCheckable(True)
        self.lock_btn.setChecked(True)
        self.lock_btn.clicked.connect(self.toggle_hardware_lock)
        layout.addWidget(self.lock_btn)

        layout.addStretch()

    def toggle_hardware_lock(self):
        if self.lock_btn.isChecked():
            self.lock_btn.setText("🔒 HARDWARE LOCK: ACTIVE")
            self.lock_btn.setStyleSheet("background-color: #201f1f; color: #00e639; border: 2px solid #00e639; padding: 10px; font-weight: bold; text-align: center; border-radius: 4px;")
        else:
            self.lock_btn.setText("🔓 HARDWARE LOCK: UNLOCKED")
            self.lock_btn.setStyleSheet("background-color: #351313; color: #ffb4ab; border: 2px solid #93000a; padding: 10px; font-weight: bold; text-align: center; border-radius: 4px;")

    def update_from_backend(self, telemetry: dict):
        """Apply a {"gps": {...}, "compass": {...}, "lrf": {...}} telemetry message
        (see ArtilleryProject_Backend/protocol.py MSG_TELEMETRY) to the live readouts."""
        gps = telemetry.get("gps") or {}
        compass = telemetry.get("compass") or {}
        lrf = telemetry.get("lrf") or {}

        if gps.get("fix_quality", 0) > 0:
            lat = gps.get("latitude")
            lon = gps.get("longitude")
            alt = gps.get("altitude_m")
            self.lat_label.setText(f"LAT: {lat:.4f}" if lat is not None else "LAT: --")
            self.lon_label.setText(f"LON: {lon:.4f}" if lon is not None else "LON: --")
            self.alt_label.setText(f"ALT: {alt:.0f}m" if alt is not None else "ALT: --")
        else:
            self.lat_label.setText("LAT: NO FIX")
            self.lon_label.setText("LON: NO FIX")
            self.alt_label.setText("ALT: --")

        heading = compass.get("heading_deg")
        if heading is not None:
            self.az_val.setText(f"{heading:.1f}°")
            self.dial.set_azimuth(heading)
        else:
            self.az_val.setText("--°")

        pitch = compass.get("pitch_deg")
        self.p_val.setText(f"{pitch:.1f}°" if pitch is not None else "--°")

        roll = compass.get("roll_deg")
        self.r_val.setText(f"{roll:.1f}°" if roll is not None else "--°")

        if lrf.get("valid"):
            distance = lrf.get("distance_m")
            self.l_val.setText(f"{distance:.1f} m" if distance is not None else "-- m")
        else:
            self.l_val.setText("-- m")

        has_lock = gps.get("fix_quality", 0) > 0 and lrf.get("valid", False)
        self.lock_btn.setChecked(has_lock)
        self.toggle_hardware_lock()
