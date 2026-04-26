from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSizePolicy, QMenu, QDialog, QFrame, QProgressBar, QFileDialog,
    QTabWidget, QScrollArea, QApplication
)
from PyQt6.QtGui import QAction, QFont, QKeySequence, QShortcut
from PyQt6.QtCore import Qt, QPoint, QTimer, QUrl, QEvent

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

ABOUT_STYLE = """
QDialog { background-color: #1a1b26; color: #c0caf5; }
QTabWidget::pane {
    border: 1px solid #2f334d;
    border-radius: 0 8px 8px 8px;
    background-color: #1a1b26;
    top: -1px;
}
QTabBar::tab {
    background-color: #24283b;
    color: #565f89;
    border: none;
    padding: 8px 20px;
    margin-right: 2px;
    border-radius: 6px 6px 0 0;
    font-weight: bold;
    font-size: 12px;
}
QTabBar::tab:selected { background-color: #7aa2f7; color: #1a1b26; }
QTabBar::tab:hover:!selected { background-color: #2f334d; color: #c0caf5; }
QLabel { color: #a9b1d6; }
QFrame#HSep { background-color: #2f334d; max-height: 1px; }
QPushButton {
    background-color: #2f334d; color: #c0caf5;
    border: none; padding: 7px 20px;
    border-radius: 6px; font-weight: bold;
}
QPushButton:hover { background-color: #414868; }
QScrollArea { border: none; background: transparent; }
QScrollBar:vertical {
    background: #1a1b26; width: 6px; border-radius: 3px;
}
QScrollBar::handle:vertical {
    background: #414868; border-radius: 3px; min-height: 20px;
}
"""

