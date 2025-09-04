import logging
import pyttsx3
from PyQt6.QtCore import Qt, QMimeData, QTimer
from PyQt6.QtGui import QDrag
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QMessageBox, QInputDialog

# Constants
WIDGET_MIN_HEIGHT = 60
BUTTON_DEFAULT_SIZE = (25, 25)
DEFAULT_FONT_SIZE = 12
DRAG_DISTANCE_THRESHOLD = 10

WIDGET_STYLE_SHEET = """
    QFrame {
        background: rgba(255, 255, 255, 0.7);
        border-radius: 15px;
        margin: 5px;
        color: black;
    }
    QPushButton {
        background-color: rgba(0, 0, 0, 0.2);
        border: 1px solid rgba(0, 0, 0, 0.3);
        border-radius: 12px;
        padding: 5px 10px;
        color: white;
        font-weight: bold;
    }
    QPushButton:hover {
        background-color: rgba(0, 0, 0, 0.3);
    }
    QLabel {
        color: black;
    }
"""


class DraggableTextWidget(QFrame):
    """Widget di testo trascinabile per l'interfaccia."""

    def __init__(self, text, settings, parent=None):
        super().__init__(parent)

        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setFrameShadow(QFrame.Shadow.Raised)
        self.setMinimumHeight(WIDGET_MIN_HEIGHT)
        self.setStyleSheet(WIDGET_STYLE_SHEET)

        self.settings = settings
        self.original_text = text

        # Text-to-speech engine
        self.tts_engine = None
        self.is_reading = False
        self.is_paused = False

        layout = QHBoxLayout(self)
        self.text_label = QLabel(text)
        self.text_label.setStyleSheet(f"font-weight: bold; font-size: {DEFAULT_FONT_SIZE}px;")
        self.text_label.setWordWrap(True)
        self.text_label.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.text_label.customContextMenuRequested.connect(self.show_context_menu)

        layout.addWidget(self.text_label, 1)

        button_layout = QVBoxLayout()

        # Read button
        self.read_button = QPushButton("📖")
        self.read_button.setFixedSize(*BUTTON_DEFAULT_SIZE)
        self.read_button.setToolTip("Leggi")
        self.read_button.clicked.connect(self.start_reading)

        # Pause button (initially hidden)
        self.pause_button = QPushButton("⏸️")
        self.pause_button.setFixedSize(*BUTTON_DEFAULT_SIZE)
        self.pause_button.setToolTip("Pausa")
        self.pause_button.clicked.connect(self.pause_reading)
        self.pause_button.hide()

        # Stop button (initially hidden)
        self.stop_button = QPushButton("⏹️")
        self.stop_button.setFixedSize(*BUTTON_DEFAULT_SIZE)
        self.stop_button.setToolTip("Ferma")
        self.stop_button.clicked.connect(self.stop_reading)
        self.stop_button.hide()

        self.edit_button = QPushButton("✏️")
        self.edit_button.setFixedSize(*BUTTON_DEFAULT_SIZE)
        self.edit_button.setToolTip("Modifica")
        self.edit_button.clicked.connect(self.edit_text)

        self.delete_button = QPushButton("❌")
        self.delete_button.setFixedSize(*BUTTON_DEFAULT_SIZE)
        self.delete_button.setToolTip("Elimina")
        self.delete_button.clicked.connect(self.delete_self)

        button_layout.addWidget(self.read_button)
        button_layout.addWidget(self.pause_button)
        button_layout.addWidget(self.stop_button)
        button_layout.addWidget(self.edit_button)
        button_layout.addWidget(self.delete_button)
        layout.addLayout(button_layout)

        self.setAcceptDrops(True)
        self.start_pos = None

    def show_context_menu(self, pos):
        """Mostra il menu contestuale per il widget."""
        from PyQt6.QtWidgets import QMenu

        context_menu = QMenu(self)
        edit_action = context_menu.addAction("Modifica Testo")
        action = context_menu.exec(self.mapToGlobal(pos))
        if action == edit_action:
            self.edit_text()

    def mouseDoubleClickEvent(self, a0):
        """Gestisce il doppio click per modificare il testo."""
        self.edit_text()

    def edit_text(self):
        """Apre una finestra di dialogo per modificare il testo del widget."""
        new_text, ok = QInputDialog.getMultiLineText(
            self, "Modifica Testo", "Modifica il contenuto del widget:",
            self.text_label.text()
        )
        if ok and new_text.strip():
            self.text_label.setText(new_text.strip())
            logging.info(f"Testo del widget modificato: {new_text[:50]}...")

    def mousePressEvent(self, a0):
        """Gestisce l'evento di pressione del mouse per iniziare il trascinamento."""
        if a0 and a0.button() == Qt.MouseButton.LeftButton:
            self.start_pos = a0.pos()
        super().mousePressEvent(a0)

    def mouseMoveEvent(self, a0):
        """Gestisce il movimento del mouse per il trascinamento."""
        if (self.start_pos is not None and self.text_label and a0 is not None and
                a0.buttons() == Qt.MouseButton.LeftButton):
            current_pos = a0.pos()
            if current_pos.x() >= 0 and current_pos.y() >= 0:
                distance = (current_pos - self.start_pos).manhattanLength()
                if distance > DRAG_DISTANCE_THRESHOLD:
                    drag = QDrag(self)
                    mime = QMimeData()
                    mime.setText(self.text_label.text())
                    mime.setData("application/x-draggable-widget", b"widget")
                    drag.setMimeData(mime)
                    drag.setPixmap(self.grab())
                    result = drag.exec(Qt.DropAction.MoveAction)
                    if result == Qt.DropAction.MoveAction:
                        self.delete_self()
        super().mouseMoveEvent(a0)

    def delete_self(self):
        """Rimuove il widget dall'interfaccia."""
        self.stop_reading()  # Stop any ongoing reading
        self.setParent(None)
        self.deleteLater()

    def start_reading(self):
        """Avvia la lettura del testo."""
        if self.is_reading:
            return

        try:
            if self.tts_engine is None:
                self.tts_engine = pyttsx3.init()

            self.is_reading = True
            self.is_paused = False

            # Hide read button, show pause and stop buttons
            self.read_button.hide()
            self.pause_button.show()
            self.stop_button.show()

            # Start reading
            text_to_read = self.text_label.text()
            self.tts_engine.say(text_to_read)
            self.tts_engine.runAndWait()

            # Reset when finished
            self.reset_reading_buttons()

        except Exception as e:
            QMessageBox.warning(self, "Errore Lettura", f"Errore durante la lettura: {str(e)}")
            self.reset_reading_buttons()

    def pause_reading(self):
        """Mette in pausa o riprende la lettura."""
        if self.tts_engine is None:
            return

        if self.is_paused:
            # Resume reading
            self.tts_engine.runAndWait()
            self.pause_button.setText("⏸️")
            self.pause_button.setToolTip("Pausa")
            self.is_paused = False
        else:
            # Pause reading
            self.tts_engine.stop()
            self.pause_button.setText("▶️")
            self.pause_button.setToolTip("Riprendi")
            self.is_paused = True

    def stop_reading(self):
        """Ferma la lettura e ricomincia dall'inizio."""
        if self.tts_engine:
            self.tts_engine.stop()
        self.reset_reading_buttons()

    def reset_reading_buttons(self):
        """Resetta i pulsanti di lettura allo stato iniziale."""
        self.is_reading = False
        self.is_paused = False

        self.read_button.show()
        self.pause_button.hide()
        self.stop_button.hide()

        self.pause_button.setText("⏸️")
        self.pause_button.setToolTip("Pausa")
