import os
import sys
import subprocess
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt, QUrl, pyqtSignal
from PyQt6.QtGui import QFont, QIcon

class MediaPlayerWidget(QWidget):
    titleChanged = pyqtSignal(str)
    urlChanged = pyqtSignal(QUrl)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: #1a1b26; color: #a9b1d6;")
        
        self.layout = QVBoxLayout(self)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.setSpacing(20)
        
        # Icon
        self.icon_label = QLabel("🎬")
        self.icon_label.setStyleSheet("font-size: 72px; color: #7aa2f7;")
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.icon_label)
        
        # Title
        self.title_label = QLabel("Media Playback")
        self.title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #c0caf5;")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.title_label)
        
        # Description
        self.desc_label = QLabel(
            "This video format requires proprietary codecs (like H.264/AAC)<br>"
            "which are not included in the open-source browser engine.<br><br>"
            "To provide the best playback experience without stuttering,<br>"
            "we can seamlessly open this video in your default system player."
        )
        self.desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.desc_label.setStyleSheet("font-size: 14px; line-height: 1.5;")
        self.layout.addWidget(self.desc_label)
        
        # Button
        self.play_btn = QPushButton("▶ Open in System Player")
        self.play_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.play_btn.setStyleSheet("""
            QPushButton {
                background-color: #7aa2f7;
                color: #1a1b26;
                border: none;
                padding: 12px 24px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #89b4fa;
            }
            QPushButton:pressed {
                background-color: #668ee0;
            }
        """)
        self.play_btn.clicked.connect(self.open_external)
        self.layout.addWidget(self.play_btn, alignment=Qt.AlignmentFlag.AlignHCenter)
        
        self.current_url = QUrl()

    def load(self, url):
        self.current_url = url
        self.titleChanged.emit(self.title())
        self.urlChanged.emit(self.current_url)
        
        # Auto-launch external player
        self.open_external()

    def open_external(self):
        filepath = self.current_url.toLocalFile()
        if os.path.exists(filepath):
            if sys.platform.startswith('linux'):
                subprocess.Popen(['xdg-open', filepath])
            elif sys.platform == 'win32':
                os.startfile(filepath)
            elif sys.platform == 'darwin':
                subprocess.Popen(['open', filepath])

    def stop(self):
        pass

    def url(self):
        return self.current_url

    def title(self):
        return os.path.basename(self.current_url.toLocalFile()) or "Media Player"
