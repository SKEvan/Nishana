"""
Test script to instantiate TacticalHUDWindow in offscreen mode to verify layout and signal integrity.
"""

import sys
import os

os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PySide6.QtWidgets import QApplication
from main import TacticalHUDWindow

def test_instantiation():
    app = QApplication(sys.argv)
    win = TacticalHUDWindow()
    assert win is not None
    assert win.top_bar is not None
    assert win.target_panel is not None
    assert win.fire_panel is not None
    assert win.telemetry_panel is not None
    print("SUCCESS: PySide6 Tactical Fire Direction Dashboard instantiated perfectly!")

if __name__ == "__main__":
    test_instantiation()