class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About Infinity Browser")
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)
        self.resize(580, 520)
        self.setStyleSheet(ABOUT_STYLE)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Hero banner ──────────────────────────────────────────────────────
        banner = QWidget()
        banner.setStyleSheet(
            "background: qlineargradient(x1:0,y1:0,x2:1,y2:1,"
            "stop:0 #1a1b26, stop:0.5 #24283b, stop:1 #1a1b26);"
            "border-bottom: 1px solid #2f334d;"
        )
        banner_lay = QHBoxLayout(banner)
        banner_lay.setContentsMargins(28, 22, 28, 22)
        banner_lay.setSpacing(20)

        logo = QLabel("∞")
        logo.setStyleSheet(
            "font-size: 72px; color: #7aa2f7;"
        )
        logo.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        banner_lay.addWidget(logo)

        txt_col = QVBoxLayout()
        txt_col.setSpacing(4)
        name = QLabel("Infinity Browser")
        name.setStyleSheet(
            "font-size: 26px; font-weight: bold; color: #c0caf5; letter-spacing: 1px;"
        )
        ver = QLabel("Version 1.0.0  ·  Official Release  ·  64-bit")
        ver.setStyleSheet("font-size: 12px; color: #565f89; letter-spacing: 0.5px;")
        tagline = QLabel("Fast. Private. Yours.")
        tagline.setStyleSheet(
            "font-size: 13px; color: #7aa2f7; font-style: italic; margin-top: 2px;"
        )
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
        footer.setStyleSheet("border-top: 1px solid #2f334d; background-color: #1a1b26;")
        foot_lay = QHBoxLayout(footer)
        foot_lay.setContentsMargins(20, 12, 20, 12)
        copy = QLabel("© 2026 Infinity Browser Project. All rights reserved.")
        copy.setStyleSheet("font-size: 11px; color: #414868;")
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
            t.setStyleSheet(
                "font-size: 11px; font-weight: bold; color: #7aa2f7;"
                "text-transform: uppercase; letter-spacing: 1px;"
            )
            vl.addWidget(t)
            b = QLabel(body)
            b.setStyleSheet("font-size: 13px; color: #a9b1d6; line-height: 1.6;")
            b.setWordWrap(True)
            b.setTextFormat(Qt.TextFormat.RichText)
            vl.addWidget(b)
            if link:
                lbl = QLabel(f'<a href="{link}" style="color:#bb9af7;text-decoration:none;">'
                             f'{link_label or link}</a>')
                lbl.setOpenExternalLinks(True)
                lbl.setStyleSheet("font-size: 12px;")
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
            "<b>Ayush Kumar Maurya</b><br>"
            "Independent software developer passionate about open-source tooling, "
            "privacy-respecting software, and native Linux applications.",
            "https://github.com/dev-hints",
            "github.com/dev-hints"
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
            hdr = QLabel(f"{version}  <span style='color:#414868;font-size:11px;'>— {date}</span>")
            hdr.setStyleSheet("font-size: 14px; font-weight: bold; color: #7aa2f7;")
            hdr.setTextFormat(Qt.TextFormat.RichText)
            vl.addWidget(hdr)
            for item in items:
                bullet = QLabel(f"  • {item}")
                bullet.setStyleSheet("font-size: 13px; color: #a9b1d6;")
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
            t.setStyleSheet(
                "font-size: 12px; font-weight: bold; color: #7aa2f7;"
                "letter-spacing: 0.5px;"
            )
            b = QLabel(body)
            b.setStyleSheet("font-size: 13px; color: #a9b1d6; line-height: 1.6;")
            b.setWordWrap(True)
            b.setTextFormat(Qt.TextFormat.RichText)
            vl.addWidget(t)
            vl.addWidget(b)
            return box

        eff_label = QLabel("Effective Date: April 2026  ·  Version 1.0")
        eff_label.setStyleSheet("font-size: 11px; color: #565f89; margin-bottom: 4px;")
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
        self.title_label = QLabel(" Infinity")
        self.title_label.setObjectName("TitleLabel")
        self.layout.addWidget(self.title_label)
        
        self.layout.addStretch()
        
        # Window Controls
        self.min_btn = QPushButton("—")
        self.min_btn.setObjectName("TitleButton")
        self.min_btn.clicked.connect(self.parent.showMinimized)
        self.layout.addWidget(self.min_btn)
        
        self.max_btn = QPushButton("□")
        self.max_btn.setObjectName("TitleButton")
        self.max_btn.clicked.connect(self.toggle_max_restore)
        self.layout.addWidget(self.max_btn)
        
        self.close_btn = QPushButton("✕")
        self.close_btn.setObjectName("TitleButton")
        self.close_btn.setProperty("class", "CloseButton")
        self.close_btn.setStyleSheet("QPushButton:hover { background-color: #f7768e; color: white; }")
        self.close_btn.clicked.connect(self.parent.close)
        self.layout.addWidget(self.close_btn)
        
        self.drag_pos = None

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
        
        # Setup frameless window
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.resize(1200, 800)
        
        # Main central widget with rounded corners background
        self.central_widget = QWidget()
        self.central_widget.setObjectName("CentralWidget")
        self.central_widget.setStyleSheet("""
            QWidget#CentralWidget {
                background-color: #1a1b26;
                border-radius: 8px;
                border: 1px solid #414868;
            }
        """)
        self.setCentralWidget(self.central_widget)
        
        # Initialize Managers
        self.settings_manager  = SettingsManager()
        self.history_manager   = HistoryManager()
        self.bookmark_manager  = BookmarkManager()
        self.password_manager  = PasswordManager()
        self.notes_manager     = NotesManager()
        
        # Main layout
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(1, 1, 1, 1) # Space for border
        self.main_layout.setSpacing(0)
        
        # Title Bar
        self.title_bar = TitleBar(self)
        self.main_layout.addWidget(self.title_bar)
        
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
        
        # Connect tab changes to navigation bar updates
        self.tab_manager.currentChanged.connect(self.nav_bar.update_ui_for_tab)
        
        # Add Tab Manager
        self.main_layout.addWidget(self.tab_manager)
        
        # Add initial tab
        self.tab_manager.add_new_tab()

        # Install app-level event filter to catch shortcuts even when
        # QWebEngineView has focus (it swallows events in its own process)
        QApplication.instance().installEventFilter(self)

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

            if mods == ctrl_shift:
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
                elif key == Qt.Key.Key_T:        # New tab
                    self.tab_manager.add_new_tab()
                    return True
                elif key == Qt.Key.Key_W:        # Close tab
                    idx = self.tab_manager.currentIndex()
                    self.tab_manager.close_tab(idx)
                    return True
                elif key == Qt.Key.Key_R:        # Reload
                    self.tab_manager.reload_page()
                    return True
                elif key == Qt.Key.Key_L:        # Focus URL bar
                    self.nav_bar.url_bar.setFocus()
                    self.nav_bar.url_bar.selectAll()
                    return True
        return super().eventFilter(obj, event)

    def setup_menu(self):
        self.menu = QMenu(self)

        def action(label, shortcut, slot):
            a = QAction(label, self)
            a.setShortcut(QKeySequence(shortcut))   # shows the hint in the menu
            a.triggered.connect(slot)
            self.menu.addAction(a)
            return a

        # Open File
        action("📂  Open File...",   "Ctrl+O", self.open_file)
        self.menu.addSeparator()

        # Browser actions
        action("Bookmarks",          "Ctrl+B",       self.show_bookmarks)
        action("History",            "Ctrl+H",       self.show_history)
        action("Notes",              "Ctrl+Shift+N", self.show_notes)
        action("Downloads",          "Ctrl+J",       self.download_manager.show_dialog)
        action("Passwords",          "",             self.show_passwords)
        action("Print to PDF",       "Ctrl+P",       self.print_to_pdf)
        self.menu.addSeparator()

        # App
        action("Settings",           "",        self.show_settings)
        action("About Infinity",     "",        self.show_about)

        self.nav_bar.menu_btn.setMenu(self.menu)

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

