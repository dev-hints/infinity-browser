import json
import os
import shutil
import sys
import time
import uuid
from datetime import datetime

from PyQt6.QtCore import QProcess, Qt
from PyQt6.QtGui import QTextCursor
from PyQt6.QtWidgets import (
    QCheckBox, QComboBox, QDialog, QFileDialog, QFormLayout, QGroupBox,
    QHBoxLayout, QLabel, QLineEdit, QMessageBox, QProgressBar, QPushButton,
    QTextEdit, QVBoxLayout
)

from theme_manager import render_template, theme_from_widget

DOWNLOAD_HISTORY_EXTS = {
    ".mp4", ".mkv", ".webm", ".mov", ".avi",
    ".mp3", ".m4a", ".opus", ".ogg", ".wav", ".flac",
}


STYLE = """
QDialog {
    background-color: {{surface}};
    color: {{text}};
}
QGroupBox {
    border: 1px solid {{border_soft}};
    border-radius: 8px;
    margin-top: 14px;
    padding: 12px 10px 10px 10px;
    color: {{accent}};
    font-weight: bold;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 4px;
}
QLabel {
    color: {{text_soft}};
}
QLabel#Title {
    color: {{text}};
    font-size: 18px;
    font-weight: bold;
}
QLineEdit, QComboBox, QTextEdit {
    background-color: {{surface_alt}};
    color: {{text}};
    border: 1px solid {{border}};
    border-radius: 6px;
    padding: 6px 10px;
}
QLineEdit:focus, QComboBox:focus, QTextEdit:focus {
    border-color: {{accent}};
}
QCheckBox {
    color: {{text_soft}};
    spacing: 8px;
}
QPushButton {
    background-color: {{border_soft}};
    color: {{text}};
    border: none;
    border-radius: 6px;
    padding: 7px 16px;
    font-weight: bold;
}
QPushButton:hover {
    background-color: {{border}};
}
QPushButton#Primary {
    background-color: {{accent}};
    color: {{surface}};
}
QPushButton#Primary:hover {
    background-color: {{accent_alt}};
}
QProgressBar {
    background-color: {{surface_alt}};
    border: none;
    border-radius: 3px;
    height: 6px;
}
QProgressBar::chunk {
    background-color: {{accent}};
    border-radius: 3px;
}
"""


def is_youtube_url(url: str) -> bool:
    lower = (url or "").lower()
    return "youtube.com/watch" in lower or "youtu.be/" in lower or "youtube.com/shorts/" in lower


def _yt_dlp_command():
    binary = shutil.which("yt-dlp")
    if binary:
        return [binary]
    return [sys.executable, "-m", "yt_dlp"]


def _format_duration(seconds):
    try:
        seconds = int(seconds or 0)
    except (TypeError, ValueError):
        return "Unknown duration"
    minutes, sec = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{sec:02d}"
    return f"{minutes}:{sec:02d}"


