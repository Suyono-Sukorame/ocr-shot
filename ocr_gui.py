#!/usr/bin/env python3
"""
ocr_gui.py - Interactive Live Text Overlay GUI using PyQt6 / PySide6 / PyQt5.
Provides Apple Live Text-like visual highlights, interactive mouse text selection,
and a floating action bar (Copy, Search, Translate).
"""

import sys
import urllib.parse
from typing import Any, Dict, List, Optional, Tuple

# Attempt Qt imports across versions (PyQt6 -> PySide6 -> PyQt5)
QT_BINDING = None
try:
    from PyQt6 import QtCore, QtGui, QtWidgets
    from PyQt6.QtCore import Qt, QRect, QPoint, QUrl
    from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QPixmap, QFont, QCursor, QDesktopServices
    from PyQt6.QtWidgets import QApplication, QWidget, QPushButton, QHBoxLayout, QVBoxLayout, QLabel, QFrame, QComboBox
    QT_BINDING = "PyQt6"
except ImportError:
    try:
        from PySide6 import QtCore, QtGui, QtWidgets
        from PySide6.QtCore import Qt, QRect, QPoint, QUrl
        from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QPixmap, QFont, QCursor, QDesktopServices
        from PySide6.QtWidgets import QApplication, QWidget, QPushButton, QHBoxLayout, QVBoxLayout, QLabel, QFrame, QComboBox
        QT_BINDING = "PySide6"
    except ImportError:
        try:
            from PyQt5 import QtCore, QtGui, QtWidgets
            from PyQt5.QtCore import Qt, QRect, QPoint, QUrl
            from PyQt5.QtGui import QPainter, QColor, QPen, QBrush, QPixmap, QFont, QCursor, QDesktopServices
            from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QHBoxLayout, QVBoxLayout, QLabel, QFrame, QComboBox
            QT_BINDING = "PyQt5"
        except ImportError:
            QT_BINDING = None
            QFrame = object  # type: ignore
            QWidget = object  # type: ignore


