import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QFileDialog, QFormLayout,
    QGroupBox, QTabWidget, QWidget, QCheckBox, QSlider,
    QSpinBox, QFrame, QScrollArea, QSizePolicy, QApplication
)
from PyQt6.QtCore import Qt
from theme_manager import apply_theme, render_template

STYLE = """
QDialog {
    background-color: {{surface}};
    color: {{text}};
}
QTabWidget::pane {
    border: 1px solid {{border_soft}};
    border-radius: 8px;
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
QTabBar::tab:selected {
    background-color: {{accent}};
    color: {{surface}};
}
QTabBar::tab:hover:!selected {
    background-color: {{border_soft}};
    color: {{text}};
}
QGroupBox {
    border: 1px solid {{border_soft}};
    border-radius: 8px;
    margin-top: 14px;
    padding: 12px 10px 10px 10px;
    font-weight: bold;
    color: {{accent}};
    font-size: 12px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 12px;
    padding: 0 4px;
}
QLabel {
    color: {{text_soft}};
    font-size: 13px;
}
QLabel#SectionDesc {
    color: {{text_muted}};
    font-size: 11px;
    margin-bottom: 2px;
}
QLineEdit, QComboBox, QSpinBox {
    background-color: {{surface_alt}};
    color: {{text}};
    border: 1px solid {{border}};
    padding: 6px 10px;
    border-radius: 6px;
    font-size: 13px;
    min-height: 28px;
}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus {
    border-color: {{accent}};
}
QComboBox::drop-down { border: none; }
QComboBox QAbstractItemView {
    background-color: {{surface_alt}};
    color: {{text}};
    selection-background-color: {{selection}};
    border: 1px solid {{border}};
}
QCheckBox {
    color: {{text_soft}};
    font-size: 13px;
    spacing: 8px;
}
QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 2px solid {{border}};
    background-color: {{surface_alt}};
}
QCheckBox::indicator:checked {
    background-color: {{accent}};
    border-color: {{accent}};
    image: none;
}
QCheckBox::indicator:hover { border-color: {{accent}}; }
QSlider::groove:horizontal {
    height: 4px;
    background: {{border_soft}};
    border-radius: 2px;
}
QSlider::handle:horizontal {
    background: {{accent}};
    width: 16px;
    height: 16px;
    margin: -6px 0;
    border-radius: 8px;
}
QSlider::sub-page:horizontal { background: {{accent}}; border-radius: 2px; }
QPushButton {
    background-color: {{border_soft}};
    color: {{text}};
    border: none;
    padding: 7px 16px;
    border-radius: 6px;
    font-size: 13px;
    font-weight: bold;
}
QPushButton:hover { background-color: {{border}}; }
QPushButton#SaveBtn {
    background-color: {{accent}};
    color: {{surface}};
    padding: 8px 24px;
}
QPushButton#SaveBtn:hover { background-color: {{accent_alt}}; }
QPushButton#DangerBtn {
    background-color: {{danger_soft}};
    color: {{danger}};
}
QPushButton#DangerBtn:hover { background-color: {{danger}}; color: {{surface}}; }
QFrame#HSep {
    background-color: {{border_soft}};
    max-height: 1px;
}
QScrollArea { border: none; background: transparent; }
QScrollBar:vertical {
    background: {{surface}};
    width: 6px;
    border-radius: 3px;
}
QScrollBar::handle:vertical {
    background: {{border}};
    border-radius: 3px;
    min-height: 20px;
}
"""


def _sep():
    f = QFrame()
    f.setObjectName("HSep")
    f.setFrameShape(QFrame.Shape.HLine)
    return f


def _check(label, checked):
    cb = QCheckBox(label)
    cb.setChecked(checked)
    return cb


def _scrollable(widget):
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setWidget(widget)
    return scroll


