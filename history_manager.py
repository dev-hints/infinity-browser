import os
import json
from datetime import datetime
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QListWidget, QPushButton, QHBoxLayout

HISTORY_FILE = os.path.join(os.path.dirname(__file__), 'history.json')

class HistoryManager:
    def __init__(self):
        self.history = self.load_history()

    def load_history(self):
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, 'r') as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    def save_history(self):
        with open(HISTORY_FILE, 'w') as f:
            json.dump(self.history, f)

    def add_url(self, url, title):
        if url.startswith("devtools://") or url.startswith("file://") or "new_tab.html" in url:
            return
            
        entry = {
            'url': url,
            'title': title,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self.history.insert(0, entry)
        
        # Limit history size to 1000 to keep it lightweight
        if len(self.history) > 1000:
            self.history = self.history[:1000]
            
        self.save_history()

    def get_history(self):
        return self.history

    def clear_history(self):
        self.history = []
        self.save_history()

class HistoryDialog(QDialog):
    def __init__(self, manager, parent=None):
        super().__init__(parent)
        self.setWindowTitle("History")
        self.resize(400, 500)
        self.manager = manager
        
        self.layout = QVBoxLayout(self)
        
        self.list_widget = QListWidget()
        for item in self.manager.get_history():
            self.list_widget.addItem(f"{item['timestamp']} - {item['title']} ({item['url']})")
            
        self.layout.addWidget(self.list_widget)
        
        self.btn_layout = QHBoxLayout()
        self.clear_btn = QPushButton("Clear History")
        self.clear_btn.clicked.connect(self.clear_history)
        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.accept)
        
        self.btn_layout.addWidget(self.clear_btn)
        self.btn_layout.addWidget(self.close_btn)
        
        self.layout.addLayout(self.btn_layout)

    def clear_history(self):
        self.manager.clear_history()
        self.list_widget.clear()
