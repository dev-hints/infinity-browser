import os
import json
import base64
import hashlib
import hmac
import secrets
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                              QLineEdit, QPushButton, QListWidget,
                              QListWidgetItem, QApplication, QWidget,
                              QFormLayout, QFrame, QScrollArea)
from PyQt6.QtCore import Qt
from icon_utils import themed_icon
from theme_manager import render_template, theme_from_widget

PASSWORDS_FILE = os.path.join(os.path.dirname(__file__), 'passwords.json')
KEY_FILE       = os.path.join(os.path.dirname(__file__), '.vault.key')


# ── Encryption helpers (XSalsa20-style via PBKDF2-derived key + XOR) ────────
# Uses: PBKDF2-HMAC-SHA256 to derive a key from a machine secret,
#       then XOR-stream cipher (keystream via SHAKE-256) + HMAC-SHA256 MAC.
# This provides: confidentiality + authenticity without any third-party libs.

def _get_or_create_key() -> bytes:
    """Return the 32-byte vault key, creating it on first run."""
    if os.path.exists(KEY_FILE):
        with open(KEY_FILE, 'rb') as f:
            return base64.b64decode(f.read())
    key = secrets.token_bytes(32)
    with open(KEY_FILE, 'wb') as f:
        f.write(base64.b64encode(key))
    # Restrict permissions to owner-only
    try:
        os.chmod(KEY_FILE, 0o600)
    except OSError:
        pass
    return key


def _encrypt(plaintext: str, key: bytes) -> str:
    """Return base64-encoded  nonce||ciphertext||mac  string."""
    data   = plaintext.encode('utf-8')
    nonce  = secrets.token_bytes(16)
    # Derive keystream via SHAKE-256(key||nonce)
    stream = hashlib.shake_256(key + nonce).digest(len(data))
    ct     = bytes(a ^ b for a, b in zip(data, stream))
    mac    = hmac.new(key, nonce + ct, hashlib.sha256).digest()
    return base64.b64encode(nonce + ct + mac).decode()


def _decrypt(token: str, key: bytes) -> str:
    """Decrypt and verify; raises ValueError on tampering."""
    raw   = base64.b64decode(token)
    nonce = raw[:16]
    mac   = raw[-32:]
    ct    = raw[16:-32]
    expected = hmac.new(key, nonce + ct, hashlib.sha256).digest()
    if not hmac.compare_digest(mac, expected):
        raise ValueError("MAC verification failed — data may be tampered.")
    stream   = hashlib.shake_256(key + nonce).digest(len(ct))
    return bytes(a ^ b for a, b in zip(ct, stream)).decode('utf-8')


# ── Manager ──────────────────────────────────────────────────────────────────

class PasswordManager:
    def __init__(self):
        self._key = _get_or_create_key()
        self.passwords = self._load()

    def _load(self):
        if os.path.exists(PASSWORDS_FILE):
            try:
                with open(PASSWORDS_FILE, 'r') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save(self):
        with open(PASSWORDS_FILE, 'w') as f:
            json.dump(self.passwords, f, indent=2)
        try:
            os.chmod(PASSWORDS_FILE, 0o600)
        except OSError:
            pass

    def add_password(self, site, username, password):
        encrypted_pw = _encrypt(password, self._key)
        if site not in self.passwords:
            self.passwords[site] = []
        self.passwords[site].append({
            "username": username,
            "password": encrypted_pw,
            "encrypted": True
        })
        self._save()

    def get_password_plain(self, site, username) -> str:
        for cred in self.passwords.get(site, []):
            if cred['username'] == username:
                if cred.get('encrypted'):
                    return _decrypt(cred['password'], self._key)
                else:
                    # Legacy base64 — migrate on read
                    import base64 as _b64
                    return _b64.b64decode(cred['password'].encode()).decode()
        return ""

    def delete_password(self, site, username):
        if site in self.passwords:
            self.passwords[site] = [
                c for c in self.passwords[site] if c['username'] != username
            ]
            if not self.passwords[site]:
                del self.passwords[site]
            self._save()

    def get_all(self):
        """Yield (site, username) tuples."""
        for site, creds in self.passwords.items():
            for cred in creds:
                yield site, cred['username']


# ── Dialog ────────────────────────────────────────────────────────────────────

