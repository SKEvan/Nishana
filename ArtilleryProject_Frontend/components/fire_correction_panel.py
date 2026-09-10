"""
Fire Correction Commands Panel for Tactical Fire Direction Dashboard.
Provides calculated impact GPS, deflection corrections, range adjustments, fine-tune sliders, and reset logic.
"""

from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSlider, QMessageBox
from PySide6.QtCore import Qt, Signal

class FireCorrectionPanel(QFrame):
    reset_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setProperty("class", "industrial-panel-high")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Title
        header_layout = QHBoxLayout()
        icon = QLabel("🚀")
        icon.setStyleSheet("font-size: 20px;")
        
        title = QLabel("FIRE CORRECTION COMMANDS")
        title.setProperty("class", "panel-header-secondary")
        
        header_layout.addWidget(icon)
        header_layout.addWidget(title)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # 1. Computed Impact GPS
        computed_box = QFrame()
        computed_box.setStyleSheet("background-color: #0e0e0e; border: 2px solid #353534; padding: 12px; border-radius: 4px;")
        comp_layout = QVBoxLayout(computed_box)
        c_title = QLabel("COMPUTED IMPACT GPS")
        c_title.setProperty("class", "label-sub")
        self.computed_val = QLabel("-- / --")
        self.computed_val.setProperty("class", "data-medium")
        self.impact_val = self.computed_val
        comp_layout.addWidget(c_title)
        comp_layout.addWidget(self.computed_val)
        layout.addWidget(computed_box)

        # 2. Deflection Correction Card
        deflect_card = QFrame()
        deflect_card.setStyleSheet("background-color: #1c1b1b; border: 2px solid #353534; padding: 14px; border-radius: 4px;")
        d_layout = QHBoxLayout(deflect_card)
        
        d_info = QVBoxLayout()
        d_title = QLabel("DEFLECTION CORRECTION")
        d_title.setStyleSheet("color: #ffba20; font-size: 10px; font-weight: bold; letter-spacing: 1px;")
        self.deflect_val = QLabel("ON TARGET 0 meters")
        self.deflect_val.setStyleSheet("color: #ffffff; font-size: 18px; font-weight: bold;")
        d_info.addWidget(d_title)
        d_info.addWidget(self.deflect_val)

        d_btn_layout = QHBoxLayout()
        self.btn_left = QPushButton("◄ LEFT")
        self.btn_left.setProperty("class", "btn-secondary")
        self.btn_left.clicked.connect(lambda: self.adjust_deflection(-5))
        
        self.btn_right = QPushButton("RIGHT ►")
        self.btn_right.setProperty("class", "btn-secondary")
        self.btn_right.clicked.connect(lambda: self.adjust_deflection(5))

        d_btn_layout.addWidget(self.btn_left)
        d_btn_layout.addWidget(self.btn_right)

        d_layout.addLayout(d_info)
        d_layout.addStretch()
        d_layout.addLayout(d_btn_layout)
        layout.addWidget(deflect_card)

        # 3. Range Correction Card
        range_card = QFrame()
        range_card.setStyleSheet("background-color: #1c1b1b; border: 2px solid #353534; padding: 14px; border-radius: 4px;")
        r_layout = QHBoxLayout(range_card)
        
        r_info = QVBoxLayout()
        r_title = QLabel("RANGE CORRECTION")
        r_title.setStyleSheet("color: #ffba20; font-size: 10px; font-weight: bold; letter-spacing: 1px;")
        self.range_val = QLabel("ON RANGE 0 meters")
        self.range_val.setStyleSheet("color: #ffffff; font-size: 18px; font-weight: bold;")
        r_info.addWidget(r_title)
        r_info.addWidget(self.range_val)

        r_btn_layout = QHBoxLayout()
        self.btn_add = QPushButton("▲ ADD")
        self.btn_add.setProperty("class", "btn-secondary")
        self.btn_add.clicked.connect(lambda: self.adjust_range(10))

        self.btn_drop = QPushButton("▼ DROP")
        self.btn_drop.setProperty("class", "btn-secondary")
        self.btn_drop.clicked.connect(lambda: self.adjust_range(-10))

        r_btn_layout.addWidget(self.btn_add)
        r_btn_layout.addWidget(self.btn_drop)

        r_layout.addLayout(r_info)
        r_layout.addStretch()
        r_layout.addLayout(r_btn_layout)
        layout.addWidget(range_card)

        # 4. Fine Tune Range Slider
        slider_box = QVBoxLayout()
        slider_labels = QHBoxLayout()
        lbl_min = QLabel("-100m")
        lbl_min.setProperty("class", "label-sub")
        lbl_mid = QLabel("FINE TUNE RANGE OFFSET")
        lbl_mid.setProperty("class", "label-sub")
        lbl_max = QLabel("+100m")
        lbl_max.setProperty("class", "label-sub")
        
        slider_labels.addWidget(lbl_min)
        slider_labels.addStretch()
        slider_labels.addWidget(lbl_mid)
        slider_labels.addStretch()
        slider_labels.addWidget(lbl_max)

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(-100, 100)
        self.slider.setValue(0)
        self.slider.valueChanged.connect(self.on_slider_changed)

        self.slider_readout = QLabel("OFFSET: 0m")
        self.slider_readout.setStyleSheet("color: #ffba20; font-size: 12px; font-weight: bold; text-align: center;")
        self.slider_readout.setAlignment(Qt.AlignCenter)

        slider_box.addLayout(slider_labels)
        slider_box.addWidget(self.slider)
        slider_box.addWidget(self.slider_readout)
        layout.addLayout(slider_box)

        layout.addStretch()

        # 5. Clear Data Emergency Button
        self.btn_clear = QPushButton("↺ CLEAR DATA & RESET CORRECTIONS")
        self.btn_clear.setProperty("class", "btn-danger")
        self.btn_clear.clicked.connect(self.confirm_clear_data)
        layout.addWidget(self.btn_clear)

        # State tracking (populated from real backend deflection results; 0 = no data yet)
        self.deflection_meters = 0
        self.range_meters = 0

    def update_deflection_result(self, data):
        """Apply a MSG_DEFLECTION_RESULT message from the backend
        (see ArtilleryProject_Backend/protocol.py)."""
        impact_n = data.get("impact_northing")
        impact_e = data.get("impact_easting")
        if impact_n is not None and impact_e is not None:
            self.computed_val.setText(f"N {impact_n:.2f} / E {impact_e:.2f}")

        lr = data.get("lr_meters")
        if lr is not None:
            self.deflection_meters = round(lr)
            self._refresh_deflection_label()

        fb = data.get("fb_meters")
        if fb is not None:
            self.range_meters = round(fb)
            self._refresh_range_label()

    def show_deflection_unavailable(self, reason):
        """Called when the backend can't provide a deflection yet (e.g. compute_deflection()
        is still a stub in ArtilleryProject_Backend/deflection.py, or no target set)."""
        self.computed_val.setText("-- / --")
        self.deflect_val.setText(f"UNAVAILABLE: {reason}")
        self.range_val.setText("UNAVAILABLE")

    def adjust_deflection(self, delta):
        self.deflection_meters += delta
        self._refresh_deflection_label()

    def adjust_range(self, delta):
        self.range_meters += delta
        self._refresh_range_label()

    def _refresh_deflection_label(self):
        if self.deflection_meters < 0:
            self.deflect_val.setText(f"LEFT {abs(self.deflection_meters)} meters")
        elif self.deflection_meters > 0:
            self.deflect_val.setText(f"RIGHT {self.deflection_meters} meters")
        else:
            self.deflect_val.setText("ON TARGET 0 meters")

    def _refresh_range_label(self):
        if self.range_meters > 0:
            self.range_val.setText(f"ADD {self.range_meters} meters")
        elif self.range_meters < 0:
            self.range_val.setText(f"DROP {abs(self.range_meters)} meters")
        else:
            self.range_val.setText("ON RANGE 0 meters")

    def on_slider_changed(self, value):
        self.slider_readout.setText(f"OFFSET: {value:+d}m")

    def confirm_clear_data(self):
        reply = QMessageBox.question(self, 'Clear Tactical Data',
                                     'Reset all fire corrections and target coordinates?',
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.deflection_meters = 0
            self.range_meters = 0
            self.deflect_val.setText("ON TARGET 0 meters")
            self.range_val.setText("ON RANGE 0 meters")
            self.slider.setValue(0)
            self.computed_val.setText("-- / --")
            self.reset_requested.emit()
