import time

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSizePolicy, QMenu, QDialog, QFrame, QProgressBar, QFileDialog,
    QTabWidget, QScrollArea, QApplication
)
from PyQt6.QtGui import QAction, QFont, QKeySequence, QShortcut
from PyQt6.QtCore import Qt, QPoint, QTimer, QUrl, QEvent, QSize

from icon_utils import themed_icon
from navigation_bar import NavigationBar
from tab_manager import TabManager
from settings_manager import SettingsManager
from settings_dialog import SettingsDialog
from password_manager import PasswordManager, PasswordManagerDialog
from history_manager import HistoryManager, HistoryDialog
from bookmark_manager import BookmarkManager, BookmarkDialog
from download_manager import DownloadManager
from ad_blocker import AdBlocker
from notes_manager import NotesManager, NotesDialog
from theme_manager import render_template, theme_from_widget
from youtube_downloader import YouTubeDownloaderDialog, is_youtube_url
from qr_generator import QRGeneratorDialog

ABOUT_STYLE = """
QDialog { background-color: {{surface}}; color: {{text}}; }
QTabWidget::pane {
    border: 1px solid {{border_soft}};
    border-radius: 0 8px 8px 8px;
    background-color: {{surface}};
    top: -1px;
}
QTabBar::tab {
    background-color: {{surface_alt}};
    color: {{text_muted}};
    border: none;
    padding: 8px 20px;
    margin-right: 2px;
    border-radius: 6px 6px 0 0;
    font-weight: bold;
    font-size: 12px;
}
QTabBar::tab:selected { background-color: {{accent}}; color: #ffffff; }
QTabBar::tab:hover:!selected { background-color: {{border_soft}}; color: {{text}}; }
QLabel { color: {{text_soft}}; }
QFrame#HSep { background-color: {{border_soft}}; max-height: 1px; }
QPushButton {
    background-color: {{border_soft}}; color: {{text}};
    border: none; padding: 7px 20px;
    border-radius: 6px; font-weight: bold;
}
QPushButton:hover { background-color: {{border}}; }
QScrollArea, QScrollArea > QWidget, QScrollArea > QWidget > QWidget {
    border: none;
    background: {{surface}};
}
QScrollBar:vertical {
    background: {{surface}}; width: 6px; border-radius: 3px;
}
QScrollBar::handle:vertical {
    background: {{border}}; border-radius: 3px; min-height: 20px;
}
"""

