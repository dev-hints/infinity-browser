import os
import json
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QLabel, QFrame, QLineEdit
)
from PyQt6.QtCore import Qt, QUrl
from theme_manager import render_template, theme_from_widget

BOOKMARKS_FILE = os.path.join(os.path.dirname(__file__), 'bookmarks.json')


class BookmarkManager:
    def __init__(self):
        self.bookmarks = self.load_bookmarks()

    def load_bookmarks(self):
        if os.path.exists(BOOKMARKS_FILE):
            try:
                with open(BOOKMARKS_FILE, 'r') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def save_bookmarks(self):
        with open(BOOKMARKS_FILE, 'w') as f:
            json.dump(self.bookmarks, f, indent=4)

    def add_bookmark(self, url, title):
        self.bookmarks[url] = title or url
        self.save_bookmarks()

    def remove_bookmark(self, url):
        if url in self.bookmarks:
            del self.bookmarks[url]
            self.save_bookmarks()

    def get_bookmarks(self):
        return self.bookmarks


class BookmarkDialog(QDialog):
    def __init__(self, manager, tab_manager, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Bookmarks")
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)
        self.resize(560, 500)
        self.manager = manager
        self.tab_manager = tab_manager

        self.setStyleSheet(render_template("""
            QDialog {
                background-color: {{surface}};
                color: {{text_soft}};
            }
            QLabel#Title {
                font-size: 18px;
                font-weight: bold;
                color: {{text}};
                padding: 4px 0;
            }
            QLineEdit {
                background-color: {{surface_alt}};
                color: {{text}};
                border: 1px solid {{border}};
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 13px;
            }
            QLineEdit:focus { border-color: {{accent}}; }
            QListWidget {
                background-color: {{surface_alt}};
                color: {{text}};
                border: 1px solid {{border}};
                border-radius: 8px;
                padding: 4px;
                font-size: 13px;
                outline: none;
            }
            QListWidget::item {
                padding: 8px 10px;
                border-radius: 6px;
            }
            QListWidget::item:selected {
                background-color: {{selection}};
                color: #ffffff;
            }
            QListWidget::item:hover:!selected {
                background-color: {{border_soft}};
            }
            QFrame#Separator { background-color: {{border_soft}}; }
            QPushButton {
                background-color: {{border_soft}};
                color: {{text}};
                border: none;
                padding: 7px 18px;
                border-radius: 6px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: {{border}}; }
            QPushButton#DeleteBtn {
                background-color: {{danger_soft}};
                color: {{danger}};
            }
            QPushButton#DeleteBtn:hover { background-color: {{danger}}; color: {{surface}}; }
        """, theme_from_widget(self)))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # Header
        title = QLabel("☆  Bookmarks")
        title.setObjectName("Title")
        layout.addWidget(title)

        sep = QFrame()
        sep.setObjectName("Separator")
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFixedHeight(1)
        layout.addWidget(sep)

        # Search bar
        self.search = QLineEdit()
        self.search.setPlaceholderText("Filter bookmarks...")
        self.search.textChanged.connect(self._filter)
        layout.addWidget(self.search)

        # List — stores url as UserRole data (never parse text)
        self.list_widget = QListWidget()
        self.list_widget.itemDoubleClicked.connect(self._open)
        layout.addWidget(self.list_widget)

        self._populate()

        # Buttons
        btn_layout = QHBoxLayout()
        del_btn = QPushButton("🗑  Remove")
        del_btn.setObjectName("DeleteBtn")
        del_btn.clicked.connect(self._remove)
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)

        btn_layout.addWidget(del_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)

    def _populate(self, filter_text=""):
        self.list_widget.clear()
        for url, title in self.manager.get_bookmarks().items():
            display = title if title else url
            if filter_text.lower() not in display.lower() and filter_text.lower() not in url.lower():
                continue
            item = QListWidgetItem()
            item.setText(f"  {display}\n  {url}")
            item.setData(Qt.ItemDataRole.UserRole, url)   # ← safe: URL stored separately
            self.list_widget.addItem(item)

    def _filter(self, text):
        self._populate(text)

    def _open(self, item):
        url = item.data(Qt.ItemDataRole.UserRole)
        if url:
            self.tab_manager.add_new_tab(QUrl(url))
            self.accept()

    def _remove(self):
        item = self.list_widget.currentItem()
        if item:
            url = item.data(Qt.ItemDataRole.UserRole)
            self.manager.remove_bookmark(url)
            self._populate(self.search.text())
