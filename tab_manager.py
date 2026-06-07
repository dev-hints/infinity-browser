import os
from PyQt6.QtWidgets import (
    QTabWidget, QWidget, QVBoxLayout, QPushButton, QTabBar,
    QStackedLayout, QSizePolicy
)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import (
    QWebEnginePage, QWebEngineProfile, QWebEngineScript, QWebEngineSettings
)
from PyQt6.QtCore import Qt, QUrl, pyqtSignal, QSize
from PyQt6.QtGui import QColor, QPalette
from icon_utils import themed_icon
from theme_manager import theme_from_widget, web_background_color, normalize_theme, tokens_for
from scheme_handler import InfinitySchemeHandler


def _disable_forced_web_dark_mode(settings):
    attr = getattr(QWebEngineSettings.WebAttribute, "ForceDarkMode", None)
    if attr is not None:
        settings.setAttribute(attr, False)


def _install_page_scheme_guard(profile, theme='light'):
    script = QWebEngineScript()
    script.setName("InfinityPageSchemeGuard")
    script.setInjectionPoint(QWebEngineScript.InjectionPoint.DocumentCreation)
    script.setWorldId(QWebEngineScript.ScriptWorldId.MainWorld)
    script.setRunsOnSubFrames(True)
    theme_value = "light" if normalize_theme(theme) == "light" else "dark"
    is_light = "true" if theme_value == "light" else "false"
    script.setSourceCode(f"""
(function () {{
    if (!/^https?:$/.test(location.protocol)) return;

    try {{
        var nativeMatchMedia = window.matchMedia ? window.matchMedia.bind(window) : null;
        if (nativeMatchMedia) {{
            window.matchMedia = function (query) {{
                var normalized = String(query || '').toLowerCase();
                if (normalized.indexOf('prefers-color-scheme') !== -1) {{
                    var isLight = {is_light};
                    return {{
                        media: query,
                        matches: isLight,
                        onchange: null,
                        addListener: function () {{}},
                        removeListener: function () {{}},
                        addEventListener: function () {{}},
                        removeEventListener: function () {{}},
                        dispatchEvent: function () {{ return false; }}
                    }};
                }}
                return nativeMatchMedia(query);
            }};
        }}
    }} catch (e) {{}}

    try {{
        var style = document.createElement('style');
        style.id = 'infinity-page-scheme';
        style.textContent = ':root, html, body {{ color-scheme: {theme_value} !important; }}';
        if (document.head) {{
            document.head.appendChild(style);
        }} else if (document.documentElement) {{
            document.documentElement.appendChild(style);
        }}
    }} catch (e) {{}}

    try {{
        var meta = document.createElement('meta');
        meta.name = 'color-scheme';
        meta.content = '{theme_value}';
        if (document.head) {{
            document.head.appendChild(meta);
        }} else if (document.documentElement) {{
            document.documentElement.appendChild(meta);
        }}
    }} catch (e) {{}}
}})();
"""
    )
    profile.scripts().insert(script)


