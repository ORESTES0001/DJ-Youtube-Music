import math
import random

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QStackedWidget,
    QLabel, QPushButton, QLineEdit, QTextEdit, QFrame, QScrollArea,
    QSlider, QSizePolicy, QDialog, QInputDialog,
)
from PySide6.QtCore import (
    Qt, Slot, Signal, QTimer, QSize, QByteArray, QThread, QObject, QUrl, Property,
    QEasingCurve, QPropertyAnimation, QPointF,
)
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from PySide6.QtGui import (
    QPixmap, QPainter, QFont, QColor, QIcon, QTextCursor, QTextCharFormat,
    QConicalGradient, QRadialGradient, QPainterPath,
)
from PySide6.QtSvg import QSvgRenderer

from workers.dj_worker import DJWorkerThread
from services.login_service import run_login_window

# ---------------------------------------------------------------------------
# SVG icon data
# ---------------------------------------------------------------------------
# SVG icon data
# ---------------------------------------------------------------------------
ICONS = {
    "play_arrow": "M8 5v14l11-7z",
    "pause": "M6 19h4V5H6v14zm8-14v14h4V5h-4z",
    "skip_previous": "M6 6h2v12H6zm3.5 6l8.5 6V6z",
    "skip_next": "M18 18V6l-8.5 6zm-9-12v12h2V6z",
    "shuffle": "M10.59 9.17L5.41 4 4 5.41l5.17 5.17 1.42-1.41zM14.5 4l2.04 2.04L4 18.59 5.41 20 17.96 7.46 20 9.5V4h-5.5zm.33 9.41l-1.41 1.41 3.13 3.13L14.5 20H20v-5.5l-2.04 2.04-3.13-3.13z",
    "repeat": "M7 7h10v3l4-4-4-4v3H5v6h2V7zm10 10H7v-3l-4 4 4 4v-3h12v-6h-2v4z",
    "home": "M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8z",
    "explore": "M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 5-5v3h6v4H10v3z",
    "radio": "M3.24 6.15C2.51 6.43 2 7.17 2 8v12c0 1.1.9 2 2 2h16c1.11 0 2-.9 2-2V8c0-1.11-.9-2-2-2H8.3l8.26-3.34L15.88 1 3.24 6.15zM7 20c-1.66 0-3-1.34-3-3s1.34-3 3-3 3 1.34 3 3-1.34 3-3 3zm13-8h-2v-2h-2v2H4V8h16v4z",
    "history": "M13 3a9 9 0 00-9 9H1l3.89 3.89.07.14L9 12H6c0-3.87 3.13-7 7-7s7 3.13 7 7-3.13 7-7 7c-1.93 0-3.68-.79-4.94-2.06l-1.42 1.42A8.954 8.954 0 0013 21a9 9 0 000-18zm-1 5v5l4.28 2.54.72-1.21-3.5-2.08V8H12z",
    "library_music": "M20 2H8c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm-2 5h-3v5.5c0 1.38-1.12 2.5-2.5 2.5S10 13.88 10 12.5s1.12-2.5 2.5-2.5c.57 0 1.08.19 1.5.51V5h4v2zM4 6H2v14c0 1.1.9 2 2 2h14v-2H4V6z",
    "search": "M15.5 14h-.79l-.28-.27A6.471 6.471 0 0016 9.5 6.5 6.5 0 109.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z",
    "settings": "M19.14 12.94c.04-.3.06-.61.06-.94 0-.32-.02-.64-.07-.94l2.03-1.58a.49.49 0 00.12-.61l-1.92-3.32a.488.488 0 00-.59-.22l-2.39.96c-.5-.38-1.03-.7-1.62-.94l-.36-2.54a.484.484 0 00-.48-.41h-3.84c-.24 0-.43.17-.47.41l-.36 2.54c-.59.24-1.13.57-1.62.94l-2.39-.96c-.22-.08-.47 0-.59.22L2.74 8.87c-.12.21-.08.47.12.61l2.03 1.58c-.05.3-.07.62-.07.94s.02.64.07.94l-2.03 1.58a.49.49 0 00-.12.61l1.92 3.32c.12.22.37.29.59.22l2.39-.96c.5.38 1.03.7 1.62.94l.36 2.54c.05.24.24.41.48.41h3.84c.24 0 .44-.17.47-.41l.36-2.54c.59-.24 1.13-.56 1.62-.94l2.39.96c.22.08.47 0 .59-.22l1.92-3.32c.12-.22.07-.47-.12-.61l-2.01-1.58zM12 15.6A3.6 3.6 0 1115.6 12 3.611 3.611 0 0112 15.6z",
    "account_circle": "M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 3c1.66 0 3 1.34 3 3s-1.34 3-3 3-3-1.34-3-3 1.34-3 3-3zm0 14.2a7.2 7.2 0 01-6-3.22c.03-1.99 4-3.08 6-3.08 1.99 0 5.97 1.09 6 3.08a7.2 7.2 0 01-6 3.22z",
    "add_circle": "M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm5 11h-4v4h-2v-4H7v-2h4V7h2v4h4v2z",
    "logout": "M16 17v-3H9v-4h7V7l5 5-5 5M14 2a2 2 0 012 2v2h-2V4H5v16h9v-2h2v2a2 2 0 01-2 2H5a2 2 0 01-2-2V4a2 2 0 012-2h9z",
    "help": "M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 17h-2v-2h2v2zm2.07-7.75l-.9.92C13.45 12.9 13 13.5 13 15h-2v-.5c0-1.1.45-2.1 1.17-2.83l1.24-1.26c.37-.36.59-.86.59-1.41 0-1.1-.9-2-2-2s-2 .9-2 2H8c0-2.21 1.79-4 4-4s4 1.79 4 4c0 .88-.36 1.68-.93 2.25z",
    "verified_user": "M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4zm-2 16l-4-4 1.41-1.41L10 14.17l6.59-6.59L18 9l-8 8z",
    "bolt": "M11 21h-1l1-7H7.5c-.58 0-.57-.32-.38-.66.19-.34.05-.08.07-.12C8.48 10.94 10.42 7.54 13 3h1l-1 7h3.5c.49 0 .56.33.47.51l-.07.15C12.96 17.55 11 21 11 21z",
    "self_improvement": "M21 16v-2l-8-5V3.5c0-.83-.67-1.5-1.5-1.5S10 2.67 10 3.5V9l-8 5v2l8-2.5V19l-2 1.5V22l3.5-1 3.5 1v-1.5L13 19v-5.5l8 2.5z",
    "spa": "M15.5 9.65c-.28-.34-.58-.72-.89-1.1l.02-.02c-2.09-2.57-4.11-4.67-4.11-4.67s-2.02 2.1-4.11 4.67l.02.02c-.3.38-.6.76-.89 1.1C4.76 10.54 4.5 11.64 4.5 12.96c0 3.8 2.68 6.94 6.36 7.54 1.26.2 2.56-.02 3.64-.64 1.08.62 2.38.84 3.64.64 3.68-.6 6.36-3.74 6.36-7.54 0-1.32-.26-2.42-.73-3.23z",
    "nightlight": "M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm4-9H9V7h7v4z",
    "fitness_center": "M20.57 14.86L22 13.43 20.57 12 17 15.57 8.43 7 12 3.43 10.57 2 9.14 3.43 7.71 2 5.57 4.14 4.14 2.71 2.71 4.14l1.43 1.43L2 7.71l1.43 1.43L2 10.57 3.43 12 7 8.43 15.57 17 12 20.57 13.43 22l1.43-1.43L16.29 22l2.14-2.14 1.43 1.43 1.43-1.43-1.43-1.43L22 16.29l-1.43-1.43z",
    "commute": "M12 4H5C3.34 4 2 5.34 2 7v8c0 1.66 1.34 3 3 3l-1 1v1h1l2-2.03L9 18v-5H4V5.98L13 6v2h2V7c0-1.66-1.34-3-3-3zM5 14c.55 0 1 .45 1 1s-.45 1-1 1-1-.45-1-1 .45-1 1-1zm15.57-4.34c-.14-.4-.52-.66-.97-.66h-7.19c-.46 0-.83.26-.98.66L10 13.77l.01 5.51c0 .38.31.72.69.72h.62c.38 0 .68-.38.68-.76V18h8v1.24c0 .38.31.76.69.76h.61c.38 0 .69-.34.69-.72l.01-1.37v-4.14l-1.43-4.11zm-8.16.34h7.19l1.03 3h-9.25l1.03-3zM12 16c-.55 0-1-.45-1-1s.45-1 1-1 1 .45 1 1-.45 1-1 1zm8 0c-.55 0-1-.45-1-1s.45-1 1-1 1 .45 1 1-.45 1-1 1z",
    "add": "M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z",
    "filter_list": "M10 18h4v-2h-4v2zM3 6v2h18V6H3zm3 7h12v-2H6v2z",
    "volume_up": "M3 9v6h4l5 5V4L7 9H3zm13.5 3A4.5 4.5 0 0014 8.5v7a4.49 4.49 0 002.5-3.5zM14 3.23v2.06c2.89.86 5 3.54 5 6.71s-2.11 5.85-5 6.71v2.06c4.01-.91 7-4.49 7-8.77s-2.99-7.86-7-8.77z",
    "more_vert": "M12 8c1.1 0 2-.9 2-2s-.9-2-2-2-2 .9-2 2 .9 2 2 2zm0 2c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm0 6c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2z",
    "play_circle": "M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 5-5v10zm4 0V7l5 5-5 5z",
    "chevron_left": "M15.41 7.41L14 6l-6 6 6 6 1.41-1.41L10.83 12z",
    "chevron_right": "M8.59 16.59L10 18l6-6-6-6-1.41 1.41L13.17 12z",
    "sync": "M12 4V1L8 5l4 4V6c3.31 0 6 2.69 6 6 0 1.01-.25 1.97-.7 2.8l1.46 1.46C19.54 15.03 20 13.57 20 12c0-4.42-3.58-8-8-8zm0 14c-3.31 0-6-2.69-6-6 0-1.01.25-1.97.7-2.8L5.24 7.74C4.46 8.97 4 10.43 4 12c0 4.42 3.58 8 8 8v3l4-4-4-4v3z",
    "equalizer": "M10 20h4V4h-4v16zm-6 0h4v-8H4v8zM16 9v11h4V9h-4z",
    "edit": "M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25zM20.71 7.04a1 1 0 000-1.41l-2.34-2.34a1 1 0 00-1.41 0l-1.83 1.83 3.75 3.75 1.83-1.83z",
    "mic": "M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3zm-1-9c0-.55.45-1 1-1s1 .45 1 1v6c0 .55-.45 1-1 1s-1-.45-1-1V5zm6 6c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z",
    "send": "M2.01 21L23 12 2.01 3 2 10l15 2-15 2z",
    "graphic_eq": "M7 18h2V6H7v12zm4 4h2V2h-2v20zm-8-8h2v-4H3v4zm12 4h2V6h-2v12zm4-8v4h2v-4h-2z",
}


def _svg_pixmap(path_data: str, size: int = 24, color: str = "#c5c6d2") -> QPixmap:
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="{}" height="{}" viewBox="0 0 24 24">'
        '<path fill="{}" d="{}"/></svg>'
    ).format(size, size, color, path_data)
    renderer = QSvgRenderer(QByteArray(svg.encode("utf-8")))
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    return pixmap


def _icon_label(name: str, size: int = 24, color: str = "#c5c6d2") -> QLabel:
    label = QLabel()
    label.setPixmap(_svg_pixmap(ICONS[name], size, color))
    label.setFixedSize(size, size)
    return label


def _icon_button(name: str, size: int = 24, color: str = "#c5c6d2",
                 obj_name: str = "", tooltip: str = "") -> QPushButton:
    btn = QPushButton()
    btn.setIcon(QIcon(_svg_pixmap(ICONS[name], size, color)))
    btn.setIconSize(QSize(size, size))
    if obj_name:
        btn.setObjectName(obj_name)
    if tooltip:
        btn.setToolTip(tooltip)
    btn.setCursor(Qt.PointingHandCursor)
    return btn


def _google_svg_pixmap(size: int = 24) -> QPixmap:
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="{}" height="{}" viewBox="0 0 24 24">'
        '<path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>'
        '<path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>'
        '<path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.26.81-.58z" fill="#FBBC05"/>'
        '<path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>'
        '</svg>'
    ).format(size, size)
    renderer = QSvgRenderer(QByteArray(svg.encode("utf-8")))
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    return pixmap


