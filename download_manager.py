import os
import platform
import subprocess
import time
import json
import uuid
from datetime import datetime
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QPushButton, QProgressBar, QWidget, QFileDialog, QScrollArea,
    QMessageBox, QSizePolicy
)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtWebEngineCore import QWebEngineDownloadRequest
from theme_manager import render_template, theme_from_widget

DOWNLOADS_FILE = os.path.join(os.path.dirname(__file__), 'downloads.json')


def _t(widget, style: str) -> str:
    return render_template(style, theme_from_widget(widget))

class DownloadHistoryWidget(QWidget):
    def __init__(self, data, manager, parent=None):
        super().__init__(parent)
        self.data = data
        self.manager = manager
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        
        info_layout = QHBoxLayout()
        self.name_label = QLabel(data.get("filename", "Unknown"))
        self.name_label.setStyleSheet(_t(self, "font-weight: bold; color: {{text}};"))
        self.name_label.setWordWrap(True)
        self.name_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.status_label = QLabel(f"{data.get('size_str', '')} • {data.get('date', '')}")
        self.status_label.setStyleSheet(_t(self, "color: {{text_soft}}; font-size: 12px;"))
        self.status_label.setWordWrap(True)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        
        info_layout.addWidget(self.name_label)
        info_layout.addStretch()
        info_layout.addWidget(self.status_label)
        
        self.layout.addLayout(info_layout)
        
        btn_layout = QGridLayout()
        btn_layout.setHorizontalSpacing(8)
        btn_layout.setVerticalSpacing(8)
        self.redownload_btn = QPushButton("Redownload")
        self.delete_btn = QPushButton("Remove")
        self.folder_btn = QPushButton("Folder")
        self.open_btn = QPushButton("Open")

        for btn in (self.redownload_btn, self.delete_btn, self.folder_btn, self.open_btn):
            btn.setMinimumWidth(96)
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        btn_layout.addWidget(self.redownload_btn, 0, 0)
        btn_layout.addWidget(self.delete_btn, 0, 1)
        btn_layout.addWidget(self.folder_btn, 1, 0)
        btn_layout.addWidget(self.open_btn, 1, 1)
        
        self.layout.addLayout(btn_layout)
        
        # Connect
        self.open_btn.clicked.connect(lambda: self.open_file(data.get("save_path")))
        self.folder_btn.clicked.connect(lambda: self.open_folder(os.path.dirname(data.get("save_path"))))
        self.delete_btn.clicked.connect(self.delete_history)
        self.redownload_btn.clicked.connect(self.redownload)
        
        self.setStyleSheet(_t(self, """
            QWidget { background-color: {{surface_alt}}; border-radius: 6px; }
            QPushButton { background-color: {{border}}; color: {{text}}; border: none; padding: 6px 10px; border-radius: 4px; }
            QPushButton:hover { background-color: {{accent}}; color: {{surface}}; }
        """))

        # Disable open buttons if file doesn't exist
        if not os.path.exists(data.get("save_path", "")):
            self.open_btn.setDisabled(True)
            self.folder_btn.setDisabled(True)
            self.status_label.setText("File Deleted • " + data.get('date', ''))
            self.status_label.setStyleSheet(_t(self, "color: {{danger}}; font-size: 12px;"))

    def open_file(self, filepath):
        if not filepath or not os.path.exists(filepath): return
        if platform.system() == 'Darwin':
            subprocess.call(('open', filepath))
        elif platform.system() == 'Windows':
            os.startfile(filepath)
        else:
            subprocess.call(('xdg-open', filepath))

    def open_folder(self, folderpath):
        if not folderpath or not os.path.exists(folderpath): return
        if platform.system() == 'Darwin':
            subprocess.call(('open', folderpath))
        elif platform.system() == 'Windows':
            os.startfile(folderpath)
        else:
            subprocess.call(('xdg-open', folderpath))

    def delete_history(self):
        self.manager.remove_history(self.data["id"])
        self.setParent(None)
        self.deleteLater()

    def redownload(self):
        url = self.data.get("url")
        if url and self.manager.parent:
            # Tell TabManager to load the URL in a new tab, which triggers a download request
            self.manager.parent.tab_manager.add_new_tab(QUrl(url))