class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About Infinity Browser")
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)
        self.resize(580, 520)
        self.theme = theme_from_widget(self)
        self.setStyleSheet(render_template(ABOUT_STYLE, self.theme))

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Hero banner ──────────────────────────────────────────────────────
        banner = QWidget()
        banner.setStyleSheet(render_template(
            "background: qlineargradient(x1:0,y1:0,x2:1,y2:1,"
            "stop:0 {{surface}}, stop:0.5 {{surface_alt}}, stop:1 {{surface}});"
            "border-bottom: 1px solid {{border_soft}};",
            self.theme,
        ))
        banner_lay = QHBoxLayout(banner)
        banner_lay.setContentsMargins(28, 22, 28, 22)
        banner_lay.setSpacing(20)

        logo = QLabel()
        logo.setPixmap(themed_icon("app", self.theme, "accent", 72).pixmap(72, 72))
        logo.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        banner_lay.addWidget(logo)

        txt_col = QVBoxLayout()
        txt_col.setSpacing(4)
        name = QLabel("Infinity Browser")
        name.setStyleSheet(render_template("font-size: 26px; font-weight: bold; color: {{text}}; letter-spacing: 1px;", self.theme))
        ver = QLabel("Version 1.0.0  ·  Official Release  ·  64-bit")
        ver.setStyleSheet(render_template("font-size: 12px; color: {{text_muted}}; letter-spacing: 0.5px;", self.theme))
        tagline = QLabel("Fast. Private. Yours.")
        tagline.setStyleSheet(render_template("font-size: 13px; color: {{accent}}; font-style: italic; margin-top: 2px;", self.theme))
        txt_col.addWidget(name)
        txt_col.addWidget(ver)
        txt_col.addWidget(tagline)
        banner_lay.addLayout(txt_col)
        banner_lay.addStretch()
        root.addWidget(banner)

        # ── Tabs ─────────────────────────────────────────────────────────────
        tabs = QTabWidget()
        tabs.setContentsMargins(0, 0, 0, 0)
        tabs.addTab(self._about_tab(),   "About")
        tabs.addTab(self._release_tab(), "Release Notes")
        tabs.addTab(self._privacy_tab(), "Privacy Policy")
        root.addWidget(tabs, stretch=1)

        # ── Footer ───────────────────────────────────────────────────────────
        footer = QWidget()
        footer.setStyleSheet(render_template("border-top: 1px solid {{border_soft}}; background-color: {{surface}};", self.theme))
        foot_lay = QHBoxLayout(footer)
        foot_lay.setContentsMargins(20, 12, 20, 12)
        copy = QLabel("© 2026 Infinity Browser Project. All rights reserved.")
        copy.setStyleSheet(render_template("font-size: 11px; color: {{text_muted}};", self.theme))
        foot_lay.addWidget(copy)
        foot_lay.addStretch()
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        foot_lay.addWidget(close_btn)
        root.addWidget(footer)

    # ── About tab ─────────────────────────────────────────────────────────────
    def _about_tab(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(24, 20, 24, 20)
        lay.setSpacing(16)

        def section(title, body, link=None, link_label=None):
            box = QWidget()
            vl = QVBoxLayout(box)
            vl.setSpacing(6)
            vl.setContentsMargins(0, 0, 0, 0)
            t = QLabel(title)
            t.setStyleSheet(render_template(
                "font-size: 11px; font-weight: bold; color: {{accent}};"
                "text-transform: uppercase; letter-spacing: 1px;",
                self.theme,
            ))
            vl.addWidget(t)
            body_color = render_template("{{text_soft}}", self.theme)
            b = QLabel(f"<span style='color:{body_color};'>{body}</span>")
            b.setStyleSheet(f"font-size: 13px; color: {body_color}; line-height: 1.6;")
            b.setWordWrap(True)
            b.setTextFormat(Qt.TextFormat.RichText)
            vl.addWidget(b)
            if link:
                link_style = render_template("color:{{link}};text-decoration:none;", self.theme)
                lbl = QLabel(f'<a href="{link}" style="{link_style}">'
                             f'{link_label or link}</a>')
                lbl.setOpenExternalLinks(True)
                lbl.setStyleSheet(render_template("font-size: 12px; color: {{link}};", self.theme))
                vl.addWidget(lbl)
            return box

        lay.addWidget(section(
            "About",
            "Infinity is a modern, privacy-focused desktop web browser built for speed, "
            "simplicity, and user control. It delivers a clean browsing experience with "
            "built-in ad blocking, a secure password vault, smart download management, "
            "and a fully customizable interface — all without sending your data to any server."
        ))
        lay.addWidget(self._hsep())
        lay.addWidget(section(
            "Technology Stack",
            "<b>Rendering Engine:</b> Chromium / Blink (via QtWebEngine)<br>"
            "<b>Media Backend:</b> FFmpeg 7.x (built-in codec support)<br>"
            "<b>UI Framework:</b> PyQt6 6.x (Qt 6.7 LTS)<br>"
            "<b>Platform:</b> Linux (x86-64)"
        ))
        lay.addWidget(self._hsep())
        lay.addWidget(section(
            "Developer",
            "<b>StrangeInfinity</b><br>"
            "Independent software developer passionate about open-source tooling, "
            "privacy-respecting software, and native Linux applications.",
            "https://github.com/StrangeInfinity",
            "github.com/StrangeInfinity"
        ))
        lay.addWidget(self._hsep())
        lay.addWidget(section(
            "License",
            "Infinity Browser is released as an open-source project. "
            "The source code is available on GitHub under the MIT License. "
            "Third-party components (Qt, Chromium, FFmpeg) are used in accordance "
            "with their respective open-source licenses."
        ))
        lay.addStretch()
        return self._scroll(w)

    # ── Release Notes tab ─────────────────────────────────────────────────────
    def _release_tab(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(24, 20, 24, 20)
        lay.setSpacing(14)

        def entry(version, date, items):
            box = QWidget()
            vl = QVBoxLayout(box)
            vl.setSpacing(6)
            vl.setContentsMargins(0, 0, 0, 0)
            hdr_meta_color = render_template("{{text_muted}}", self.theme)
            hdr = QLabel(f"{version}  <span style='color:{hdr_meta_color};font-size:11px;'>— {date}</span>")
            hdr.setStyleSheet(render_template("font-size: 14px; font-weight: bold; color: {{accent}};", self.theme))
            hdr.setTextFormat(Qt.TextFormat.RichText)
            vl.addWidget(hdr)
            for item in items:
                bullet = QLabel(f"  • {item}")
                bullet.setStyleSheet(render_template("font-size: 13px; color: {{text_soft}};", self.theme))
                bullet.setWordWrap(True)
                vl.addWidget(bullet)
            return box

        lay.addWidget(entry("v1.0.0", "April 2026", [
            "Initial public release of Infinity Browser",
            "Chromium-based rendering engine via QtWebEngine",
            "Built-in ad blocker with rule-based URL interception",
            "Secure local password vault (PBKDF2-HMAC-SHA256 encrypted, owner-only file permissions)",
            "Smart download manager with live speed and progress tracking",
            "Custom infinity:// URL scheme for internal pages",
            "Full keyboard shortcut support (Ctrl+T/W/H/B/O/P/J/L/R)",
            "Tabbed browsing with drag-and-drop tab reordering",
            "Bookmark manager with live search filter",
            "Browsing history with full search capability",
            "PDF viewer via native Chromium PDF plugin",
            "Local file opener (Ctrl+O) with format-aware file dialog",
            "Browser fullscreen toggle (F11) and site video fullscreen support",
            "Built-in QR generator for the current page, websites, and text",
            "Comprehensive settings: Privacy, Security, Appearance, Downloads",
            "Frameless window with custom title bar and system controls",
        ]))
        lay.addStretch()
        return self._scroll(w)

    # ── Privacy Policy tab ────────────────────────────────────────────────────
    def _privacy_tab(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(24, 20, 24, 20)
        lay.setSpacing(14)

        def policy_section(title, body):
            box = QWidget()
            vl = QVBoxLayout(box)
            vl.setSpacing(5)
            vl.setContentsMargins(0, 0, 0, 0)
            t = QLabel(title)
            t.setStyleSheet(render_template(
                "font-size: 12px; font-weight: bold; color: {{accent}};"
                "letter-spacing: 0.5px;",
                self.theme,
            ))
            body_color = render_template("{{text_soft}}", self.theme)
            b = QLabel(f"<span style='color:{body_color};'>{body}</span>")
            b.setStyleSheet(f"font-size: 13px; color: {body_color}; line-height: 1.6;")
            b.setWordWrap(True)
            b.setTextFormat(Qt.TextFormat.RichText)
            vl.addWidget(t)
            vl.addWidget(b)
            return box

        eff_label = QLabel("Effective Date: April 2026  ·  Version 1.0")
        eff_label.setStyleSheet(render_template("font-size: 11px; color: {{text_muted}}; margin-bottom: 4px;", self.theme))
        lay.addWidget(eff_label)
        lay.addWidget(self._hsep())

        lay.addWidget(policy_section(
            "1. Data Collection",
            "Infinity Browser does <b>not collect, transmit, or sell any personal data</b>. "
            "We do not operate any servers, analytics services, or telemetry pipelines. "
            "All data generated during your browsing session — including history, bookmarks, "
            "passwords, and settings — is stored exclusively on your local device."
        ))
        lay.addWidget(self._hsep())
        lay.addWidget(policy_section(
            "2. Browsing History",
            "Your browsing history is stored locally in <code>history.json</code> inside the "
            "application directory. It is never uploaded or shared. You may clear your history "
            "at any time from <b>Settings → Privacy → Clear History</b>."
        ))
        lay.addWidget(self._hsep())
        lay.addWidget(policy_section(
            "3. Passwords & Credentials",
            "Passwords saved in Infinity are encrypted using a PBKDF2-HMAC-SHA256 derived key "
            "with per-entry random nonces and HMAC-SHA256 message authentication. "
            "The encryption key is stored in a local key file (<code>.vault.key</code>) with owner-only "
            "file permissions (chmod 600). Passwords are never transmitted to any external service."
        ))
        lay.addWidget(self._hsep())
        lay.addWidget(policy_section(
            "4. Cookies & Site Data",
            "Cookies and site storage are managed by the embedded Chromium engine and stored "
            "locally in your browser profile directory. Infinity does not read or process these "
            "cookies. You may clear all site data at any time from Settings → Privacy."
        ))
        lay.addWidget(self._hsep())
        lay.addWidget(policy_section(
            "5. Third-Party Websites",
            "When you visit websites, those sites may collect data according to their own "
            "privacy policies. Infinity's built-in ad blocker helps reduce third-party tracking "
            "by blocking known tracker domains and ad networks."
        ))
        lay.addWidget(self._hsep())
        lay.addWidget(policy_section(
            "6. Search Engines",
            "Search queries typed in the URL bar or the new tab page are sent directly to your "
            "chosen search engine (Google, DuckDuckGo, Bing, Ecosia, or Brave Search). "
            "Infinity does not intercept, log, or modify these queries."
        ))
        lay.addWidget(self._hsep())
        lay.addWidget(policy_section(
            "7. Updates",
            "This Privacy Policy may be updated in future releases of Infinity Browser. "
            "Changes will be reflected in the Release Notes and this dialog."
        ))
        lay.addStretch()
        return self._scroll(w)

    def _hsep(self):
        f = QFrame()
        f.setObjectName("HSep")
        f.setFrameShape(QFrame.Shape.HLine)
        return f

    def _scroll(self, widget):
        from PyQt6.QtWidgets import QScrollArea
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(widget)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        return scroll



class TitleBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("TitleBar")
        self.setAutoFillBackground(True)
        self.parent = parent
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        # Title Label
        self.app_icon = QLabel()
        self.app_icon.setObjectName("TitleAppIcon")
        self.app_icon.setPixmap(themed_icon("app", theme_from_widget(self), "accent").pixmap(18, 18))
        self.layout.addWidget(self.app_icon)

        self.title_label = QLabel("Infinity")
        self.title_label.setObjectName("TitleLabel")
        self.layout.addWidget(self.title_label)
        
        self.layout.addStretch()
        
        # Window Controls
        self.min_btn = QPushButton()
        self.min_btn.setObjectName("TitleButton")
        self.min_btn.setIcon(themed_icon("minus", theme_from_widget(self)))
        self.min_btn.setIconSize(QSize(14, 14))
        self.min_btn.clicked.connect(self.parent.showMinimized)
        self.layout.addWidget(self.min_btn)
        
        self.max_btn = QPushButton()
        self.max_btn.setObjectName("TitleButton")
        self.max_btn.setIcon(themed_icon("maximize", theme_from_widget(self)))
        self.max_btn.setIconSize(QSize(14, 14))
        self.max_btn.clicked.connect(self.toggle_max_restore)
        self.layout.addWidget(self.max_btn)
        
        self.close_btn = QPushButton()
        self.close_btn.setObjectName("TitleButton")
        self.close_btn.setIcon(themed_icon("close", theme_from_widget(self)))
        self.close_btn.setIconSize(QSize(14, 14))
        self.close_btn.setProperty("class", "CloseButton")
        self.close_btn.clicked.connect(self.parent.close)
        self.layout.addWidget(self.close_btn)
        
        self.drag_pos = None

    def refresh_icons(self):
        theme = theme_from_widget(self)
        self.app_icon.setPixmap(themed_icon("app", theme, "accent").pixmap(18, 18))
        self.min_btn.setIcon(themed_icon("minus", theme))
        self.max_btn.setIcon(themed_icon("maximize", theme))
        self.close_btn.setIcon(themed_icon("close", theme))

    def toggle_max_restore(self):
        if self.parent.isMaximized():
            self.parent.showNormal()
        else:
            self.parent.showMaximized()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            window = self.parent.windowHandle()
            if window:
                window.startSystemMove()
            event.accept()

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.toggle_max_restore()

class BrowserWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Infinity")
        self.settings_manager = SettingsManager()
        self._use_system_title_bar = bool(self.settings_manager.get("use_system_title_bar"))
        
        # Setup window chrome
        if self._use_system_title_bar:
            self.setWindowFlags(Qt.WindowType.Window)
            self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        else:
            self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
            self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.resize(1200, 800)
        self._browser_fullscreen = False
        self._web_fullscreen_tab = None
        self._web_fullscreen_started_from_browser_fullscreen = False
        self._was_maximized_before_fullscreen = False
        self._main_layout_fullscreen_margins = None
        self._last_fullscreen_toggle_at = 0.0
        
        # Main central widget with rounded corners background
        self.central_widget = QWidget()
        self.central_widget.setObjectName("CentralWidget")
        self.central_widget.setProperty("systemChrome", self._use_system_title_bar)
        self.setCentralWidget(self.central_widget)
        
        # Initialize Managers
        self.history_manager   = HistoryManager()
        self.bookmark_manager  = BookmarkManager()
        self.password_manager  = PasswordManager()
        self.notes_manager     = NotesManager()
        
        # Main layout
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(*self._normal_layout_margins())
        self.main_layout.setSpacing(0)
        
        # Title Bar
        self.title_bar = TitleBar(self)
        self.main_layout.addWidget(self.title_bar)
        self.title_bar.setVisible(not self._use_system_title_bar)
        
        # Tab Manager (Initializes WebEngine View logic)
        self.tab_manager = TabManager(self)
        
        # Initialize Download and AdBlocker for the Profile
        self.download_manager = DownloadManager(self.tab_manager.profile, self.settings_manager, self)
        
        if self.settings_manager.get("adblock_enabled"):
            self.ad_blocker = AdBlocker()
            self.tab_manager.profile.setUrlRequestInterceptor(self.ad_blocker)
        
        # Navigation Bar
        self.nav_bar = NavigationBar(self.tab_manager, self)
        self.main_layout.addWidget(self.nav_bar)
        
        # Loading Progress Bar (Thin line)
        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("LoadingBar")
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(2)
        self.progress_bar.hide()
        self.main_layout.addWidget(self.progress_bar)
        
        # Connect menu actions
        self.setup_menu()
        self.setup_shortcuts()
        
        # Connect tab changes to navigation bar updates
        self.tab_manager.currentChanged.connect(self.nav_bar.update_ui_for_tab)
        
        # Add Tab Manager
        self.main_layout.addWidget(self.tab_manager)
        
        # Add initial tab
        self.tab_manager.add_new_tab()

        # Install app-level event filter to catch shortcuts even when
        # QWebEngineView has focus (it swallows events in its own process)
        QApplication.instance().installEventFilter(self)

    def _normal_layout_margins(self):
        return (0, 0, 0, 0) if self._use_system_title_bar else (1, 1, 1, 1)

    def _refresh_central_chrome_style(self):
        if not hasattr(self, "central_widget"):
            return
        self.central_widget.setProperty("systemChrome", self._use_system_title_bar)
        style = self.central_widget.style()
        style.unpolish(self.central_widget)
        style.polish(self.central_widget)
        self.central_widget.update()

    def apply_window_chrome(self, use_system_title_bar=None):
        """Switch between native system chrome and the custom frameless chrome."""
        use_system = bool(use_system_title_bar)
        if use_system == self._use_system_title_bar:
            self._refresh_central_chrome_style()
            return

        was_visible = self.isVisible()
        geometry = self.geometry()
        state = self.windowState()

        self._use_system_title_bar = use_system
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint, not use_system)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, not use_system)
        self._refresh_central_chrome_style()

        in_fullscreen = self._browser_fullscreen or self._web_fullscreen_tab is not None or self.isFullScreen()
        chrome_visible = not in_fullscreen
        if hasattr(self, "title_bar"):
            self.title_bar.setVisible(chrome_visible and not self._use_system_title_bar)
        if hasattr(self, "main_layout"):
            if in_fullscreen:
                self.main_layout.setContentsMargins(0, 0, 0, 0)
                self._main_layout_fullscreen_margins = self._normal_layout_margins()
            else:
                self.main_layout.setContentsMargins(*self._normal_layout_margins())

        if was_visible:
            if state & Qt.WindowState.WindowFullScreen:
                self.showFullScreen()
            elif state & Qt.WindowState.WindowMaximized:
                self.showMaximized()
            elif state & Qt.WindowState.WindowMinimized:
                self.showMinimized()
            else:
                self.setGeometry(geometry)
                self.show()

    def refresh_window_icons(self):
        if hasattr(self, "title_bar"):
            self.title_bar.refresh_icons()
        if hasattr(self, "nav_bar") and hasattr(self.nav_bar, "refresh_icons"):
            self.nav_bar.refresh_icons()
        if hasattr(self, "tab_manager") and hasattr(self.tab_manager, "refresh_icons"):
            self.tab_manager.refresh_icons()

    def eventFilter(self, obj, event):
        """Intercept key presses at the application level.
        Only fires when the main browser window (not a dialog) is focused.
        """
        if event.type() == QEvent.Type.KeyPress:
            # ── Guard: let dialogs handle their own keyboard events ──────────
            focused_widget = QApplication.focusWidget()
            if focused_widget:
                top = focused_widget.window()
                if isinstance(top, QDialog):
                    # Pass through — let the dialog's widgets handle it
                    return super().eventFilter(obj, event)

            mods = event.modifiers()
            key  = event.key()
            ctrl = Qt.KeyboardModifier.ControlModifier
            ctrl_shift = ctrl | Qt.KeyboardModifier.ShiftModifier

            if self._is_plain_key_event(mods):
                if key == Qt.Key.Key_F11:        # Browser fullscreen
                    self.toggle_browser_fullscreen()
                    return True
                if key == Qt.Key.Key_Escape and self._browser_fullscreen:
                    self.toggle_browser_fullscreen()
                    return True

            elif mods == ctrl_shift:
                if key == Qt.Key.Key_N:          # Notes
                    self.show_notes()
                    return True

            elif mods == ctrl:
                if key == Qt.Key.Key_O:          # Open file
                    self.open_file()
                    return True
                elif key == Qt.Key.Key_B:        # Bookmarks
                    self.show_bookmarks()
                    return True
                elif key == Qt.Key.Key_H:        # History
                    self.show_history()
                    return True
                elif key == Qt.Key.Key_P:        # Print to PDF
                    self.print_to_pdf()
                    return True
                elif key == Qt.Key.Key_J:        # Downloads
                    self.download_manager.show_dialog()
                    return True
        return super().eventFilter(obj, event)

    def setup_menu(self):
        self.menu = QMenu(self)

        def action(label, shortcut, slot):
            a = QAction(label, self)
            if shortcut:
                a.setShortcut(QKeySequence(shortcut))   # shows the hint in the menu
                a.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)
            a.triggered.connect(slot)
            self.menu.addAction(a)
            if shortcut:
                self.addAction(a)
            return a

        # Open File
        action("Open File...",   "Ctrl+O", self.open_file)
        self.menu.addSeparator()

        # Browser actions
        action("Bookmarks",          "Ctrl+B",       self.show_bookmarks)
        action("History",            "Ctrl+H",       self.show_history)
        action("Notes",              "Ctrl+Shift+N", self.show_notes)
        action("Downloads",          "Ctrl+J",       self.download_manager.show_dialog)
        action("Fullscreen (F11)",   "",             self.toggle_browser_fullscreen)
        action("QR Generator",       "",             self.show_qr_generator)
        action("YouTube Downloader", "",             self.show_youtube_downloader)
        action("Passwords",          "",             self.show_passwords)
        action("Print to PDF",       "Ctrl+P",       self.print_to_pdf)
        self.menu.addSeparator()

        # App
        action("Settings",           "",        self.show_settings)
        action("About Infinity",     "",        self.show_about)

        self.nav_bar.menu_btn.setMenu(self.menu)

    def setup_shortcuts(self):
        """Window shortcuts that continue to work when WebEngine has focus."""
        self._shortcuts = []
        shortcuts = (
            ("Ctrl+T", self.tab_manager.add_new_tab),
            ("Ctrl+W", lambda: self.tab_manager.close_tab(self.tab_manager.currentIndex())),
            ("Ctrl+R", self.tab_manager.reload_page),
            ("Ctrl+L", self._focus_url_bar),
        )
        for sequence, slot in shortcuts:
            shortcut = QShortcut(QKeySequence(sequence), self)
            shortcut.setContext(Qt.ShortcutContext.ApplicationShortcut)
            shortcut.activated.connect(slot)
            self._shortcuts.append(shortcut)

    def toggle_browser_fullscreen(self):
        """Toggle fullscreen for the whole browser window."""
        if self._web_fullscreen_tab is not None:
            return

        now = time.monotonic()
        if now - self._last_fullscreen_toggle_at < 0.25:
            return
        self._last_fullscreen_toggle_at = now

        if self._browser_fullscreen or self.isFullScreen():
            self._browser_fullscreen = False
            self._set_browser_chrome_visible(True)
            self._restore_window_after_fullscreen()
        else:
            self._was_maximized_before_fullscreen = self.isMaximized()
            self._browser_fullscreen = True
            self._set_browser_chrome_visible(False)
            self.showFullScreen()
            self.raise_()
            self.activateWindow()
        self._sync_fullscreen_button()

    def handle_fullscreen_request(self, tab, request):
        """Accept page fullscreen requests, including YouTube's video button."""
        request.accept()
        if request.toggleOn():
            self._enter_web_fullscreen(tab)
        else:
            self._exit_web_fullscreen()

    def _enter_web_fullscreen(self, tab):
        if self._web_fullscreen_tab is not None:
            return

        self._web_fullscreen_tab = tab
        self._web_fullscreen_started_from_browser_fullscreen = self._browser_fullscreen or self.isFullScreen()
        self._was_maximized_before_fullscreen = self.isMaximized()
        index = self.tab_manager.indexOf(tab)
        if index != -1:
            self.tab_manager.setCurrentIndex(index)

        self._set_browser_chrome_visible(False)
        if not self.isFullScreen():
            self.showFullScreen()

    def _exit_web_fullscreen(self):
        if self._web_fullscreen_tab is None:
            return

        self._web_fullscreen_tab = None
        self._set_browser_chrome_visible(True)
        if not self._web_fullscreen_started_from_browser_fullscreen:
            self._restore_window_after_fullscreen()
        self._sync_fullscreen_button()

    def _set_browser_chrome_visible(self, visible):
        self.title_bar.setVisible(visible and not self._use_system_title_bar)
        self.nav_bar.setVisible(visible)
        self.tab_manager.tabBar().setVisible(visible)
        corner = self.tab_manager.cornerWidget(Qt.Corner.TopRightCorner)
        if corner:
            corner.setVisible(visible)
        if visible:
            if self.progress_bar.value() < 100:
                self.progress_bar.show()
        else:
            self.progress_bar.hide()

        if visible:
            if self._main_layout_fullscreen_margins is not None:
                self.main_layout.setContentsMargins(*self._main_layout_fullscreen_margins)
                self._main_layout_fullscreen_margins = None
            else:
                self.main_layout.setContentsMargins(*self._normal_layout_margins())
        else:
            if self._main_layout_fullscreen_margins is None:
                margins = self.main_layout.contentsMargins()
                self._main_layout_fullscreen_margins = (
                    margins.left(), margins.top(), margins.right(), margins.bottom()
                )
            self.main_layout.setContentsMargins(0, 0, 0, 0)

    def _restore_window_after_fullscreen(self):
        if self._was_maximized_before_fullscreen:
            self.showMaximized()
        else:
            self.showNormal()

    def _sync_fullscreen_button(self):
        if hasattr(self, "nav_bar") and hasattr(self.nav_bar, "fullscreen_btn"):
            if self._browser_fullscreen or self.isFullScreen():
                self.nav_bar.fullscreen_btn.setToolTip("Exit Browser Fullscreen (F11)")
            else:
                self.nav_bar.fullscreen_btn.setToolTip("Toggle Browser Fullscreen (F11)")

    def _is_plain_key_event(self, modifiers):
        shortcut_modifiers = (
            Qt.KeyboardModifier.ControlModifier |
            Qt.KeyboardModifier.AltModifier |
            Qt.KeyboardModifier.MetaModifier
        )
        return not bool(modifiers & shortcut_modifiers)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_F11 and self._is_plain_key_event(event.modifiers()):
            self.toggle_browser_fullscreen()
            event.accept()
            return
        if event.key() == Qt.Key.Key_Escape and self._browser_fullscreen:
            self.toggle_browser_fullscreen()
            event.accept()
            return
        super().keyPressEvent(event)

    def _focus_url_bar(self):
        self.nav_bar.url_bar.setFocus()
        self.nav_bar.url_bar.selectAll()

    def _show_panel(self, attr, DialogClass, *args):
        """Show a non-modal floating window. Re-raise if already open."""
        panel = getattr(self, attr, None)
        if panel is None or not panel.isVisible():
            panel = DialogClass(*args)
            panel.setWindowFlags(
                Qt.WindowType.Window |
                Qt.WindowType.WindowCloseButtonHint |
                Qt.WindowType.WindowMinimizeButtonHint
            )
            setattr(self, attr, panel)
            panel.show()
        else:
            panel.raise_()
            panel.activateWindow()

    def show_settings(self):
        self._show_panel('_settings_panel', SettingsDialog, self.settings_manager, self)

    def show_passwords(self):
        self._show_panel('_passwords_panel', PasswordManagerDialog, self.password_manager, self)

    def print_to_pdf(self):
        current_view = self.tab_manager.currentWidget()
        if current_view:
            import os
            default_path = os.path.join(os.path.expanduser("~"), "Documents", "page.pdf")
            filepath, _ = QFileDialog.getSaveFileName(self, "Save PDF", default_path, "PDF Files (*.pdf)")
            if filepath:
                current_view.page().printToPdf(filepath)

    def show_history(self):
        self._show_panel('_history_panel', HistoryDialog, self.history_manager, self)

    def show_bookmarks(self):
        self._show_panel('_bookmarks_panel', BookmarkDialog,
                         self.bookmark_manager, self.tab_manager, self)

    def show_notes(self):
        self._show_panel('_notes_panel', NotesDialog, self.notes_manager, self)

    def is_youtube_url(self, url):
        return is_youtube_url(url)

    def current_page_url(self):
        current_view = self.tab_manager.currentWidget()
        if current_view:
            return current_view.url().toString()
        return ""

    def show_youtube_downloader(self):
        current_url = self.current_page_url()
        initial_url = current_url if is_youtube_url(current_url) else ""
        panel = getattr(self, '_youtube_downloader_panel', None)
        if panel is not None and panel.isVisible():
            if initial_url:
                panel.url_input.setText(initial_url)
                panel.fetch_info()
            panel.raise_()
            panel.activateWindow()
            return
        self._show_panel(
            '_youtube_downloader_panel',
            YouTubeDownloaderDialog,
            initial_url,
            self.settings_manager.get("download_dir"),
            self
        )

    def show_qr_generator(self):
        initial_text = self.current_page_url()
        panel = getattr(self, '_qr_generator_panel', None)
        if panel is not None and panel.isVisible():
            if initial_text:
                panel.input.setText(initial_text)
                panel.generate()
            panel.raise_()
            panel.activateWindow()
            return
        self._show_panel('_qr_generator_panel', QRGeneratorDialog, initial_text, self)
        
    def show_about(self):
        self._show_panel('_about_panel', AboutDialog, self)

    def open_file(self):
        """Open a local file in a new tab via the native file picker."""
        import os
        file_filter = (
            "All Supported Files ("
            "*.html *.htm *.pdf "
            "*.mp4 *.mkv *.avi *.mov *.flv *.wmv "
            "*.mp3 *.wav *.ogg *.flac "
            "*.png *.jpg *.jpeg *.gif *.webp *.svg "
            "*.txt *.md *.json *.xml *.csv"
            ");;"
            "Web Pages (*.html *.htm);;"
            "PDF Files (*.pdf);;"
            "Video Files (*.mp4 *.mkv *.avi *.mov *.flv *.wmv);;"
            "Audio Files (*.mp3 *.wav *.ogg *.flac);;"
            "Images (*.png *.jpg *.jpeg *.gif *.webp *.svg);;"
            "Text Files (*.txt *.md *.json *.xml *.csv);;"
            "All Files (*)"
        )
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "Open File",
            os.path.expanduser("~"),
            file_filter
        )
        if filepath:
            url = QUrl.fromLocalFile(filepath)
            self.tab_manager.add_new_tab(url)

    def show_progress(self):
        self.progress_bar.show()
        self.progress_bar.setValue(0)

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def hide_progress(self):
        self.progress_bar.setValue(100)
        # Small delay before hiding to show the completed state briefly
        QTimer.singleShot(300, self.progress_bar.hide)
