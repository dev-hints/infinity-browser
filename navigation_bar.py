from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLineEdit, QPushButton
from PyQt6.QtCore import Qt, QUrl
from theme_manager import theme_from_widget, tokens_for

class NavigationBar(QWidget):
    def __init__(self, tab_manager, parent=None):
        super().__init__(parent)
        self.setObjectName("NavigationBar")
        self.tab_manager = tab_manager
        
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(5, 5, 5, 5)
        self.layout.setSpacing(5)
        
        # Navigation Buttons
        self.back_btn = QPushButton("◀")
        self.back_btn.setObjectName("NavButton")
        self.back_btn.clicked.connect(self.tab_manager.navigate_back)
        self.layout.addWidget(self.back_btn)
        
        self.forward_btn = QPushButton("▶")
        self.forward_btn.setObjectName("NavButton")
        self.forward_btn.clicked.connect(self.tab_manager.navigate_forward)
        self.layout.addWidget(self.forward_btn)
        
        self.reload_btn = QPushButton("↻")
        self.reload_btn.setObjectName("NavButton")
        self.reload_btn.clicked.connect(self.tab_manager.reload_page)
        self.layout.addWidget(self.reload_btn)
        
        self.home_btn = QPushButton("⌂")
        self.home_btn.setObjectName("NavButton")
        self.home_btn.clicked.connect(self.tab_manager.navigate_home)
        self.layout.addWidget(self.home_btn)
        
        # URL Bar
        self.url_bar = QLineEdit()
        self.url_bar.setObjectName("UrlBar")
        self.url_bar.setPlaceholderText("Search or enter address")
        self.url_bar.returnPressed.connect(self.navigate_to_url)
        self.layout.addWidget(self.url_bar)
        
        # Bookmark Button
        self.bookmark_btn = QPushButton("☆")
        self.bookmark_btn.setObjectName("NavButton")
        self.bookmark_btn.clicked.connect(self.toggle_bookmark)
        self.layout.addWidget(self.bookmark_btn)

        # YouTube Downloader Button
        self.youtube_btn = QPushButton("YT↓")
        self.youtube_btn.setObjectName("NavButton")
        self.youtube_btn.setToolTip("YouTube Downloader")
        self.youtube_btn.clicked.connect(lambda: self.window().show_youtube_downloader())
        self.youtube_btn.setEnabled(False)
        self.layout.addWidget(self.youtube_btn)
        
        # Settings / Menu Button
        self.menu_btn = QPushButton("⋮")
        self.menu_btn.setObjectName("NavButton")
        # Menu will be attached later
        self.layout.addWidget(self.menu_btn)

    def navigate_to_url(self):
        text = self.url_bar.text().strip()
        if not text:
            return
        
        # Check if it's a local file path
        import os
        if text.startswith("file://"):
            url = QUrl(text)
        elif os.path.exists(text) and os.path.isabs(text):
            url = QUrl.fromLocalFile(text)
        # Simple format check for URLs vs Search
        elif "." not in text or " " in text:
            # Assume it's a search query
            try:
                url_string = self.window().settings_manager.get_search_url(text)
                url = QUrl(url_string)
            except Exception:
                url = QUrl(f"https://www.google.com/search?q={text}")
        else:
            if not text.startswith("http://") and not text.startswith("https://"):
                url = QUrl(f"https://{text}")
            else:
                url = QUrl(text)
        
        self.tab_manager.load_url(url)

    def update_ui_for_tab(self, index):
        """Called when tab is switched to update URL bar and nav buttons."""
        if index < 0:
            return
        current_view = self.tab_manager.widget(index)
        if current_view:
            url = current_view.url()
            url_str = url.toString()
            # Show blank for internal pages (like Chrome's new tab)
            display = "" if url.scheme() == "infinity" else url_str
            self.url_bar.setText(display)
            self.back_btn.setEnabled(current_view.history().canGoBack())
            self.forward_btn.setEnabled(current_view.history().canGoForward())
            
            # Check if bookmarked
            if hasattr(self.window(), 'bookmark_manager'):
                if url_str in self.window().bookmark_manager.get_bookmarks():
                    self._set_bookmark_state(True)
                else:
                    self._set_bookmark_state(False)

            if hasattr(self.window(), "is_youtube_url"):
                self.youtube_btn.setEnabled(self.window().is_youtube_url(url_str))

    def toggle_bookmark(self):
        current_view = self.tab_manager.currentWidget()
        if not current_view or not hasattr(self.window(), 'bookmark_manager'):
            return

        qurl = current_view.url()
        url = qurl.toString()

        # Don't bookmark empty, new-tab, or internal pages
        if not url or qurl.scheme() in ("", "infinity") or url in ("about:blank",):
            self._flash_bookmark_btn(self._theme_tokens()["danger"], "✕")  # red flash = can't bookmark
            return

        title = current_view.title() or url
        manager = self.window().bookmark_manager

        if url in manager.get_bookmarks():
            manager.remove_bookmark(url)
            self._set_bookmark_state(False)
        else:
            manager.add_bookmark(url, title)
            self._set_bookmark_state(True)
            self._flash_bookmark_btn(self._theme_tokens()["bookmark"], "★")

    def _theme_tokens(self):
        return tokens_for(theme_from_widget(self))

    def _set_bookmark_state(self, bookmarked):
        self.bookmark_btn.setText("★" if bookmarked else "☆")
        self.bookmark_btn.setProperty("bookmarked", bool(bookmarked))
        self.bookmark_btn.style().unpolish(self.bookmark_btn)
        self.bookmark_btn.style().polish(self.bookmark_btn)

    def _flash_bookmark_btn(self, color, symbol):
        """Brief color flash to give visual feedback."""
        from PyQt6.QtCore import QTimer
        self.bookmark_btn.setStyleSheet(
            f"color: {color}; background-color: rgba(255,255,255,0.1); border-radius: 4px;"
        )
        self.bookmark_btn.setText(symbol)
        def restore():
            url = ""
            current_view = self.tab_manager.currentWidget()
            if current_view:
                url = current_view.url().toString()
            if hasattr(self.window(), 'bookmark_manager') and url in self.window().bookmark_manager.get_bookmarks():
                self.bookmark_btn.setStyleSheet("")
                self._set_bookmark_state(True)
            else:
                self.bookmark_btn.setStyleSheet("")
                self._set_bookmark_state(False)
        QTimer.singleShot(600, restore)