class DownloadTaskWidget(QWidget):
    def __init__(self, download_item, save_path, manager, parent=None):
        super().__init__(parent)
        self.download_item = download_item
        self.save_path = save_path
        self.manager = manager
        self.start_time = time.time()
        self.filename = os.path.basename(save_path)
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        
        info_layout = QHBoxLayout()
        self.name_label = QLabel(self.filename)
        self.name_label.setStyleSheet(_t(self, "font-weight: bold; color: {{text}};"))
        self.name_label.setWordWrap(True)
        self.name_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.status_label = QLabel("Starting...")
        self.status_label.setStyleSheet(_t(self, "color: {{text_soft}}; font-size: 12px;"))
        self.status_label.setWordWrap(True)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        info_layout.addWidget(self.name_label)
        info_layout.addStretch()
        info_layout.addWidget(self.status_label)
        self.layout.addLayout(info_layout)
        
        self.progress = QProgressBar()
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(4)
        self.layout.addWidget(self.progress)
        
        btn_layout = QGridLayout()
        btn_layout.setHorizontalSpacing(8)
        btn_layout.setVerticalSpacing(8)
        self.cancel_btn = QPushButton("Cancel")
        self.open_btn = QPushButton("Open")
        self.folder_btn = QPushButton("Folder")

        for btn in (self.cancel_btn, self.open_btn, self.folder_btn):
            btn.setMinimumWidth(96)
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        self.open_btn.hide()
        self.folder_btn.hide()
        
        btn_layout.addWidget(self.cancel_btn, 0, 0, 1, 2)
        btn_layout.addWidget(self.folder_btn, 1, 0)
        btn_layout.addWidget(self.open_btn, 1, 1)
        self.layout.addLayout(btn_layout)
        
        self.cancel_btn.clicked.connect(self.download_item.cancel)
        self.open_btn.clicked.connect(lambda: self.open_file(self.save_path))
        self.folder_btn.clicked.connect(lambda: self.open_folder(os.path.dirname(self.save_path)))
        
        self.download_item.receivedBytesChanged.connect(self.on_progress)
        self.download_item.totalBytesChanged.connect(self.on_progress)
        self.download_item.stateChanged.connect(self.on_state_changed)
        
        self.setStyleSheet(_t(self, """
            QWidget { background-color: {{surface_alt}}; border-radius: 6px; }
            QPushButton { background-color: {{border}}; color: {{text}}; border: none; padding: 6px 10px; border-radius: 4px; }
            QPushButton:hover { background-color: {{accent}}; color: {{surface}}; }
            QProgressBar { border: none; background-color: {{surface}}; }
            QProgressBar::chunk { background-color: {{accent}}; }
        """))

    def format_size(self, bytes_size):
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_size < 1024.0:
                return f"{bytes_size:.1f} {unit}"
            bytes_size /= 1024.0
        return f"{bytes_size:.1f} TB"

    def on_progress(self):
        received = self.download_item.receivedBytes()
        total = self.download_item.totalBytes()
        
        elapsed = time.time() - self.start_time
        speed = received / elapsed if elapsed > 0 else 0
        speed_str = f"{self.format_size(speed)}/s"
        
        received_str = self.format_size(received)
        if total > 0:
            total_str = self.format_size(total)
            percentage = int((received / total) * 100)
            self.progress.setMaximum(100)
            self.progress.setValue(percentage)
            self.status_label.setText(f"{percentage}% • {speed_str} • {received_str} of {total_str}")
        else:
            self.progress.setMaximum(0)
            self.status_label.setText(f"Downloading • {speed_str} • {received_str}")

    def on_state_changed(self, state):
        if state == QWebEngineDownloadRequest.DownloadState.DownloadCompleted:
            self.progress.setMaximum(100)
            self.progress.setValue(100)
            self.status_label.setText("Completed")
            self.status_label.setStyleSheet(_t(self, "color: {{accent_alt}}; font-size: 12px;"))
            self.cancel_btn.hide()
            self.open_btn.show()
            self.folder_btn.show()
            
            # Save to history
            total = self.download_item.totalBytes()
            if total <= 0: total = self.download_item.receivedBytes()
            self.manager.add_history({
                "id": str(uuid.uuid4()),
                "filename": self.filename,
                "save_path": self.save_path,
                "url": self.download_item.url().toString(),
                "size_str": self.format_size(total),
                "date": datetime.now().strftime("%Y-%m-%d %H:%M")
            })
                
        elif state == QWebEngineDownloadRequest.DownloadState.DownloadCancelled:
            self.status_label.setText("Cancelled")
            self.status_label.setStyleSheet(_t(self, "color: {{danger}}; font-size: 12px;"))
            self.cancel_btn.hide()
            self.progress.hide()
            
        elif state == QWebEngineDownloadRequest.DownloadState.DownloadInterrupted:
            self.status_label.setText("Interrupted")
            self.status_label.setStyleSheet(_t(self, "color: {{danger}}; font-size: 12px;"))
            self.cancel_btn.hide()

    def open_file(self, filepath):
        if platform.system() == 'Darwin':
            subprocess.call(('open', filepath))
        elif platform.system() == 'Windows':
            os.startfile(filepath)
        else:
            subprocess.call(('xdg-open', filepath))

    def open_folder(self, folderpath):
        if platform.system() == 'Darwin':
            subprocess.call(('open', folderpath))
        elif platform.system() == 'Windows':
            os.startfile(folderpath)
        else:
            subprocess.call(('xdg-open', folderpath))


