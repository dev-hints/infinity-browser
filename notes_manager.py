import os
import json
import uuid
from datetime import datetime
from PyQt6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QListWidget, QListWidgetItem, QTextEdit, QLineEdit,
    QPushButton, QLabel, QFrame, QApplication, QInputDialog,
    QMessageBox, QSizePolicy, QToolButton, QMenu
)
from PyQt6.QtCore import Qt, QTimer, QSize
from PyQt6.QtGui import QFont, QKeySequence, QShortcut, QAction
from icon_utils import themed_icon
from theme_manager import render_template, theme_from_widget

NOTES_FILE = os.path.join(os.path.dirname(__file__), 'notes.json')

# ── Data layer ────────────────────────────────────────────────────────────────

class NotesManager:
    def __init__(self):
        self.notes = self._load()

    def _load(self):
        if os.path.exists(NOTES_FILE):
            try:
                with open(NOTES_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    def _save(self):
        try:
            with open(NOTES_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.notes, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving notes: {e}")

    def _now(self):
        return datetime.now().strftime("%Y-%m-%d %H:%M")

    def create(self, title="Untitled Note", content="") -> dict:
        note = {
            "id":       str(uuid.uuid4()),
            "title":    title,
            "content":  content,
            "created":  self._now(),
            "modified": self._now(),
        }
        self.notes.insert(0, note)
        self._save()
        return note

    def update_content(self, note_id, content):
        for n in self.notes:
            if n["id"] == note_id:
                n["content"]  = content
                n["modified"] = self._now()
                self._save()
                return

    def rename(self, note_id, new_title):
        for n in self.notes:
            if n["id"] == note_id:
                n["title"]    = new_title.strip() or "Untitled Note"
                n["modified"] = self._now()
                self._save()
                return

    def delete(self, note_id):
        self.notes = [n for n in self.notes if n["id"] != note_id]
        self._save()

    def get_all(self):
        return self.notes          # sorted newest-first by creation order

    def get_by_id(self, note_id):
        return next((n for n in self.notes if n["id"] == note_id), None)


# ── Dialog ────────────────────────────────────────────────────────────────────

NOTES_STYLE = """
QDialog, QWidget {
    background-color: {{surface}};
    color: {{text}};
    font-family: '{{font_ui}}', 'Segoe UI', 'Helvetica Neue', sans-serif;
}
/* Sidebar */
QListWidget {
    background-color: {{surface_soft}};
    border: none;
    border-right: 1px solid {{border_soft}};
    outline: none;
    padding: 8px;
}
QListWidget::item {
    padding: 12px 16px;
    border-radius: 12px;
    margin: 4px 6px;
    color: {{text_soft}};
    font-size: 14px;
    font-weight: 500;
}
QListWidget::item:selected {
    background-color: {{accent}};
    color: {{surface}};
}
QListWidget::item:hover:!selected {
    background-color: {{surface_alt}};
    color: {{text}};
}
/* Editor */
QTextEdit {
    background-color: {{surface}};
    color: {{text}};
    border: none;
    font-size: 15px;
    font-family: '{{font_mono}}', 'JetBrains Mono', 'Fira Code', monospace;
    padding: 20px;
    selection-background-color: {{selection}};
    line-height: 1.7;
}
QTextEdit::placeholder {
    color: {{text_muted}};
}
/* Title edit */
QLineEdit {
    background-color: transparent;
    color: {{text}};
    border: none;
    border-bottom: 2px solid {{border_soft}};
    font-size: 20px;
    font-weight: 600;
    padding: 8px 4px;
}
QLineEdit:focus { border-bottom-color: {{accent}}; }
QLineEdit::placeholder {
    color: {{text_muted}};
    font-weight: 400;
}
#SearchBox::placeholder {
    color: {{text_muted}};
}
/* Buttons */
QPushButton, QToolButton {
    background-color: {{surface_alt}};
    color: {{text_soft}};
    border: none;
    border-radius: 8px;
    padding: 8px 16px;
    font-size: 13px;
    font-weight: 500;
}
QPushButton:hover, QToolButton:hover {
    background-color: {{border_soft}};
    color: {{text}};
}
QPushButton#NewBtn {
    background-color: {{accent}};
    color: {{surface}};
    border-radius: 21px;
    font-size: 30px;
    font-weight: bold;
}
QPushButton#NewBtn:hover { background-color: {{accent_alt}}; }
QPushButton#DelBtn { color: {{danger}}; background-color: {{danger_soft}}; }
QPushButton#DelBtn:hover { background-color: {{danger}}; color: {{surface}}; }
/* Labels */
QLabel#Meta {
    color: {{text_muted}};
    font-size: 12px;
    padding: 0 4px;
}
QLabel#SideTitle {
    color: {{accent}};
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 2px;
    text-transform: uppercase;
    padding: 8px 16px 6px 16px;
}
QLabel#WordCount {
    color: {{text_muted}};
    font-size: 12px;
    padding: 4px 10px;
}
QFrame#VSep { background-color: {{border_soft}}; max-width: 1px; }
QFrame#HSep { background-color: {{border_soft}}; max-height: 1px; }
QSplitter::handle { background-color: {{border_soft}}; width: 1px; }
"""


class NotesDialog(QDialog):
    def __init__(self, manager: NotesManager, parent=None):
        super().__init__(parent)
        self.manager = manager
        self.current_id = None
        self._auto_save_timer = QTimer(self)
        self._auto_save_timer.setSingleShot(True)
        self._auto_save_timer.timeout.connect(self._auto_save)

        self.setWindowTitle("Notes")
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)
        self.resize(900, 600)
        self.theme = theme_from_widget(self)
        self.setStyleSheet(render_template(NOTES_STYLE, self.theme))

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(1)

        # ── Left sidebar ──────────────────────────────────────────────────────
        sidebar = QWidget()
        sidebar.setStyleSheet(render_template("background-color: {{surface_soft}};", self.theme))
        sidebar.setFixedWidth(260)
        sidebar_lay = QVBoxLayout(sidebar)
        sidebar_lay.setContentsMargins(0, 0, 0, 0)
        sidebar_lay.setSpacing(0)

        # Header
        hdr = QWidget()
        hdr.setStyleSheet(render_template("background-color: {{surface_soft}}; border-bottom: 1px solid {{border_soft}};", self.theme))
        hdr_lay = QHBoxLayout(hdr)
        hdr_lay.setContentsMargins(10, 10, 10, 10)
        hdr_title = QLabel("NOTES")
        hdr_title.setObjectName("SideTitle")
        hdr_title.setStyleSheet(render_template("color: {{accent}}; font-size: 11px; font-weight: bold; letter-spacing: 1.5px;", self.theme))
        new_btn = QPushButton()
        new_btn.setObjectName("NewBtn")
        new_btn.setFixedSize(42, 42)
        new_btn.setIcon(themed_icon("plus", self.theme))
        new_btn.setIconSize(QSize(20, 20))
        new_btn.setToolTip("Create New Note (Ctrl+N)")
        new_btn.clicked.connect(self._new_note)
        hdr_lay.addWidget(hdr_title)
        hdr_lay.addStretch()
        hdr_lay.addWidget(new_btn)
        sidebar_lay.addWidget(hdr)

        # Search
        self.search_box = QLineEdit()
        self.search_box.setObjectName("SearchBox")
        self.search_box.setPlaceholderText("Search notes...")
        self.search_box.setStyleSheet(render_template(
            "background-color: {{surface_alt}}; color: {{text}}; border: none;"
            "border-bottom: 1px solid {{border_soft}}; padding: 8px 12px; font-size: 12px;",
            self.theme,
        ) + f" QLineEdit::placeholder {{ color: {render_template('{{text_muted}}', self.theme)}; }}")
        self.search_box.textChanged.connect(self._filter_list)
        sidebar_lay.addWidget(self.search_box)

        # Note list
        self.note_list = QListWidget()
        self.note_list.currentItemChanged.connect(self._on_select)
        sidebar_lay.addWidget(self.note_list, stretch=1)

        # Note count
        self.count_lbl = QLabel()
        self.count_lbl.setObjectName("WordCount")
        self.count_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sidebar_lay.addWidget(self.count_lbl)

        splitter.addWidget(sidebar)

        # ── Right editor panel ────────────────────────────────────────────────
        editor_panel = QWidget()
        editor_lay = QVBoxLayout(editor_panel)
        editor_lay.setContentsMargins(0, 0, 0, 0)
        editor_lay.setSpacing(0)

        # Toolbar
        toolbar = QWidget()
        toolbar.setStyleSheet(render_template("background-color: {{surface_alt}}; border-bottom: 1px solid {{border_soft}};", self.theme))
        tb_lay = QHBoxLayout(toolbar)
        tb_lay.setContentsMargins(14, 8, 14, 8)
        tb_lay.setSpacing(6)

        self.rename_btn = QPushButton("Rename")
        self.rename_btn.setIcon(themed_icon("edit", self.theme))
        self.rename_btn.clicked.connect(self._rename)
        self.copy_btn   = QPushButton("Copy")
        self.copy_btn.setIcon(themed_icon("copy", self.theme))
        self.copy_btn.clicked.connect(self._copy)
        self.export_btn = QPushButton("Export")
        self.export_btn.setIcon(themed_icon("save", self.theme))
        self.export_btn.clicked.connect(self._export)
        self.del_btn    = QPushButton("Delete")
        self.del_btn.setIcon(themed_icon("trash", self.theme, "danger"))
        self.del_btn.setObjectName("DelBtn")
        self.del_btn.clicked.connect(self._delete)
        self.word_count_lbl = QLabel()
        self.word_count_lbl.setObjectName("WordCount")

        tb_lay.addWidget(self.rename_btn)
        tb_lay.addWidget(self.copy_btn)
        tb_lay.addWidget(self.export_btn)
        tb_lay.addWidget(self.del_btn)
        tb_lay.addStretch()
        tb_lay.addWidget(self.word_count_lbl)
        editor_lay.addWidget(toolbar)

        # Title area
        title_bar = QWidget()
        title_bar.setStyleSheet(render_template("background-color: {{surface}}; padding: 0 16px;", self.theme))
        title_bar_lay = QVBoxLayout(title_bar)
        title_bar_lay.setContentsMargins(16, 14, 16, 8)
        title_bar_lay.setSpacing(4)
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("Note title…")
        self.title_edit.editingFinished.connect(self._title_changed)
        self.meta_lbl = QLabel()
        self.meta_lbl.setObjectName("Meta")
        title_bar_lay.addWidget(self.title_edit)
        title_bar_lay.addWidget(self.meta_lbl)
        editor_lay.addWidget(title_bar)

        sep = QFrame(); sep.setObjectName("HSep"); sep.setFrameShape(QFrame.Shape.HLine)
        editor_lay.addWidget(sep)

        # Editor
        self.editor = QTextEdit()
        self.editor.setPlaceholderText("Start writing your note here…")
        self.editor.textChanged.connect(self._on_text_changed)
        editor_lay.addWidget(self.editor, stretch=1)

        # Status bar
        status = QWidget()
        status.setStyleSheet(render_template("background-color: {{surface_soft}}; border-top: 1px solid {{border_soft}};", self.theme))
        status_lay = QHBoxLayout(status)
        status_lay.setContentsMargins(14, 4, 14, 4)
        self.status_lbl = QLabel("Select or create a note to begin")
        self.status_lbl.setObjectName("WordCount")
        status_lay.addWidget(self.status_lbl)
        editor_lay.addWidget(status)

        splitter.addWidget(editor_panel)
        splitter.setSizes([260, 640])
        root.addWidget(splitter)

        # Shortcuts
        new_sc = QShortcut(QKeySequence("Ctrl+N"), self)
        new_sc.activated.connect(self._new_note)

        self._set_editor_enabled(False)
        self._refresh_list()

    # ── List management ───────────────────────────────────────────────────────

    def _refresh_list(self, filter_text=""):
        self.note_list.blockSignals(True)
        self.note_list.clear()
        notes = self.manager.get_all()
        shown = 0
        for note in notes:
            if filter_text.lower() not in note["title"].lower() and \
               filter_text.lower() not in note["content"].lower():
                continue
            item = QListWidgetItem()
            preview = note["content"].replace('\n', ' ')[:50]
            item.setText(f"{note['title']}\n{preview or '—'}")
            item.setData(Qt.ItemDataRole.UserRole, note["id"])
            self.note_list.addItem(item)
            shown += 1
        self.count_lbl.setText(f"{shown} note{'s' if shown != 1 else ''}")
        self.note_list.blockSignals(False)

        # Re-select current note if still visible
        if self.current_id:
            for i in range(self.note_list.count()):
                if self.note_list.item(i).data(Qt.ItemDataRole.UserRole) == self.current_id:
                    self.note_list.setCurrentRow(i)
                    break

    def _filter_list(self, text):
        self._refresh_list(text)

    def _on_select(self, current, _previous):
        if not current:
            return
        note_id = current.data(Qt.ItemDataRole.UserRole)
        self._load_note(note_id)

    def _load_note(self, note_id):
        self._flush_current()
        note = self.manager.get_by_id(note_id)
        if not note:
            return
        self.current_id = note_id
        self.title_edit.setText(note["title"])
        self.editor.blockSignals(True)
        self.editor.setPlainText(note["content"])
        self.editor.blockSignals(False)
        self.meta_lbl.setText(f"Created {note['created']}  ·  Modified {note['modified']}")
        self._update_word_count()
        self._set_editor_enabled(True)
        self.status_lbl.setText(f"Editing: {note['title']}")

    # ── Actions ───────────────────────────────────────────────────────────────

    def _new_note(self):
        note = self.manager.create("Untitled Note")
        self._refresh_list()
        # Select the new note
        for i in range(self.note_list.count()):
            if self.note_list.item(i).data(Qt.ItemDataRole.UserRole) == note["id"]:
                self.note_list.setCurrentRow(i)
                break
        self.title_edit.setFocus()
        self.title_edit.selectAll()

    def _rename(self):
        if not self.current_id:
            return
        note = self.manager.get_by_id(self.current_id)
        new_title, ok = QInputDialog.getText(
            self, "Rename Note", "Enter new title:", text=note["title"]
        )
        if ok and new_title.strip():
            self.manager.rename(self.current_id, new_title.strip())
            self.title_edit.setText(new_title.strip())
            self.status_lbl.setText(f"Renamed to: {new_title.strip()}")
            self._refresh_list()

    def _title_changed(self):
        if self.current_id:
            new_title = self.title_edit.text().strip() or "Untitled Note"
            self.manager.rename(self.current_id, new_title)
            self._refresh_list()

    def _copy(self):
        if not self.current_id:
            return
        note = self.manager.get_by_id(self.current_id)
        QApplication.clipboard().setText(note['content'])
        self.status_lbl.setText("✓ Note content copied to clipboard")
        QTimer.singleShot(2000, lambda: self.status_lbl.setText(f"Editing: {note['title']}"))

    def _export(self):
        if not self.current_id:
            return
        note = self.manager.get_by_id(self.current_id)
        if not note:
            return
        from PyQt6.QtWidgets import QFileDialog
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Export Note", f"{note['title']}.txt", "Text Files (*.txt)"
        )
        if filepath:
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(f"Title: {note['title']}\n")
                    f.write(f"Created: {note['created']}\n")
                    f.write(f"Modified: {note['modified']}\n\n")
                    f.write(note['content'])
                self.status_lbl.setText("✓ Note exported to file")
                QTimer.singleShot(2000, lambda: self.status_lbl.setText(f"Editing: {note['title']}"))
            except Exception as e:
                QMessageBox.warning(self, "Export Failed", f"Could not export note: {e}")

    def _delete(self):
        if not self.current_id:
            return
        note = self.manager.get_by_id(self.current_id)
        reply = QMessageBox.question(
            self, "Delete Note",
            f"Delete \"{note['title']}\"?\nThis cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.manager.delete(self.current_id)
            self.current_id = None
            self._set_editor_enabled(False)
            self.title_edit.clear()
            self.editor.clear()
            self.meta_lbl.clear()
            self.status_lbl.setText("Note deleted")
            self._refresh_list()

    def _on_text_changed(self):
        self._update_word_count()
        # Debounce auto-save: save 800ms after typing stops
        self._auto_save_timer.start(800)

    def _auto_save(self):
        if self.current_id:
            content = self.editor.toPlainText()
            self.manager.update_content(self.current_id, content)
            note = self.manager.get_by_id(self.current_id)
            if note:
                self.meta_lbl.setText(
                    f"Created {note['created']}  ·  Modified {note['modified']}"
                )
            self._refresh_list()

    def _flush_current(self):
        """Save immediately when switching away from a note."""
        if self.current_id:
            content = self.editor.toPlainText()
            self.manager.update_content(self.current_id, content)

    def _update_word_count(self):
        text  = self.editor.toPlainText()
        words = len(text.split()) if text.strip() else 0
        chars = len(text)
        self.word_count_lbl.setText(f"{words} words  ·  {chars} chars")

    def _set_editor_enabled(self, enabled: bool):
        self.editor.setEnabled(enabled)
        self.title_edit.setEnabled(enabled)
        self.rename_btn.setEnabled(enabled)
        self.copy_btn.setEnabled(enabled)
        self.del_btn.setEnabled(enabled)
        if not enabled:
            self.word_count_lbl.clear()
            self.status_lbl.setText("Select or create a note to begin")

    def closeEvent(self, event):
        self._flush_current()
        super().closeEvent(event)
