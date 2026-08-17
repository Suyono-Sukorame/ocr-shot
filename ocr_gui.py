#!/usr/bin/env python3
"""
ocr_gui.py - Interactive Live Text Overlay GUI using PyQt6 / PySide6 / PyQt5.
Provides Apple Live Text-like visual highlights, interactive mouse text selection,
and a floating action bar (Copy, Search, Translate).
"""

import re
import sys
import urllib.parse
from typing import Any, Dict, List, Optional, Tuple

# Attempt Qt imports across versions (PyQt6 -> PySide6 -> PyQt5)
QT_BINDING = None
try:
    from PyQt6 import QtCore, QtGui, QtWidgets
    from PyQt6.QtCore import Qt, QRect, QPoint, QUrl, QTimer
    from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QPixmap, QFont, QCursor, QDesktopServices
    from PyQt6.QtWidgets import QApplication, QWidget, QPushButton, QHBoxLayout, QVBoxLayout, QLabel, QFrame, QComboBox, QMenu
    QT_BINDING = "PyQt6"
except ImportError:
    try:
        from PySide6 import QtCore, QtGui, QtWidgets
        from PySide6.QtCore import Qt, QRect, QPoint, QUrl, QTimer
        from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QPixmap, QFont, QCursor, QDesktopServices
        from PySide6.QtWidgets import QApplication, QWidget, QPushButton, QHBoxLayout, QVBoxLayout, QLabel, QFrame, QComboBox, QMenu
        QT_BINDING = "PySide6"
    except ImportError:
        try:
            from PyQt5 import QtCore, QtGui, QtWidgets
            from PyQt5.QtCore import Qt, QRect, QPoint, QUrl, QTimer
            from PyQt5.QtGui import QPainter, QColor, QPen, QBrush, QPixmap, QFont, QCursor, QDesktopServices
            from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QHBoxLayout, QVBoxLayout, QLabel, QFrame, QComboBox, QMenu
            QT_BINDING = "PyQt5"
        except ImportError:
            QT_BINDING = None
            QFrame = object  # type: ignore
            QWidget = object  # type: ignore
            QMenu = object  # type: ignore


class ToastNotification(QLabel):
    """Sleek toast notification for visual feedback upon actions like Copying."""

    def __init__(self, parent=None, text: str = "📋 Copied to Clipboard!"):
        super().__init__(parent)
        self.setText(text)
        align_center = getattr(Qt.AlignmentFlag, "AlignCenter", getattr(Qt, "AlignCenter", 0x0084))
        self.setAlignment(align_center)
        self.setStyleSheet("""
            QLabel {
                background-color: rgba(16, 185, 129, 0.95);
                color: #FFFFFF;
                font-weight: bold;
                font-size: 14px;
                padding: 10px 20px;
                border-radius: 10px;
                border: 1px solid rgba(255, 255, 255, 0.25);
            }
        """)
        self.adjustSize()
        if parent:
            px = (parent.width() - self.width()) // 2
            py = (parent.height() - self.height()) // 2
            self.move(px, py)