class DownloadsDialog(QDialog):
    def __init__(self, manager, parent=None):
        super().__init__(parent)
        self.manager = manager
        self.setWindowTitle("Downloads Manager")
        self.resize(560, 520)
        self.setMinimumSize(440, 420)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)
        self.setStyleSheet(_t(self, """
            QDialog { background-color: {{surface}}; color: {{text}}; }
            QScrollArea { border: none; background-color: transparent; }
            QPushButton {
                background-color: {{border_soft}};
                color: {{text}};
                border: none;
                padding: 7px 12px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: {{border}}; }
        """))
        
        layout = QVBoxLayout(self)
        
        header_layout = QHBoxLayout()
        title = QLabel("Downloads")
        title.setStyleSheet(_t(self, "color: {{text}}; font-size: 18px; font-weight: bold;"))
        clear_btn = QPushButton("Clear History")
        clear_btn.setStyleSheet(_t(self, "background-color: {{danger}}; color: white; border: none; padding: 5px 10px; border-radius: 4px;"))
        clear_btn.clicked.connect(self.clear_history)
        
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(clear_btn)
        layout.addLayout(header_layout)
        
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_widget)
        self.scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll_layout.setSpacing(10)
        
        self.scroll.setWidget(self.scroll_widget)
        layout.addWidget(self.scroll)
        
        self.refresh_list()

    def refresh_list(self):
        # Clear existing widgets
        for i in reversed(range(self.scroll_layout.count())): 
            widget = self.scroll_layout.itemAt(i).widget()
            if widget is not None:
                widget.setParent(None)
        
        # Add active tasks
        for task in self.manager.active_tasks:
            self.scroll_layout.addWidget(task)
            
        # Add historical tasks
        for hist_item in reversed(self.manager.history):
            widget = DownloadHistoryWidget(hist_item, self.manager, self)
            self.scroll_layout.addWidget(widget)

    def add_active_task(self, task_widget):
        self.scroll_layout.insertWidget(0, task_widget)

    def clear_history(self):
        reply = QMessageBox.question(self, 'Clear History', 'Are you sure you want to clear your download history? (Files will not be deleted)',
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.manager.clear_history()
            self.refresh_list()


class DownloadManager:
    def __init__(self, profile, settings_manager, parent=None):
        self.profile = profile
        self.settings = settings_manager
        self.parent = parent
        self.profile.downloadRequested.connect(self.on_download_requested)
        self.active_tasks = []
        self.history = self.load_history()
        self.dialog = None

    def load_history(self):
        if os.path.exists(DOWNLOADS_FILE):
            try:
                with open(DOWNLOADS_FILE, 'r') as f:
                    return json.load(f)
            except Exception:
                pass
        return []

    def save_history(self):
        with open(DOWNLOADS_FILE, 'w') as f:
            json.dump(self.history, f, indent=4)

    def add_history(self, item_data):
        self.history.append(item_data)
        self.save_history()

    def remove_history(self, item_id):
        self.history = [h for h in self.history if h.get("id") != item_id]
        self.save_history()

    def clear_history(self):
        self.history = []
        self.save_history()

    def get_unique_filename(self, directory, filename):
        base, ext = os.path.splitext(filename)
        counter = 1
        new_path = os.path.join(directory, filename)
        while os.path.exists(new_path):
            new_path = os.path.join(directory, f"{base} ({counter}){ext}")
            counter += 1
        return new_path

    def on_download_requested(self, download_item):
        mode = self.settings.get("download_mode")
        download_dir = self.settings.get("download_dir")
        
        if not os.path.exists(download_dir):
            os.makedirs(download_dir, exist_ok=True)
            
        suggested_name = download_item.downloadFileName()
        if not suggested_name:
            suggested_name = "downloaded_file"

        if mode == "auto":
            save_path = self.get_unique_filename(download_dir, suggested_name)
        else:
            default_path = os.path.join(download_dir, suggested_name)
            save_path, _ = QFileDialog.getSaveFileName(self.parent, "Save File", default_path)
            if not save_path:
                download_item.cancel()
                return

        download_item.setDownloadDirectory(os.path.dirname(save_path))
        download_item.setDownloadFileName(os.path.basename(save_path))
        
        task_widget = DownloadTaskWidget(download_item, save_path, self, self.parent)
        self.active_tasks.append(task_widget)
        
        if self.dialog and self.dialog.isVisible():
            self.dialog.add_active_task(task_widget)
        else:
            self.show_dialog()
            self.dialog.add_active_task(task_widget)
            
        download_item.accept()

    def show_dialog(self):
        if not self.dialog:
            self.dialog = DownloadsDialog(self, self.parent)
        else:
            # Refresh list if reopening to sync history properly
            self.dialog.refresh_list()
        self.dialog.show()
        self.dialog.raise_()
        self.dialog.activateWindow()
