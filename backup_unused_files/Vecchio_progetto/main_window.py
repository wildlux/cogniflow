# main_window.py - Finestra principale dell'applicazione

import sys
import logging
from PyQt6.QtCore import Qt, QTimer, QObject, pyqtSignal, QEvent, QMimeData, QPoint, QPropertyAnimation, QRect, QBuffer, QIODevice
from PyQt6.QtGui import QIcon, QPixmap, QImage, QDrag, QCursor, QPainter, QPen
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QFrame,
    QTextEdit,
    QMessageBox,
    QDialog,
    QScrollArea,
    QGridLayout,
    QComboBox,
    QCheckBox,
    QSlider,
    QRadioButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QStackedWidget,
    QSpacerItem,
    QGroupBox,
    QMenu,
)

from ui_style import DRAGGABLE_WIDGET_STYLE, LOG_WIDGET_STYLE, TEXT_INPUT_STYLE, AI_RESULTS_STYLE, get_scrollable_panel_style
from ui_style.main_styles import get_main_stylesheet
from animations import toggle_log_panel_visibility
from Opzioni import ConfigurationDialog
from webcam_manager import VideoThread
from ollama_thread import OllamaThread
from voice_recognition_thread import VoiceRecognitionThread
from tts_thread import TTSThread

from ui_components import ScrollablePanel, DraggableTextWidget
from logging_utils import LogEmitter, TextEditLogger