class SettingsDialog(QDialog):
    def __init__(self, settings_manager, parent=None):
        super().__init__(parent)
        self.settings = settings_manager
        self.current_theme = self.settings.get("ui_theme", "dark")
        self.setWindowTitle("Infinity — Settings")
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)
        self.resize(620, 580)
        self.setStyleSheet(render_template(STYLE, self.current_theme))

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)

        # Header
        hdr = QLabel("⚙  Settings")
        hdr.setStyleSheet(render_template("font-size: 20px; font-weight: bold; color: {{text}}; padding-bottom: 4px;", self.current_theme))
        root.addWidget(hdr)
        root.addWidget(_sep())

        # Tabs
        tabs = QTabWidget()
        tabs.addTab(self._general_tab(),   "🌐  General")
        tabs.addTab(self._appearance_tab(),"🎨  Appearance")
        tabs.addTab(self._privacy_tab(),   "🔒  Privacy")
        tabs.addTab(self._security_tab(),  "🛡  Security")
        tabs.addTab(self._downloads_tab(), "⬇  Downloads")
        root.addWidget(tabs)

        # Save / Cancel
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        cancel = QPushButton("Cancel")
        cancel.clicked.connect(self.reject)
        save = QPushButton("  Save Settings  ")
        save.setObjectName("SaveBtn")
        save.clicked.connect(self._save)
        btn_row.addWidget(cancel)
        btn_row.addWidget(save)
        root.addLayout(btn_row)

    # ── TAB: General ──────────────────────────────────────────────────────────
    def _general_tab(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setSpacing(16)
        lay.setContentsMargins(12, 12, 12, 12)

        # Startup
        grp = QGroupBox("Startup")
        form = QFormLayout(grp)
        form.setSpacing(10)
        self.homepage_input = QLineEdit(self.settings.get("homepage_url"))
        self.homepage_input.setPlaceholderText("e.g. https://google.com  (leave blank for new tab)")
        form.addRow("Homepage URL:", self.homepage_input)
        self.restore_tabs_cb = _check("Restore previous tabs on startup", self.settings.get("restore_tabs"))
        form.addRow("", self.restore_tabs_cb)
        lay.addWidget(grp)

        # Search engine
        grp2 = QGroupBox("Search Engine")
        form2 = QFormLayout(grp2)
        form2.setSpacing(10)
        self.engine_combo = QComboBox()
        engines = list(self.settings.get("search_urls").keys())
        self.engine_combo.addItems(engines)
        self.engine_combo.setCurrentText(self.settings.get("search_engine"))
        form2.addRow("Default Engine:", self.engine_combo)
        lay.addWidget(grp2)

        # UI
        grp3 = QGroupBox("Interface")
        form3 = QFormLayout(grp3)
        self.show_home_cb = _check("Show Home button in toolbar", self.settings.get("show_home_btn"))
        form3.addRow("", self.show_home_cb)
        lay.addWidget(grp3)

        lay.addStretch()
        return _scrollable(w)

    # ── TAB: Appearance ───────────────────────────────────────────────────────
    def _appearance_tab(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setSpacing(16)
        lay.setContentsMargins(12, 12, 12, 12)

        grp = QGroupBox("Page Display")
        form = QFormLayout(grp)
        form.setSpacing(12)

        # Font size
        self.font_spin = QSpinBox()
        self.font_spin.setRange(8, 32)
        self.font_spin.setSuffix(" px")
        self.font_spin.setValue(self.settings.get("font_size"))
        form.addRow("Default Font Size:", self.font_spin)

        # Zoom
        zoom_row = QHBoxLayout()
        self.zoom_slider = QSlider(Qt.Orientation.Horizontal)
        self.zoom_slider.setRange(25, 300)
        self.zoom_slider.setValue(self.settings.get("default_zoom"))
        self.zoom_label = QLabel(f"{self.settings.get('default_zoom')}%")
        self.zoom_label.setFixedWidth(42)
        self.zoom_slider.valueChanged.connect(lambda v: self.zoom_label.setText(f"{v}%"))
        zoom_row.addWidget(self.zoom_slider)
        zoom_row.addWidget(self.zoom_label)
        form.addRow("Default Zoom:", zoom_row)

        # Browser chrome theme
        self.theme_combo = QComboBox()
        self.theme_combo.addItem("Dark", "dark")
        self.theme_combo.addItem("Light", "light")
        saved_theme = self.settings.get("ui_theme", "dark")
        self.theme_combo.setCurrentIndex(1 if saved_theme == "light" else 0)
        form.addRow("Browser Theme:", self.theme_combo)

        lay.addWidget(grp)
        lay.addStretch()
        return _scrollable(w)

    # ── TAB: Privacy ──────────────────────────────────────────────────────────
    def _privacy_tab(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setSpacing(16)
        lay.setContentsMargins(12, 12, 12, 12)

        grp = QGroupBox("Tracking & Ads")
        form = QFormLayout(grp)
        form.setSpacing(10)
        self.adblock_cb = _check("Enable Ad Blocker", self.settings.get("adblock_enabled"))
        self.dnt_cb = _check('Send "Do Not Track" request to websites', self.settings.get("do_not_track"))
        self.popup_cb = _check("Block pop-up windows", self.settings.get("block_popups"))
        self.js_cb = _check("Enable JavaScript", self.settings.get("javascript_enabled"))
        for cb in [self.adblock_cb, self.dnt_cb, self.popup_cb, self.js_cb]:
            form.addRow("", cb)
        lay.addWidget(grp)

        # Clear data
        grp2 = QGroupBox("Clear Browsing Data")
        vlay = QVBoxLayout(grp2)
        vlay.setSpacing(8)
        note = QLabel("These actions are immediate and cannot be undone.")
        note.setObjectName("SectionDesc")
        vlay.addWidget(note)

        btn_row1 = QHBoxLayout()
        clear_hist = QPushButton("🕐  Clear History")
        clear_hist.setObjectName("DangerBtn")
        clear_hist.clicked.connect(self._clear_history)
        clear_cache = QPushButton("🗑  Clear Cache")
        clear_cache.setObjectName("DangerBtn")
        clear_cache.clicked.connect(self._clear_cache)
        btn_row1.addWidget(clear_hist)
        btn_row1.addWidget(clear_cache)
        btn_row1.addStretch()
        vlay.addLayout(btn_row1)

        btn_row2 = QHBoxLayout()
        clear_cookies = QPushButton("🍪  Clear Cookies")
        clear_cookies.setObjectName("DangerBtn")
        clear_cookies.clicked.connect(self._clear_cookies)
        clear_all = QPushButton("⚠  Clear All Data")
        clear_all.setObjectName("DangerBtn")
        clear_all.clicked.connect(self._clear_all)
        btn_row2.addWidget(clear_cookies)
        btn_row2.addWidget(clear_all)
        btn_row2.addStretch()
        vlay.addLayout(btn_row2)
        lay.addWidget(grp2)

        lay.addStretch()
        return _scrollable(w)

    # ── TAB: Security ─────────────────────────────────────────────────────────
    def _security_tab(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setSpacing(16)
        lay.setContentsMargins(12, 12, 12, 12)

        grp = QGroupBox("Connection & Safety")
        form = QFormLayout(grp)
        form.setSpacing(10)
        self.https_cb = _check(
            "HTTPS-Only Mode (warn before loading HTTP sites)",
            self.settings.get("https_only")
        )
        self.safe_cb = _check(
            "Enable Safe Browsing protection",
            self.settings.get("safe_browsing")
        )
        form.addRow("", self.https_cb)
        form.addRow("", self.safe_cb)

        note = QLabel(
            "ℹ  HTTPS-Only mode will show a warning when visiting insecure (http://) sites.\n"
            "   Safe Browsing helps protect against known malicious websites."
        )
        note.setObjectName("SectionDesc")
        note.setWordWrap(True)
        form.addRow(note)
        lay.addWidget(grp)

        lay.addStretch()
        return _scrollable(w)

    # ── TAB: Downloads ────────────────────────────────────────────────────────
    def _downloads_tab(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setSpacing(16)
        lay.setContentsMargins(12, 12, 12, 12)

        grp = QGroupBox("Download Behaviour")
        form = QFormLayout(grp)
        form.setSpacing(10)

        self.dl_mode_combo = QComboBox()
        self.dl_mode_combo.addItems(["ask", "auto"])
        self.dl_mode_combo.setCurrentText(self.settings.get("download_mode"))
        form.addRow("Download Mode:", self.dl_mode_combo)
        mode_note = QLabel(
            "ask — show a Save dialog for every download\n"
            "auto — save directly to the folder below"
        )
        mode_note.setObjectName("SectionDesc")
        form.addRow(mode_note)

        dl_row = QHBoxLayout()
        self.dl_path_input = QLineEdit(self.settings.get("download_dir"))
        browse_btn = QPushButton("Browse…")
        browse_btn.clicked.connect(self._browse_dl)
        dl_row.addWidget(self.dl_path_input)
        dl_row.addWidget(browse_btn)
        form.addRow("Save Location:", dl_row)

        lay.addWidget(grp)
        lay.addStretch()
        return _scrollable(w)

    # ── Helpers ───────────────────────────────────────────────────────────────
    def _browse_dl(self):
        p = QFileDialog.getExistingDirectory(self, "Select Download Directory", self.dl_path_input.text())
        if p:
            self.dl_path_input.setText(p)

    def _get_profile(self):
        try:
            return self.parent().tab_manager.profile
        except Exception:
            return None

    def _clear_history(self):
        try:
            win = self.parent()
            if hasattr(win, 'history_manager'):
                win.history_manager.clear_history()
        except Exception as e:
            print("Clear history error:", e)

    def _clear_cache(self):
        profile = self._get_profile()
        if profile:
            profile.clearHttpCache()

    def _clear_cookies(self):
        profile = self._get_profile()
        if profile:
            profile.cookieStore().deleteAllCookies()

    def _clear_all(self):
        self._clear_history()
        self._clear_cache()
        self._clear_cookies()

    def _save(self):
        s = self.settings

        # General
        s.set("homepage_url",  self.homepage_input.text().strip())
        s.set("search_engine", self.engine_combo.currentText())
        s.set("restore_tabs",  self.restore_tabs_cb.isChecked())
        s.set("show_home_btn", self.show_home_cb.isChecked())

        # Appearance
        s.set("ui_theme",    self.theme_combo.currentData())
        s.set("font_size",    self.font_spin.value())
        s.set("default_zoom", self.zoom_slider.value())

        # Privacy
        s.set("adblock_enabled",    self.adblock_cb.isChecked())
        s.set("do_not_track",       self.dnt_cb.isChecked())
        s.set("block_popups",       self.popup_cb.isChecked())
        s.set("javascript_enabled", self.js_cb.isChecked())

        # Security
        s.set("https_only",    self.https_cb.isChecked())
        s.set("safe_browsing", self.safe_cb.isChecked())

        # Downloads
        s.set("download_mode", self.dl_mode_combo.currentText())
        s.set("download_dir",  self.dl_path_input.text().strip())

        # Apply live settings to the running browser
        self._apply_live_settings()
        self.accept()

    def _apply_live_settings(self):
        """Apply settings that can be changed at runtime without restart."""
        try:
            win = self.parent()
            profile = win.tab_manager.profile
            from PyQt6.QtWebEngineCore import QWebEngineSettings, QWebEngineProfile
            ws = profile.settings()

            ws.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled,
                            self.settings.get("javascript_enabled"))
            ws.setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanOpenWindows,
                            not self.settings.get("block_popups"))

            # Font size
            ws.setFontSize(QWebEngineSettings.FontSize.DefaultFontSize,
                           self.settings.get("font_size"))

            # Show/hide home button
            nav = win.nav_bar
            nav.home_btn.setVisible(self.settings.get("show_home_btn"))

            # Apply UI theme globally at runtime
            app = QApplication.instance()
            if app:
                apply_theme(app, self.settings.get("ui_theme", "dark"))
            if hasattr(win.tab_manager, "apply_theme_to_tabs"):
                win.tab_manager.apply_theme_to_tabs(reload_internal_pages=True)

            # Apply zoom to all open tabs
            zoom = self.settings.get("default_zoom") / 100.0
            for i in range(win.tab_manager.count()):
                tab = win.tab_manager.widget(i)
                if hasattr(tab, 'web_view'):
                    tab.web_view.setZoomFactor(zoom)

        except Exception as e:
            print("Apply live settings error:", e)
