# ui_components.py - Componenti UI riutilizzabili

import logging
from PyQt6.QtCore import Qt, QMimeData, QPoint
from PyQt6.QtGui import QDrag, QPixmap
from PyQt6.QtWidgets import (
    QScrollArea,
    QWidget,
    QVBoxLayout,
    QLabel,
    QFrame,
    QHBoxLayout,
    QPushButton,
    QApplication,
)

from ui_style import DRAGGABLE_WIDGET_STYLE, get_scrollable_panel_style
from tts_thread import TTSThread


class ScrollablePanel(QScrollArea):
    def __init__(self, title, color_class):
        super().__init__()
        self.setWidgetResizable(True)
        self.setAcceptDrops(True)
        self.container = QWidget()
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        title_label = QLabel(title)
        title_label.setStyleSheet("font-weight: bold; font-size: 14px; margin-bottom: 10px; color: #4a90e2;")
        self.container_layout.addWidget(title_label)
        self.setWidget(self.container)
        self.setStyleSheet(get_scrollable_panel_style(color_class))

    def add_widget(self, widget):
        self.container_layout.addWidget(widget)

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dropEvent(self, event):
        text = event.mimeData().text()
        if text:
            # Placeholder - need DraggableTextWidget
            pass
        event.acceptProposedAction()


class DraggableTextWidget(QFrame):
    def __init__(self, text, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setFrameShadow(QFrame.Shadow.Raised)
        self.setMinimumHeight(60)
        self.setStyleSheet(DRAGGABLE_WIDGET_STYLE)
        self.tts_thread = None
        self.is_reading = False
        layout = QHBoxLayout(self)
        self.text_label = QLabel(text)
        self.text_label.setStyleSheet("color: white; font-weight: bold; font-size: 12px;")
        self.text_label.setWordWrap(True)
        layout.addWidget(self.text_label, 1)
        button_layout = QVBoxLayout()
        self.read_button = QPushButton("🔊")
        self.read_button.setFixedSize(25, 25)
        self.read_button.setToolTip("Leggi testo")
        self.read_button.clicked.connect(self.toggle_read_text)
        self.delete_button = QPushButton("❌")
        self.delete_button.setFixedSize(25, 25)
        self.delete_button.setToolTip("Elimina")
        self.delete_button.clicked.connect(self.delete_self)
        button_layout.addWidget(self.read_button)
        button_layout.addWidget(self.delete_button)
        layout.addLayout(button_layout)
        self.setAcceptDrops(True)
        self.start_pos = None

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.start_pos = event.pos()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self.start_pos:
            distance = (event.pos() - self.start_pos).manhattanLength()
            if distance > QApplication.startDragDistance():
                drag = QDrag(self)
                mime = QMimeData()
                mime.setText(self.text_label.text())
                drag.setMimeData(mime)
                drag.setPixmap(self.grab())
                drag.exec(Qt.DropAction.MoveAction)

    def toggle_read_text(self):
        if not self.is_reading:
            self.start_reading()
        else:
            self.stop_reading()

    def start_reading(self):
        if self.tts_thread and self.tts_thread.isRunning():
            return
        self.is_reading = True
        self.read_button.setText("⏹️")
        self.read_button.setStyleSheet("background-color: #e74c3c; color: white;")
        self.tts_thread = TTSThread(self.text_label.text())
        self.tts_thread.started_reading.connect(self.on_reading_started)
        self.tts_thread.finished_reading.connect(self.on_reading_finished)
        self.tts_thread.error_occurred.connect(self.on_reading_error)
        self.tts_thread.start()

    def stop_reading(self):
        if self.tts_thread and self.tts_thread.isRunning():
            self.tts_thread.stop()
        self.is_reading = False
        self.read_button.setText("🔊")
        self.read_button.setStyleSheet("")
        logging.info("Lettura testo interrotta.")

    def on_reading_started(self):
        logging.info("Lettura del testo iniziata.")

    def on_reading_finished(self):
        self.is_reading = False
        self.read_button.setText("🔊")
        self.read_button.setStyleSheet("")
        logging.info("Lettura testo completata.")
        self.tts_thread = None

    def on_reading_error(self, message):
        self.is_reading = False
        self.read_button.setText("🔊")
        self.read_button.setStyleSheet("")
        logging.error(f"Errore durante la lettura vocale: {message}")
        self.tts_thread = None

    def delete_self(self):
        if self.is_reading:
            self.stop_reading()
        self.setParent(None)
        self.deleteLater()