"""
Tactical HUD QSS Stylesheet and Theme Tokens for PySide6 Application.
Strictly matching the Google Stitch IOE TACTICAL HUD v4.2 design palette.
"""

HUD_STYLESHEET = """
/* Global Application Settings - UI default is Inter */
QWidget {
    background-color: #131313;
    color: #e5e2e1;
    font-family: 'Inter', 'Segoe UI', sans-serif;
    font-size: 13px;
    selection-background-color: #00e639;
    selection-color: #131313;
}

QLabel {
    background-color: transparent;
    background: transparent;
    border: none;
}

QMainWindow, QWidget#CentralWidget {
    background-color: #131313;
    color: #e5e2e1;
    font-family: 'Inter', 'Segoe UI', sans-serif;
}

/* Header Bar */
#HeaderBar, QFrame#HeaderBar {
    background-color: #131313;
    border-bottom: 2px solid #353534;
}

#HeaderTitle, QLabel#HeaderTitle {
    color: #00e639;
    font-size: 20px;
    font-weight: 800;
    font-family: 'Inter', sans-serif;
    letter-spacing: -0.5px;
    background-color: transparent;
}

#HeaderIp, QLabel#IPLabel, QLabel#HeaderIp {
    color: #b9ccb2;
    opacity: 0.6;
    font-size: 13px;
    font-family: 'JetBrains Mono', monospace;
    background-color: transparent;
}

#ConnectedBadge, QLabel#StatusLabel {
    color: #00e639;
    font-weight: bold;
    font-size: 12px;
    font-family: 'JetBrains Mono', monospace;
    letter-spacing: 1px;
    background-color: transparent;
}

/* Side Navigation Bar & Rail */
#SideNav, QFrame#SideNavRail {
    background-color: #131313;
    border-right: 2px solid #353534;
}

QPushButton.nav-btn, QPushButton.NavButton {
    background-color: transparent;
    color: #84967e;
    border: none;
    border-left: 4px solid transparent;
    padding: 14px 6px;
    font-size: 11px;
    font-weight: 700;
    font-family: 'JetBrains Mono', monospace;
    text-align: center;
}

QPushButton.nav-btn:hover, QPushButton.NavButton:hover {
    background-color: #353534;
    color: #72ff70;
}

QPushButton.nav-btn:checked, QPushButton.nav-btn.active, QPushButton.NavButton[active="true"] {
    background-color: #201f1f;
    color: #00ff41;
    border-left: 4px solid #00e639;
    font-weight: bold;
}

QPushButton.nav-btn-alarm {
    color: #ffb4ab;
}

QPushButton.nav-btn-alarm:hover {
    background-color: #93000a;
    color: #ffffff;
}

/* Panel Frames & Cards */
QFrame.industrial-panel, QFrame.IndustrialCard {
    background-color: #1c1b1b;
    border: 2px solid #353534;
    border-radius: 2px;
}

QFrame.industrial-panel-active, QFrame.IndustrialCardActive {
    background-color: #201f1f;
    border: 2px solid #00e639;
    border-radius: 2px;
}

QFrame.industrial-panel-high, QFrame.IndustrialCardHigh {
    background-color: #2a2a2a;
    border: 2px solid #353534;
    border-radius: 2px;
}

QFrame.industrial-panel-dark {
    background-color: #0e0e0e;
    border: 2px solid #353534;
    border-radius: 2px;
}

/* Headers & Section Titles */
QLabel.panel-header, QLabel.SectionHeader {
    color: #84967e;
    font-size: 14px;
    font-weight: 800;
    font-family: 'Inter', sans-serif;
    letter-spacing: 1px;
    background-color: transparent;
}

QLabel.SectionHeaderActive {
    color: #00e639;
    font-size: 20px;
    font-weight: 800;
    font-family: 'Inter', sans-serif;
    letter-spacing: -0.3px;
    background-color: transparent;
}

QLabel.panel-header-secondary, QLabel.SectionHeaderAmber {
    color: #ffba20;
    font-size: 20px;
    font-weight: 800;
    font-family: 'Inter', sans-serif;
    letter-spacing: -0.3px;
    background-color: transparent;
}

/* Field Captions & Labels */
QLabel.label-caps, QLabel.FieldCaption {
    color: #84967e;
    font-size: 11px;
    font-weight: 700;
    font-family: 'JetBrains Mono', monospace;
    letter-spacing: 1px;
    background-color: transparent;
}

QLabel.label-sub {
    color: #84967e;
    font-size: 10px;
    font-family: 'JetBrains Mono', monospace;
    letter-spacing: 1px;
    background-color: transparent;
}

QLabel.floating-input-label {
    background-color: transparent;
    background: transparent;
    color: #b9ccb2;
    font-size: 11px;
    font-weight: bold;
    font-family: 'JetBrains Mono', monospace;
    letter-spacing: 1.5px;
    padding: 0px;
    margin: 0px;
}

/* Data Displays */
QLabel.data-large, QLabel.DataGreenLarge {
    color: #00e639;
    font-size: 36px;
    font-weight: 800;
    font-family: 'JetBrains Mono', monospace;
    letter-spacing: 2px;
}

QLabel.data-medium, QLabel.DataGreen {
    color: #00e639;
    font-size: 18px;
    font-weight: 700;
    font-family: 'JetBrains Mono', monospace;
}

QLabel.data-warning, QLabel.DataAmber {
    color: #ffba20;
    font-size: 20px;
    font-weight: 700;
    font-family: 'JetBrains Mono', monospace;
}

/* Inputs & Form Controls */
QLineEdit.tactical-input, QLineEdit.TacticalInput {
    background-color: #1c1b1b;
    border: 2px solid #353534;
    border-radius: 2px;
    color: #00e639;
    font-size: 20px;
    font-weight: bold;
    font-family: 'JetBrains Mono', monospace;
    padding-top: 10px;
    padding-bottom: 10px;
    padding-left: 14px;
    padding-right: 14px;
    letter-spacing: 2px;
    selection-background-color: #00e639;
    selection-color: #131313;
}

QLineEdit.tactical-input:focus, QLineEdit.TacticalInput:focus {
    border: 2px solid #00e639;
    background-color: #201f1f;
}

/* Buttons */
QPushButton.btn-primary, QPushButton.PrimaryTactileButton {
    background-color: #00e639;
    color: #002203;
    font-size: 18px;
    font-weight: bold;
    font-family: 'Inter', sans-serif;
    border: none;
    border-bottom: 4px solid #00530e;
    border-right: 4px solid #00530e;
    border-radius: 4px;
    padding: 14px 20px;
    letter-spacing: 1px;
}

QPushButton.btn-primary:hover, QPushButton.PrimaryTactileButton:hover {
    background-color: #72ff70;
    color: #002203;
}

QPushButton.btn-primary:pressed, QPushButton.PrimaryTactileButton:pressed {
    background-color: #00e639;
    border: none;
}

QPushButton.btn-secondary {
    background-color: #201f1f;
    color: #ffba20;
    font-size: 14px;
    font-weight: bold;
    font-family: 'Inter', sans-serif;
    border: 2px solid #5e4200;
    border-radius: 4px;
    padding: 10px 14px;
}

QPushButton.btn-secondary:hover {
    background-color: #353534;
    color: #ffdea8;
    border-color: #ffba20;
}

QPushButton.btn-danger, QPushButton.DangerButton {
    background-color: transparent;
    color: #ffb4ab;
    font-size: 13px;
    font-weight: bold;
    font-family: 'Inter', sans-serif;
    border: 2px solid #93000a;
    border-radius: 4px;
    padding: 10px 16px;
    letter-spacing: 1px;
}

QPushButton.btn-danger:hover, QPushButton.DangerButton:hover {
    background-color: #93000a;
    color: #ffffff;
}

QPushButton.btn-icon {
    background-color: transparent;
    color: #b9ccb2;
    border: 1px solid #353534;
    border-radius: 4px;
    padding: 6px;
}

QPushButton.btn-icon:hover {
    background-color: #353534;
    color: #00e639;
    border-color: #00e639;
}

/* Sliders */
QSlider::groove:horizontal {
    height: 12px;
    background: #0e0e0e;
    border: 1px solid #353534;
    border-radius: 2px;
}

QSlider::sub-page:horizontal {
    background: #5e4200;
    border-radius: 2px;
}

QSlider::handle:horizontal {
    background: #ffba20;
    border: 2px solid #feb700;
    width: 18px;
    margin-top: -4px;
    margin-bottom: -4px;
    border-radius: 3px;
}

QSlider::handle:horizontal:hover {
    background: #ffdea8;
    border-color: #ffffff;
}

/* Progress Bars */
QProgressBar {
    background-color: #353534;
    border: none;
    height: 6px;
    border-radius: 3px;
    text-align: center;
}

QProgressBar::chunk {
    background-color: #00e639;
    border-radius: 3px;
}

/* Scroll Bars */
QScrollBar:vertical {
    background: #1c1b1b;
    width: 6px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background: #353534;
    min-height: 20px;
    border-radius: 3px;
}

QScrollBar::handle:vertical:hover {
    background: #00e639;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

/* Separator Line */
QFrame[frameShape="4"] { /* HLine */
    color: #353534;
    background-color: #353534;
    height: 1px;
    border: none;
}
"""

DARK_HUD_STYLE = HUD_STYLESHEET


