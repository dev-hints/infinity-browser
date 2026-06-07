from __future__ import annotations

from PyQt6.QtCore import QByteArray, QRectF, QSize, Qt
from PyQt6.QtGui import QIcon, QPainter, QPixmap
from PyQt6.QtSvg import QSvgRenderer

from theme_manager import tokens_for


SVG_ICONS = {
    "app": '<path d="M7 12c2.2-4 5.8-4 8 0s5.8 4 8 0-1.8-4-4-4-4.2 1.8-6 4-3.8 4-6 4-4-1.8-2-4Z"/>',
    "back": '<path d="M15 6 9 12l6 6"/>',
    "forward": '<path d="m9 6 6 6-6 6"/>',
    "reload": '<path d="M20 12a8 8 0 1 1-2.34-5.66"/><path d="M20 4v5h-5"/>',
    "home": '<path d="m4 11 8-7 8 7"/><path d="M6 10v10h12V10"/><path d="M10 20v-6h4v6"/>',
    "star": '<path d="m12 3 2.8 5.67 6.26.91-4.53 4.41 1.07 6.23L12 17.28l-5.6 2.94 1.07-6.23-4.53-4.41 6.26-.91L12 3Z"/>',
    "youtube": '<path d="M22 12s0-3.2-.41-4.74a2.75 2.75 0 0 0-1.94-1.95C17.93 4.85 12 4.85 12 4.85s-5.93 0-7.65.46a2.75 2.75 0 0 0-1.94 1.95C2 8.8 2 12 2 12s0 3.2.41 4.74a2.75 2.75 0 0 0 1.94 1.95c1.72.46 7.65.46 7.65.46s5.93 0 7.65-.46a2.75 2.75 0 0 0 1.94-1.95C22 15.2 22 12 22 12Z"/><path d="m10 15 5-3-5-3v6Z"/>',
    "qr": '<path d="M4 4h6v6H4z"/><path d="M14 4h6v6h-6z"/><path d="M4 14h6v6H4z"/><path d="M14 14h2v2h-2z"/><path d="M18 14h2v4h-2z"/><path d="M14 18h4v2h-4z"/>',
    "fullscreen": '<path d="M8 3H3v5"/><path d="M21 8V3h-5"/><path d="M3 16v5h5"/><path d="M16 21h5v-5"/>',
    "download": '<path d="M12 3v12"/><path d="m7 10 5 5 5-5"/><path d="M5 21h14"/>',
    "notes": '<path d="M6 3h9l3 3v15H6z"/><path d="M14 3v4h4"/><path d="M9 11h6"/><path d="M9 15h6"/>',
    "menu": '<path d="M12 6h.01"/><path d="M12 12h.01"/><path d="M12 18h.01"/>',
    "plus": '<path d="M12 5v14"/><path d="M5 12h14"/>',
    "minus": '<path d="M5 12h14"/>',
    "maximize": '<path d="M7 7h10v10H7z"/>',
    "close": '<path d="m6 6 12 12"/><path d="m18 6-12 12"/>',
    "search": '<path d="m21 21-4.35-4.35"/><circle cx="11" cy="11" r="7"/>',
    "copy": '<path d="M8 8h11v11H8z"/><path d="M5 16H4a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1h11a1 1 0 0 1 1 1v1"/>',
    "trash": '<path d="M3 6h18"/><path d="M8 6V4h8v2"/><path d="m6 6 1 15h10l1-15"/>',
    "edit": '<path d="M12 20h9"/><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4Z"/>',
    "save": '<path d="M5 3h12l2 2v16H5z"/><path d="M8 3v6h8"/><path d="M8 21v-7h8v7"/>',
    "play": '<path d="m8 5 12 7-12 7V5Z"/>',
    "video": '<path d="M4 6h12v12H4z"/><path d="m16 10 5-3v10l-5-3z"/>',
    "key": '<circle cx="8" cy="15" r="4"/><path d="m11 12 9-9"/><path d="m16 3 5 5"/><path d="m18 5-2 2"/>',
    "lock": '<rect x="5" y="11" width="14" height="10" rx="2"/><path d="M8 11V7a4 4 0 0 1 8 0v4"/>',
    "shield": '<path d="M12 3 20 6v6c0 5-3.4 8-8 9-4.6-1-8-4-8-9V6l8-3Z"/>',
    "globe": '<circle cx="12" cy="12" r="9"/><path d="M3 12h18"/><path d="M12 3c3 3 3 15 0 18"/><path d="M12 3c-3 3-3 15 0 18"/>',
    "palette": '<circle cx="12" cy="12" r="9"/><circle cx="8" cy="10" r="1"/><circle cx="12" cy="7" r="1"/><circle cx="16" cy="10" r="1"/><path d="M13 16h1a2 2 0 1 0 0-4h-2a4 4 0 0 0-4 4 3 3 0 0 0 3 3h1"/>',
}


def themed_icon(name: str, theme_name: str | None = None, role: str = "text_soft", size: int = 24) -> QIcon:
    tokens = tokens_for(theme_name)
    color = tokens.get(role, tokens["text_soft"])
    return svg_icon(name, color, size)


def svg_icon(name: str, color: str, size: int = 24) -> QIcon:
    body = SVG_ICONS["star"] if name == "star-filled" else SVG_ICONS[name]
    fill = "none"
    stroke = color
    if name == "star-filled":
        fill = color
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
        f'viewBox="0 0 24 24" fill="{fill}" stroke="{stroke}" stroke-width="2" '
        f'stroke-linecap="round" stroke-linejoin="round">{body}</svg>'
    )
    pixmap = QPixmap(QSize(size, size))
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    QSvgRenderer(QByteArray(svg.encode("utf-8"))).render(painter, QRectF(0, 0, size, size))
    painter.end()
    return QIcon(pixmap)
