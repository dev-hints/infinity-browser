from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLineEdit, QPushButton, QSizePolicy
from PyQt6.QtCore import Qt, QUrl, QSize
from icon_utils import themed_icon
from theme_manager import theme_from_widget, tokens_for

class NavigationBar(QWidget):
    def __init__(self, tab_manager, parent=None):
        super().__init__(parent)
        self.setObjectName("NavigationBar")
        self.tab_manager = tab_manager
        
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(5, 5, 5, 5)
        self.layout.setSpacing(5)
        self._icon_buttons = []

        def make_nav_button(icon_name, tooltip=None, callback=None):
            btn = QPushButton()
            btn.setObjectName("NavButton")
            btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
            btn.setFixedWidth(38)
            btn.setFixedHeight(34)
            btn.setIcon(themed_icon(icon_name, theme_from_widget(self)))
            btn.setIconSize(QSize(18, 18))
            self._icon_buttons.append((btn, icon_name))
            if tooltip:
                btn.setToolTip(tooltip)
            if callback:
                btn.clicked.connect(callback)
            return btn

        # Navigation Buttons
        self.back_btn = make_nav_button("back", "Back", self.tab_manager.navigate_back)
        self.layout.addWidget(self.back_btn)
        
        self.forward_btn = make_nav_button("forward", "Forward", self.tab_manager.navigate_forward)
        self.layout.addWidget(self.forward_btn)
        
        self.reload_btn = make_nav_button("reload", "Reload", self.tab_manager.reload_page)
        self.layout.addWidget(self.reload_btn)
        
        self.home_btn = make_nav_button("home", "Home", self.tab_manager.navigate_home)
        self.layout.addWidget(self.home_btn)
        
        # URL Bar
        self.url_bar = QLineEdit()
        self.url_bar.setObjectName("UrlBar")
        self.url_bar.setPlaceholderText("Search or enter address")
        self.url_bar.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.url_bar.setMinimumWidth(220)
        self.url_bar.returnPressed.connect(self.navigate_to_url)
        self.layout.addWidget(self.url_bar)
        
        # Bookmark Button
        self.bookmark_btn = make_nav_button("star", "Toggle Bookmark", self.toggle_bookmark)
        self.layout.addWidget(self.bookmark_btn)

        # YouTube Downloader Button
        self.youtube_btn = make_nav_button("youtube", "YouTube Downloader",
                                         lambda: self.window().show_youtube_downloader())
        self.youtube_btn.setEnabled(False)
        self.layout.addWidget(self.youtube_btn)

        # QR Generator Button
        self.qr_btn = make_nav_button("qr", "QR Generator",
                                      lambda: self.window().show_qr_generator())
        self.layout.addWidget(self.qr_btn)

        # Browser Fullscreen Button
        self.fullscreen_btn = make_nav_button("fullscreen", "Toggle Browser Fullscreen (F11)",
                                             lambda: self.window().toggle_browser_fullscreen())
        self.layout.addWidget(self.fullscreen_btn)

        # Downloads Button
        self.downloads_btn = make_nav_button("download", "Downloads",
                                             lambda: self.window().download_manager.show_dialog())
        self.layout.addWidget(self.downloads_btn)

        # Notes Button
        self.notes_btn = make_nav_button("notes", "Notes",
                                        lambda: self.window().show_notes())
        self.layout.addWidget(self.notes_btn)
        
        # Settings / Menu Button
        self.menu_btn = make_nav_button("menu", "Menu")
        # Menu will be attached later
        self.layout.addWidget(self.menu_btn)

    def refresh_icons(self):
        theme = theme_from_widget(self)
        for btn, icon_name in self._icon_buttons:
            if btn is self.bookmark_btn:
                continue
            btn.setIcon(themed_icon(icon_name, theme))
        self._set_bookmark_state(bool(self.bookmark_btn.property("bookmarked")))

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
            self._flash_bookmark_btn(self._theme_tokens()["danger"], "close")
            return

        title = current_view.title() or url
        manager = self.window().bookmark_manager

        if url in manager.get_bookmarks():
            manager.remove_bookmark(url)
            self._set_bookmark_state(False)
        else:
            manager.add_bookmark(url, title)
            self._set_bookmark_state(True)
            self._flash_bookmark_btn(self._theme_tokens()["bookmark"], "star-filled")

    def _theme_tokens(self):
        return tokens_for(theme_from_widget(self))

    def _set_bookmark_state(self, bookmarked):
        theme = theme_from_widget(self)
        role = "bookmark" if bookmarked else "text_soft"
        self.bookmark_btn.setIcon(themed_icon("star-filled" if bookmarked else "star", theme, role))
        self.bookmark_btn.setProperty("bookmarked", bool(bookmarked))
        self.bookmark_btn.style().unpolish(self.bookmark_btn)
        self.bookmark_btn.style().polish(self.bookmark_btn)

    def _flash_bookmark_btn(self, color, icon_name):
        """Brief color flash to give visual feedback."""
        from PyQt6.QtCore import QTimer
        from icon_utils import svg_icon
        self.bookmark_btn.setStyleSheet(
            f"color: {color}; background-color: rgba(255,255,255,0.1); border-radius: 4px;"
        )
        self.bookmark_btn.setIcon(svg_icon(icon_name, color))
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