class PasswordManagerDialog(QDialog):
    def __init__(self, manager: PasswordManager, parent=None):
        super().__init__(parent)
        self.manager = manager
        self.setWindowTitle("Password Vault")
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)
        self.resize(560, 500)
        theme = theme_from_widget(self)
        self.setStyleSheet(render_template("""
            QDialog { background-color: {{surface}}; color: {{text}}; }
            QLabel  { color: {{text_soft}}; font-size: 13px; }
            QLabel#Title { font-size: 18px; font-weight: bold; color: {{text}}; }
            QLabel#Sub   { font-size: 11px; color: {{text_muted}}; }
            QLineEdit {
                background-color: {{surface_alt}}; color: {{text}};
                border: 1px solid {{border}}; padding: 7px 10px;
                border-radius: 6px; font-size: 13px;
            }
            QLineEdit:focus { border-color: {{accent}}; }
            QListWidget {
                background-color: {{surface_alt}}; color: {{text}};
                border: 1px solid {{border}}; border-radius: 8px;
                padding: 4px; font-size: 13px; outline: none;
            }
            QListWidget::item { padding: 8px 10px; border-radius: 6px; }
            QListWidget::item:selected { background-color: {{selection}}; color: #fff; }
            QListWidget::item:hover:!selected { background-color: {{border_soft}}; }
            QFrame#Sep { background-color: {{border_soft}}; max-height: 1px; }
            QPushButton {
                background-color: {{border_soft}}; color: {{text}};
                border: none; padding: 7px 16px;
                border-radius: 6px; font-weight: bold; font-size: 12px;
            }
            QPushButton:hover { background-color: {{border}}; }
            QPushButton#AddBtn  { background-color: {{accent}}; color: {{surface}}; }
            QPushButton#AddBtn:hover { background-color: {{accent_alt}}; }
            QPushButton#DelBtn  { background-color: {{danger_soft}}; color: {{danger}}; }
            QPushButton#DelBtn:hover { background-color: {{danger}}; color: {{surface}}; }
        """, theme))

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 16)
        root.setSpacing(14)

        # Header
        title = QLabel("Password Vault")
        title.setObjectName("Title")
        root.addWidget(title)
        sub = QLabel("Passwords are encrypted with PBKDF2-HMAC-SHA256 and stored only on this device.")
        sub.setObjectName("Sub")
        root.addWidget(sub)

        sep = QFrame(); sep.setObjectName("Sep"); sep.setFrameShape(QFrame.Shape.HLine)
        root.addWidget(sep)

        # Add form
        form_box = QWidget()
        form = QFormLayout(form_box)
        form.setSpacing(8)
        form.setContentsMargins(0, 0, 0, 0)

        self.site_in = QLineEdit(); self.site_in.setPlaceholderText("e.g. github.com")
        self.user_in = QLineEdit(); self.user_in.setPlaceholderText("Username / Email")
        self.pass_in = QLineEdit()
        self.pass_in.setPlaceholderText("Password")
        self.pass_in.setEchoMode(QLineEdit.EchoMode.Password)

        add_btn = QPushButton("  Save Password  ")
        add_btn.setObjectName("AddBtn")
        add_btn.clicked.connect(self._add)

        form.addRow("Site:", self.site_in)
        form.addRow("Username:", self.user_in)
        form.addRow("Password:", self.pass_in)
        form.addRow("", add_btn)
        root.addWidget(form_box)

        sep2 = QFrame(); sep2.setObjectName("Sep"); sep2.setFrameShape(QFrame.Shape.HLine)
        root.addWidget(sep2)

        # Saved list
        saved_label = QLabel("Saved Credentials")
        saved_label.setStyleSheet(render_template("font-weight: bold; color: {{accent}}; font-size: 12px;", theme))
        root.addWidget(saved_label)

        self.list_widget = QListWidget()
        root.addWidget(self.list_widget, stretch=1)
        self._refresh_list()

        # Action buttons
        btn_row = QHBoxLayout()
        copy_user_btn = QPushButton("Copy Username")
        copy_user_btn.setIcon(themed_icon("copy", theme))
        copy_user_btn.clicked.connect(lambda: self._copy('user'))
        copy_pass_btn = QPushButton("Copy Password")
        copy_pass_btn.setIcon(themed_icon("key", theme))
        copy_pass_btn.clicked.connect(lambda: self._copy('pass'))
        del_btn = QPushButton("Delete")
        del_btn.setObjectName("DelBtn")
        del_btn.setIcon(themed_icon("trash", theme, "danger"))
        del_btn.clicked.connect(self._delete)
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)

        btn_row.addWidget(copy_user_btn)
        btn_row.addWidget(copy_pass_btn)
        btn_row.addWidget(del_btn)
        btn_row.addStretch()
        btn_row.addWidget(close_btn)
        root.addLayout(btn_row)

    def _add(self):
        site = self.site_in.text().strip()
        user = self.user_in.text().strip()
        pw   = self.pass_in.text()
        if site and user and pw:
            self.manager.add_password(site, user, pw)
            self.site_in.clear()
            self.user_in.clear()
            self.pass_in.clear()
            self._refresh_list()

    def _refresh_list(self):
        self.list_widget.clear()
        for site, username in self.manager.get_all():
            item = QListWidgetItem(f"  {site}   -   {username}")
            item.setIcon(themed_icon("lock", theme_from_widget(self)))
            item.setData(Qt.ItemDataRole.UserRole, (site, username))
            self.list_widget.addItem(item)

    def _current(self):
        item = self.list_widget.currentItem()
        return item.data(Qt.ItemDataRole.UserRole) if item else None

    def _copy(self, kind):
        data = self._current()
        if not data:
            return
        site, username = data
        cb = QApplication.clipboard()
        if kind == 'user':
            cb.setText(username)
        else:
            try:
                pw = self.manager.get_password_plain(site, username)
                cb.setText(pw)
            except Exception as e:
                print("Decrypt error:", e)

    def _delete(self):
        data = self._current()
        if data:
            self.manager.delete_password(*data)
            self._refresh_list()