# ---------------------------------------------------------------------------
# Loading overlay
# ---------------------------------------------------------------------------
class LoadingOverlay(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("glassCard")
        self.setStyleSheet(
            "QFrame#glassCard {"
            " background-color: rgba(13, 14, 18, 0.85);"
            " border: 1px solid rgba(53, 53, 52, 0.5);"
            " border-radius: 16px; }"
        )
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(16)

        spinner = QFrame()
        spinner.setFixedSize(40, 40)
        spinner.setStyleSheet(
            "background: qlineargradient(x1:0 y1:0, x2:1 y2:1,"
            " stop:0 #5f74b7, stop:1 #b4c5ff); border-radius: 20px;"
        )
        layout.addWidget(spinner, alignment=Qt.AlignCenter)

        msg = QLabel("Loading...")
        msg.setObjectName("labelBold")
        msg.setStyleSheet("color: #b4c5ff; font-size: 14px;")
        msg.setAlignment(Qt.AlignCenter)
        layout.addWidget(msg)

        self.hide()

    def show_event(self, message: str = "Loading..."):
        self.findChild(QLabel, "").setText(message)
        self.show()
        self.raise_()

    def hide_event(self):
        self.hide()


# ---------------------------------------------------------------------------
# Vibe Velocity QSS
# ---------------------------------------------------------------------------
VIBE_QSS = """
QMainWindow, QWidget#centralWidget {
    background-color: #0b0b0f;
}

QWidget#sidebar {
    background-color: #121216;
    border-right: 1px solid #2a2a30;
}

QWidget#glassCard {
    background-color: rgba(24, 24, 29, 0.85);
    border: 1px solid #2a2a30;
    border-radius: 12px;
}
QWidget#glassCard:hover {
    background-color: rgba(30, 30, 36, 0.95);
}

QWidget#glassPill {
    background-color: rgba(24, 24, 29, 0.7);
    border: 1px solid #2a2a30;
    border-radius: 9999px;
}

QWidget#loadingOverlay {
    background-color: rgba(11, 11, 14, 0.9);
    border: 1px solid rgba(42, 42, 48, 0.5);
    border-radius: 16px;
}

QFrame#playbackBar {
    background-color: rgba(18, 18, 22, 0.95);
    border: 1px solid #2a2a30;
    border-radius: 12px;
}

QFrame#historyRow {
    background-color: transparent;
    border: none;
    border-bottom: 1px solid #222228;
    min-height: 68px;
}
QFrame#historyRow:hover {
    background-color: rgba(95, 116, 183, 0.08);
    border-radius: 8px;
}

QFrame#velocityBar-bg {
    background-color: #222228;
    border-radius: 4px;
}
QFrame#velocityBar-fill {
    background-color: #fcb970;
    border-radius: 4px;
}

QFrame#volumeSlider {
    background-color: transparent;
}

QSlider#volumeSlider::groove:horizontal,
QSlider#velocitySlider::groove:horizontal {
    height: 4px;
    background-color: #222228;
    border-radius: 2px;
}
QSlider#volumeSlider::handle:horizontal,
QSlider#velocitySlider::handle:horizontal {
    background-color: #b4c5ff;
    width: 12px;
    height: 12px;
    margin: -4px 0;
    border-radius: 6px;
}
QSlider#volumeSlider::handle:horizontal:hover,
QSlider#velocitySlider::handle:horizontal:hover {
    background-color: #d0daff;
}
QSlider#volumeSlider::sub-page:horizontal,
QSlider#velocitySlider::sub-page:horizontal {
    background-color: #5f74b7;
    border-radius: 2px;
}

QFrame#musicCard {
    background-color: #18181d;
    border-radius: 10px;
    border: none;
}
QFrame#musicCard:hover {
    background-color: #222229;
}

QWidget#homeContainer {
    background-color: transparent;
}
QWidget#homeWidget {
    background-color: transparent;
}
QWidget#homeWidget > QWidget {
    background-color: transparent;
}

QLabel#brandLabel {
    font-size: 32px; font-weight: 700; color: #b4c5ff;
    font-family: 'Segoe UI', 'Montserrat', sans-serif;
    letter-spacing: -0.02em;
}

QLabel#brandSmall {
    font-size: 22px; font-weight: 700; color: #b4c5ff;
    font-family: 'Segoe UI', 'Montserrat', sans-serif;
    letter-spacing: -0.02em;
}

QLabel#displayLg {
    font-size: 48px; font-weight: 700; color: #e4e1e8;
    font-family: 'Segoe UI', 'Montserrat', sans-serif;
    letter-spacing: -0.02em;
}

QLabel#headlineLg {
    font-size: 32px; font-weight: 700; color: #e4e1e8;
    font-family: 'Segoe UI', 'Montserrat', sans-serif;
    letter-spacing: -0.01em;
}

QLabel#headlineMd {
    font-size: 24px; font-weight: 600; color: #e4e1e8;
    font-family: 'Segoe UI', 'Montserrat', sans-serif;
}

QLabel#bodyLg {
    font-size: 18px; font-weight: 400; color: #c5c6d2;
    font-family: 'Segoe UI', sans-serif;
}

QLabel#bodyMd {
    font-size: 16px; font-weight: 400; color: #c5c6d2;
    font-family: 'Segoe UI', sans-serif;
}

QLabel#labelBold {
    font-size: 14px; font-weight: 700; color: #c5c6d2;
    font-family: 'Segoe UI', sans-serif;
    letter-spacing: 0.05em;
    text-transform: uppercase;
}

QLabel#codeLog {
    font-size: 13px; font-weight: 400; color: #c5c6d2;
    font-family: 'JetBrains Mono', 'Consolas', 'Courier New', monospace;
}

QLabel#sectionHeader {
    font-size: 13px; font-weight: 700; color: #c5c6d2;
    font-family: 'Segoe UI', sans-serif;
    letter-spacing: 0.05em;
    text-transform: uppercase;
}

QLabel#statusBadge {
    font-size: 12px; font-weight: 700; color: #b4c5ff;
    font-family: 'Segoe UI', sans-serif;
    letter-spacing: 0.05em;
    text-transform: uppercase;
}

QLabel#goldText {
    font-size: 13px; font-weight: 600; color: #fcb970;
    font-family: 'Segoe UI', sans-serif;
}

QLineEdit {
    background-color: #1f1f24; color: #e4e1e8;
    border: 1px solid #2a2a30; border-radius: 22px;
    padding: 11px 22px; font-size: 14px;
    font-family: 'Segoe UI', 'Montserrat', sans-serif;
    min-height: 20px;
    selection-background-color: #5f74b7;
    selection-color: #0b0b0e;
}
QLineEdit:focus {
    border-color: #b4c5ff;
    background-color: #222228;
}
QLineEdit::placeholder { color: #8f909b; }

QPushButton {
    border: none; border-radius: 22px;
    padding: 11px 32px; font-size: 14px;
    font-weight: 700; min-height: 20px;
    font-family: 'Segoe UI', 'Montserrat', sans-serif;
}

QPushButton#updateBtn {
    background-color: #5f74b7; color: #ffffff;
}
QPushButton#updateBtn:hover { background-color: #6d82c9; }
QPushButton#updateBtn:pressed { background-color: #465b9d; }
QPushButton#updateBtn:disabled {
    background-color: #343439; color: #6f7692;
}

QPushButton#updateBtnSmall {
    background-color: #5f74b7; color: #ffffff;
    border-radius: 22px; padding: 8px 24px; font-size: 13px;
}
QPushButton#updateBtnSmall:hover { background-color: #6d82c9; }

QPushButton#ghostBtn {
    background-color: transparent; color: #c5c6d2;
    border: 1px solid #8f909b; border-radius: 22px;
    padding: 10px 20px; min-width: 70px; font-weight: 600;
    font-family: 'Inter', 'Segoe UI', sans-serif;
}
QPushButton#ghostBtn:hover {
    background-color: #29292f; border-color: #b4c5ff; color: #b4c5ff;
}
QPushButton#ghostBtn:disabled {
    background-color: #1b1b20; color: #444650; border-color: #343439;
}

QPushButton#navBtn {
    background-color: transparent; color: #c5c6d2;
    border: none; border-radius: 8px;
    padding: 10px 14px; font-size: 14px; font-weight: 600;
    font-family: 'Inter', 'Segoe UI', sans-serif; text-align: left;
}
QPushButton#navBtn:hover {
    background-color: rgba(180, 197, 255, 0.08); color: #e4e1e8;
}
QPushButton#navBtn:checked {
    background-color: rgba(65, 72, 98, 0.25); color: #b4c5ff; font-weight: 700;
}

QPushButton#newSessionBtn {
    background-color: #29292f; color: #e4e1e8;
    border: 1px solid #444650; border-radius: 10px;
    padding: 8px 12px; font-size: 13px; font-weight: 600;
    font-family: 'Inter', 'Segoe UI', sans-serif; text-align: left;
}
QPushButton#newSessionBtn:hover {
    background-color: #343439; border-color: #b4c5ff;
}

QPushButton#bottomLinkBtn {
    background-color: transparent; color: #c5c6d2;
    border: none; border-radius: 8px;
    padding: 6px 14px; font-size: 13px; font-weight: 400;
    font-family: 'Inter', 'Segoe UI', sans-serif; text-align: left;
}
QPushButton#bottomLinkBtn:hover {
    background-color: rgba(180, 197, 255, 0.08); color: #e4e1e8;
}

QPushButton#whiteBtn {
    background-color: #ffffff; color: #131a32;
    border-radius: 9999px; padding: 14px 32px;
    font-size: 14px; font-weight: 700;
    font-family: 'Inter', 'Segoe UI', sans-serif;
}
QPushButton#whiteBtn:hover { background-color: #f0f0f0; }
QPushButton#whiteBtn:pressed { background-color: #e0e0e0; }

QPushButton#googleBtn {
    background-color: #ffffff; color: #131a32;
    border-radius: 9999px; padding: 16px 32px;
    font-size: 15px; font-weight: 600;
    font-family: 'Inter', 'Segoe UI', sans-serif; min-height: 24px;
}
QPushButton#googleBtn:hover { background-color: #f5f5f5; }
QPushButton#googleBtn:pressed { background-color: #e8e8e8; }

QPushButton#textLink {
    background: transparent; border: none; color: #b4c5ff;
    font-family: 'Inter', 'Segoe UI', sans-serif;
    font-size: 13px; font-weight: 400; padding: 0;
    text-decoration: underline;
}
QPushButton#textLink:hover { color: #dbe1ff; }

QPushButton#playBtn {
    background-color: #ffffff; color: #000000;
    border-radius: 9999px; padding: 0;
    min-width: 44px; min-height: 44px; max-width: 44px; max-height: 44px;
    font-size: 18px;
}
QPushButton#playBtn:hover { background-color: #e0e0e0; }

QPushButton#iconBtn {
    background-color: transparent; border: none; border-radius: 9999px;
    padding: 6px; min-width: 34px; min-height: 34px;
    color: #c5c6d2; font-size: 18px;
}
QPushButton#iconBtn:hover { background-color: #29292f; color: #ffffff; }

QPushButton#barPlayBtn {
    background-color: rgba(175, 145, 246, 0.6);
    color: #ffffff;
    border: 1px solid rgba(175, 145, 255, 0.9);
    border-radius: 18px;
    min-width: 10px; max-width: 10px;
    min-height: 16px; max-height: 16px;
}
QPushButton#barPlayBtn:hover {
    background-color: rgba(255, 255, 255, 0.14);
    border-color: rgba(255, 255, 255, 0.25);
}
QPushButton#barPlayBtn:pressed {
    background-color: rgba(255, 255, 255, 0.05);
}

QPushButton#barIconBtn {
    background-color: transparent; border: none; border-radius: 9999px;
    padding: 4px; min-width: 30px; min-height: 30px;
    color: #c5c6d2;
}
QPushButton#barIconBtn:hover { background-color: #29292f; color: #ffffff; }

QPushButton#moodPill {
    background-color: rgba(28, 27, 27, 0.6);
    border: 1px solid #353534;
    border-radius: 16px;
    padding: 16px 24px;
    font-size: 14px;
    font-weight: 600;
    font-family: 'Inter', sans-serif;
    color: #e4e1e8;
    min-width: 100px;
}
QPushButton#moodPill:hover {
    border-color: #5f74b7;
    background-color: rgba(95, 116, 183, 0.1);
}

QPushButton#pillActive {
    background-color: rgba(95, 116, 183, 0.1);
    border: 1px solid rgba(180, 197, 255, 0.4);
    border-radius: 16px;
    padding: 16px 24px;
    font-size: 14px;
    font-weight: 600;
    font-family: 'Inter', sans-serif;
    color: #e4e1e8;
    min-width: 100px;
}

QPushButton#heroPlayBtn {
    background-color: #ffffff; color: #000000;
    border-radius: 9999px; padding: 12px 24px;
    font-size: 14px; font-weight: 700;
}
QPushButton#heroPlayBtn:hover { background-color: #f0f0f0; }

QTextEdit {
    background-color: #0d0e12; color: #e4e1e8;
    border: 1px solid #444650; border-radius: 8px;
    font-family: 'JetBrains Mono', 'Consolas', 'Courier New', monospace;
    font-size: 13px; padding: 12px;
}

QSlider::groove:horizontal {
    background: #29292f; height: 4px; border-radius: 2px;
}
QSlider::handle:horizontal {
    background: #b4c5ff; width: 12px; height: 12px;
    margin: -4px 0; border-radius: 6px;
}
QSlider::sub-page:horizontal {
    background: #b4c5ff; border-radius: 2px;
}

QScrollBar:vertical {
    background-color: #0d0e12; width: 6px; border: none;
}
QScrollBar::handle:vertical {
    background-color: #343439; border-radius: 3px; min-height: 30px;
}
QScrollBar::handle:vertical:hover { background-color: #444650; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }

QScrollBar:horizontal {
    background-color: transparent; height: 6px; border: none;
}
QScrollBar::handle:horizontal {
    background-color: #343439; border-radius: 3px; min-width: 30px;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0px; }
"""

# ---- Gradient colour pairs for rich card backgrounds ----
BENTO_GRADIENTS = [
    ("#6a3093", "#a044ff"), ("#0f2027", "#2c5364"),
    ("#c94b4b", "#4b134f"), ("#1d976c", "#93f9b9"),
    ("#02aab0", "#00cdac"), ("#da22ff", "#9733ee"),
    ("#ff416c", "#ff4b2b"), ("#654ea3", "#eaafc8"),
    ("#2c3e50", "#3498db"), ("#3a1c71", "#d76d77"),
    ("#0b8793", "#360033"), ("#1e130c", "#9a8478"),
]

MOOD_CATEGORIES = [
    ("Energy", "bolt"), ("Focus", "self_improvement"),
    ("Relax", "spa"), ("Late Night", "nightlight"),
    ("Workout", "fitness_center"), ("Commute", "commute"),
]


# ---------------------------------------------------------------------------
# Paste-Auth Dialog — manual cookie / header paste
# ---------------------------------------------------------------------------



# ---------------------------------------------------------------------------
# Login Widget (Screen 0)  -- mirrors Iniciar sesion.html
# ---------------------------------------------------------------------------
class LoginWidget(QWidget):
    web_auth_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("centralWidget")
        self._setup_ui()
        self._anim_timer = QTimer(self)
        self._anim_timer.timeout.connect(self._animate_bars)
        self._anim_phase = 0
        self._anim_timer.start(15)

    def _animate_bars(self):
        self._anim_phase += 1
        for i, bar in enumerate(self._waveform_bars):
            shift = i * 0.1
            raw = (self._anim_phase * 0.01 + shift) * 3.14159
            h = 10 + abs(22 * math.sin(raw))
            bar.setFixedHeight(max(6, min(38, int(h))))

    def show_auth_status(self, message: str, error: bool = False):
        self.auth_status.setText(message)
        if error:
            self.auth_status.setStyleSheet("color: #ffb4ab; font-size: 14px;")
        else:
            self.auth_status.setStyleSheet("color: #b4c5ff; font-size: 14px;")
        self.auth_status.show()

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setAlignment(Qt.AlignCenter)

        bg = QFrame(self)
        bg.setGeometry(0, 0, 1200, 900)
        bg_low = QLabel(bg)
        bg_low.setGeometry(-120, -200, 600, 600)
        bg_low.setStyleSheet(
            "background-color: rgba(95, 116, 183, 0.04); border-radius: 300px;"
        )
        bg_high = QLabel(bg)
        bg_high.setGeometry(700, 300, 500, 500)
        bg_high.setStyleSheet(
            "background-color: rgba(161, 107, 41, 0.04); border-radius: 250px;"
        )

        container = QWidget()
        container.setMaximumWidth(480)
        container_layout = QVBoxLayout(container)
        container_layout.setAlignment(Qt.AlignCenter)
        container_layout.setSpacing(24)

        brand_section = QVBoxLayout()
        brand_section.setAlignment(Qt.AlignCenter)
        brand_section.setSpacing(12)

        waveform = QHBoxLayout()
        waveform.setAlignment(Qt.AlignCenter)
        waveform.setSpacing(3)
        self._waveform_bars = []
        for _ in range(6):
            bar = QFrame()
            bar.setFixedSize(3, 14)
            bar.setStyleSheet("background-color: #5f74b7; border-radius: 4px;")
            waveform.addWidget(bar)
            self._waveform_bars.append(bar)
        brand_section.addLayout(waveform)

        brand = QLabel("QueNota?")
        brand.setObjectName("displayLg")
        brand.setAlignment(Qt.AlignCenter)
        brand.setStyleSheet("color: #b4c5ff;")
        brand_section.addWidget(brand)

        tagline = QLabel("AI-Driven Rhythmic Intelligence")
        tagline.setObjectName("headlineMd")
        tagline.setAlignment(Qt.AlignCenter)
        tagline.setStyleSheet("color: #c5c6d2; font-weight: 400; font-size: 20px;")
        brand_section.addWidget(tagline)
        container_layout.addLayout(brand_section)

        card = QFrame()
        card.setObjectName("glassCard")
        card.setStyleSheet(
            "QFrame#glassCard { background-color: rgba(28, 27, 27, 0.6);"
            " border: 1px solid #353534; border-radius: 12px; padding: 24px; }"
        )
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(20)
        card_layout.setContentsMargins(24, 24, 24, 24)

        welcome = QLabel("Welcome Back")
        welcome.setObjectName("headlineMd")
        card_layout.addWidget(welcome)

        signin_msg = QLabel("Sign in to resume your curated mixing session.")
        signin_msg.setObjectName("bodyMd")
        signin_msg.setStyleSheet("color: #c5c6d2;")
        signin_msg.setWordWrap(True)
        card_layout.addWidget(signin_msg)

        self.google_btn = QPushButton("Authenticate with Google")
        self.google_btn.setObjectName("googleBtn")
        self.google_btn.setIcon(QIcon(_google_svg_pixmap(22)))
        self.google_btn.setIconSize(QSize(22, 22))
        self.google_btn.clicked.connect(self._on_web_auth)
        card_layout.addWidget(self.google_btn)

        self.auth_status = QLabel("")
        self.auth_status.setObjectName("bodyMd")
        self.auth_status.setAlignment(Qt.AlignCenter)
        self.auth_status.setWordWrap(True)
        self.auth_status.hide()
        card_layout.addWidget(self.auth_status)

        footer = QLabel(
            'By signing in, you agree to our '
            '<a style="color:#b4c5ff;" href="#">Terms of Service</a> '
            'and <a style="color:#b4c5ff;" href="#">Privacy Policy</a>.'
        )
        footer.setObjectName("codeLog")
        footer.setStyleSheet("color: #8f909b; font-size: 12px;")
        footer.setAlignment(Qt.AlignCenter)
        footer.setWordWrap(True)
        card_layout.addWidget(footer)

        container_layout.addWidget(card)


        root.addWidget(container)

    def _on_web_auth(self):
        self.web_auth_requested.emit()


# ---------------------------------------------------------------------------
# Persistent Metropolitan Playback Bar
# ---------------------------------------------------------------------------
class PlaybackBar(QFrame):
    play_pause_requested = Signal()
    skip_requested = Signal()
    back_requested = Signal()
    volume_changed = Signal(int)
    velocity_changed = Signal(float)
    shuffle_requested = Signal()
    repeat_requested = Signal()

    def __init__(self, thumbnail_loader, parent=None):
        super().__init__(parent)
        self._thumbnail_loader = thumbnail_loader
        self.setObjectName("playbackBar")
        self.setFixedHeight(72)
        self._paused = True
        self._shuffle_on = False
        self._repeat_on = False
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 10, 16, 10)
        layout.setSpacing(16)

        left = QHBoxLayout()
        left.setSpacing(12)

        self.cover_art = QFrame()
        self.cover_art.setFixedSize(50, 50)
        self.cover_art.setStyleSheet(
            "background-color: qlineargradient(x1:0 y1:0, x2:1 y2:1,"
            " stop:0 #5f74b7, stop:1 #b4c5ff); border-radius: 8px;"
        )
        self._cover_label = QLabel(self.cover_art)
        self._cover_label.setFixedSize(50, 50)
        self._cover_label.setScaledContents(True)
        self._cover_label.setStyleSheet("background: transparent; border-radius: 8px;")
        left.addWidget(self.cover_art)

        info_col = QVBoxLayout()
        info_col.setSpacing(2)
        self.bar_title = QLabel("No track playing")
        self.bar_title.setObjectName("labelBold")
        self.bar_title.setStyleSheet("color: #e4e1e8; font-size: 13px;")
        info_col.addWidget(self.bar_title)
        self.bar_subtitle = QLabel("Ready")
        self.bar_subtitle.setObjectName("codeLog")
        self.bar_subtitle.setStyleSheet("color: #8f909b; font-size: 11px;")
        info_col.addWidget(self.bar_subtitle)
        left.addLayout(info_col)
        layout.addLayout(left, stretch=3)

        center = QHBoxLayout()
        center.setSpacing(8)
        center.setAlignment(Qt.AlignCenter)

        self.shuffle_btn = _icon_button("shuffle", 20, "#8f909b", "barIconBtn", "Shuffle")
        self.shuffle_btn.clicked.connect(self._on_shuffle)
        center.addWidget(self.shuffle_btn)

        self.btn_back = _icon_button("skip_previous", 22, "#c5c6d2", "barIconBtn", "Previous")
        self.btn_back.clicked.connect(self.back_requested.emit)
        center.addWidget(self.btn_back)

        self.btn_play = QPushButton()
        self.btn_play.setObjectName("barPlayBtn")
        self.btn_play.setFixedSize(36, 36)
        self.btn_play.setIcon(QIcon(_svg_pixmap(ICONS["play_arrow"], 18, "#ffffff")))
        self.btn_play.setIconSize(QSize(18, 18))
        self.btn_play.clicked.connect(self._on_play_pause)
        self.btn_play.setCursor(Qt.PointingHandCursor)
        center.addWidget(self.btn_play)

        self.btn_next = _icon_button("skip_next", 22, "#c5c6d2", "barIconBtn", "Next")
        self.btn_next.clicked.connect(self.skip_requested.emit)
        center.addWidget(self.btn_next)

        self.repeat_btn = _icon_button("repeat", 20, "#8f909b", "barIconBtn", "Repeat")
        self.repeat_btn.clicked.connect(self._on_repeat)
        center.addWidget(self.repeat_btn)

        layout.addLayout(center, stretch=3)

        right = QHBoxLayout()
        right.setSpacing(12)
        right.setAlignment(Qt.AlignRight)

        vol_btn = _icon_button("volume_up", 18, "#8f909b", "", "Volume")
        vol_btn.setStyleSheet(
            "QPushButton { background: transparent; border: none; padding: 4px; }"
        )
        right.addWidget(vol_btn)

        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setObjectName("volumeSlider")
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(80)
        self.volume_slider.setFixedWidth(80)
        self.volume_slider.valueChanged.connect(self._on_volume)
        right.addWidget(self.volume_slider)

        sep = QFrame()
        sep.setFrameShape(QFrame.VLine)
        sep.setStyleSheet("background-color: #444650; max-width: 1px; max-height: 24px;")
        right.addWidget(sep)

        speed_header = QVBoxLayout()
        speed_header.setSpacing(2)
        speed_header.setAlignment(Qt.AlignRight)
        speed_label = QLabel("SPEED")
        speed_label.setObjectName("codeLog")
        speed_label.setStyleSheet("color: #8f909b; font-size: 9px; letter-spacing: 0.1em;")
        speed_header.addWidget(speed_label)

        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setObjectName("velocitySlider")
        self.speed_slider.setRange(50, 200)
        self.speed_slider.setValue(100)
        self.speed_slider.setFixedWidth(80)
        self.speed_slider.valueChanged.connect(self._on_speed)
        speed_header.addWidget(self.speed_slider)
        right.addLayout(speed_header)

        layout.addLayout(right, stretch=3)

    def _on_play_pause(self):
        self.play_pause_requested.emit()

    def _on_shuffle(self):
        self._shuffle_on = not self._shuffle_on
        color = "#b4c5ff" if self._shuffle_on else "#8f909b"
        self.shuffle_btn.setIcon(QIcon(_svg_pixmap(ICONS["shuffle"], 20, color)))
        self.shuffle_requested.emit()

    def _on_repeat(self):
        self._repeat_on = not self._repeat_on
        color = "#b4c5ff" if self._repeat_on else "#8f909b"
        self.repeat_btn.setIcon(QIcon(_svg_pixmap(ICONS["repeat"], 20, color)))
        self.repeat_requested.emit()

    def _on_volume(self, value: int):
        self.volume_changed.emit(value)

    def _on_speed(self, value: int):
        speed = round(value / 100.0, 1)
        self.velocity_changed.emit(speed)

    def on_track_loaded(self, title: str, artist: str, thumb_url: str = ""):
        self.bar_title.setText(title or "No track playing")
        self.bar_subtitle.setText(artist or "Ready")
        self.bar_title.setStyleSheet("color: #b4c5ff; font-size: 13px;")
        if thumb_url and self._thumbnail_loader:
            self._thumbnail_loader.load(self._cover_label, thumb_url)

    def on_play_state(self, paused: bool):
        self._paused = paused
        icon_name = "play_arrow" if paused else "pause"
        self.btn_play.setIcon(QIcon(_svg_pixmap(ICONS[icon_name], 18, "#ffffff")))

    def on_velocity_update(self, count: int):
        pass

    def set_transport_enabled(self, enabled: bool):
        self.btn_back.setEnabled(enabled)
        self.btn_play.setEnabled(enabled)
        self.btn_next.setEnabled(enabled)

    def reset(self):
        self.bar_title.setText("No track playing")
        self.bar_subtitle.setText("Ready")
        self.bar_title.setStyleSheet("color: #e4e1e8; font-size: 13px;")
        self.on_play_state(True)
        self.set_transport_enabled(False)
        self._cover_label.clear()
        self._cover_label.setStyleSheet("background: transparent; border-radius: 8px;")
        if self._shuffle_on:
            self._on_shuffle()
        if self._repeat_on:
            self._on_repeat()


