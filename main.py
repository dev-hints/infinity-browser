import sys
import os


def _configure_web_engine_color_scheme(theme_name: str):
    flags = os.environ.get("QTWEBENGINE_CHROMIUM_FLAGS", "")
    theme = theme_name.lower() if theme_name else "dark"
    preferred = "dark" if theme == "dark" else "light"
    needed_flags = [
        "--disable-features=WebContentsForceDark,AutoDarkMode",
        f"--force-prefers-color-scheme={preferred}",
    ]
    missing_flags = [flag for flag in needed_flags if flag not in flags]
    if missing_flags:
        os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = " ".join([flags, *missing_flags]).strip()

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from scheme_handler import register_infinity_scheme
from settings_manager import SettingsManager
from theme_manager import apply_theme

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

    # Use fixed app themes only (dark default, light optional), independent of OS theme.
    settings = SettingsManager()
    _configure_web_engine_color_scheme(settings.get("ui_theme", "dark"))
    apply_theme(app, settings.get("ui_theme", "dark"))

    window = BrowserWindow()
    window.show()

    sys.exit(app.exec())

if __name__ == '__main__':
    main()
