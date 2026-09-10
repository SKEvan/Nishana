"""
Tactical Military Radar & Optical Rangefinder Scope Widget (PySide6 QPainter).
Features 360° compass rose, concentric range rings, rotating radar sweep beam with phosphor sector,
dynamic radar contacts/blips, mil-dot stadiametric rangefinder scales, and live target tracking telemetry.
"""

from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QTimer, QPointF, QRectF
from PySide6.QtGui import QPainter, QPen, QColor, QFont, QBrush, QRadialGradient, QConicalGradient
import math
import random


class ReticleWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(320, 300)

        # Animation states
        self.scan_angle = 0.0
        self.is_locked = False
        self.target_text = "[ RADAR ACQUISITION ACTIVE ]"
        self.northing = "5024.18"
        self.easting = "7891.42"
        
        # Simulated radar contacts (polar coordinates: angle_deg, distance_factor 0.2 to 0.9, size)
        self.contacts = [
            {"angle": 42.0, "dist": 0.35, "label": "TGT-01", "size": 6},
            {"angle": 135.0, "dist": 0.65, "label": "TGT-02", "size": 5},
            {"angle": 210.0, "dist": 0.80, "label": "UNKN", "size": 4},
            {"angle": 305.0, "dist": 0.48, "label": "TGT-04", "size": 5},
            {"angle": 185.4, "dist": 0.72, "label": "LOCK-TGT", "size": 8}, # Primary target
        ]

        # Timer for smooth radar scanning animation (~33 FPS)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_scan)
        self.timer.start(30)

        # Pulsating lock animation state
        self.pulse_alpha = 255
        self.pulse_growing = False

    def update_scan(self):
        # Rotate sweep 2.5 degrees per frame
        self.scan_angle = (self.scan_angle + 2.5) % 360.0

        if self.is_locked:
            if self.pulse_growing:
                self.pulse_alpha += 12
                if self.pulse_alpha >= 255:
                    self.pulse_alpha = 255
                    self.pulse_growing = False
            else:
                self.pulse_alpha -= 12
                if self.pulse_alpha <= 90:
                    self.pulse_alpha = 90
                    self.pulse_growing = True

        self.update()

    def set_target_locked(self, locked=True, northing="5024.18", easting="7891.42"):
        self.is_locked = locked
        self.northing = northing
        self.easting = easting
        if locked:
            self.target_text = f"[ TARGET LOCKED: N{northing} / E{easting} ]"
        else:
            self.target_text = "[ RADAR ACQUISITION ACTIVE ]"
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        width = self.width()
        height = self.height()
        cx = width / 2.0
        cy = height / 2.0
                # Use available square space for radar scope with proper padding
        radius = (min(width, height) / 2.0) - 34.0
        if radius < 50:
            return

        # -------------------------------------------------------------
        # 1. Scope Background Chassis & Radial Glow
        # -------------------------------------------------------------
        painter.fillRect(self.rect(), QColor(14, 14, 14))

        # Radial Scope Gradient Fill
        radial_bg = QRadialGradient(QPointF(cx, cy), radius)
        radial_bg.setColorAt(0.0, QColor(8, 28, 12, 230))
        radial_bg.setColorAt(0.7, QColor(4, 18, 7, 240))
        radial_bg.setColorAt(1.0, QColor(2, 8, 3, 255))
        painter.setBrush(QBrush(radial_bg))
        painter.setPen(QPen(QColor(53, 53, 52), 2))
        painter.drawEllipse(QPointF(cx, cy), radius, radius)

        # Outer Metallic Scope Ring
        painter.setPen(QPen(QColor(0, 230, 57, 180), 2))
        painter.drawEllipse(QPointF(cx, cy), radius + 2, radius + 2)

        # -------------------------------------------------------------
        # 2. Concentric Range Rings (500m, 1000m, 1500m, 2000m)
        # -------------------------------------------------------------
        ring_factors = [0.25, 0.50, 0.75, 1.00]
        ring_labels = ["500m", "1000m", "1500m", "2000m"]
        
        pen_ring = QPen(QColor(0, 230, 57, 50 if not self.is_locked else 100), 1, Qt.DashLine if not self.is_locked else Qt.SolidLine)
        painter.setPen(pen_ring)
        painter.setBrush(Qt.NoBrush)

        font_small = QFont("JetBrains Mono", 8, QFont.Bold)
        painter.setFont(font_small)

        for factor, label in zip(ring_factors, ring_labels):
            r = radius * factor
            painter.drawEllipse(QPointF(cx, cy), r, r)
            
            # Distance labels along vertical axis
            painter.setPen(QPen(QColor(132, 150, 126, 160)))
            painter.drawText(QRectF(cx + 4, cy - r - 10, 45, 14), Qt.AlignLeft, label)
            painter.setPen(pen_ring)

        # -------------------------------------------------------------
        # 3. 360° Polar Compass Rose & Tick Marks
        # -------------------------------------------------------------
        cardinals = {0: "N", 45: "NE", 90: "E", 135: "SE", 180: "S", 225: "SW", 270: "W", 315: "NW"}
        
        for deg in range(0, 360, 5):
            rad = math.radians(deg - 90)
            is_major = (deg % 30 == 0)
            is_cardinal = (deg in cardinals)
            
            t_start = radius if not is_major else radius - 6.0
            t_end = radius + (4.0 if is_major else 2.0)
            
            x1 = cx + t_start * math.cos(rad)
            y1 = cy + t_start * math.sin(rad)
            x2 = cx + t_end * math.cos(rad)
            y2 = cy + t_end * math.sin(rad)

            pen_tick = QPen(QColor(0, 230, 57, 220 if is_major else 90), 2 if is_major else 1)
            painter.setPen(pen_tick)
            painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))

            # Cardinal / Degree text cleanly bounded
            if is_cardinal:
                tx = cx + (radius + 12.0) * math.cos(rad)
                ty = cy + (radius + 12.0) * math.sin(rad)
                painter.setPen(QPen(QColor(0, 255, 65, 230)))
                painter.drawText(QRectF(tx - 12, ty - 8, 24, 16), Qt.AlignCenter, cardinals[deg])

        # -------------------------------------------------------------
        # 4. Mil-Dot Stadiametric Rangefinder Crosshairs
        # -------------------------------------------------------------
        pen_cross = QPen(QColor(0, 230, 57, 120), 1, Qt.SolidLine)
        painter.setPen(pen_cross)
        painter.drawLine(QPointF(cx - radius, cy), QPointF(cx + radius, cy))
        painter.drawLine(QPointF(cx, cy - radius), QPointF(cx, cy + radius))

        # Mil-dots along horizontal & vertical axes
        pen_dot = QPen(QColor(0, 230, 57, 220), 3)
        painter.setPen(pen_dot)
        for i in range(1, 7):
            offset = (radius / 7.0) * i
            painter.drawPoint(QPointF(cx + offset, cy))
            painter.drawPoint(QPointF(cx - offset, cy))
            painter.drawPoint(QPointF(cx, cy + offset))
            painter.drawPoint(QPointF(cx, cy - offset))

        # -------------------------------------------------------------
        # 5. Continuous Rotating Radar Sweep Beam & Phosphor Sector
        # -------------------------------------------------------------
        if not self.is_locked:
            sweep_rad = math.radians(self.scan_angle - 90)
            sx = cx + radius * math.cos(sweep_rad)
            sy = cy + radius * math.sin(sweep_rad)

            # Draw 40-degree CRT Phosphor Sector Sweep
            brush_sector = QBrush(QColor(0, 230, 57, 30))
            painter.setBrush(brush_sector)
            painter.setPen(Qt.NoPen)
            rect_scope = QRectF(cx - radius, cy - radius, radius * 2, radius * 2)
            painter.drawPie(rect_scope, int((-self.scan_angle + 90) * 16), int(-40 * 16))

            # Main Leading Radar Beam Line
            pen_beam = QPen(QColor(0, 255, 65, 240), 2)
            painter.setPen(pen_beam)
            painter.drawLine(QPointF(cx, cy), QPointF(sx, sy))

        # -------------------------------------------------------------
        # 6. Tactical Radar Contacts / Blips
        # -------------------------------------------------------------
        for c in self.contacts:
            c_rad = math.radians(c["angle"] - 90)
            c_r = radius * c["dist"]
            bx = cx + c_r * math.cos(c_rad)
            by = cy + c_r * math.sin(c_rad)

            # Check angle distance to sweep line for hit animation
            angle_diff = abs((self.scan_angle - c["angle"]) % 360)
            is_hit = angle_diff < 35.0

            blip_color = QColor(255, 186, 32) if (self.is_locked and c["label"] == "LOCK-TGT") else QColor(0, 230, 57)
            alpha = 255 if (is_hit or self.is_locked) else 140

            # Draw Blip Contact Dot
            painter.setBrush(QBrush(QColor(blip_color.red(), blip_color.green(), blip_color.blue(), alpha)))
            painter.setPen(Qt.NoPen)
            sz = c["size"]
            painter.drawEllipse(QPointF(bx, by), sz, sz)

            # Hit pulse ring
            if is_hit:
                painter.setPen(QPen(QColor(blip_color.red(), blip_color.green(), blip_color.blue(), 180), 1))
                painter.setBrush(Qt.NoBrush)
                painter.drawEllipse(QPointF(bx, by), sz + 4, sz + 4)

            # Contact Label
            painter.setFont(QFont("JetBrains Mono", 7))
            painter.setPen(QPen(QColor(185, 204, 178, 180)))
            painter.drawText(QRectF(bx + 6, by - 6, 50, 12), Qt.AlignLeft, c["label"])

        # -------------------------------------------------------------
        # 7. Locked Target Reticle Bracket (When Target Acquired)
        # -------------------------------------------------------------
        if self.is_locked:
            box_size = radius * 0.45
            pen_lock = QPen(QColor(255, 186, 32, self.pulse_alpha), 2)
            painter.setPen(pen_lock)
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(QRectF(cx - box_size/2, cy - box_size/2, box_size, box_size))

            # Tactile Corner Brackets
            n_len = 14
            painter.setPen(QPen(QColor(0, 230, 57, 255), 3))
            # Top-Left
            painter.drawLine(QPointF(cx - box_size/2, cy - box_size/2), QPointF(cx - box_size/2 + n_len, cy - box_size/2))
            painter.drawLine(QPointF(cx - box_size/2, cy - box_size/2), QPointF(cx - box_size/2, cy - box_size/2 + n_len))
            # Top-Right
            painter.drawLine(QPointF(cx + box_size/2, cy - box_size/2), QPointF(cx + box_size/2 - n_len, cy - box_size/2))
            painter.drawLine(QPointF(cx + box_size/2, cy - box_size/2), QPointF(cx + box_size/2, cy - box_size/2 + n_len))
            # Bottom-Left
            painter.drawLine(QPointF(cx - box_size/2, cy + box_size/2), QPointF(cx - box_size/2 + n_len, cy + box_size/2))
            painter.drawLine(QPointF(cx - box_size/2, cy + box_size/2), QPointF(cx - box_size/2, cy + box_size/2 - n_len))
            # Bottom-Right
            painter.drawLine(QPointF(cx + box_size/2, cy + box_size/2), QPointF(cx + box_size/2 - n_len, cy + box_size/2))
            painter.drawLine(QPointF(cx + box_size/2, cy + box_size/2), QPointF(cx + box_size/2, cy + box_size/2 - n_len))

        # -------------------------------------------------------------
        # 8. Corner Telemetry HUD Overlays (Cleanly Placed & Bounded)
        # -------------------------------------------------------------
        painter.setFont(QFont("JetBrains Mono", 8, QFont.Bold))
        painter.setPen(QPen(QColor(0, 230, 57, 220)))

        # Top-Left HUD: Mode
        painter.drawText(QRectF(10, 10, 140, 18), Qt.AlignLeft, "RADAR: 4.0 GHz")

        # Top-Right HUD: Sweep Speed
        painter.drawText(QRectF(width - 150, 10, 140, 18), Qt.AlignRight, "SWEEP: 60 RPM")

        # Bottom-Left HUD: Live Bearing
        bearing_val = f"BRG: {self.scan_angle:.1f}°"
        painter.drawText(QRectF(10, height - 24, 140, 18), Qt.AlignLeft, bearing_val)

        # Bottom-Right HUD: Range Estimate
        range_val = "RNG: 1450.5m" if not self.is_locked else f"RNG: {self.northing[:4]}m"
        painter.drawText(QRectF(width - 150, height - 24, 140, 18), Qt.AlignRight, range_val)

        # Bottom Center Status Readout Ticker
        painter.setFont(QFont("JetBrains Mono", 9, QFont.Bold))
        status_color = QColor(255, 186, 32, self.pulse_alpha) if self.is_locked else QColor(0, 230, 57, 220)
        painter.setPen(QPen(status_color))
        painter.drawText(QRectF(0, height - 44, width, 18), Qt.AlignCenter, self.target_text)

