"""
Target Grid Reference Panel for Tactical Fire Direction Dashboard.
Strictly matching the Google Stitch IOE TACTICAL HUD v4.2 design specification.
"""

from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox, QWidget
)
from PySide6.QtCore import Signal, Qt
try:
    from components.reticle_widget import ReticleWidget
except ModuleNotFoundError:
    try:
        from widgets.reticle_widget import ReticleWidget
    except ModuleNotFoundError:
        from reticle_widget import ReticleWidget



class FloatingInputField(QWidget):
    """Tactical input field widget with crystal clear label header & input box."""
    def __init__(self, label_text, default_value="", placeholder="0000.00", parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # Clear Top Label Header
        self.label = QLabel(label_text)
        self.label.setStyleSheet(
            "color: #b9ccb2; font-size: 11px; font-weight: bold; "
            "font-family: 'JetBrains Mono', monospace; letter-spacing: 1.5px; padding-left: 2px;"
        )

        # Input Box
        self.input_field = QLineEdit(default_value)
        self.input_field.setProperty("class", "tactical-input")
        self.input_field.setPlaceholderText(placeholder)

        layout.addWidget(self.label)
        layout.addWidget(self.input_field)

    def text(self):
        return self.input_field.text()

    def setText(self, val):
        self.input_field.setText(val)



class TargetPanel(QFrame):
    target_acquired = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setProperty("class", "industrial-panel-active")

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(20, 20, 20, 20)
        root_layout.setSpacing(16)

        # 1. Header Bar with Priority Badge
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)

        title_icon = QLabel("🎯")
        title_icon.setStyleSheet("font-size: 22px;")
        
        title_text = QLabel("TARGET GRID REFERENCE")
        title_text.setProperty("class", "panel-header")
        title_text.setStyleSheet("font-size: 18px; font-weight: 800; color: #00e639; font-family: 'Inter', sans-serif;")

        priority_badge = QLabel("⚡ PRIORITY ACQUISITION")
        priority_badge.setStyleSheet(
            "background-color: #00e639; color: #002203; font-weight: bold; "
            "padding: 4px 10px; border-radius: 2px; font-size: 11px; font-family: 'JetBrains Mono', monospace;"
        )

        header_layout.addWidget(title_icon)
        header_layout.addWidget(title_text)
        header_layout.addStretch()
        header_layout.addWidget(priority_badge)
        root_layout.addLayout(header_layout)

        # 2. Vector Reticle Viewport
        self.reticle = ReticleWidget()
        root_layout.addWidget(self.reticle, 1)

        # 3. Form Controls (Northing, Easting, Altitude)
        form_layout = QVBoxLayout()
        form_layout.setSpacing(12)

        self.field_northing = FloatingInputField(
            "TARGET NORTHING", default_value="5024.18", placeholder="0000.00"
        )
        self.field_easting = FloatingInputField(
            "TARGET EASTING", default_value="7891.42", placeholder="0000.00"
        )
        self.field_altitude = FloatingInputField(
            "TARGET ALTITUDE (m)", default_value="485.0", placeholder="000.0"
        )

        # Direct shortcuts for backward compatibility
        self.input_northing = self.field_northing.input_field
        self.input_easting = self.field_easting.input_field
        self.input_altitude = self.field_altitude.input_field

        form_layout.addWidget(self.field_northing)
        form_layout.addWidget(self.field_easting)
        form_layout.addWidget(self.field_altitude)
        root_layout.addLayout(form_layout)

        # 4. Tactile SET TARGET Button
        self.btn_set_target = QPushButton("🎯 SET TARGET & ACQUIRE")
        self.btn_set_target.setProperty("class", "btn-primary")
        self.btn_set_target.setFixedHeight(54)
        self.btn_set_target.setCursor(Qt.PointingHandCursor)
        self.btn_set_target.clicked.connect(self.on_set_target_clicked)
        root_layout.addWidget(self.btn_set_target)

    def on_set_target_clicked(self):
        northing = self.input_northing.text().strip()
        easting = self.input_easting.text().strip()
        altitude = self.input_altitude.text().strip()

        if not northing or not easting or not altitude:
            QMessageBox.warning(
                self, "Invalid Parameters",
                "Please provide complete Northing, Easting, and Altitude grid values."
            )
            return

        # Trigger reticle lock animation state
        self.reticle.set_target_locked(True, northing, easting)

        # Emit signal to notify other panels and footer
        target_info = {
            "northing": northing,
            "easting": easting,
            "altitude": altitude
        }
        self.target_acquired.emit(target_info)

    def reset_target(self):
        self.input_northing.setText("0000.00")
        self.input_easting.setText("0000.00")
        self.input_altitude.setText("000.0")
        self.reticle.set_target_locked(False)


TargetGridPanel = TargetPanel