class CustomTabBar(QTabBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTabsClosable(True)
        self.setMovable(True)
        self.setDrawBase(False)

class CustomWebView(QWebEngineView):
    def __init__(self, tab_manager, parent=None):
        super().__init__(parent)
        self.tab_manager = tab_manager
        self.setObjectName("WebContentView")
        self.setAutoFillBackground(True)

    def _apply_theme(self, theme_name):
        palette = self.palette()
        tokens = tokens_for(theme_name)
        bg = QColor(tokens["window_bg"])
        text = QColor(tokens["text"])
        for role in (
            QPalette.ColorRole.Window,
            QPalette.ColorRole.Base,
            QPalette.ColorRole.AlternateBase,
        ):
            palette.setColor(role, bg)
        for role in (
            QPalette.ColorRole.WindowText,
            QPalette.ColorRole.Text,
        ):
            palette.setColor(role, text)
        self.setPalette(palette)

    def createWindow(self, windowType):
        return self.tab_manager.add_empty_tab().web_view

    def keyPressEvent(self, event):
        parent_window = self.tab_manager.parent_window
        if parent_window and hasattr(parent_window, "_is_plain_key_event"):
            if event.key() == Qt.Key.Key_F11 and parent_window._is_plain_key_event(event.modifiers()):
                parent_window.toggle_browser_fullscreen()
                event.accept()
                return
            if event.key() == Qt.Key.Key_Escape and getattr(parent_window, "_browser_fullscreen", False):
                parent_window.toggle_browser_fullscreen()
                event.accept()
                return
        super().keyPressEvent(event)

class BrowserTab(QWidget):
    titleChanged = pyqtSignal(str)
    urlChanged = pyqtSignal(QUrl)
    loadStarted = pyqtSignal()
    loadProgress = pyqtSignal(int)
    loadFinished = pyqtSignal(bool)

    def __init__(self, tab_manager, parent=None):
        super().__init__(parent)
        self.setObjectName("WebPageHost")
        self.setAutoFillBackground(True)
        self.tab_manager = tab_manager
        theme = "dark"
        if self.tab_manager.parent_window and hasattr(self.tab_manager.parent_window, "settings_manager"):
            theme = self.tab_manager.parent_window.settings_manager.get("ui_theme", "dark")
        self._apply_theme(normalize_theme(theme))
        self.layout = QStackedLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.is_media = False
        
        # Web View
        self.web_view = CustomWebView(self.tab_manager)
        self._page = QWebEnginePage(self.tab_manager.profile, self.web_view)
        self.web_view.setPage(self._page)
        self._page.settings().setAttribute(QWebEngineSettings.WebAttribute.FullScreenSupportEnabled, True)
        _disable_forced_web_dark_mode(self._page.settings())
        self.apply_theme()
        self.layout.addWidget(self.web_view)
        
        # Handle print requests from within the page
        if self.tab_manager.parent_window and hasattr(self.tab_manager.parent_window, 'print_to_pdf'):
            self._page.printRequested.connect(self.tab_manager.parent_window.print_to_pdf)

        # Let sites such as YouTube promote their video element to fullscreen.
        if self.tab_manager.parent_window and hasattr(self.tab_manager.parent_window, 'handle_fullscreen_request'):
            self._page.fullScreenRequested.connect(
                lambda request, t=self: self.tab_manager.parent_window.handle_fullscreen_request(t, request)
            )
        
        # Media Player
        from media_player import MediaPlayerWidget
        self.media_player = MediaPlayerWidget(self)
        self.layout.addWidget(self.media_player)
        
        # Connect Web View Signals
        self.web_view.titleChanged.connect(self.titleChanged.emit)
        self.web_view.urlChanged.connect(self.urlChanged.emit)
        self.web_view.loadStarted.connect(self.loadStarted.emit)
        self.web_view.loadProgress.connect(self.loadProgress.emit)
        self.web_view.loadFinished.connect(self.loadFinished.emit)
        
        # Connect Media Player Signals
        self.media_player.titleChanged.connect(self.titleChanged.emit)
        self.media_player.urlChanged.connect(self.urlChanged.emit)

    def _apply_theme(self, theme_name):
        palette = self.palette()
        tokens = tokens_for(theme_name)
        bg = QColor(tokens["window_bg"])
        text = QColor(tokens["text"])
        for role in (
            QPalette.ColorRole.Window,
            QPalette.ColorRole.Base,
            QPalette.ColorRole.AlternateBase,
        ):
            palette.setColor(role, bg)
        for role in (
            QPalette.ColorRole.WindowText,
            QPalette.ColorRole.Text,
        ):
            palette.setColor(role, text)
        self.setPalette(palette)
        
    def apply_theme(self, url=None):
        url = url or self.url()
        theme = "dark"
        if self.tab_manager.parent_window and hasattr(self.tab_manager.parent_window, "settings_manager"):
            theme = self.tab_manager.parent_window.settings_manager.get("ui_theme", "dark")
        theme = normalize_theme(theme)
        tokens = tokens_for(theme)
        color = QColor(tokens["window_bg"])

        try:
            self._page.setBackgroundColor(color)
        except Exception:
            pass

        self.web_view._apply_theme(theme)
        self.web_view.setStyleSheet(
            f"QWebEngineView#WebContentView {{ background-color: {color.name()}; color: {tokens['text']}; }}"
        )

    def _background_color_for_url(self, url):
        theme = "dark"
        if self.tab_manager.parent_window and hasattr(self.tab_manager.parent_window, "settings_manager"):
            theme = self.tab_manager.parent_window.settings_manager.get("ui_theme", "dark")
        return web_background_color(theme)

    def load(self, url):
        url_str = url.toString().lower()
        media_exts = ('.mp4', '.mkv', '.avi', '.mov', '.flv', '.wmv')
        
        if url.isLocalFile() and url_str.endswith(media_exts):
            self.is_media = True
            self.layout.setCurrentWidget(self.media_player)
            self.media_player.load(url)
        else:
            if self.is_media:
                self.media_player.stop()
            self.is_media = False
            self.layout.setCurrentWidget(self.web_view)
            self.apply_theme(url)
            _disable_forced_web_dark_mode(self._page.settings())
            self.web_view.load(url)

    def url(self):
        if self.is_media: return self.media_player.url()
        return self.web_view.url()

    def title(self):
        if self.is_media: return self.media_player.title()
        return self.web_view.title()

    def history(self):
        return self.web_view.history()

    def back(self):
        if not self.is_media: self.web_view.back()

    def forward(self):
        if not self.is_media: self.web_view.forward()

    def reload(self):
        if not self.is_media: self.web_view.reload()

    def page(self):
        return self._page

class TabManager(QTabWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("BrowserTabs")
        self.parent_window = parent
        self.setTabBar(CustomTabBar(self))
        self.setDocumentMode(True)
        self.setTabsClosable(True)
        self.tabCloseRequested.connect(self.close_tab)
        
        # Corner widget for new tab
        self.new_tab_btn = QPushButton(self)
        self.new_tab_btn.setObjectName("NewTabButton")
        self.new_tab_btn.setFixedSize(40, 34)
        self.new_tab_btn.setIcon(themed_icon("plus", theme_from_widget(self)))
        self.new_tab_btn.setIconSize(QSize(18, 18))
        self.new_tab_btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.new_tab_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.new_tab_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.new_tab_btn.setToolTip("New Tab")
        self.new_tab_btn.clicked.connect(self.add_new_tab)
        self.setCornerWidget(self.new_tab_btn, Qt.Corner.TopRightCorner)
        self.new_tab_btn.show()

        # Profile for settings, adblock, downloads
        self.profile = QWebEngineProfile("InfinityProfile", self)
        self.profile.setHttpUserAgent(
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        )
        theme = "dark"
        if self.parent_window and hasattr(self.parent_window, 'settings_manager'):
            theme = self.parent_window.settings_manager.get("ui_theme", "dark")
        _install_page_scheme_guard(self.profile, theme)

        # Register custom infinity:// scheme handler
        self.scheme_handler = InfinitySchemeHandler(self)
        self.profile.installUrlSchemeHandler(b"infinity", self.scheme_handler)

        # Apply settings from settings_manager
        ws = self.profile.settings()
        sm = parent.settings_manager if parent and hasattr(parent, 'settings_manager') else None

        ws.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        ws.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True)
        ws.setAttribute(QWebEngineSettings.WebAttribute.PdfViewerEnabled, True)
        ws.setAttribute(QWebEngineSettings.WebAttribute.PluginsEnabled, True)
        ws.setAttribute(QWebEngineSettings.WebAttribute.PlaybackRequiresUserGesture, False)
        ws.setAttribute(QWebEngineSettings.WebAttribute.FullScreenSupportEnabled, True)
        _disable_forced_web_dark_mode(ws)

        # User-controlled settings
        js_on      = sm.get("javascript_enabled") if sm else True
        popup_on   = sm.get("block_popups")       if sm else True
        font_size  = sm.get("font_size")          if sm else 16

        ws.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, js_on)
        ws.setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanOpenWindows, not popup_on)
        ws.setFontSize(QWebEngineSettings.FontSize.DefaultFontSize, font_size)

    def refresh_icons(self):
        self.new_tab_btn.setIcon(themed_icon("plus", theme_from_widget(self)))

    def _get_home_url(self):
        """Return the configured home page as a QUrl."""
        homepage = "new_tab.html"
        if self.parent_window and hasattr(self.parent_window, 'settings_manager'):
            homepage = self.parent_window.settings_manager.get("homepage_url")

        homepage = (homepage or "").strip()

        if homepage == "new_tab.html" or not homepage:
            return QUrl("infinity://newtab")

        if homepage.startswith("file://"):
            return QUrl(homepage)

        if os.path.isabs(homepage) and os.path.exists(homepage):
            return QUrl.fromLocalFile(homepage)

        if not homepage.startswith(("http://", "https://")):
            homepage = "https://" + homepage
        return QUrl(homepage)


    def create_web_view(self):
        tab = BrowserTab(self)
        
        # Signals to update title/URL and progress
        tab.titleChanged.connect(lambda title, t=tab: self.update_tab_title(t, title))
        tab.urlChanged.connect(lambda url, t=tab: self.update_tab_url(t, url))
        tab.loadStarted.connect(lambda t=tab: self.on_load_started(t))
        tab.loadProgress.connect(lambda p, t=tab: self.on_load_progress(t, p))
        tab.loadFinished.connect(lambda ok, t=tab: self.on_load_finished(t, ok))
        
        return tab

    def add_empty_tab(self):
        tab = self.create_web_view()
        i = self.addTab(tab, "Loading...")
        self.setCurrentIndex(i)
        return tab

    def add_new_tab(self, url=None):
        # PyQt6 clicked signal passes a boolean (False), which overrides the None default
        if not url or isinstance(url, bool):
            url = self._get_home_url()
        
        tab = self.add_empty_tab()
        self._apply_default_zoom(tab)
        tab.load(url)
        return tab

    def _apply_default_zoom(self, tab):
        if self.parent_window and hasattr(self.parent_window, "settings_manager"):
            zoom = self.parent_window.settings_manager.get("default_zoom", 100) / 100.0
            if hasattr(tab, "web_view"):
                tab.web_view.setZoomFactor(zoom)

    def _update_page_scheme_guard(self):
        to_remove = self.profile.scripts().find("InfinityPageSchemeGuard")
        for script in to_remove:
            self.profile.scripts().remove(script)
        theme = "dark"
        if self.parent_window and hasattr(self.parent_window, 'settings_manager'):
            theme = self.parent_window.settings_manager.get("ui_theme", "dark")
        _install_page_scheme_guard(self.profile, theme)

    def apply_theme_to_tabs(self, reload_internal_pages=False):
        self._update_page_scheme_guard()
        for i in range(self.count()):
            tab = self.widget(i)
            if hasattr(tab, "apply_theme"):
                tab.apply_theme()
            if reload_internal_pages and hasattr(tab, "url") and tab.url().scheme() == "infinity":
                tab.reload()

    def close_tab(self, index):
        if self.count() > 1:
            widget = self.widget(index)
            self.removeTab(index)
            widget.deleteLater()
        else:
            self.parent_window.close()

    def update_tab_title(self, view, title):
        index = self.indexOf(view)
        if index != -1:
            self.setTabText(index, title[:20] + "..." if len(title) > 20 else title)

    def update_tab_url(self, view, url):
        index = self.indexOf(view)
        # If this is the current tab, update the nav bar
        if index == self.currentIndex() and self.parent_window:
            url_str = url.toString()
            # Show blank for internal pages
            display = "" if url.scheme() == "infinity" else url_str
            self.parent_window.nav_bar.url_bar.setText(display)
            self.parent_window.nav_bar.back_btn.setEnabled(view.history().canGoBack())
            self.parent_window.nav_bar.forward_btn.setEnabled(view.history().canGoForward())
            if hasattr(self.parent_window.nav_bar, "youtube_btn"):
                self.parent_window.nav_bar.youtube_btn.setEnabled(
                    self.parent_window.is_youtube_url(url_str)
                )

    def on_load_started(self, view):
        if self.indexOf(view) == self.currentIndex() and self.parent_window:
            self.parent_window.show_progress()

    def on_load_progress(self, view, progress):
        if self.indexOf(view) == self.currentIndex() and self.parent_window:
            self.parent_window.update_progress(progress)

    def on_load_finished(self, view, ok):
        if self.indexOf(view) == self.currentIndex() and self.parent_window:
            self.parent_window.hide_progress()
            
        if ok and self.parent_window and hasattr(self.parent_window, 'history_manager'):
            url = view.url()
            # Don't store internal pages in history
            if url.scheme() != "infinity":
                self.parent_window.history_manager.add_url(url.toString(), view.title())

    def load_url(self, url):
        current_view = self.currentWidget()
        if current_view:
            current_view.load(url)

    def navigate_back(self):
        current_view = self.currentWidget()
        if current_view and current_view.history().canGoBack():
            current_view.back()

    def navigate_forward(self):
        current_view = self.currentWidget()
        if current_view and current_view.history().canGoForward():
            current_view.forward()

    def reload_page(self):
        current_view = self.currentWidget()
        if current_view:
            current_view.reload()

    def navigate_home(self):
        self.load_url(self._get_home_url())