# ---------------------------------------------------------------------------
# OndaVisualizer — custom-painted conical-gradient rotating ring + pulse
# ---------------------------------------------------------------------------
class OndaVisualizer(QWidget):
    """Custom-painted circle with a rotating QConicalGradient border
    and a QPropertyAnimation-based talking pulse."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(350, 350)
        self.setAttribute(Qt.WA_TranslucentBackground, False)

        # ── rotation angle for the conical gradient ──
        self._angle = 0.0
        self._rotate_timer = QTimer(self)
        self._rotate_timer.timeout.connect(self._rotate_step)
        self._rotate_timer.start(40)  # 25 fps smooth rotation

        # ── pulse animation property ──
        self._pulse = 0.0  # 0 = idle, 1 = max glow
        self._pulse_anim = QPropertyAnimation(self, b"pulse")
        self._pulse_anim.setLoopCount(1)

        # ── talking glow multiplier ──
        self._glow_alpha = 80

        # center icon
        self._center_pixmap = _svg_pixmap(ICONS["graphic_eq"], 48, "#ffffff")

    # -- Q_PROPERTY for QPropertyAnimation --------------------------------
    def _pulse_prop(self) -> float:
        return self._pulse

    def _set_pulse_prop(self, v: float):
        self._pulse = v
        self._glow_alpha = int(60 + v * 160)
        self.update()

    pulse = Property(float, _pulse_prop, _set_pulse_prop)

    # -- rotation timer ---------------------------------------------------
    def _rotate_step(self):
        self._angle = (self._angle + 1.5) % 360
        self.update()

    # -- paint ------------------------------------------------------------
    def paintEvent(self, event):
        sz = self.width()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        center = sz / 2.0
        radius = center - 4  # leave room for border

        # clip circle
        path = QPainterPath()
        path.addEllipse(2, 2, sz - 4, sz - 4)
        painter.setClipPath(path)

        # ── background fill ──
        painter.fillPath(path, QColor("#121216"))

        # ── conical gradient border ──
        border_w = 4 + int(self._pulse * 4)
        cg = QConicalGradient(center, center, self._angle)
        cg.setColorAt(0.0,  QColor(122, 140, 232, 180))
        cg.setColorAt(0.25, QColor(226, 162, 255, 180))
        cg.setColorAt(0.5,  QColor(255, 179, 138, 180))
        cg.setColorAt(0.75, QColor(122, 140, 232, 180))
        cg.setColorAt(1.0,  QColor(122, 140, 232, 180))

        pen = painter.pen()
        pen.setBrush(cg)
        pen.setWidth(border_w)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)

        inner_radius = radius - border_w / 2.0
        painter.drawEllipse(QPointF(center, center), inner_radius, inner_radius)

        # ── outer glow ring during pulse ──
        if self._pulse > 0.05:
            glow_radius = radius + 2 + self._pulse * 6
            rg = QRadialGradient(center, center, glow_radius)
            glow_col = QColor(122, 140, 232, int(30 * self._pulse))
            rg.setColorAt(0.85, glow_col)
            rg.setColorAt(1.0,  QColor(122, 140, 232, 0))
            painter.setPen(Qt.NoPen)
            painter.setBrush(rg)
            painter.drawEllipse(QPointF(center, center), glow_radius, glow_radius)

        # ── center icon ──
        icon_size = 48
        icon_x = int(center - icon_size / 2)
        icon_y = int(center - icon_size / 2)
        painter.drawPixmap(icon_x, icon_y, self._center_pixmap)

        painter.end()

    # -- public API -------------------------------------------------------
    def start_pulse(self, text_length: int = 0):
        """Animate the breathing glow. Longer text → faster animation."""
        duration = max(600, 2000 - text_length * 15)
        self._pulse_anim.stop()
        self._pulse_anim.setDuration(duration)
        self._pulse_anim.setStartValue(1.0)
        self._pulse_anim.setEndValue(0.0)
        self._pulse_anim.setEasingCurve(QEasingCurve.Type.OutQuad)
        self._pulse_anim.start()

    def stop_pulse(self):
        self._pulse_anim.stop()
        self._pulse = 0.0
        self._glow_alpha = 80
        self.update()


# ---------------------------------------------------------------------------
# DJ Booth Widget — Centered QueNota? Landing
# ---------------------------------------------------------------------------
class DJBoothWidget(QWidget):
    start_session_requested = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.worker_thread = None
        self._setup_ui()

    def _setup_ui(self):
        self.setStyleSheet("background-color: #0b0b0f;")
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Left: centered conversational area ──
        center = QWidget()
        center.setStyleSheet("background-color: #0b0b0f;")
        col = QVBoxLayout(center)
        col.setContentsMargins(0, 0, 0, 0)
        col.setSpacing(0)

        col.addStretch(1)

        # Status Pill
        pill_row = QHBoxLayout()
        pill_row.addStretch()
        self.status_pill = QLabel("●  QueNota? AI está escuchando")
        self.status_pill.setStyleSheet(
            "background-color: #1a1a24; color: #b4c5ff;"
            " border-radius: 12px; padding: 5px 15px; font-size: 11px;"
            " font-family: 'Segoe UI', sans-serif;"
        )
        pill_row.addWidget(self.status_pill)
        pill_row.addStretch()
        col.addLayout(pill_row)

        col.addSpacing(30)

        # Giant Visualizer
        viz_row = QHBoxLayout()
        viz_row.addStretch()
        self.onda = OndaVisualizer()
        viz_row.addWidget(self.onda)
        viz_row.addStretch()
        col.addLayout(viz_row)

        col.addSpacing(40)

        # Floating Input Bar
        input_row = QHBoxLayout()
        input_row.addStretch()

        self.input_bar = QFrame()
        self.input_bar.setFixedWidth(600)
        self.input_bar.setFixedHeight(60)
        self.input_bar.setStyleSheet(
            "QFrame { background-color: #16161e; border-radius: 15px; border: none; }"
        )
        bar_layout = QHBoxLayout(self.input_bar)
        bar_layout.setContentsMargins(14, 0, 8, 0)
        bar_layout.setSpacing(8)

        mic_icon = QLabel()
        mic_icon.setPixmap(_svg_pixmap(ICONS["mic"], 20, "#7a8ce8"))
        mic_icon.setFixedSize(20, 20)
        bar_layout.addWidget(mic_icon)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("¿Qué vibe quieres escuchar hoy o dime qué elija?")
        self.search_input.setStyleSheet(
            "QLineEdit { background: transparent; border: none;"
            " color: #e4e1e8; font-size: 14px; padding: 0;"
            " font-family: 'Segoe UI', sans-serif; }"
            "QLineEdit::placeholder { color: #555566; }"
        )
        self.search_input.returnPressed.connect(self._on_start)
        bar_layout.addWidget(self.search_input, stretch=1)

        self.send_btn = QPushButton()
        self.send_btn.setFixedSize(40, 40)
        self.send_btn.setCursor(Qt.PointingHandCursor)
        self.send_btn.setStyleSheet(
            "QPushButton { background-color: #7a8ce8; border: none;"
            " border-radius: 10px; }"
            "QPushButton:hover { background-color: #8a9cf8; }"
            "QPushButton:pressed { background-color: #6a7cd8; }"
        )
        self.send_btn.setIcon(QIcon(_svg_pixmap(ICONS["send"], 20, "#ffffff")))
        self.send_btn.setIconSize(QSize(20, 20))
        self.send_btn.clicked.connect(self._on_start)
        bar_layout.addWidget(self.send_btn)

        input_row.addWidget(self.input_bar)
        input_row.addStretch()
        col.addLayout(input_row)

        col.addSpacing(12)

        # "o" separator
        sep_row = QHBoxLayout()
        sep_row.addStretch()
        sep_lbl = QLabel("o")
        sep_lbl.setStyleSheet("color: #555560; font-size: 12px; background: transparent;")
        sep_row.addWidget(sep_lbl)
        sep_row.addStretch()
        col.addLayout(sep_row)

        col.addSpacing(8)

        # Surprise Me Button
        surprise_row = QHBoxLayout()
        surprise_row.addStretch()
        self.surprise_btn = QPushButton("✨  ¿Quieres que QueNota? elija por ti?")
        self.surprise_btn.setCursor(Qt.PointingHandCursor)
        self.surprise_btn.setStyleSheet(
            "QPushButton { background-color: transparent; border: 1px solid #333340;"
            " border-radius: 10px; padding: 8px 20px; color: #a0a0b0;"
            " font-size: 13px; font-family: 'Segoe UI', sans-serif; }"
            "QPushButton:hover { border-color: #7a8ce8; color: #c5c6d2; }"
        )
        self.surprise_btn.clicked.connect(self._on_surprise)
        surprise_row.addWidget(self.surprise_btn)
        surprise_row.addStretch()
        col.addLayout(surprise_row)

        col.addStretch(1)

        # (track info lives exclusively in the bottom PlaybackBar)

        # ── Right: AI Rationale Panel ──
        self.rationale_panel = QFrame()
        self.rationale_panel.setFixedWidth(280)
        self.rationale_panel.setObjectName("rationalePanel")
        self.rationale_panel.setStyleSheet(
            "QFrame#rationalePanel {"
            " background-color: #121216;"
            " border-left: 1px solid #2a2a30;"
            "}"
        )
        rp_layout = QVBoxLayout(self.rationale_panel)
        rp_layout.setContentsMargins(16, 20, 16, 20)
        rp_layout.setSpacing(12)

        rp_header = QLabel("DJ Commentary")
        rp_header.setStyleSheet(
            "color: #b4c5ff; font-size: 12px; font-weight: 700;"
            " letter-spacing: 1px; text-transform: uppercase;"
            " font-family: 'Segoe UI', sans-serif;"
        )
        rp_layout.addWidget(rp_header)

        self.rationale_scroll = QScrollArea()
        self.rationale_scroll.setWidgetResizable(True)
        self.rationale_scroll.setObjectName("rationaleScroll")
        self.rationale_scroll.setStyleSheet(
            "QScrollArea#rationaleScroll { background: transparent; border: none; }"
            "QScrollBar:vertical { width: 4px; background: transparent; }"
            "QScrollBar::handle:vertical { background: #2a2a30; border-radius: 2px; }"
        )
        self.rationale_text = QLabel("The DJ's commentary will appear here once a session starts.")
        self.rationale_text.setWordWrap(True)
        self.rationale_text.setStyleSheet(
            "color: #c5c6d2; font-size: 13px; line-height: 1.5;"
            " font-family: 'Segoe UI', sans-serif; background: transparent;"
        )
        self.rationale_scroll.setWidget(self.rationale_text)
        rp_layout.addWidget(self.rationale_scroll, stretch=1)

        self.rationale_panel.hide()
        root.addWidget(center, stretch=1)
        root.addWidget(self.rationale_panel)

    def _on_surprise(self):
        import random
        surprises = [
            "algo inesperado y experimental",
            "música indie de Nicaragua",
            "lo-fi para programar de noche",
            "algo que me vuele la cabeza",
            "ritmos africanos modernos",
            "electronica ambiental",
            "jazz fusion latinoamericano",
            "algo con guitarra acústica",
        ]
        query = random.choice(surprises)
        self.search_input.setText(query)
        self._on_start()

    def _on_start(self):
        query = self.search_input.text().strip()
        if not query:
            query = "lo-fi programming music"
        self.status_pill.setText("●  QueNota? AI está pensando...")
        self.rationale_text.setText("Waiting for AI response...")
        if self.worker_thread and self.worker_thread.isRunning():
            self.worker_thread.update_query(query)
        else:
            self.start_session_requested.emit(query)

    def on_song_playing(self, title: str, artist: str, thumb_url: str = ""):
        pass  # track info displayed on bottom PlaybackBar

    def on_log_message(self, msg: str):
        pass

    def on_dj_speaking(self, comment: str):
        self.status_pill.setText("●  QueNota? AI está hablando...")
        self.onda.start_pulse(len(comment or ""))
        self.show_commentary(comment)
        QTimer.singleShot(3000, self._stop_dj_speaking)

    def _stop_dj_speaking(self):
        self.status_pill.setText("●  QueNota? AI está escuchando")
        self.onda.stop_pulse()

    def on_session_finished(self):
        self.status_pill.setText("●  QueNota? AI está escuchando")
        self.onda.stop_pulse()

    def reset_state(self):
        self.status_pill.setText("●  QueNota? AI está escuchando")
        self.onda.stop_pulse()
        self.search_input.clear()

    def show_commentary(self, text: str):
        self.rationale_text.setText(text or "")
        self.rationale_panel.show()

    def set_next_tracks(self, tracks: list):
        pass


# ---------------------------------------------------------------------------
# Discover Widget (Screen 2)  -- mirrors Explorar.html
# ---------------------------------------------------------------------------
class _BentoCard(QFrame):
    clicked = Signal(str)

    def __init__(self, title, subtitle, gradient_pair, parent=None):
        super().__init__(parent)
        self._card_title = title
        self.setObjectName("glassCard")
        self.setFixedSize(200, 150)
        self.setCursor(Qt.PointingHandCursor)
        g0, g1 = gradient_pair
        ss = (
            "QFrame#glassCard {{background: qlineargradient(x1:0, y1:0, x2:1, y2:1,"
            " stop:0 {0}, stop:1 {1});"
            " border: 1px solid rgba(255,255,255,0.08);"
            " border-radius: 14px; padding: 14px;"
            "}}"
        ).format(g0, g1)
        self.setStyleSheet(ss)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(4)

        top = QHBoxLayout()
        top.addStretch()
        play_hint = _icon_label("play_circle", 22, "rgba(255,255,255,0.7)")
        top.addWidget(play_hint)
        layout.addLayout(top)

        layout.addStretch()

        t = QLabel(title)
        t.setObjectName("labelBold")
        t.setStyleSheet("color: #ffffff; font-size: 14px;")
        t.setWordWrap(True)
        layout.addWidget(t)

        s = QLabel(subtitle)
        s.setObjectName("codeLog")
        s.setStyleSheet("color: rgba(255,255,255,0.7); font-size: 11px;")
        layout.addWidget(s)

    def mousePressEvent(self, event):
        self.clicked.emit(self._card_title)
        super().mousePressEvent(event)


class DiscoverWidget(QWidget):
    def __init__(self, auth_service, music_service, thumbnail_loader, parent=None):
        super().__init__(parent)
        self.auth_service = auth_service
        self.music_service = music_service
        self._thumbnail_loader = thumbnail_loader
        self._loading = None
        self._setup_ui()

    def _build_mood_grid(self, parent_layout):
        grid = QGridLayout()
        grid.setSpacing(12)
        moods = [
            ("Energy", "bolt", "#ff6b6b"),
            ("Focus", "self_improvement", "#5f74b7"),
            ("Relax", "spa", "#51cf66"),
            ("Late Night", "nightlight", "#845ef7"),
            ("Workout", "fitness_center", "#ff922b"),
            ("Commute", "commute", "#20c997"),
        ]
        row, col = 0, 0
        for name, icon, color in moods:
            tile = QPushButton()
            tile.setObjectName("moodPill")
            tile.setFixedSize(160, 80)
            tile.setCursor(Qt.PointingHandCursor)
            tile.setStyleSheet(f"""
                QPushButton#moodPill {{
                    background-color: qlineargradient(x1:0 y1:0, x2:1 y2:1,
                        stop:0 {color}44, stop:1 {color}22);
                    border: 1px solid {color}66;
                    border-radius: 14px;
                    padding: 12px;
                }}
                QPushButton#moodPill:hover {{
                    background-color: qlineargradient(x1:0 y1:0, x2:1 y2:1,
                        stop:0 {color}66, stop:1 {color}44);
                    border-color: {color};
                }}
            """)
            tile_layout = QVBoxLayout(tile)
            tile_layout.setSpacing(4)
            tile_layout.setAlignment(Qt.AlignCenter)
            icon_lbl = _icon_label(icon, 24, color)
            tile_layout.addWidget(icon_lbl, alignment=Qt.AlignCenter)
            text = QLabel(name)
            text.setStyleSheet(f"color: #e4e1e8; font-size: 12px; font-weight: 600; background: transparent;")
            text.setAlignment(Qt.AlignCenter)
            tile_layout.addWidget(text, alignment=Qt.AlignCenter)
            tile.clicked.connect(lambda checked=False, m=name: self.on_mood_selected(m))
            grid.addWidget(tile, row, col)
            col += 1
            if col >= 3:
                col = 0
                row += 1
        parent_layout.addLayout(grid)

    def _setup_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { background-color: transparent; border: none; }")

        content = QWidget()
        content.setStyleSheet("background-color: transparent;")
        root = QVBoxLayout(content)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(28)

        hero = QFrame()
        hero.setObjectName("glassCard")
        hero.setStyleSheet(
            "QFrame#glassCard {"
            " background: qlineargradient(x1:0 y1:0, x2:1 y2:1,"
            " stop:0 rgba(95,116,183,0.15), stop:1 rgba(180,197,255,0.05));"
            " border: 1px solid #2a2a30; border-radius: 24px; padding: 28px; }"
        )
        hero_layout = QVBoxLayout(hero)
        hero_layout.setSpacing(8)

        hero_title = QLabel("Explorar")
        hero_title.setObjectName("displayLg")
        hero_title.setStyleSheet("font-size: 36px;")
        hero_layout.addWidget(hero_title)

        hero_desc = QLabel(
            "Descubre nueva música por estado de ánimo, género o tendencias globales."
        )
        hero_desc.setObjectName("bodyLg")
        hero_desc.setWordWrap(True)
        hero_layout.addWidget(hero_desc)
        root.addWidget(hero)

        moods_header = QLabel("Moods y Géneros")
        moods_header.setStyleSheet("color: #e4e1e8; font-size: 20px; font-weight: 700;")
        root.addWidget(moods_header)

        self._build_mood_grid(root)

        charts_header = QLabel("Top Charts")
        charts_header.setStyleSheet("color: #e4e1e8; font-size: 20px; font-weight: 700;")
        root.addWidget(charts_header)

        self.charts_scroll = QFrame()
        self.charts_scroll.setFixedHeight(210)
        self.charts_layout = QHBoxLayout(self.charts_scroll)
        self.charts_layout.setContentsMargins(0, 0, 0, 0)
        self.charts_layout.setSpacing(12)
        self.charts_layout.addStretch()
        root.addWidget(self.charts_scroll)

        self.auth_placeholder = QLabel(
            "Sign in with YouTube Music to see trending charts and personalized mood stations."
        )
        self.auth_placeholder.setObjectName("bodyMd")
        self.auth_placeholder.setWordWrap(True)
        self.auth_placeholder.setAlignment(Qt.AlignCenter)
        self.auth_placeholder.setStyleSheet(
            "color: #8f909b; padding: 40px; background-color: rgba(24, 24, 29, 0.4);"
            " border: 1px dashed #2a2a30; border-radius: 16px; font-size: 15px;"
        )
        root.addWidget(self.auth_placeholder)

        root.addStretch()
        scroll.setWidget(content)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def on_mood_selected(self, mood_title: str):
        parent_win = self.window()
        if hasattr(parent_win, "start_mood_session"):
            parent_win.start_mood_session(mood_title)
        else:
            print(f"[DISCOVER] Mood selected but no handler: {mood_title}")

    def refresh(self, charts: dict = None):
        while self.charts_layout.count():
            item = self.charts_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if self.auth_service and self.auth_service.is_authenticated:
            self.auth_placeholder.hide()
            if charts is None:
                charts = self.music_service.get_explore_charts()
            if not isinstance(charts, dict):
                charts = {}
            trending = charts.get("trending", [])
            if isinstance(trending, list) and trending:
                for i, track in enumerate(trending[:10]):
                    if not isinstance(track, dict):
                        continue
                    sub = track.get("artist", "") or "Various"
                    if track.get("plays"):
                        sub += "  |  " + track["plays"]
                    thumbnails = track.get("thumbnails", [])
                    thumb_url = ""
                    if isinstance(thumbnails, list) and thumbnails:
                        last = thumbnails[-1]
                        if isinstance(last, dict):
                            thumb_url = last.get("url", "")
                    card = _ChartCard(
                        track.get("title", "Track"),
                        sub,
                        thumb_url,
                        track.get("video_id", ""),
                        self._thumbnail_loader,
                    )
                    video_id = track.get("video_id", "")
                    if video_id:
                        card.clicked.connect(lambda v=video_id: self._play_station(v))
                    self.charts_layout.addWidget(card)
                self.charts_layout.addStretch()
            else:
                placeholder = QLabel("No trending data available.")
                placeholder.setObjectName("bodyMd")
                placeholder.setStyleSheet("color: #8f909b; padding: 20px;")
                self.charts_layout.addWidget(placeholder)
                self.charts_layout.addStretch()
        else:
            self.auth_placeholder.show()

    def _play_station(self, video_id: str):
        parent_win = self.window()
        if hasattr(parent_win, "play_station"):
            parent_win.play_station(video_id)


# ---------------------------------------------------------------------------
# Library / Playlists Widget (Screen 3)  -- mirrors Mis Playlist.html
# ---------------------------------------------------------------------------
class LibraryWidget(QWidget):
    def __init__(self, auth_service, music_service, thumbnail_loader, parent=None):
        super().__init__(parent)
        self.auth_service = auth_service
        self.music_service = music_service
        self._thumbnail_loader = thumbnail_loader
        self._featured_playlist_id = ""
        self._setup_ui()

    def _setup_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { background-color: transparent; border: none; }")

        content = QWidget()
        content.setStyleSheet("background-color: transparent;")
        root = QVBoxLayout(content)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(24)

        header_row = QHBoxLayout()
        header_text = QVBoxLayout()
        pl_title = QLabel("My Playlists")
        pl_title.setObjectName("headlineLg")
        header_text.addWidget(pl_title)
        pl_sub = QLabel("Synced from YouTube Music")
        pl_sub.setObjectName("bodyMd")
        header_text.addWidget(pl_sub)
        header_row.addLayout(header_text)
        header_row.addStretch()
        self.create_pl_btn = QPushButton("  Create New Playlist")
        self.create_pl_btn.setObjectName("updateBtnSmall")
        self.create_pl_btn.setIcon(QIcon(_svg_pixmap(ICONS["add"], 18, "#ffffff")))
        self.create_pl_btn.setIconSize(QSize(18, 18))
        self.create_pl_btn.clicked.connect(self._on_create_playlist)
        header_row.addWidget(self.create_pl_btn)
        root.addLayout(header_row)

        self.featured_container = QWidget()
        self.featured_container.setStyleSheet("background-color: transparent;")
        self.featured_layout = QHBoxLayout(self.featured_container)
        self.featured_layout.setSpacing(12)
        self.featured_layout.setContentsMargins(0, 0, 0, 0)
        root.addWidget(self.featured_container)

        self.playlist_row_header = QLabel("ALL PLAYLISTS")
        self.playlist_row_header.setObjectName("sectionHeader")
        root.addWidget(self.playlist_row_header)

        self.playlist_scroll = QScrollArea()
        self.playlist_scroll.setWidgetResizable(False)
        self.playlist_scroll.setFrameShape(QFrame.NoFrame)
        self.playlist_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.playlist_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.playlist_scroll.setFixedHeight(180)
        self.playlist_scroll.setStyleSheet("QScrollArea { background-color: transparent; }")

        self.playlist_row = QWidget()
        self.playlist_row.setStyleSheet("background-color: transparent;")
        self.playlist_row_layout = QHBoxLayout(self.playlist_row)
        self.playlist_row_layout.setSpacing(12)
        self.playlist_row_layout.setContentsMargins(0, 0, 0, 0)
        self.playlist_scroll.setWidget(self.playlist_row)
        root.addWidget(self.playlist_scroll)

        scroll.setWidget(content)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def _on_create_playlist(self):
        title, ok = QInputDialog.getText(
            self, "Create New Playlist", "Enter a name for your playlist:",
            text="My Curation"
        )
        if ok and title and title.strip():
            title = title.strip()
            result = self.music_service.create_remote_playlist(title)
            if result:
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.information(
                    self, "Playlist Created",
                    'Playlist "{}" created successfully on YouTube Music.'.format(title)
                )
                self.refresh()
            else:
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.warning(
                    self, "Error",
                    "Could not create playlist. Ensure you are signed in and try again."
                )

    def _play_featured(self):
        if not self._featured_playlist_id:
            return
        parent_win = self.window()
        if hasattr(parent_win, "play_playlist"):
            parent_win.play_playlist(self._featured_playlist_id)

    def refresh(self, playlists: list = None):
        if playlists is not None:
            self._rebuild_featured(playlists)
            self._rebuild_playlist_row(playlists)
        else:
            self._rebuild_featured()
            self._rebuild_playlist_row()

    def _rebuild_featured(self, cached_playlists: list = None):
        while self.featured_layout.count():
            item = self.featured_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not self.auth_service or not self.auth_service.is_authenticated:
            placeholder = QLabel("Sign in to sync your YouTube Music playlists.")
            placeholder.setObjectName("bodyMd")
            placeholder.setAlignment(Qt.AlignCenter)
            placeholder.setWordWrap(True)
            placeholder.setStyleSheet(
                "color: #8f909b; padding: 40px; background-color: rgba(28,27,27,0.4);"
                " border: 1px dashed #444650; border-radius: 16px; font-size: 15px;"
            )
            self.featured_layout.addWidget(placeholder)
            return

        playlists = cached_playlists if cached_playlists is not None else self.music_service.get_user_playlists()
        if not isinstance(playlists, list):
            print(f"[UI DEBUG] playlists is not a list: {type(playlists).__name__}")
            playlists = []
        if playlists:
            print(f"[UI DEBUG] first playlist entry keys: {list(playlists[0].keys()) if isinstance(playlists[0], dict) else type(playlists[0]).__name__}")
        else:
            print(f"[UI DEBUG] playlists list is empty (length {len(playlists)})")
            placeholder = QLabel("No playlists found. Create one!")
            placeholder.setObjectName("bodyMd")
            placeholder.setAlignment(Qt.AlignCenter)
            placeholder.setStyleSheet("color: #8f909b; padding: 20px;")
            self.featured_layout.addWidget(placeholder)
            return

        featured = playlists[0] if isinstance(playlists[0], dict) else {}
        self._featured_playlist_id = featured.get("playlistId", "")
        featured_thumbs = featured.get("thumbnails") or []
        featured_thumb_url = ""
        if isinstance(featured_thumbs, list) and featured_thumbs and isinstance(featured_thumbs[0], dict):
            featured_thumb_url = featured_thumbs[0].get("url", "")
        feat_card = QFrame()
        feat_card.setObjectName("glassCard")
        feat_card.setStyleSheet(
            "QFrame#glassCard {"
            " background: qlineargradient(x1:0 y1:0, x2:1 y2:1,"
            " stop:0 #0f2027, stop:1 #2c5364);"
            " border: 1px solid rgba(255,255,255,0.06);"
            " border-radius: 16px; padding: 20px; min-height: 160px; }"
        )
        if featured_thumb_url:
            feat_thumb = QLabel(feat_card)
            feat_thumb.setFixedSize(80, 80)
            feat_thumb.setScaledContents(True)
            feat_thumb.setStyleSheet("background: transparent; border-radius: 8px;")
            self._thumbnail_loader.load(feat_thumb, featured_thumb_url)
        feat_layout = QVBoxLayout(feat_card)
        feat_layout.setSpacing(8)

        recent_badge = QLabel("MOST RECENT")
        recent_badge.setObjectName("statusBadge")
        recent_badge.setStyleSheet(
            "color: #b4c5ff; font-size: 11px;"
            " background-color: rgba(180,197,255,0.12);"
            " padding: 4px 12px; border-radius: 12px;"
        )
        feat_layout.addWidget(recent_badge)

        feat_title = QLabel(featured.get("title", "Featured Playlist"))
        feat_title.setObjectName("headlineMd")
        feat_title.setStyleSheet("color: #ffffff; font-size: 22px;")
        feat_layout.addWidget(feat_title)

        feat_desc = QLabel(
            "{} tracks  |  Synced from YouTube Music".format(featured.get("count", 0))
        )
        feat_desc.setObjectName("bodyMd")
        feat_desc.setStyleSheet("color: rgba(255,255,255,0.7); font-size: 13px;")
        feat_layout.addWidget(feat_desc)

        feat_layout.addStretch()
        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)

        edit_btn = QPushButton("  Edit Playlist")
        edit_btn.setObjectName("ghostBtn")
        edit_btn.setIcon(QIcon(_svg_pixmap(ICONS["edit"], 16, "#c5c6d2")))
        edit_btn.setIconSize(QSize(16, 16))
        edit_btn.setStyleSheet(
            "QPushButton { background: transparent; border: 1px solid rgba(255,255,255,0.3);"
            " border-radius: 22px; padding: 8px 20px; color: #ffffff;"
            " font-size: 13px; font-weight: 600; }"
            " QPushButton:hover { background: rgba(255,255,255,0.1); }"
        )
        btn_row.addWidget(edit_btn)

        play_feat_btn = QPushButton()
        play_feat_btn.setIcon(QIcon(_svg_pixmap(ICONS["play_arrow"], 18, "#000000")))
        play_feat_btn.setIconSize(QSize(18, 18))
        play_feat_btn.setText(" Play Now")
        play_feat_btn.setObjectName("heroPlayBtn")
        play_feat_btn.setStyleSheet(
            "QPushButton { background-color: #ffffff; color: #000000;"
            " border-radius: 22px; padding: 8px 20px; font-size: 13px; font-weight: 700; }"
        )
        play_feat_btn.clicked.connect(self._play_featured)
        btn_row.addWidget(play_feat_btn)
        btn_row.addStretch()
        feat_layout.addLayout(btn_row)
        self.featured_layout.addWidget(feat_card, stretch=8)

        stack = QVBoxLayout()
        stack.setSpacing(8)
        for pl in (playlists[1:4] if len(playlists) > 1 else []):
            if not isinstance(pl, dict):
                continue
            item_card = QFrame()
            item_card.setObjectName("glassCard")
            item_card.setStyleSheet(
                "QFrame#glassCard { background-color: rgba(28,27,27,0.6);"
                " border: 1px solid #353534; border-radius: 10px;"
                " padding: 12px; min-height: 52px; }"
            )
            il = QHBoxLayout(item_card)
            il.setSpacing(12)
            il.setContentsMargins(12, 8, 12, 8)

            cover = QFrame()
            cover.setFixedSize(48, 48)
            g = BENTO_GRADIENTS[random.randint(0, len(BENTO_GRADIENTS)-1)]
            cover.setStyleSheet(
                "background: qlineargradient(x1:0 y1:0, x2:1 y2:1,"
                " stop:0 {}, stop:1 {}); border-radius: 8px;".format(g[0], g[1])
            )
            il.addWidget(cover)

            text_col = QVBoxLayout()
            text_col.setSpacing(2)
            n = QLabel(pl.get("title", "Playlist"))
            n.setObjectName("labelBold")
            n.setStyleSheet("color: #e4e1e8; font-size: 13px;")
            text_col.addWidget(n)
            c = QLabel("{} Songs  |  YouTube Music".format(pl.get("count", 0)))
            c.setObjectName("codeLog")
            c.setStyleSheet("color: #c5c6d2; font-size: 11px;")
            text_col.addWidget(c)
            il.addLayout(text_col, stretch=1)

            play_icon = _icon_label("play_circle", 22, "#c5c6d2")
            il.addWidget(play_icon)

            stack.addWidget(item_card)

        import_card = QFrame()
        import_card.setObjectName("glassCard")
        import_card.setStyleSheet(
            "QFrame#glassCard { background-color: transparent;"
            " border: 2px dashed rgba(143,144,155,0.3);"
            " border-radius: 10px; min-height: 52px; }"
        )
        import_layout = QHBoxLayout(import_card)
        import_layout.setAlignment(Qt.AlignCenter)
        import_layout.setSpacing(8)
        import_icon = _icon_label("library_music", 22, "#b4c5ff")
        import_layout.addWidget(import_icon)
        import_text = QLabel("Import more from YTM")
        import_text.setObjectName("labelBold")
        import_text.setStyleSheet("color: #c5c6d2; font-size: 12px;")
        import_layout.addWidget(import_text)
        stack.addWidget(import_card)

        stack.addStretch()
        stack_widget = QWidget()
        stack_widget.setStyleSheet("background-color: transparent;")
        stack_widget.setLayout(stack)
        self.featured_layout.addWidget(stack_widget, stretch=4)

    def _rebuild_playlist_row(self, cached_playlists: list = None):
        while self.playlist_row_layout.count():
            item = self.playlist_row_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not self.auth_service or not self.auth_service.is_authenticated:
            self.playlist_row_header.hide()
            return

        self.playlist_row_header.show()
        playlists = cached_playlists if cached_playlists is not None else self.music_service.get_user_playlists()
        if not isinstance(playlists, list):
            playlists = []
        if not playlists:
            placeholder = QLabel("No playlists yet.")
            placeholder.setObjectName("codeLog")
            placeholder.setStyleSheet("color: #8f909b; padding: 10px;")
            self.playlist_row_layout.addWidget(placeholder)
            self.playlist_row_layout.addStretch()
            return

        for pl in playlists:
            if not isinstance(pl, dict):
                print(f"[UI DEBUG] skipping non-dict playlist entry: {type(pl).__name__}")
                continue
            thumb_url = ""
            thumbs = pl.get("thumbnails") or []
            if isinstance(thumbs, list) and thumbs and isinstance(thumbs[0], dict):
                thumb_url = thumbs[0].get("url", "")
            card = QFrame()
            card.setObjectName("glassCard")
            card.setFixedSize(140, 150)
            card.setStyleSheet(
                "QFrame#glassCard { background-color: rgba(28,27,27,0.6);"
                " border: 1px solid #353534; border-radius: 12px;"
                " padding: 10px; }"
                " QFrame#glassCard:hover { border-color: #5f74b7; }"
            )
            cl = QVBoxLayout(card)
            cl.setSpacing(6)
            cl.setContentsMargins(8, 8, 8, 8)

            cover = QFrame()
            cover.setFixedSize(60, 60)
            g = BENTO_GRADIENTS[random.randint(0, len(BENTO_GRADIENTS)-1)]
            cover.setStyleSheet(
                "background: qlineargradient(x1:0 y1:0, x2:1 y2:1,"
                " stop:0 {}, stop:1 {}); border-radius: 8px;".format(g[0], g[1])
            )
            thumb_label = QLabel(cover)
            thumb_label.setFixedSize(60, 60)
            thumb_label.setScaledContents(True)
            thumb_label.setStyleSheet("background: transparent; border-radius: 8px;")
            if thumb_url:
                self._thumbnail_loader.load(thumb_label, thumb_url)
            cl.addWidget(cover, alignment=Qt.AlignCenter)

            name = QLabel(pl.get("title", "Playlist"))
            name.setObjectName("labelBold")
            name.setStyleSheet("color: #e4e1e8; font-size: 11px;")
            name.setWordWrap(True)
            name.setAlignment(Qt.AlignCenter)
            cl.addWidget(name)

            cnt = QLabel("{} Tracks".format(pl.get("count", 0)))
            cnt.setObjectName("codeLog")
            cnt.setStyleSheet("color: #c5c6d2; font-size: 10px;")
            cnt.setAlignment(Qt.AlignCenter)
            cl.addWidget(cnt)

            self.playlist_row_layout.addWidget(card)

        self.playlist_row_layout.addStretch()


# ---------------------------------------------------------------------------
# History Widget (Screen 4)  -- mirrors Biblioteca e Historial.html
# ---------------------------------------------------------------------------
class HistoryWidget(QWidget):
    track_selected = Signal(str)

    def __init__(self, auth_service, music_service, thumbnail_loader, parent=None):
        super().__init__(parent)
        self.auth_service = auth_service
        self.music_service = music_service
        self._thumbnail_loader = thumbnail_loader
        self._setup_ui()

    def _setup_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { background-color: transparent; border: none; }")

        content = QWidget()
        content.setStyleSheet("background-color: transparent;")
        root = QVBoxLayout(content)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(24)

        header_section = QFrame()
        header_section.setObjectName("glassCard")
        header_section.setStyleSheet(
            "QFrame#glassCard { background-color: rgba(28,27,27,0.6);"
            " border: 1px solid #353534; border-radius: 16px; padding: 24px; }"
        )
        header_layout = QVBoxLayout(header_section)
        header_layout.setSpacing(8)

        live_row = QHBoxLayout()
        pulse_dot = QFrame()
        pulse_dot.setFixedSize(8, 8)
        pulse_dot.setStyleSheet("background-color: #b4c5ff; border-radius: 4px;")
        live_row.addWidget(pulse_dot)
        history_badge = QLabel("  HISTORY LOG")
        history_badge.setObjectName("statusBadge")
        live_row.addWidget(history_badge)
        live_row.addStretch()

        filter_btn = QPushButton("  Filter")
        filter_btn.setObjectName("ghostBtn")
        filter_btn.setIcon(QIcon(_svg_pixmap(ICONS["filter_list"], 16, "#c5c6d2")))
        filter_btn.setIconSize(QSize(16, 16))
        filter_btn.setStyleSheet(
            "QPushButton { background-color: #29292f; border: 1px solid #444650;"
            " border-radius: 22px; padding: 8px 18px; font-size: 13px; }"
        )
        live_row.addWidget(filter_btn)

        resume_btn = QPushButton("  Resume Session")
        resume_btn.setObjectName("updateBtnSmall")
        resume_btn.setIcon(QIcon(_svg_pixmap(ICONS["play_arrow"], 16, "#ffffff")))
        resume_btn.setIconSize(QSize(16, 16))
        live_row.addWidget(resume_btn)
        header_layout.addLayout(live_row)

        hist_title = QLabel("Your Sonic Journey")
        hist_title.setObjectName("headlineLg")
        hist_title.setStyleSheet("font-size: 32px;")
        header_layout.addWidget(hist_title)

        hist_desc = QLabel(
            "A curated timeline of your last discoveries from YouTube Music, "
            "processed through QueNota? for optimized mixing."
        )
        hist_desc.setObjectName("bodyMd")
        hist_desc.setStyleSheet("color: #c5c6d2; max-width: 600px;")
        hist_desc.setWordWrap(True)
        header_layout.addWidget(hist_desc)
        root.addWidget(header_section)

        grid = QHBoxLayout()
        grid.setSpacing(16)

        self.featured_frame = QFrame()
        self.featured_frame.setObjectName("glassCard")
        self.featured_frame.setStyleSheet(
            "QFrame#glassCard { background-color: rgba(28,27,27,0.6);"
            " border: 1px solid #353534; border-radius: 14px;"
            " padding: 12px; min-width: 260px; }"
        )
        self.featured_layout_inner = QVBoxLayout(self.featured_frame)
        self.featured_layout_inner.setSpacing(8)

        self.featured_cover = QFrame()
        self.featured_cover.setFixedSize(200, 200)
        self.featured_cover.setStyleSheet(
            "background: qlineargradient(x1:0 y1:0, x2:1 y2:1,"
            " stop:0 #6a3093, stop:1 #a044ff); border-radius: 10px;"
        )
        self.featured_layout_inner.addWidget(self.featured_cover, alignment=Qt.AlignCenter)

        self.featured_badge = QLabel("MOST PLAYED")
        self.featured_badge.setObjectName("statusBadge")
        self.featured_badge.setStyleSheet(
            "color: #fcb970; font-size: 11px; letter-spacing: 0.1em;"
        )
        self.featured_layout_inner.addWidget(self.featured_badge)

        self.featured_song = QLabel("Hyper-Reality Drift")
        self.featured_song.setObjectName("headlineMd")
        self.featured_song.setStyleSheet("font-size: 18px; color: #e4e1e8;")
        self.featured_layout_inner.addWidget(self.featured_song)

        self.featured_artist = QLabel("Synthwave Prophet")
        self.featured_artist.setObjectName("bodyMd")
        self.featured_artist.setStyleSheet("color: #c5c6d2; font-size: 13px;")
        self.featured_layout_inner.addWidget(self.featured_artist)

        grid.addWidget(self.featured_frame, stretch=4)

        list_frame = QFrame()
        list_frame.setObjectName("glassCard")
        list_frame.setStyleSheet(
            "QFrame#glassCard { background-color: rgba(28,27,27,0.6);"
            " border: 1px solid #353534; border-radius: 14px; }"
        )
        list_layout = QVBoxLayout(list_frame)
        list_layout.setContentsMargins(0, 0, 0, 0)
        list_layout.setSpacing(0)

        list_header = QFrame()
        list_header.setStyleSheet("background: transparent; border-bottom: 1px solid #444650;")
        list_header_layout = QHBoxLayout(list_header)
        list_header_layout.setContentsMargins(20, 16, 20, 16)
        recent_title = QLabel("Recent Tracks")
        recent_title.setObjectName("headlineMd")
        recent_title.setStyleSheet("font-size: 20px;")
        list_header_layout.addWidget(recent_title)
        list_header_layout.addStretch()
        self.list_count = QLabel("0 Songs  |  YT Music API")
        self.list_count.setObjectName("codeLog")
        self.list_count.setStyleSheet("color: #8f909b; font-size: 12px;")
        list_header_layout.addWidget(self.list_count)
        list_layout.addWidget(list_header)

        self.history_scroll = QScrollArea()
        self.history_scroll.setWidgetResizable(True)
        self.history_scroll.setFrameShape(QFrame.NoFrame)
        self.history_scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        self.history_scroll.setMaximumHeight(600)

        self.history_container = QWidget()
        self.history_container.setStyleSheet("background: transparent;")
        self.history_container_layout = QVBoxLayout(self.history_container)
        self.history_container_layout.setContentsMargins(0, 0, 0, 0)
        self.history_container_layout.setSpacing(0)
        self.history_container_layout.addStretch()

        self.history_scroll.setWidget(self.history_container)
        list_layout.addWidget(self.history_scroll)
        grid.addWidget(list_frame, stretch=8)

        root.addLayout(grid)

        self.auth_placeholder = QLabel(
            "Sign in to see your listening history from YouTube Music."
        )
        self.auth_placeholder.setObjectName("bodyMd")
        self.auth_placeholder.setWordWrap(True)
        self.auth_placeholder.setAlignment(Qt.AlignCenter)
        self.auth_placeholder.setStyleSheet(
            "color: #8f909b; padding: 40px; background-color: rgba(28,27,27,0.4);"
            " border: 1px dashed #444650; border-radius: 16px;"
        )
        root.addWidget(self.auth_placeholder)

        root.addStretch()
        scroll.setWidget(content)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def refresh(self, history: list = None):
        if self.auth_service and self.auth_service.is_authenticated:
            self.auth_placeholder.hide()
            if history is None:
                history = self.music_service.get_user_history(limit=30) or []
            if isinstance(history, list) and history:
                self._populate_history(history)
            else:
                self._clear_history()
                self.list_count.setText("Trending Tracks (Public Fallback)")
                fallback = self.music_service.get_explore_charts().get("trending", [])
                if fallback:
                    self._populate_history(fallback)
                else:
                    placeholder = QLabel("No history available.")
                    placeholder.setObjectName("bodyMd")
                    placeholder.setStyleSheet("color: #8f909b; padding: 20px;")
                    self.history_container_layout.insertWidget(0, placeholder)
        else:
            self.auth_placeholder.show()
            self._clear_history()

    def _clear_history(self):
        while self.history_container_layout.count():
            item = self.history_container_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.history_container_layout.addStretch()

    def _populate_history(self, history: list):
        self._clear_history()
        if not isinstance(history, list):
            history = []
        self.list_count.setText("{} Songs  |  YT Music API".format(len(history)))

        if history:
            first = history[0]
            if isinstance(first, dict):
                self.featured_song.setText(first.get("title", "Track"))
                self.featured_artist.setText(first.get("artist", "Artist") or "Artist")

        for entry in history:
            if not isinstance(entry, dict):
                continue
            video_id = entry.get("videoId") or entry.get("video_id", "")
            row = _ClickableRow(video_id)
            row.setObjectName("historyRow")
            row.clicked.connect(self.track_selected.emit)
            layout = QHBoxLayout(row)
            layout.setContentsMargins(16, 8, 16, 8)
            layout.setSpacing(14)

            cover = QFrame()
            cover.setFixedSize(48, 48)
            g = BENTO_GRADIENTS[random.randint(0, len(BENTO_GRADIENTS)-1)]
            cover.setStyleSheet(
                "background: qlineargradient(x1:0 y1:0, x2:1 y2:1,"
                " stop:0 {}, stop:1 {}); border-radius: 6px;".format(g[0], g[1])
            )
            thumb_label = QLabel(cover)
            thumb_label.setFixedSize(48, 48)
            thumb_label.setScaledContents(True)
            thumb_label.setStyleSheet("background: transparent; border-radius: 6px;")
            thumbs = entry.get("thumbnails") or []
            thumb_url = ""
            if isinstance(thumbs, list) and thumbs and isinstance(thumbs[0], dict):
                thumb_url = thumbs[0].get("url", "")
            if thumb_url:
                self._thumbnail_loader.load(thumb_label, thumb_url)
            layout.addWidget(cover)

            info = QVBoxLayout()
            info.setSpacing(2)
            title = QLabel(entry.get("title", "Unknown Track"))
            title.setObjectName("labelBold")
            title.setStyleSheet("color: #e4e1e8; font-size: 13px;")
            info.addWidget(title)
            artist = QLabel(entry.get("artist", "") or "Unknown Artist")
            artist.setObjectName("codeLog")
            artist.setStyleSheet("color: #c5c6d2; font-size: 11px;")
            info.addWidget(artist)
            layout.addLayout(info, stretch=1)

            album = QLabel(entry.get("album", "") or "")
            album.setObjectName("codeLog")
            album.setStyleSheet("color: #8f909b; font-size: 11px;")
            album.setFixedWidth(200)
            layout.addWidget(album)

            duration = QLabel(entry.get("duration", ""))
            duration.setObjectName("goldText")
            duration.setFixedWidth(60)
            duration.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            layout.addWidget(duration)

            more_btn = _icon_button("more_vert", 18, "#8f909b", "", "")
            more_btn.setStyleSheet(
                "QPushButton { background: transparent; border: none;"
                " padding: 4px; min-width: 28px; min-height: 28px; }"
            )
            layout.addWidget(more_btn)

            self.history_container_layout.insertWidget(
                self.history_container_layout.count() - 1, row
            )


# ---------------------------------------------------------------------------
# Async data workers
# ---------------------------------------------------------------------------
class _ChartsWorker(QThread):
    data_loaded = Signal(dict)
    def __init__(self, music_service):
        super().__init__()
        self.music_service = music_service
    def run(self):
        try:
            charts = self.music_service.get_explore_charts()
        except Exception:
            charts = {"moods": [], "trending": []}
        self.data_loaded.emit(charts)

class _PlaylistsWorker(QThread):
    data_loaded = Signal(list)
    def __init__(self, music_service):
        super().__init__()
        self.music_service = music_service
    def run(self):
        try:
            playlists = self.music_service.get_user_playlists()
        except Exception:
            playlists = []
        self.data_loaded.emit(playlists)

class _HistoryWorker(QThread):
    data_loaded = Signal(list)
    def __init__(self, music_service):
        super().__init__()
        self.music_service = music_service
    def run(self):
        try:
            history = self.music_service.get_user_history(limit=30)
        except Exception:
            history = []
        self.data_loaded.emit(history)


class _HomeWorker(QThread):
    data_loaded = Signal(list)
    def __init__(self, music_service):
        super().__init__()
        self.music_service = music_service
    def run(self):
        try:
            home_data = self.music_service.get_home()
        except Exception:
            home_data = []
        self.data_loaded.emit(home_data)


# ---------------------------------------------------------------------------
# Home / Inicio Widget (YouTube Music style)
# ---------------------------------------------------------------------------
class _HomeCard(QFrame):
    clicked = Signal(str)
    def __init__(self, title: str, subtitle: str, thumb_url: str, video_id: str, thumbnail_loader, parent=None):
        super().__init__(parent)
        self._video_id = video_id
        self.setObjectName("musicCard")
        self.setFixedSize(160, 200)
        self.setCursor(Qt.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self.thumb = QLabel()
        self.thumb.setFixedSize(160, 160)
        self.thumb.setScaledContents(True)
        self.thumb.setStyleSheet("background-color: #29292f; border-radius: 10px;")
        layout.addWidget(self.thumb)

        title_lbl = QLabel(title)
        title_lbl.setStyleSheet("color: #e4e1e8; font-size: 12px; font-weight: 600; padding: 0 4px;")
        title_lbl.setWordWrap(True)
        title_lbl.setFixedWidth(160)
        layout.addWidget(title_lbl)

        sub_lbl = QLabel(subtitle)
        sub_lbl.setStyleSheet("color: #8f909b; font-size: 11px; padding: 0 4px;")
        sub_lbl.setFixedWidth(160)
        layout.addWidget(sub_lbl)

        layout.addStretch()

        if thumb_url and thumbnail_loader:
            thumbnail_loader.load(self.thumb, thumb_url)

    def mousePressEvent(self, event):
        if self._video_id:
            self.clicked.emit(self._video_id)
        super().mousePressEvent(event)


class HomeWidget(QScrollArea):
    track_selected = Signal(str)

    def __init__(self, music_service, thumbnail_loader, parent=None):
        super().__init__(parent)
        self.music_service = music_service
        self._thumbnail_loader = thumbnail_loader
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setObjectName("homeWidget")

        self._container = QWidget()
        self._container.setObjectName("homeContainer")
        self._layout = QVBoxLayout(self._container)
        self._layout.setContentsMargins(24, 24, 24, 24)
        self._layout.setSpacing(24)
        self.setWidget(self._container)

        self._loading = QLabel("Loading your home...")
        self._loading.setStyleSheet("color: #8f909b; font-size: 14px;")
        self._loading.setAlignment(Qt.AlignCenter)
        self._layout.addWidget(self._loading)

    def refresh(self, sections: list):
        while self._layout.count():
            item = self._layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        if not sections:
            placeholder = QLabel("Sign in to see your personalized Home feed.")
            placeholder.setStyleSheet("color: #8f909b; font-size: 14px;")
            placeholder.setAlignment(Qt.AlignCenter)
            self._layout.addWidget(placeholder)
            return

        for section in sections:
            if not isinstance(section, dict):
                continue
            section_title = section.get("title", "")
            contents = section.get("contents", [])
            if not contents or not isinstance(contents, list):
                continue

            title_lbl = QLabel(section_title)
            title_lbl.setStyleSheet("color: #e4e1e8; font-size: 20px; font-weight: 700;")
            self._layout.addWidget(title_lbl)

            scroll_frame = QFrame()
            scroll_frame.setFixedHeight(240)
            scroll_layout = QHBoxLayout(scroll_frame)
            scroll_layout.setContentsMargins(0, 0, 0, 0)
            scroll_layout.setSpacing(12)

            for item in contents:
                if not isinstance(item, dict):
                    continue
                item_title = item.get("title", "")
                item_sub = ""
                artists = item.get("artists")
                if isinstance(artists, list) and artists:
                    item_sub = artists[0].get("name", "")
                if not item_sub:
                    item_sub = item.get("artist", "")
                if not item_sub:
                    item_sub = item.get("subtitle", "")
                thumbnails = item.get("thumbnails", [])
                thumb_url = ""
                if isinstance(thumbnails, list) and thumbnails:
                    last = thumbnails[-1]
                    if isinstance(last, dict):
                        thumb_url = last.get("url", "")
                video_id = item.get("videoId", "") or item.get("playlistId", "")

                card = _HomeCard(item_title, item_sub, thumb_url, video_id, self._thumbnail_loader)
                card.clicked.connect(self._on_card_clicked)
                scroll_layout.addWidget(card)

            scroll_layout.addStretch()
            self._layout.addWidget(scroll_frame)

        self._layout.addStretch()

    def _on_card_clicked(self, video_id: str):
        self.track_selected.emit(video_id)


class _ChartCard(QFrame):
    clicked = Signal(str)

    def __init__(self, title: str, subtitle: str, thumb_url: str, video_id: str, thumbnail_loader, parent=None):
        super().__init__(parent)
        self._video_id = video_id
        self.setObjectName("musicCard")
        self.setFixedSize(140, 185)
        self.setCursor(Qt.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self.thumb = QLabel()
        self.thumb.setFixedSize(140, 140)
        self.thumb.setScaledContents(True)
        self.thumb.setStyleSheet("background-color: #29292f; border-radius: 10px;")
        layout.addWidget(self.thumb)

        title_lbl = QLabel(title)
        title_lbl.setStyleSheet("color: #e4e1e8; font-size: 12px; font-weight: 600; padding: 0 4px;")
        title_lbl.setFixedWidth(140)
        title_lbl.setWordWrap(True)
        layout.addWidget(title_lbl)

        sub_lbl = QLabel(subtitle)
        sub_lbl.setStyleSheet("color: #8f909b; font-size: 10px; padding: 0 4px;")
        sub_lbl.setFixedWidth(140)
        layout.addWidget(sub_lbl)

        if thumb_url and thumbnail_loader:
            thumbnail_loader.load(self.thumb, thumb_url)

    def mousePressEvent(self, event):
        if self._video_id:
            self.clicked.emit(self._video_id)
        super().mousePressEvent(event)


# ---------------------------------------------------------------------------
# Async thumbnail loader
# ---------------------------------------------------------------------------
class _ThumbnailLoader(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._nam = QNetworkAccessManager(self)
        self._nam.finished.connect(self._on_finished)
        self._pending = {}

    def load(self, label: QLabel, url: str):
        if not url:
            return
        req = QNetworkRequest(QUrl(url))
        reply = self._nam.get(req)
        self._pending[reply] = label

    def _on_finished(self, reply):
        label = self._pending.pop(reply, None)
        if label is not None and reply.error() == QNetworkReply.NoError:
            data = reply.readAll()
            pixmap = QPixmap()
            if pixmap.loadFromData(data):
                try:
                    label.setPixmap(pixmap)
                except RuntimeError:
                    pass
                except Exception as e:
                    print(f"[IMAGE LOADER] Ignored error: {e}")
        reply.deleteLater()


class _ClickableRow(QFrame):
    clicked = Signal(str)
    def __init__(self, data_id="", parent=None):
        super().__init__(parent)
        self._data_id = data_id
        self.setCursor(Qt.PointingHandCursor)

    def mousePressEvent(self, event):
        self.clicked.emit(self._data_id)
        super().mousePressEvent(event)


# ---------------------------------------------------------------------------
# Main Window
# ---------------------------------------------------------------------------
class DJMainWindow(QMainWindow):
    def __init__(self, llm_service, music_service, auth_service):
        super().__init__()
        self.llm_service = llm_service
        self.music_service = music_service
        self.auth_service = auth_service

        self.setWindowTitle(f"QueNota? - {self.auth_service.user_display_name}")
        self.setMinimumSize(1100, 720)
        self.setStyleSheet(VIBE_QSS)

        self.worker_thread = None
        self._current_nav = 0
        self._thumbnail_loader = _ThumbnailLoader(self)

        self._build_outer_stack()
        self._connect_auth_signals()
        self._restore_session()

    def _build_outer_stack(self):
        self.outer_stack = QStackedWidget()
        self.outer_stack.setObjectName("centralWidget")
        self.setCentralWidget(self.outer_stack)

        self.login_widget = LoginWidget()
        self.login_widget.web_auth_requested.connect(self._on_web_auth)
        self.outer_stack.addWidget(self.login_widget)

        self.app_shell = QWidget()
        self.app_shell.setObjectName("centralWidget")
        shell_layout = QVBoxLayout(self.app_shell)
        shell_layout.setContentsMargins(0, 0, 0, 0)
        shell_layout.setSpacing(0)

        content_row = QHBoxLayout()
        content_row.setContentsMargins(0, 0, 0, 0)
        content_row.setSpacing(0)

        self._build_sidebar()
        content_row.addWidget(self.sidebar)

        self.inner_stack = QStackedWidget()
        content_row.addWidget(self.inner_stack, stretch=1)
        shell_layout.addLayout(content_row, stretch=1)

        self.playback_bar = PlaybackBar(self._thumbnail_loader)
        self.playback_bar.play_pause_requested.connect(self.toggle_playback_state)
        self.playback_bar.skip_requested.connect(self._on_bar_skip)
        self.playback_bar.back_requested.connect(self._on_bar_back)
        self.playback_bar.volume_changed.connect(self._on_bar_volume)
        self.playback_bar.velocity_changed.connect(self._on_bar_speed)
        self.playback_bar.shuffle_requested.connect(self._on_bar_shuffle)
        self.playback_bar.repeat_requested.connect(self._on_bar_repeat)
        self.playback_bar.set_transport_enabled(False)
        shell_layout.addWidget(self.playback_bar)

        self.outer_stack.addWidget(self.app_shell)

    def _build_sidebar(self):
        self.sidebar = QWidget()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setFixedWidth(240)
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(12, 20, 12, 20)
        sidebar_layout.setSpacing(4)

        brand = QLabel("QueNota?")
        brand.setObjectName("brandSmall")
        brand.setStyleSheet("padding: 0 12px 16px 12px;")
        sidebar_layout.addWidget(brand)

        user_card = QWidget()
        user_card.setObjectName("glassCard")
        user_card.setStyleSheet(
            "QWidget#glassCard { background-color: rgba(52,52,57,0.4);"
            " border-radius: 10px; padding: 10px; margin: 0 4px 16px 4px; }"
        )
        user_layout = QHBoxLayout(user_card)
        user_layout.setSpacing(10)
        user_layout.setContentsMargins(10, 8, 10, 8)

        self.sidebar_avatar = QLabel()
        self.sidebar_avatar.setFixedSize(36, 36)
        self.sidebar_avatar.setObjectName("sidebarAvatar")
        self.sidebar_avatar.setScaledContents(True)
        self.sidebar_avatar.setStyleSheet(
            "QLabel#sidebarAvatar {"
            " background-color: #2a2a32;"
            " border-radius: 18px;"
            "}"
        )
        self._apply_avatar_mask()
        user_layout.addWidget(self.sidebar_avatar)

        user_col = QVBoxLayout()
        user_col.setSpacing(2)
        self.sidebar_user = QLabel(self.auth_service.user_display_name)
        self.sidebar_user.setObjectName("labelBold")
        self.sidebar_user.setStyleSheet("color: #e4e1e8; font-size: 13px;")
        user_col.addWidget(self.sidebar_user)
        self.bottom_auth_label = QLabel("Vibe: Bronco")
        self.bottom_auth_label.setObjectName("codeLog")
        self.bottom_auth_label.setStyleSheet("color: #c5c6d2; font-size: 10px;")
        user_col.addWidget(self.bottom_auth_label)
        user_layout.addLayout(user_col)
        sidebar_layout.addWidget(user_card)

        self.nav_buttons = []
        nav_items = [
            ("home", "Inicio"),
            ("radio", "QueNota?"),
            ("explore", "Explorar"),
            ("library_music", "Biblioteca"),
            ("history", "Historial"),
        ]
        for icon_name, label in nav_items:
            btn = QPushButton()
            btn.setObjectName("navBtn")
            btn.setIcon(QIcon(_svg_pixmap(ICONS[icon_name], 20, "#c5c6d2")))
            btn.setIconSize(QSize(20, 20))
            btn.setText("  " + label)
            btn.setCheckable(True)
            btn.clicked.connect(
                lambda checked=False, idx=len(self.nav_buttons): self._switch_nav(idx)
            )
            self.nav_buttons.append(btn)
            sidebar_layout.addWidget(btn)

        sidebar_layout.addStretch()

        new_session = QPushButton()
        new_session.setObjectName("newSessionBtn")
        new_session.setIcon(QIcon(_svg_pixmap(ICONS["add_circle"], 18, "#e4e1e8")))
        new_session.setIconSize(QSize(18, 18))
        new_session.setText("  New Session")
        new_session.setCursor(Qt.PointingHandCursor)
        new_session.clicked.connect(self._on_new_session)
        sidebar_layout.addWidget(new_session)

        support_btn = QPushButton()
        support_btn.setObjectName("bottomLinkBtn")
        support_btn.setIcon(QIcon(_svg_pixmap(ICONS["help"], 18, "#c5c6d2")))
        support_btn.setIconSize(QSize(18, 18))
        support_btn.setText("  Support")
        sidebar_layout.addWidget(support_btn)

        self.logout_btn = QPushButton()
        self.logout_btn.setObjectName("bottomLinkBtn")
        self.logout_btn.setIcon(QIcon(_svg_pixmap(ICONS["logout"], 18, "#c5c6d2")))
        self.logout_btn.setIconSize(QSize(18, 18))
        self.logout_btn.setText("  Logout")
        self.logout_btn.clicked.connect(self._on_logout)
        sidebar_layout.addWidget(self.logout_btn)

    def _build_inner_stack(self):
        self.home = HomeWidget(self.music_service, self._thumbnail_loader)
        self.home.track_selected.connect(self.play_station)
        self.inner_stack.addWidget(self.home)

        self.dj_booth = DJBoothWidget()
        self.dj_booth._thumbnail_loader = self._thumbnail_loader
        self.dj_booth.start_session_requested.connect(self._on_start_session)
        self.inner_stack.addWidget(self.dj_booth)

        self.discover = DiscoverWidget(self.auth_service, self.music_service, self._thumbnail_loader)
        self.inner_stack.addWidget(self.discover)

        self.library = LibraryWidget(self.auth_service, self.music_service, self._thumbnail_loader)
        self.inner_stack.addWidget(self.library)

        self.history = HistoryWidget(self.auth_service, self.music_service, self._thumbnail_loader)
        self.history.track_selected.connect(self.play_station)
        self.inner_stack.addWidget(self.history)

    def _switch_nav(self, idx: int):
        self._current_nav = idx
        for i, btn in enumerate(self.nav_buttons):
            btn.setChecked(i == idx)
        self.inner_stack.setCurrentIndex(idx)

    def _connect_auth_signals(self):
        self.auth_service.logout_success.connect(self._on_logout_success)

    def _restore_session(self):
        if self.auth_service.try_restore_session():
            self._build_inner_stack()
            self._switch_to_app()
        else:
            self._build_inner_stack()
            self.outer_stack.setCurrentIndex(0)

    @Slot()
    def _on_web_auth(self):
        self.hide()
        ok = run_login_window()
        if ok:
            if self.auth_service.try_restore_session():
                self._switch_to_app()
                self.show()
            else:
                self.login_widget.show_auth_status(
                    "Session file found but could not be loaded. Try again.",
                    error=True,
                )
                self.show()
        else:
            self.login_widget.show_auth_status(
                "Sign-in window was closed before completion.",
                error=True,
            )
            self.show()

    @Slot()
    def _switch_to_app(self):
        self.sidebar_user.setText(self.auth_service.user_display_name)
        self.llm_service.username = self.auth_service.user_display_name
        self.setWindowTitle(f"QueNota? - {self.auth_service.user_display_name}")
        self.bottom_auth_label.setText("Signed in")
        self.outer_stack.setCurrentIndex(1)
        self.inner_stack.setCurrentIndex(0)
        self.nav_buttons[0].setChecked(True)

        QTimer.singleShot(0, self.discover.refresh)
        QTimer.singleShot(0, self.library.refresh)
        QTimer.singleShot(0, self.history.refresh)

        # load profile avatar from the API (async via thumbnail loader)
        avatar_url = self.music_service.get_account_avatar()
        if avatar_url:
            self._thumbnail_loader.load(self.sidebar_avatar, avatar_url)

        self._home_worker = _HomeWorker(self.music_service)
        self._home_worker.data_loaded.connect(
            lambda data: QTimer.singleShot(0, lambda: self.home.refresh(data))
        )
        self._home_worker.start()

        self._charts_worker = _ChartsWorker(self.music_service)
        self._playlists_worker = _PlaylistsWorker(self.music_service)
        self._history_worker = _HistoryWorker(self.music_service)

        self._charts_worker.data_loaded.connect(
            lambda charts: QTimer.singleShot(0, lambda: self.discover.refresh(charts))
        )
        self._playlists_worker.data_loaded.connect(
            lambda playlists: QTimer.singleShot(0, lambda: self.library.refresh(playlists))
        )
        self._history_worker.data_loaded.connect(
            lambda history: QTimer.singleShot(0, lambda: self.history.refresh(history))
        )

        self._charts_worker.start()
        self._playlists_worker.start()
        self._history_worker.start()

    @Slot(str, str)
    def _on_user_info(self, name: str, avatar_url: str):
        if name and name != "Oyente":
            self.sidebar_user.setText(name)
            self.llm_service.username = name
            self.setWindowTitle(f"QueNota? - {name}")
        if avatar_url:
            self._thumbnail_loader.load(self.sidebar_avatar, avatar_url)

    def _apply_avatar_mask(self):
        from PySide6.QtGui import QPainterPath, QRegion
        path = QPainterPath()
        path.addEllipse(0, 0, 36, 36)
        polygon = path.toFillPolygon().toPolygon()
        region = QRegion(polygon)
        self.sidebar_avatar.setMask(region)

    @Slot()
    def _on_new_session(self):
        self._switch_nav(1)
        self.dj_booth.reset_state()
        if self.worker_thread and self.worker_thread.isRunning():
            self.worker_thread.requestInterruption()
            self.worker_thread.wait(2000)
            self.worker_thread = None
            self.playback_bar.set_transport_enabled(False)
            self.playback_bar.reset()

    @Slot()
    def _on_logout(self):
        if self.worker_thread and self.worker_thread.isRunning():
            self.worker_thread.requestInterruption()
            self.worker_thread.wait(3000)
            self.worker_thread = None
        self.auth_service.logout()

    @Slot()
    def _on_logout_success(self):
        self.bottom_auth_label.setText("Signed out")
        self.sidebar_user.setText(self.auth_service.user_display_name)
        self.llm_service.username = self.auth_service.user_display_name
        self.setWindowTitle(f"QueNota? - {self.auth_service.user_display_name}")
        self.playback_bar.reset()
        self.outer_stack.setCurrentIndex(0)

    @Slot(str)
    def _on_start_session(self, query: str):
        if self.worker_thread and self.worker_thread.isRunning():
            self.worker_thread.update_query(query)
            return

        self.llm_service.username = self.auth_service.user_display_name
        self.worker_thread = DJWorkerThread(query, self.llm_service, self.music_service)
        self.music_service._worker_thread = self.worker_thread
        self.worker_thread.song_playing.connect(self.dj_booth.on_song_playing)
        self.worker_thread.song_playing.connect(self.playback_bar.on_track_loaded)
        self.worker_thread.log_message.connect(self.dj_booth.on_log_message)
        self.worker_thread.dj_speaking.connect(self.dj_booth.on_dj_speaking)
        self.worker_thread.dj_commentary.connect(self.dj_booth.show_commentary)
        self.worker_thread.dj_commentary_ready.connect(self.dj_booth.show_commentary)
        self.worker_thread.user_info_loaded.connect(self._on_user_info)
        self.worker_thread.pause_state_changed.connect(self.playback_bar.on_play_state)
        self.worker_thread.track_finished.connect(self._on_track_finished)
        self.worker_thread.finished_signal.connect(self.dj_booth.on_session_finished)
        self.worker_thread.finished_signal.connect(
            lambda: self.playback_bar.set_transport_enabled(False)
        )
        self.worker_thread.finished_signal.connect(self._on_worker_finished)
        self.worker_thread.start()
        self.playback_bar.set_transport_enabled(True)

    @Slot()
    def _on_worker_finished(self):
        self.playback_bar.set_transport_enabled(False)
        self.music_service._worker_thread = None
        self.worker_thread = None

    @Slot()
    def toggle_playback_state(self):
        print(f"[DEBUG] Signal received in UI: toggle_playback_state")
        if self.worker_thread and self.worker_thread.isRunning():
            self.music_service.toggle_pause()

    @Slot(str)
    def start_mood_session(self, mood_title: str):
        self._switch_nav(1)
        self.dj_booth.search_input.setText(mood_title)
        QTimer.singleShot(100, lambda: self.dj_booth._on_start())

    @Slot(str)
    def play_station(self, video_id: str):
        self._switch_nav(1)
        self.dj_booth.search_input.setText("")
        if self.worker_thread and self.worker_thread.isRunning():
            self.worker_thread.play_video_id(video_id)
        else:
            self.dj_booth.status_pill.setText("●  Loading track...")
            stream_data = self.music_service.extract_stream_url(video_id)
            if not stream_data:
                self.dj_booth.status_pill.setText("●  Could not load this track.")
                return
            stream_data["video_id"] = video_id
            self.llm_service.username = self.auth_service.user_display_name
            self.worker_thread = DJWorkerThread("", self.llm_service, self.music_service)
            self.music_service._worker_thread = self.worker_thread
            self.worker_thread._next_video_id = video_id
            self.worker_thread.song_playing.connect(self.dj_booth.on_song_playing)
            self.worker_thread.song_playing.connect(self.playback_bar.on_track_loaded)
            self.worker_thread.log_message.connect(self.dj_booth.on_log_message)
            self.worker_thread.user_info_loaded.connect(self._on_user_info)
            self.worker_thread.dj_commentary.connect(self.dj_booth.show_commentary)
            self.worker_thread.dj_commentary_ready.connect(self.dj_booth.show_commentary)
            self.worker_thread.dj_speaking.connect(self.dj_booth.on_dj_speaking)
            self.worker_thread.pause_state_changed.connect(self.playback_bar.on_play_state)
            self.worker_thread.track_finished.connect(self._on_track_finished)
            self.worker_thread.finished_signal.connect(self.dj_booth.on_session_finished)
            self.worker_thread.finished_signal.connect(
                lambda: self.playback_bar.set_transport_enabled(False)
            )
            self.worker_thread.finished_signal.connect(self._on_worker_finished)
            self.worker_thread.start()
            self.playback_bar.set_transport_enabled(True)

    @Slot(str)
    def play_playlist(self, playlist_id: str):
        tracks = self.music_service.get_playlist_tracks(playlist_id)
        if not tracks:
            return
        first = tracks[0]
        video_id = first.get("videoId", "")
        if video_id:
            self.play_station(video_id)

    @Slot(int)
    def _on_bar_volume(self, value: int):
        print(f"[DEBUG] Signal received in UI: volume {value}")
        if self.worker_thread and self.worker_thread.isRunning():
            self.music_service.set_volume(value)

    @Slot(float)
    def _on_bar_speed(self, value: float):
        print(f"[DEBUG] Signal received in UI: speed {value}")
        if self.worker_thread and self.worker_thread.isRunning():
            self.music_service.set_speed(value)

    @Slot()
    def _on_bar_shuffle(self):
        if self.worker_thread and self.worker_thread.isRunning():
            self.worker_thread.toggle_shuffle()

    @Slot()
    def _on_bar_repeat(self):
        if self.worker_thread and self.worker_thread.isRunning():
            self.worker_thread.toggle_repeat()

    @Slot()
    def _on_track_finished(self):
        pass

    @Slot()
    def _on_bar_skip(self):
        self.music_service.skip_next()

    @Slot()
    def _on_bar_back(self):
        self.music_service.go_previous()
