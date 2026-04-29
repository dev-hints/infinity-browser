from io import BytesIO

import qrcode
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QFileDialog, QMessageBox
)

from theme_manager import render_template, theme_from_widget

QR_STYLE = """
QDialog { background-color: {{surface}}; color: {{text}}; }
QLabel { color: {{text_soft}}; }
QLabel#Title {
    color: {{text}};
    font-size: 18px;
    font-weight: bold;
}
QLabel#Preview {
    background-color: white;
    border: 1px solid {{border_soft}};
    border-radius: 8px;
    padding: 16px;
}
QLineEdit {
    background-color: {{surface_alt}};
    color: {{text}};
    border: 1px solid {{border}};
    border-radius: 8px;
    padding: 9px 12px;
    selection-background-color: {{accent}};
}
QLineEdit:focus { border-color: {{accent}}; }
QPushButton {
    background-color: {{border_soft}};
    color: {{text}};
    border: none;
    border-radius: 6px;
    padding: 8px 14px;
    font-weight: bold;
}
QPushButton:hover { background-color: {{border}}; }
QPushButton#Primary {
    background-color: {{accent}};
    color: {{surface}};
}
"""


class QRGeneratorDialog(QDialog):
    def __init__(self, initial_text="", parent=None):
        super().__init__(parent)
        self.setWindowTitle("QR Generator")
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)
        self.resize(460, 560)
        self._pixmap = None
        self.theme = theme_from_widget(self)
        self.setStyleSheet(render_template(QR_STYLE, self.theme))

        root = QVBoxLayout(self)
        root.setContentsMargins(22, 20, 22, 20)
        root.setSpacing(14)

        title = QLabel("QR Generator")
        title.setObjectName("Title")
        root.addWidget(title)

        hint = QLabel("Create a QR code for the current page, a website, or any text.")
        hint.setWordWrap(True)
        root.addWidget(hint)

        self.input = QLineEdit()
        self.input.setPlaceholderText("Website URL or text")
        self.input.setText(initial_text)
        self.input.returnPressed.connect(self.generate)
        root.addWidget(self.input)

        row = QHBoxLayout()
        current_btn = QPushButton("Current Page")
        current_btn.clicked.connect(self.use_current_page)
        row.addWidget(current_btn)

        generate_btn = QPushButton("Generate")
        generate_btn.setObjectName("Primary")
        generate_btn.clicked.connect(self.generate)
        row.addWidget(generate_btn)
        root.addLayout(row)

        self.preview = QLabel()
        self.preview.setObjectName("Preview")
        self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview.setMinimumSize(320, 320)
        root.addWidget(self.preview, stretch=1)

        actions = QHBoxLayout()
        self.copy_btn = QPushButton("Copy PNG")
        self.copy_btn.clicked.connect(self.copy_to_clipboard)
        actions.addWidget(self.copy_btn)

        self.save_btn = QPushButton("Save PNG")
        self.save_btn.clicked.connect(self.save_png)
        actions.addWidget(self.save_btn)
        root.addLayout(actions)

        self._set_actions_enabled(False)
        if initial_text:
            self.generate()

    def use_current_page(self):
        if self.parent() and hasattr(self.parent(), "current_page_url"):
            current_url = self.parent().current_page_url()
            if current_url:
                self.input.setText(current_url)
        self.generate()

    def generate(self):
        text = self.input.text().strip()
        if not text:
            QMessageBox.warning(self, "Missing Text", "Enter a website URL or text first.")
            return

        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=12,
            border=2,
        )
        qr.add_data(text)
        qr.make(fit=True)
        image = qr.make_image(fill_color="black", back_color="white").convert("RGB")

        buffer = BytesIO()
        image.save(buffer, format="PNG")
        pixmap = QPixmap()
        pixmap.loadFromData(buffer.getvalue(), "PNG")
        self._pixmap = pixmap
        self.preview.setPixmap(
            pixmap.scaled(
                320, 320,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )
        self._set_actions_enabled(True)

    def copy_to_clipboard(self):
        if not self._pixmap:
            return
        from PyQt6.QtWidgets import QApplication
        QApplication.clipboard().setPixmap(self._pixmap)

    def save_png(self):
        if not self._pixmap:
            return
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save QR Code",
            "qr-code.png",
            "PNG Images (*.png)"
        )
        if path:
            if not path.lower().endswith(".png"):
                path += ".png"
            self._pixmap.save(path, "PNG")

    def _set_actions_enabled(self, enabled):
        self.copy_btn.setEnabled(enabled)
        self.save_btn.setEnabled(enabled)
