import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from scheme_handler import register_infinity_scheme

# MUST be called before QApplication is created
register_infinity_scheme()

from browser_window import BrowserWindow

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Infinity")
    app.setOrganizationName("Infinity")
    app.setOrganizationDomain("infinity.browser")

    # Link this process to the .desktop file so GNOME shows the correct
    # icon in the dock/taskbar instead of the generic Python gear icon.
    app.setDesktopFileName("infinity-browser")

    # Set the application icon (used by the window manager / taskbar)
    icon_path = os.path.join(os.path.dirname(__file__), "icons", "infinity-browser.png")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    # Load stylesheet
    style_path = os.path.join(os.path.dirname(__file__), 'styles.qss')
    if os.path.exists(style_path):
        with open(style_path, 'r') as f:
            app.setStyleSheet(f.read())

    window = BrowserWindow()
    window.show()

    sys.exit(app.exec())

if __name__ == '__main__':
    main()