class YouTubeDownloaderDialog(QDialog):
    def __init__(self, initial_url="", default_dir=None, parent=None):
        super().__init__(parent)
        self.process = None
        self.metadata = None
        self._downloaded_paths = []
        self._download_started_at = 0
        self._download_output_dir = ""
        self.setWindowTitle("YouTube Downloader")
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)
        self.resize(700, 620)
        self.setStyleSheet(render_template(STYLE, theme_from_widget(self)))

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(12)

        title = QLabel("YouTube Downloader")
        title.setObjectName("Title")
        root.addWidget(title)

        source_group = QGroupBox("Source")
        source_form = QFormLayout(source_group)
        source_form.setSpacing(10)
        self.url_input = QLineEdit(initial_url)
        self.url_input.setPlaceholderText("Paste a YouTube video URL")
        source_form.addRow("Video URL:", self.url_input)

        fetch_row = QHBoxLayout()
        self.fetch_btn = QPushButton("Fetch Info")
        self.fetch_btn.clicked.connect(self.fetch_info)
        fetch_row.addStretch()
        fetch_row.addWidget(self.fetch_btn)
        source_form.addRow("", fetch_row)
        root.addWidget(source_group)

        info_group = QGroupBox("Video Info")
        info_lay = QVBoxLayout(info_group)
        self.info_label = QLabel("Fetch info to see the title, channel, duration, and available formats.")
        self.info_label.setWordWrap(True)
        info_lay.addWidget(self.info_label)
        root.addWidget(info_group)

        options_group = QGroupBox("Download Options")
        options_form = QFormLayout(options_group)
        options_form.setSpacing(10)

        self.mode_combo = QComboBox()
        self.mode_combo.addItem("Video + audio", "video")
        self.mode_combo.addItem("Audio only", "audio")
        self.mode_combo.currentIndexChanged.connect(self._sync_options)
        options_form.addRow("Type:", self.mode_combo)

        self.quality_combo = QComboBox()
        self.quality_combo.addItem("Best available", "best")
        for h in (2160, 1440, 1080, 720, 480, 360):
            self.quality_combo.addItem(f"Up to {h}p", h)
        options_form.addRow("Quality:", self.quality_combo)

        self.format_combo = QComboBox()
        self.format_combo.addItem("Best matching format", "")
        options_form.addRow("Exact Format:", self.format_combo)

        self.audio_combo = QComboBox()
        self.audio_combo.addItem("Original audio", "")
        self.audio_combo.addItem("MP3", "mp3")
        self.audio_combo.addItem("M4A", "m4a")
        self.audio_combo.addItem("Opus", "opus")
        options_form.addRow("Audio Format:", self.audio_combo)

        self.subs_cb = QCheckBox("Download subtitles when available")
        options_form.addRow("", self.subs_cb)
        self.thumb_cb = QCheckBox("Download thumbnail")
        options_form.addRow("", self.thumb_cb)

        dir_row = QHBoxLayout()
        self.dir_input = QLineEdit(default_dir or os.path.join(os.path.expanduser("~"), "Downloads"))
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self.browse_dir)
        dir_row.addWidget(self.dir_input)
        dir_row.addWidget(browse_btn)
        options_form.addRow("Save To:", dir_row)
        root.addWidget(options_group)

        self.progress = QProgressBar()
        self.progress.setTextVisible(False)
        self.progress.hide()
        root.addWidget(self.progress)

        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setMinimumHeight(120)
        root.addWidget(self.log)

        btn_row = QHBoxLayout()
        self.status_label = QLabel("")
        btn_row.addWidget(self.status_label)
        btn_row.addStretch()
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.reject)
        self.download_btn = QPushButton("Download")
        self.download_btn.setObjectName("Primary")
        self.download_btn.clicked.connect(self.start_download)
        btn_row.addWidget(close_btn)
        btn_row.addWidget(self.download_btn)
        root.addLayout(btn_row)

        self._sync_options()
        if initial_url:
            self.fetch_info()

    def browse_dir(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Download Folder", self.dir_input.text())
        if directory:
            self.dir_input.setText(directory)

    def fetch_info(self):
        url = self.url_input.text().strip()
        if not self._validate_url(url):
            return
        self._run_process(_yt_dlp_command() + ["--dump-json", "--no-playlist", url], "fetch")
        self.status_label.setText("Fetching video info...")
        self.fetch_btn.setEnabled(False)

    def start_download(self):
        url = self.url_input.text().strip()
        if not self._validate_url(url):
            return
        output_dir = self.dir_input.text().strip()
        if not output_dir:
            QMessageBox.warning(self, "Missing Folder", "Choose a download folder first.")
            return
        os.makedirs(output_dir, exist_ok=True)

        args = _yt_dlp_command()
        args += [
            "--newline",
            "--no-playlist",
            "--print",
            "after_move:filepath",
            "-P",
            output_dir,
            "-o",
            "%(title).200s.%(ext)s",
        ]
        format_selector = self._format_selector()
        if format_selector:
            args += ["-f", format_selector]
        audio_format = self.audio_combo.currentData()
        if self.mode_combo.currentData() == "audio":
            args += ["-x"]
            if audio_format:
                args += ["--audio-format", audio_format]
        else:
            args += ["--merge-output-format", "mp4"]
        if self.subs_cb.isChecked():
            args += ["--write-subs", "--write-auto-subs", "--sub-langs", "all,-live_chat"]
        if self.thumb_cb.isChecked():
            args += ["--write-thumbnail"]
        args.append(url)

        self._downloaded_paths = []
        self._download_started_at = time.time()
        self._download_output_dir = output_dir
        self._run_process(args, "download")
        self.progress.show()
        self.progress.setMaximum(0)
        self.download_btn.setEnabled(False)
        self.fetch_btn.setEnabled(False)
        self.status_label.setText("Downloading...")

    def _run_process(self, args, mode):
        if self.process and self.process.state() != QProcess.ProcessState.NotRunning:
            QMessageBox.information(self, "Busy", "A downloader task is already running.")
            return
        self.log.clear()
        self.process = QProcess(self)
        self.process.setProperty("mode", mode)
        self.process.setProgram(args[0])
        self.process.setArguments(args[1:])
        self.process.readyReadStandardOutput.connect(self._read_stdout)
        self.process.readyReadStandardError.connect(self._read_stderr)
        self.process.finished.connect(self._process_finished)
        self.process.start()

    def _read_stdout(self):
        text = bytes(self.process.readAllStandardOutput()).decode("utf-8", errors="replace")
        if self.process.property("mode") == "fetch":
            self._fetch_output = getattr(self, "_fetch_output", "") + text
        else:
            self._append_log(text)
            self._collect_downloaded_paths(text)
            self._update_progress_from_text(text)

    def _read_stderr(self):
        text = bytes(self.process.readAllStandardError()).decode("utf-8", errors="replace")
        self._append_log(text)

    def _process_finished(self, exit_code, _status):
        mode = self.process.property("mode")
        self.fetch_btn.setEnabled(True)
        self.download_btn.setEnabled(True)
        self.progress.hide()
        if mode == "fetch":
            raw = getattr(self, "_fetch_output", "")
            self._fetch_output = ""
            if exit_code == 0:
                self._load_metadata(raw)
                self.status_label.setText("Info loaded")
            else:
                self.status_label.setText("Could not fetch info")
                self._show_dependency_help()
        else:
            if exit_code == 0:
                self._register_downloads()
                self.status_label.setText("Download complete")
                QMessageBox.information(self, "Download Complete", "The download finished successfully.")
            else:
                self.status_label.setText("Download failed")
                self._show_dependency_help()

    def _load_metadata(self, raw):
        try:
            self.metadata = json.loads(raw)
        except json.JSONDecodeError:
            QMessageBox.warning(self, "Info Error", "Could not read video info from yt-dlp.")
            return
        title = self.metadata.get("title") or "Untitled"
        channel = self.metadata.get("uploader") or self.metadata.get("channel") or "Unknown channel"
        duration = _format_duration(self.metadata.get("duration"))
        self.info_label.setText(f"{title}\n{channel} • {duration}")
        self._populate_formats()

    def _populate_formats(self):
        self.format_combo.clear()
        self.format_combo.addItem("Best matching format", "")
        formats = self.metadata.get("formats", []) if self.metadata else []
        seen = set()
        for item in formats:
            format_id = item.get("format_id")
            if not format_id or format_id in seen:
                continue
            seen.add(format_id)
            height = item.get("height")
            ext = item.get("ext") or "?"
            fps = item.get("fps")
            acodec = item.get("acodec")
            vcodec = item.get("vcodec")
            size = item.get("filesize") or item.get("filesize_approx")
            parts = [format_id, ext]
            if height:
                parts.append(f"{height}p")
            if fps:
                parts.append(f"{fps}fps")
            if vcodec and vcodec != "none":
                parts.append("video")
            if acodec and acodec != "none":
                parts.append("audio")
            if size:
                parts.append(self._format_size(size))
            self.format_combo.addItem(" • ".join(parts), format_id)

    def _format_selector(self):
        exact = self.format_combo.currentData()
        if exact:
            return exact
        if self.mode_combo.currentData() == "audio":
            return "bestaudio/best"
        quality = self.quality_combo.currentData()
        if quality == "best":
            return "bv*+ba/best"
        return f"bv*[height<={quality}]+ba/b[height<={quality}]"

    def _sync_options(self):
        audio_only = self.mode_combo.currentData() == "audio"
        self.quality_combo.setEnabled(not audio_only)
        self.audio_combo.setEnabled(audio_only)

    def _validate_url(self, url):
        if not url:
            QMessageBox.warning(self, "Missing URL", "Paste or open a YouTube video URL first.")
            return False
        if not is_youtube_url(url):
            QMessageBox.warning(self, "Unsupported URL", "This downloader expects a YouTube video URL.")
            return False
        return True

    def _append_log(self, text):
        if text.strip():
            self.log.moveCursor(QTextCursor.MoveOperation.End)
            self.log.insertPlainText(text)
            self.log.moveCursor(QTextCursor.MoveOperation.End)

    def _update_progress_from_text(self, text):
        if "[download]" in text and "%" in text:
            self.progress.setMaximum(100)
            for chunk in text.split():
                if chunk.endswith("%"):
                    try:
                        self.progress.setValue(int(float(chunk[:-1])))
                        break
                    except ValueError:
                        pass

    def _collect_downloaded_paths(self, text):
        output_dir = os.path.abspath(self._download_output_dir or self.dir_input.text().strip())
        for line in text.splitlines():
            candidate = line.strip()
            if not candidate or candidate.startswith("["):
                continue
            if not os.path.isabs(candidate):
                candidate = os.path.join(output_dir, candidate)
            candidate = os.path.abspath(os.path.expanduser(candidate))
            if os.path.exists(candidate) and os.path.isfile(candidate):
                self._add_downloaded_path(candidate)

    def _add_downloaded_path(self, path):
        if os.path.splitext(path)[1].lower() not in DOWNLOAD_HISTORY_EXTS:
            return
        if path not in self._downloaded_paths:
            self._downloaded_paths.append(path)

    def _fallback_downloaded_paths(self):
        output_dir = self._download_output_dir or self.dir_input.text().strip()
        if not output_dir or not os.path.isdir(output_dir):
            return []
        candidates = []
        for name in os.listdir(output_dir):
            path = os.path.join(output_dir, name)
            if not os.path.isfile(path):
                continue
            if os.path.splitext(path)[1].lower() not in DOWNLOAD_HISTORY_EXTS:
                continue
            try:
                if os.path.getmtime(path) >= self._download_started_at - 2:
                    candidates.append(path)
            except OSError:
                continue
        candidates.sort(key=lambda p: os.path.getmtime(p), reverse=True)
        return candidates[:3]

    def _register_downloads(self):
        for path in self._fallback_downloaded_paths():
            self._add_downloaded_path(os.path.abspath(path))
        manager = getattr(self.parent(), "download_manager", None)
        if not manager:
            return
        source_url = self.url_input.text().strip()
        for path in self._downloaded_paths:
            if not os.path.exists(path):
                continue
            manager.add_history({
                "id": str(uuid.uuid4()),
                "filename": os.path.basename(path),
                "save_path": path,
                "url": source_url,
                "size_str": self._format_size(os.path.getsize(path)),
                "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "source": "YouTube Downloader",
            })
        if manager.dialog and manager.dialog.isVisible():
            manager.dialog.refresh_list()

    def _show_dependency_help(self):
        self._append_log("\nInstall or update yt-dlp if this failed because the downloader is missing.\n")

    def _format_size(self, size):
        size = float(size)
        for unit in ("B", "KB", "MB", "GB"):
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"

    def closeEvent(self, event):
        if self.process and self.process.state() != QProcess.ProcessState.NotRunning:
            self.process.kill()
        super().closeEvent(event)