class FloatingActionBar(QFrame):
    """Floating bar containing action buttons (Copy, Detectors, Search, Translate, Format, Select All, Close)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ActionBar")
        sub_window_flag = getattr(Qt.WindowType, "SubWindow", getattr(Qt, "SubWindow", 0))
        self.setWindowFlags(sub_window_flag)

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
            QPushButton.SmartDetector {
                background-color: rgba(16, 185, 129, 0.25);
                border: 1px solid rgba(16, 185, 129, 0.5);
                color: #34D399;
            }
            QPushButton.SmartDetector:hover {
                background-color: #10B981;
                color: #FFFFFF;
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
        self.btn_select_all = QPushButton("🔳 All")
        self.btn_select_all.setToolTip("Select all detected text on screen (Ctrl+A)")

        # Smart Data Detector buttons
        self.btn_open_link = QPushButton("🔗 Open Link")
        self.btn_open_link.setProperty("class", "SmartDetector")
        self.btn_open_link.hide()

        self.btn_email = QPushButton("📧 Email")
        self.btn_email.setProperty("class", "SmartDetector")
        self.btn_email.hide()

        self.btn_phone = QPushButton("📞 Phone")
        self.btn_phone.setProperty("class", "SmartDetector")
        self.btn_phone.hide()

        self.btn_maps = QPushButton("📍 Maps")
        self.btn_maps.setProperty("class", "SmartDetector")
        self.btn_maps.hide()

        self.btn_search = QPushButton("🔍 Search")
        self.btn_translate = QPushButton("🌐 Translate")
        self.btn_format = QPushButton("≡ Lines")
        self.btn_format.setToolTip("Toggle between original lines and single paragraph mode")

        self.lang_combo = QComboBox()
        self.lang_combo.addItems(["ind+eng+ara", "ind", "eng", "ara"])

        self.btn_close = QPushButton("✕")
        self.btn_close.setFixedWidth(28)

        layout.addWidget(self.btn_copy)
        layout.addWidget(self.btn_select_all)
        layout.addWidget(self.btn_open_link)
        layout.addWidget(self.btn_email)
        layout.addWidget(self.btn_phone)
        layout.addWidget(self.btn_maps)
        layout.addWidget(self.btn_search)
        layout.addWidget(self.btn_translate)
        layout.addWidget(self.btn_format)
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
        self.paragraph_mode = False

        # Smart Data Detector States
        self.detected_url: Optional[str] = None
        self.detected_email: Optional[str] = None
        self.detected_phone: Optional[str] = None
        self.detected_address: Optional[str] = None
        self.toast: Optional[ToastNotification] = None

        self.selected_indices: set[int] = set()

        frameless = getattr(Qt.WindowType, "FramelessWindowHint", getattr(Qt, "FramelessWindowHint", 0))
        stays_on_top = getattr(Qt.WindowType, "WindowStaysOnTopHint", getattr(Qt, "WindowStaysOnTopHint", 0))
        tool_flag = getattr(Qt.WindowType, "Tool", getattr(Qt, "Tool", 0))

        self.setWindowFlags(frameless | stays_on_top | tool_flag)
        delete_on_close = getattr(Qt.WidgetAttribute, "WA_DeleteOnClose", getattr(Qt, "WA_DeleteOnClose", 55))
        self.setAttribute(delete_on_close)

        # Fullscreen setup
        screen = QApplication.primaryScreen()
        if screen:
            self.setGeometry(screen.geometry())

        self.action_bar = FloatingActionBar(self)
        self.action_bar.btn_copy.clicked.connect(self.action_copy)
        self.action_bar.btn_select_all.clicked.connect(self.action_select_all)
        self.action_bar.btn_open_link.clicked.connect(self.action_open_link)
        self.action_bar.btn_email.clicked.connect(self.action_open_email)
        self.action_bar.btn_phone.clicked.connect(self.action_open_phone)
        self.action_bar.btn_maps.clicked.connect(self.action_open_maps)
        self.action_bar.btn_search.clicked.connect(self.action_search)
        self.action_bar.btn_translate.clicked.connect(self.action_translate)
        self.action_bar.btn_format.clicked.connect(self.action_toggle_format)
        self.action_bar.btn_close.clicked.connect(self.close)
        self.action_bar.lang_combo.currentTextChanged.connect(self.action_lang_changed)

        current_lang = ocr_data.get("language", "ind+eng+ara")
        index = self.action_bar.lang_combo.findText(current_lang)
        if index >= 0:
            self.action_bar.lang_combo.setCurrentIndex(index)

        self.action_bar.hide()
        self.setMouseTracking(True)

    def keyPressEvent(self, event: QtGui.QKeyEvent):
        key_esc = getattr(Qt.Key, "Key_Escape", getattr(Qt, "Key_Escape", 0x01000000))
        key_a = getattr(Qt.Key, "Key_A", getattr(Qt, "Key_A", 0x41))
        
        control_modifier = getattr(Qt.KeyboardModifier, "ControlModifier", getattr(Qt, "ControlModifier", 0x04000000))
        meta_modifier = getattr(Qt.KeyboardModifier, "MetaModifier", getattr(Qt, "MetaModifier", 0x10000000))

        modifiers = event.modifiers()
        has_ctrl = bool(modifiers & (control_modifier | meta_modifier))

        if event.key() == key_esc:
            self.close()
        elif has_ctrl and event.key() == key_a:
            self.action_select_all()
        elif event.matches(QtGui.QKeySequence.StandardKey.Copy):
            self.action_copy()

    def get_selected_text(self) -> str:
        if not self.selected_indices:
            raw_text = self.full_text
        else:
            selected_words = [self.words[i] for i in sorted(self.selected_indices)]
            lines: Dict[Tuple[int, int], List[str]] = {}
            for w in selected_words:
                key = (w.get("block_num", 0), w.get("line_num", 0))
                lines.setdefault(key, []).append(w["text"])
            
            result_lines = [" ".join(words) for words in lines.values()]
            raw_text = "\n".join(result_lines)

        if self.paragraph_mode:
            # Join lines into a continuous paragraph, repairing broken hyphenations
            clean = re.sub(r'-\s*\n\s*', '', raw_text)
            clean = re.sub(r'\s*\n\s*', ' ', clean)
            return clean.strip()
        
        return raw_text

    def check_for_data_detectors(self, text: str):
        # 1. URL detector
        url_match = re.search(r'https?://[^\s,;()"\']+|www\.[^\s,;()"\']+', text)
        if url_match:
            url = url_match.group(0)
            if url.startswith("www."):
                url = "https://" + url
            self.detected_url = url
            self.action_bar.btn_open_link.show()
        else:
            self.detected_url = None
            self.action_bar.btn_open_link.hide()

        # 2. Email detector
        email_match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
        if email_match:
            self.detected_email = email_match.group(0)
            self.action_bar.btn_email.show()
        else:
            self.detected_email = None
            self.action_bar.btn_email.hide()

        # 3. Phone detector
        phone_match = re.search(r'(?:\+?\d{1,4}[-.\s]?)?\(?\d{2,5}\)?[-.\s]?\d{3,5}[-.\s]?\d{3,5}', text)
        if phone_match and len(re.sub(r'\D', '', phone_match.group(0))) >= 6:
            self.detected_phone = phone_match.group(0).strip()
            self.action_bar.btn_phone.show()
        else:
            self.detected_phone = None
            self.action_bar.btn_phone.hide()

        # 4. Address / Maps detector
        address_match = re.search(r'\b(?:Jalan|Jl\.|Street|St\.|Avenue|Ave|Drive|Dr\.|Road|Rd\.|Boulevard|Blvd|Blok|Kota|Kabupaten)\b', text, re.IGNORECASE) or re.search(r'-?\d{1,2}\.\d{4,},\s*-?\d{1,3}\.\d{4,}', text)
        if address_match:
            self.detected_address = text.strip()
            self.action_bar.btn_maps.show()
        else:
            self.detected_address = None
            self.action_bar.btn_maps.hide()

        self.action_bar.adjustSize()

    def action_copy(self):
        text = self.get_selected_text()
        if text:
            clipboard = QApplication.clipboard()
            if clipboard:
                clipboard.setText(text)
            if self.on_copy_cb:
                self.on_copy_cb(text)

        # Show visual Toast Notification
        self.toast = ToastNotification(self, "📋 Copied to Clipboard!")
        self.toast.show()
        self.action_bar.hide()
        QTimer.singleShot(500, self.close)

    def action_select_all(self):
        self.selected_indices = set(range(len(self.words)))
        if self.words:
            min_x = min(w["x"] for w in self.words)
            max_x = max(w["x"] + w["w"] for w in self.words)
            min_y = min(w["y"] for w in self.words)
            max_y = max(w["y"] + w["h"] for w in self.words)

            self.selection_start = QPoint(min_x, min_y)
            self.selection_end = QPoint(max_x, max_y)

        selected_text = self.get_selected_text()
        self.check_for_data_detectors(selected_text)

        self.update_action_bar_position()
        self.action_bar.show()
        self.update()

    def action_open_link(self):
        if self.detected_url:
            QDesktopServices.openUrl(QUrl(self.detected_url))
            self.close()

    def action_open_email(self):
        if self.detected_email:
            QDesktopServices.openUrl(QUrl("mailto:" + self.detected_email))
            self.close()

    def action_open_phone(self):
        if self.detected_phone:
            clipboard = QApplication.clipboard()
            if clipboard:
                clipboard.setText(self.detected_phone)
            if self.on_copy_cb:
                self.on_copy_cb(self.detected_phone)
            self.toast = ToastNotification(self, f"📞 Copied Phone: {self.detected_phone}")
            self.toast.show()
            self.action_bar.hide()
            QTimer.singleShot(500, self.close)

    def action_open_maps(self):
        if self.detected_address:
            maps_url = "https://www.google.com/maps/search/?api=1&query=" + urllib.parse.quote(self.detected_address)
            QDesktopServices.openUrl(QUrl(maps_url))
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

    def action_toggle_format(self):
        self.paragraph_mode = not self.paragraph_mode
        if self.paragraph_mode:
            self.action_bar.btn_format.setText("¶ Para")
        else:
            self.action_bar.btn_format.setText("≡ Lines")
        self.action_bar.adjustSize()
        self.update_action_bar_position()

    def action_lang_changed(self, new_lang: str):
        if self.on_lang_change_cb:
            self.on_lang_change_cb(new_lang)

    def mousePressEvent(self, event: QtGui.QMouseEvent):
        btn_left = getattr(Qt.MouseButton, "LeftButton", getattr(Qt, "LeftButton", 1))
        if event.button() == btn_left:
            self.is_selecting = True
            self.selection_start = event.pos()
            self.selection_end = event.pos()
            self.selected_indices.clear()
            self.action_bar.hide()
            self.update()

    def mouseDoubleClickEvent(self, event: QtGui.QMouseEvent):
        pos = event.pos()
        clicked_idx = None
        for idx, w in enumerate(self.words):
            rect = QRect(w["x"], w["y"], w["w"], w["h"])
            if rect.contains(pos):
                clicked_idx = idx
                break

        if clicked_idx is not None:
            w_target = self.words[clicked_idx]
            target_block = w_target.get("block_num", 0)
            target_line = w_target.get("line_num", 0)

            # If double click on an already selected single word, convert to triple-click line selection
            if clicked_idx in self.selected_indices and len(self.selected_indices) == 1:
                self.selected_indices = {
                    idx for idx, w in enumerate(self.words)
                    if w.get("block_num", 0) == target_block and w.get("line_num", 0) == target_line
                }
            else:
                self.selected_indices = {clicked_idx}

            selected_text = self.get_selected_text()
            self.check_for_data_detectors(selected_text)

            sel_words = [self.words[i] for i in self.selected_indices]
            min_x = min(w["x"] for w in sel_words)
            max_x = max(w["x"] + w["w"] for w in sel_words)
            min_y = min(w["y"] for w in sel_words)
            max_y = max(w["y"] + w["h"] for w in sel_words)

            self.selection_start = QPoint(min_x, min_y)
            self.selection_end = QPoint(max_x, max_y)

            self.update_action_bar_position()
            self.action_bar.show()
            self.update()

    def contextMenuEvent(self, event: QtGui.QContextMenuEvent):
        if not QT_BINDING:
            return

        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #1E222A;
                color: #FFFFFF;
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 8px;
                padding: 4px;
            }
            QMenu::item {
                padding: 6px 20px;
                border-radius: 4px;
                font-size: 13px;
            }
            QMenu::item:selected {
                background-color: #3B82F6;
            }
        """)

        action_copy = menu.addAction("📋 Copy (Ctrl+C)")
        action_select_all = menu.addAction("🔳 Select All (Ctrl+A)")
        menu.addSeparator()

        action_open_link = menu.addAction(f"🔗 Open Link ({self.detected_url[:25]}...)") if self.detected_url else None
        action_email = menu.addAction(f"📧 Send Email ({self.detected_email})") if self.detected_email else None
        action_phone = menu.addAction(f"📞 Copy/Call Phone ({self.detected_phone})") if self.detected_phone else None
        action_maps = menu.addAction("📍 Open in Google Maps") if self.detected_address else None

        if self.detected_url or self.detected_email or self.detected_phone or self.detected_address:
            menu.addSeparator()

        action_search = menu.addAction("🔍 Search Google")
        action_translate = menu.addAction("🌐 Translate")
        menu.addSeparator()
        action_close = menu.addAction("✕ Close (Esc)")

        exec_pos = event.globalPos() if hasattr(event, "globalPos") else QCursor.pos()
        chosen = menu.exec(exec_pos)

        if chosen == action_copy:
            self.action_copy()
        elif chosen == action_select_all:
            self.action_select_all()
        elif action_open_link and chosen == action_open_link:
            self.action_open_link()
        elif action_email and chosen == action_email:
            self.action_open_email()
        elif action_phone and chosen == action_phone:
            self.action_open_phone()
        elif action_maps and chosen == action_maps:
            self.action_open_maps()
        elif chosen == action_search:
            self.action_search()
        elif chosen == action_translate:
            self.action_translate()
        elif chosen == action_close:
            self.close()

    def mouseMoveEvent(self, event: QtGui.QMouseEvent):
        pos = event.pos()
        
        hovering_word = False
        for w in self.words:
            rect = QRect(w["x"], w["y"], w["w"], w["h"])
            if rect.contains(pos):
                hovering_word = True
                break

        cursor_ibeam = getattr(Qt.CursorShape, "IBeamCursor", getattr(Qt, "IBeamCursor", 2))
        cursor_arrow = getattr(Qt.CursorShape, "ArrowCursor", getattr(Qt, "ArrowCursor", 0))

        if hovering_word:
            self.setCursor(QCursor(cursor_ibeam))
        else:
            self.setCursor(QCursor(cursor_arrow))

        if self.is_selecting and self.selection_start:
            self.selection_end = pos
            self.update_selection_box()
            self.update()

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent):
        btn_left = getattr(Qt.MouseButton, "LeftButton", getattr(Qt, "LeftButton", 1))
        if event.button() == btn_left and self.is_selecting:
            self.is_selecting = False
            self.selection_end = event.pos()
            self.update_selection_box()
            
            selected_text = self.get_selected_text()
            self.check_for_data_detectors(selected_text)

            self.update_action_bar_position()
            self.action_bar.show()
            self.update()

    def update_action_bar_position(self):
        if not self.selection_start or not self.selection_end:
            return

        mid_x = (self.selection_start.x() + self.selection_end.x()) // 2
        top_y = min(self.selection_start.y(), self.selection_end.y()) - self.action_bar.height() - 10
        if top_y < 10:
            top_y = max(self.selection_start.y(), self.selection_end.y()) + 20

        # Smart screen boundary constraints
        bar_width = self.action_bar.width()
        bar_height = self.action_bar.height()
        
        bar_x = max(10, min(self.width() - bar_width - 10, mid_x - bar_width // 2))
        bar_y = max(10, min(self.height() - bar_height - 10, top_y))

        self.action_bar.move(bar_x, bar_y)

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
        render_aa = getattr(QPainter.RenderHint, "Antialiasing", getattr(QPainter, "Antialiasing", 1))
        painter.setRenderHint(render_aa)

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
            pen_style_dash = getattr(Qt.PenStyle, "DashLine", getattr(Qt, "DashLine", 2))
            painter.setPen(QPen(QColor(255, 255, 255, 220), 1, pen_style_dash))
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