class FloatingActionBar(QFrame):
    """Floating bar containing action buttons (Copy, Search, Translate, Close)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ActionBar")
        self.setWindowFlags(Qt.WindowType.SubWindow)
        
        # Modern glassmorphism / dark theme styling
        self.setStyleSheet("""
            QFrame#ActionBar {
                background-color: rgba(30, 34, 42, 0.92);
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 12px;
            }
            QPushButton {
                background-color: rgba(255, 255, 255, 0.08);
                color: #FFFFFF;
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 6px;
                padding: 6px 12px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #3B82F6;
                color: #FFFFFF;
            }
            QPushButton:pressed {
                background-color: #1D4ED8;
            }
            QComboBox {
                background-color: rgba(255, 255, 255, 0.08);
                color: #FFFFFF;
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 6px;
                padding: 4px 8px;
                font-size: 12px;
            }
            QComboBox QAbstractItemView {
                background-color: #1E222A;
                color: #FFFFFF;
                selection-background-color: #3B82F6;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(8)

        self.btn_copy = QPushButton("📋 Copy")
        self.btn_search = QPushButton("🔍 Search")
        self.btn_translate = QPushButton("🌐 Translate")

        self.lang_combo = QComboBox()
        self.lang_combo.addItems(["ind+eng+ara", "ind", "eng", "ara"])

        self.btn_close = QPushButton("✕")
        self.btn_close.setFixedWidth(28)

        layout.addWidget(self.btn_copy)
        layout.addWidget(self.btn_search)
        layout.addWidget(self.btn_translate)
        layout.addWidget(self.lang_combo)
        layout.addWidget(self.btn_close)

        self.adjustSize()


class LiveTextOverlay(QWidget):
    """Fullscreen frameless overlay displaying screenshot with interactive text bounding boxes."""

    def __init__(self, image_path: str, ocr_data: Dict[str, Any], on_copy_cb=None, on_lang_change_cb=None):
        super().__init__()
        self.image_path = image_path
        self.ocr_data = ocr_data
        self.words: List[Dict[str, Any]] = ocr_data.get("words", [])
        self.full_text: str = ocr_data.get("text", "")
        self.on_copy_cb = on_copy_cb
        self.on_lang_change_cb = on_lang_change_cb

        self.pixmap = QPixmap(image_path)
        self.selection_start: Optional[QPoint] = None
        self.selection_end: Optional[QPoint] = None
        self.is_selecting = False

        self.selected_indices: set[int] = set()

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)

        # Fullscreen setup
        screen = QApplication.primaryScreen()
        if screen:
            self.setGeometry(screen.geometry())

        self.action_bar = FloatingActionBar(self)
        self.action_bar.btn_copy.clicked.connect(self.action_copy)
        self.action_bar.btn_search.clicked.connect(self.action_search)
        self.action_bar.btn_translate.clicked.connect(self.action_translate)
        self.action_bar.btn_close.clicked.connect(self.close)
        self.action_bar.lang_combo.currentTextChanged.connect(self.action_lang_changed)

        current_lang = ocr_data.get("language", "ind+eng+ara")
        index = self.action_bar.lang_combo.findText(current_lang)
        if index >= 0:
            self.action_bar.lang_combo.setCurrentIndex(index)

        self.action_bar.hide()
        self.setMouseTracking(True)

    def keyPressEvent(self, event: QtGui.QKeyEvent):
        if event.key() == Qt.Key.Key_Escape:
            self.close()
        elif event.matches(QtGui.QKeySequence.StandardKey.Copy):
            self.action_copy()

    def get_selected_text(self) -> str:
        if not self.selected_indices:
            return self.full_text
        
        selected_words = [self.words[i] for i in sorted(self.selected_indices)]
        lines: Dict[Tuple[int, int], List[str]] = {}
        for w in selected_words:
            key = (w.get("block_num", 0), w.get("line_num", 0))
            lines.setdefault(key, []).append(w["text"])
        
        result_lines = [" ".join(words) for words in lines.values()]
        return "\n".join(result_lines)

    def action_copy(self):
        text = self.get_selected_text()
        if text:
            clipboard = QApplication.clipboard()
            if clipboard:
                clipboard.setText(text)
            if self.on_copy_cb:
                self.on_copy_cb(text)
        self.close()

    def action_search(self):
        text = self.get_selected_text()
        if text:
            url = QUrl("https://www.google.com/search?q=" + urllib.parse.quote(text))
            QDesktopServices.openUrl(url)
        self.close()

    def action_translate(self):
        text = self.get_selected_text()
        if text:
            url = QUrl("https://translate.google.com/?sl=auto&tl=id&text=" + urllib.parse.quote(text))
            QDesktopServices.openUrl(url)
        self.close()

    def action_lang_changed(self, new_lang: str):
        if self.on_lang_change_cb:
            self.on_lang_change_cb(new_lang)

    def mousePressEvent(self, event: QtGui.QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_selecting = True
            self.selection_start = event.pos()
            self.selection_end = event.pos()
            self.selected_indices.clear()
            self.action_bar.hide()
            self.update()

    def mouseMoveEvent(self, event: QtGui.QMouseEvent):
        pos = event.pos()
        
        hovering_word = False
        for w in self.words:
            rect = QRect(w["x"], w["y"], w["w"], w["h"])
            if rect.contains(pos):
                hovering_word = True
                break

        if hovering_word:
            self.setCursor(QCursor(Qt.CursorShape.IBeamCursor))
        else:
            self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))

        if self.is_selecting and self.selection_start:
            self.selection_end = pos
            self.update_selection_box()
            self.update()

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton and self.is_selecting:
            self.is_selecting = False
            self.selection_end = event.pos()
            self.update_selection_box()
            
            if self.selection_start and self.selection_end:
                mid_x = (self.selection_start.x() + self.selection_end.x()) // 2
                top_y = min(self.selection_start.y(), self.selection_end.y()) - 50
                if top_y < 10:
                    top_y = max(self.selection_start.y(), self.selection_end.y()) + 20
                
                bar_x = max(10, min(self.width() - self.action_bar.width() - 10, mid_x - self.action_bar.width() // 2))
                self.action_bar.move(bar_x, top_y)
                self.action_bar.show()

            self.update()

    def update_selection_box(self):
        if not self.selection_start or not self.selection_end:
            return

        sel_rect = QRect(self.selection_start, self.selection_end).normalized()
        self.selected_indices.clear()

        for idx, w in enumerate(self.words):
            word_rect = QRect(w["x"], w["y"], w["w"], w["h"])
            if sel_rect.intersects(word_rect):
                self.selected_indices.add(idx)

    def paintEvent(self, event: QtGui.QPaintEvent):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if not self.pixmap.isNull():
            painter.drawPixmap(0, 0, self.pixmap)

        painter.fillRect(self.rect(), QColor(0, 0, 0, 40))

        pen_default = QPen(QColor(59, 130, 246, 180), 1)
        brush_default = QBrush(QColor(59, 130, 246, 50))

        pen_selected = QPen(QColor(239, 68, 68, 240), 2)
        brush_selected = QBrush(QColor(245, 158, 11, 120))

        for idx, w in enumerate(self.words):
            rect = QRect(w["x"], w["y"], w["w"], w["h"])
            if idx in self.selected_indices:
                painter.setPen(pen_selected)
                painter.setBrush(brush_selected)
            else:
                painter.setPen(pen_default)
                painter.setBrush(brush_default)

            painter.drawRoundedRect(rect, 4, 4)

        if self.is_selecting and self.selection_start and self.selection_end:
            drag_rect = QRect(self.selection_start, self.selection_end).normalized()
            painter.setPen(QPen(QColor(255, 255, 255, 220), 1, Qt.PenStyle.DashLine))
            painter.setBrush(QBrush(QColor(255, 255, 255, 30)))
            painter.drawRect(drag_rect)


def launch_gui_overlay(image_path: str, ocr_data: Dict[str, Any], on_copy_cb=None, on_lang_change_cb=None) -> bool:
    """Launches the PyQt Live Text GUI Overlay application."""
    if not QT_BINDING:
        return False

    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)

    overlay = LiveTextOverlay(
        image_path=image_path,
        ocr_data=ocr_data,
        on_copy_cb=on_copy_cb,
        on_lang_change_cb=on_lang_change_cb,
    )
    overlay.showFullScreen()
    app.exec()
    return True