class MainWindow(QMainWindow):
    """Finestra principale dell'applicazione."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Assistente per Dislessia")
        self.setGeometry(100, 100, 1400, 800)

        self.settings = {}
        self.is_listening = False
        self.voice_thread = None

        self.setup_ui()
        self.setup_video_thread()
        self.setStyleSheet(get_main_stylesheet())

        self.ollama_thread = None

        self.init_settings()

    def init_settings(self):
        """Inizializza le impostazioni e tenta di connettersi a Ollama all'avvio."""
        dialog = ConfigurationDialog(self, self.settings)
        self.settings = dialog.get_settings()
        logging.info("Impostazioni iniziali caricate.")

    def setup_ui(self):
        """Configura l'interfaccia utente."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setScaledContents(True)
        self.video_label.setMinimumHeight(200)
        main_layout.addWidget(self.video_label)

        overlay_widget = QWidget()
        overlay_widget.setStyleSheet("background-color: transparent;")
        overlay_layout = QVBoxLayout(overlay_widget)
        overlay_layout.setContentsMargins(20, 20, 20, 20)

        self.setup_top_bar(overlay_layout)
        self.setup_central_panels(overlay_layout)

        self.log_widget = QTextEdit()
        self.log_widget.setReadOnly(True)
        self.log_widget.hide()
        self.log_widget.setStyleSheet(LOG_WIDGET_STYLE)
        overlay_layout.addWidget(self.log_widget)

        self.setup_bottom_bar(overlay_layout)

        overlay_widget.setParent(central_widget)
        overlay_widget.setGeometry(central_widget.rect())
        central_widget.installEventFilter(self)

        self.log_emitter = LogEmitter()
        self.log_handler = TextEditLogger(self.log_emitter, self.log_widget)
        self.log_emitter.new_record.connect(self.log_widget.append)
        self.log_emitter.error_occurred.connect(self.toggle_log_visibility)
        logging.root.addHandler(self.log_handler)
        logging.root.setLevel(logging.INFO)

    def setup_top_bar(self, parent_layout):
        """Configura la barra superiore."""
        top_layout = QHBoxLayout()

        self.options_btn = QPushButton("⚙️ Opzioni")
        self.options_btn.clicked.connect(self.show_options)
        top_layout.addWidget(self.options_btn)

        top_layout.addStretch()

        title_label = QLabel("Assistente per Dislessia")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: white;")
        top_layout.addWidget(title_label)

        top_layout.addStretch()

        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: white; font-weight: bold;")
        top_layout.addWidget(self.status_label)

        self.save_btn = QPushButton("💾 Salva")
        top_layout.addWidget(self.save_btn)

        parent_layout.addLayout(top_layout)

    def setup_central_panels(self, parent_layout):
        """Configura i pannelli centrali."""
        panels_layout = QHBoxLayout()
        panels_layout.setSpacing(10)

        self.contents_panel = ScrollablePanel("📝 Contenuti pensieri creativi (A)", "blue")
        panels_layout.addWidget(self.contents_panel, 1)

        self.work_area_panel = ScrollablePanel("🎯 Area di Lavoro (B)", "red")
        placeholder_label = QLabel("Trascina gli elementi qui per lavorarci")
        placeholder_label.setStyleSheet("color: #888; font-style: italic; margin: 20px;")
        placeholder_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.work_area_panel.add_widget(placeholder_label)
        panels_layout.addWidget(self.work_area_panel, 1)

        self.ai_panel = ScrollablePanel("📋 Dettagli & Risultati Artificial Intelligence (C)", "green")
        self.ai_results_text = QTextEdit()
        self.ai_results_text.setReadOnly(True)
        self.ai_results_text.setPlainText("Le risposte dell'AI appariranno qui.")
        self.ai_results_text.setStyleSheet(AI_RESULTS_STYLE)
        self.ai_panel.add_widget(self.ai_results_text)
        panels_layout.addWidget(self.ai_panel, 1)

        parent_layout.addLayout(panels_layout)

    def setup_bottom_bar(self, parent_layout):
        """Configura la barra inferiore."""
        bottom_layout = QHBoxLayout()

        self.text_input = QLineEdit()
        self.text_input.setPlaceholderText("Inserisci il tuo testo qui...")
        self.text_input.returnPressed.connect(self.add_text)
        self.text_input.setStyleSheet(TEXT_INPUT_STYLE)
        bottom_layout.addWidget(self.text_input, 1)

        self.add_btn = QPushButton("➕ Aggiungi")
        self.add_btn.clicked.connect(lambda: self.add_text())

        self.ai_btn = QPushButton("🧠 AI")
        self.ai_btn.clicked.connect(self.send_to_ai)

        voice_icon = QIcon(self.get_svg_icon("M12 14c1.66 0 2.99-1.34 2.99-3L15 5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3zm5.3-3c0 3.99-3.98 5.75-5.3 5.75S6.7 14.99 6.7 11H5c0 4.14 3.36 7.48 7.48 7.48V21h-3v2h6v-2h-3v-2.52c4.14 0 7.48-3.34 7.48-7.48h-2.18z"))
        recording_icon = QIcon(self.get_svg_icon("M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zM12 17c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5z"))
        self.voice_btn = QPushButton("Registra Voce")
        self.voice_btn.setObjectName("voiceButton")
        self.voice_btn.setIcon(voice_icon)
        self.voice_btn.clicked.connect(self.toggle_voice_input)

        self.hands_btn = QPushButton("✋ Mani")
        self.face_btn = QPushButton("😊 Faccia")
        self.clean_btn = QPushButton("🧹 Pulisci")
        self.clean_btn.clicked.connect(self.clean_input)

        self.log_btn = QPushButton("📊 Mostra Log")
        self.log_btn.clicked.connect(self.toggle_log_visibility)

        for btn in [self.add_btn, self.ai_btn, self.voice_btn, self.hands_btn, self.face_btn, self.clean_btn, self.log_btn]:
            bottom_layout.addWidget(btn)

        parent_layout.addLayout(bottom_layout)

    def get_svg_icon(self, path_data):
        """Genera un'icona da dati SVG."""
        svg_content = f"""
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="#fff">
            <path d="{path_data}"/>
        </svg>
        """
        buffer = QBuffer()
        buffer.open(QIODevice.OpenModeFlag.WriteOnly)
        buffer.write(svg_content.encode("utf-8"))
        buffer.close()
        svg_bytes = buffer.data()
        pixmap = QPixmap()
        pixmap.loadFromData(svg_bytes)
        return pixmap

    def setup_video_thread(self):
        """Inizializza il thread video."""
        self.video_thread = VideoThread()
        self.video_thread.change_pixmap_signal.connect(self.update_video)
        self.video_thread.status_signal.connect(self.update_status)
        self.video_thread.start()

    def eventFilter(self, obj, event):
        """Gestisce il ridimensionamento dell'overlay."""
        if obj is self.centralWidget() and event.type() == QEvent.Type.Resize:
            for child in obj.findChildren(QWidget):
                if child.parent() == obj and hasattr(child, "setGeometry"):
                    child.setGeometry(obj.rect())
        return super().eventFilter(obj, event)

    def toggle_log_visibility(self):
        """Mostra o nasconde il pannello di log."""
        toggle_log_panel_visibility(self.log_widget, self.log_btn)

    def show_options(self):
        """Mostra il dialog delle opzioni."""
        dialog = ConfigurationDialog(self, self.settings)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.settings = dialog.get_settings()
            logging.info("Impostazioni aggiornate")

    def add_text(self, text=None):
        """Aggiunge testo al pannello contenuti."""
        if text is None or isinstance(text, bool):
            text = self.text_input.text().strip()
            if not text:
                return
            self.text_input.clear()

        widget = DraggableTextWidget(text)
        self.contents_panel.add_widget(widget)
        logging.info(f"Testo aggiunto: {text}")

    def send_to_ai(self):
        """Invia il testo all'AI."""
        input_text = self.text_input.text().strip()
        if not input_text:
            logging.warning("Inserisci del testo per inviarlo all'AI.")
            QMessageBox.warning(self, "Attenzione", "Inserisci del testo per inviarlo all'AI.")
            return

        ollama_model = self.settings.get("ollama_model")
        if not ollama_model or ollama_model == "Seleziona un modello":
            logging.error("Nessuno modello Ollama selezionato.")
            QMessageBox.critical(self, "Errore", "Nessuno modello Ollama selezionato. Controlla le opzioni.")
            return

        self.update_status(f"🧠 AI in elaborazione con {ollama_model}...")
        self.ai_btn.setEnabled(False)
        self.add_btn.setEnabled(False)

        self.ollama_thread = OllamaThread(input_text, ollama_model)
        self.ollama_thread.ollama_response.connect(self.handle_ollama_response)
        self.ollama_thread.ollama_error.connect(self.handle_ollama_error)
        self.ollama_thread.start()

    def handle_ollama_response(self, response_text):
        """Gestisce la risposta di Ollama."""
        self.update_status("✅ Risposta AI ricevuta.")
        self.ai_btn.setEnabled(True)
        self.add_btn.setEnabled(True)
        self.add_text(response_text)
        self.ai_results_text.setText(response_text)
        logging.info("Risposta Ollama processata con successo.")

    def handle_ollama_error(self, error_message):
        """Gestisce gli errori di Ollama."""
        self.update_status("❌ Errore nella richiesta AI.")
        self.ai_btn.setEnabled(True)
        self.add_btn.setEnabled(True)
        self.ai_results_text.setText(f"Errore: {error_message}")
        logging.error(f"Errore nella richiesta Ollama: {error_message}")
        QMessageBox.critical(self, "Errore Ollama", error_message)

    def toggle_voice_input(self, checked=False):
        """Inizia o ferma la registrazione vocale."""
        try:
            import speech_recognition as sr
        except ImportError:
            QMessageBox.critical(self, "Errore", "Libreria speech_recognition non disponibile.")
            return

        if not self.is_listening:
            self.is_listening = True
            self.voice_btn.setText("Registrazione in corso...")
            voice_icon = QIcon(self.get_svg_icon("M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zM12 17c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5z"))
            self.voice_btn.setIcon(voice_icon)
            self.voice_btn.setStyleSheet("""
                #voiceButton {
                    background-color: #e74c3c;
                    color: white;
                    border-radius: 12px;
                    padding: 8px 16px;
                }
            """)
            self.update_status("🎤 Registrazione in corso...")

            self.voice_thread = VoiceRecognitionThread(self.settings.get("language", "Italiano"))
            self.voice_thread.recognized_text.connect(self.handle_recognized_text)
            self.voice_thread.recognition_error.connect(self.handle_recognition_error)
            self.voice_thread.finished.connect(self.stop_voice_input)
            self.voice_thread.start()
        else:
            if self.voice_thread and self.voice_thread.isRunning():
                self.voice_thread.stop()
            self.stop_voice_input()

    def handle_recognized_text(self, text):
        """Gestisce il testo riconosciuto."""
        current_text = self.text_input.text()
        if current_text:
            self.text_input.setText(f"{current_text} {text}")
        else:
            self.text_input.setText(text)
        self.update_status("✅ Testo riconosciuto.")
        logging.info(f"Testo riconosciuto vocalmente: {text}")

    def handle_recognition_error(self, message):
        """Gestisce gli errori di riconoscimento vocale."""
        QMessageBox.warning(self, "Errore Riconoscimento Vocale", message)
        self.update_status(f"❌ Errore: {message}")
        logging.error(f"Errore di riconoscimento vocale: {message}")

    def stop_voice_input(self):
        """Ferma la registrazione vocale."""
        self.is_listening = False
        self.voice_btn.setText("Registra Voce")
        voice_icon = QIcon(self.get_svg_icon("M12 14c1.66 0 2.99-1.34 2.99-3L15 5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3zm5.3-3c0 3.99-3.98 5.75-5.3 5.75S6.7 14.99 6.7 11H5c0 4.14 3.36 7.48 7.48 7.48V21h-3v2h6v-2h-3v-2.52c4.14 0 7.48-3.34 7.48-7.48h-2.18z"))
        self.voice_btn.setIcon(voice_icon)
        self.voice_btn.setStyleSheet("")
        self.update_status("✅ Sistema attivo - Mostra le mani o il viso")

    def clean_input(self):
        """Pulisce l'input di testo."""
        self.text_input.clear()
        logging.info("Campo di input testo pulito.")

    def update_video(self, q_image):
        """Aggiorna il frame video."""
        pixmap = QPixmap.fromImage(q_image)
        self.video_label.setPixmap(pixmap)

    def update_status(self, message):
        """Aggiorna il messaggio di stato."""
        self.status_label.setText(message)
        logging.info(f"Status: {message}")

    def closeEvent(self, event):
        """Gestisce la chiusura dell'applicazione."""
        self.video_thread.stop()
        if self.voice_thread and self.voice_thread.isRunning():
            self.voice_thread.stop()
        event.accept()


from logging_utils import LogEmitter, TextEditLogger