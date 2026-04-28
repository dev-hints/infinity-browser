from __future__ import annotations

import os
from typing import Dict

from PyQt6.QtGui import QColor, QFont, QPalette

BASE_DIR = os.path.dirname(__file__)
STYLE_FILE = os.path.join(BASE_DIR, "styles.qss")

THEMES: Dict[str, Dict[str, str]] = {
    "dark": {
        "window_bg": "#0f1015",
        "window_text": "#e0e0e0",
        "surface": "#1a1b26",
        "surface_alt": "#24283b",
        "surface_soft": "#1f2335",
        "border": "#414868",
        "border_soft": "#2f334d",
        "text": "#c0caf5",
        "text_soft": "#a9b1d6",
        "text_muted": "#565f89",
        "accent": "#7aa2f7",
        "accent_alt": "#89b4fa",
        "danger": "#f7768e",
        "danger_soft": "#3b1219",
        "selection": "#3d59a1",
        "bookmark": "#e0af68",
        "link": "#bb9af7",
        "font_ui": "Noto Sans",
        "font_mono": "JetBrains Mono",
    },
    "light": {
        "window_bg": "#f5f7fb",
        "window_text": "#1e2432",
        "surface": "#ffffff",
        "surface_alt": "#eef2fb",
        "surface_soft": "#e6ecf8",
        "border": "#c7d1e5",
        "border_soft": "#d8e0ef",
        "text": "#1f2b45",
        "text_soft": "#33476b",
        "text_muted": "#5f7092",
        "accent": "#2e6be6",
        "accent_alt": "#4a82ef",
        "danger": "#cc334f",
        "danger_soft": "#fce9ec",
        "selection": "#c7dafd",
        "bookmark": "#b7791f",
        "link": "#6e59cf",
        "font_ui": "Noto Sans",
        "font_mono": "JetBrains Mono",
    },
}


def normalize_theme(theme_name: str | None) -> str:
    if not theme_name:
        return "dark"
    return "light" if str(theme_name).lower() == "light" else "dark"


def tokens_for(theme_name: str | None) -> Dict[str, str]:
    return THEMES[normalize_theme(theme_name)].copy()


def theme_from_widget(widget, fallback: str = "dark") -> str:
    current = widget
    for _ in range(8):
        if current is None:
            break
        try:
            if hasattr(current, "settings_manager"):
                return normalize_theme(current.settings_manager.get("ui_theme", fallback))
            parent = current.parent() if hasattr(current, "parent") else None
        except Exception:
            parent = None
        current = parent
    return normalize_theme(fallback)


def render_template(template: str, theme_name: str | None) -> str:
    out = template
    for key, value in tokens_for(theme_name).items():
        out = out.replace(f"{{{{{key}}}}}", value)
    return out


def load_app_stylesheet(theme_name: str | None) -> str:
    with open(STYLE_FILE, "r", encoding="utf-8") as f:
        base = f.read()
    return render_template(base, theme_name)


def build_palette(theme_name: str | None) -> QPalette:
    t = tokens_for(theme_name)
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(t["surface"]))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(t["text"]))
    palette.setColor(QPalette.ColorRole.Base, QColor(t["surface_alt"]))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(t["surface"]))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(t["surface_alt"]))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor(t["text"]))
    palette.setColor(QPalette.ColorRole.Text, QColor(t["text"]))
    palette.setColor(QPalette.ColorRole.Button, QColor(t["surface"]))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(t["text"]))
    palette.setColor(QPalette.ColorRole.BrightText, QColor("#ffffff"))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(t["accent"]))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
    return palette


def apply_theme(app, theme_name: str | None) -> str:
    theme = normalize_theme(theme_name)
    tokens = tokens_for(theme)

    # Use Fusion so controls look deterministic and not inherited from desktop theme.
    app.setStyle("Fusion")
    app.setPalette(build_palette(theme))
    app.setFont(QFont(tokens["font_ui"], 10))
    app.setStyleSheet(load_app_stylesheet(theme))
    return theme
