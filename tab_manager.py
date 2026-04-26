import os
from PyQt6.QtWidgets import QTabWidget, QWidget, QVBoxLayout, QPushButton, QTabBar, QStackedLayout
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEnginePage, QWebEngineProfile
from PyQt6.QtCore import QUrl, pyqtSignal
from scheme_handler import InfinitySchemeHandler

class CustomTabBar(QTabBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTabsClosable(True)
        self.setMovable(True)

class CustomWebView(QWebEngineView):
    def __init__(self, tab_manager, parent=None):
        super().__init__(parent)
        self.tab_manager = tab_manager

    def createWindow(self, windowType):
        return self.tab_manager.add_empty_tab().web_view

class BrowserTab(QWidget):
    titleChanged = pyqtSignal(str)
    urlChanged = pyqtSignal(QUrl)
    loadStarted = pyqtSignal()
    loadProgress = pyqtSignal(int)
    loadFinished = pyqtSignal(bool)

    def __init__(self, tab_manager, parent=None):
        super().__init__(parent)
        self.tab_manager = tab_manager
        self.layout = QStackedLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        # Web View
        self.web_view = CustomWebView(self.tab_manager)
        self._page = QWebEnginePage(self.tab_manager.profile, self.web_view)
        self.web_view.setPage(self._page)
        self.layout.addWidget(self.web_view)
        
        # Handle print requests from within the page
        if self.tab_manager.parent_window and hasattr(self.tab_manager.parent_window, 'print_to_pdf'):
            self._page.printRequested.connect(self.tab_manager.parent_window.print_to_pdf)
        
        # Media Player
        from media_player import MediaPlayerWidget
        self.media_player = MediaPlayerWidget()
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
        
        self.is_media = False

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
        self.parent_window = parent
        self.setDocumentMode(True)
        self.setTabsClosable(True)
        self.tabCloseRequested.connect(self.close_tab)
        
        # Corner widget for new tab
        self.new_tab_btn = QPushButton("+")
        self.new_tab_btn.setObjectName("NavButton")
        self.new_tab_btn.clicked.connect(self.add_new_tab)
        self.setCornerWidget(self.new_tab_btn)

        # Profile for settings, adblock, downloads
        self.profile = QWebEngineProfile("InfinityProfile", self)

        # Register custom infinity:// scheme handler
        self.scheme_handler = InfinitySchemeHandler(self)
        self.profile.installUrlSchemeHandler(b"infinity", self.scheme_handler)

        # Apply settings from settings_manager
        from PyQt6.QtWebEngineCore import QWebEngineSettings
        ws = self.profile.settings()
        sm = parent.settings_manager if parent and hasattr(parent, 'settings_manager') else None

        ws.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        ws.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True)
        ws.setAttribute(QWebEngineSettings.WebAttribute.PdfViewerEnabled, True)
        ws.setAttribute(QWebEngineSettings.WebAttribute.PluginsEnabled, True)
        ws.setAttribute(QWebEngineSettings.WebAttribute.PlaybackRequiresUserGesture, False)

        # User-controlled settings
        js_on      = sm.get("javascript_enabled") if sm else True
        popup_on   = sm.get("block_popups")       if sm else True
        font_size  = sm.get("font_size")          if sm else 16

        ws.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, js_on)
        ws.setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanOpenWindows, not popup_on)
        ws.setFontSize(QWebEngineSettings.FontSize.DefaultFontSize, font_size)


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
            homepage = "new_tab.html"
            if self.parent_window and hasattr(self.parent_window, 'settings_manager'):
                homepage = self.parent_window.settings_manager.get("homepage_url")
            
            if homepage == "new_tab.html" or not homepage:
                url = QUrl("infinity://newtab")
            else:
                if not homepage.startswith("http"):
                    homepage = "https://" + homepage
                url = QUrl(homepage)
        
        tab = self.add_empty_tab()
        tab.load(url)
        return tab

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
        self.load_url(self.new_tab_url)
