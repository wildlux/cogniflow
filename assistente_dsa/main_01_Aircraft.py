#!/usr/bin/env python3
"""
Main 01 Aircraft - Launcher per la schermata principale
Richiama la porta aerei per avviare l'interfaccia principale
"""

import sys
import os
import json
import logging
from datetime import datetime
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel,
    QPushButton, QHBoxLayout, QLineEdit, QTextEdit, QGroupBox,
    QScrollArea, QMessageBox, QFileDialog, QSlider
)

# Import del sistema di configurazione
from main_03_configurazione_e_opzioni import get_config, load_settings

try:
    from UI.draggable_text_widget import DraggableTextWidget
except ImportError:
    DraggableTextWidget = None

try:
    from UI.settings_dialog import SettingsDialog
except ImportError:
    SettingsDialog = None

# Import del bridge Ollama per l'integrazione AI
try:
    from Artificial_Intelligence.Ollama.ollama_bridge import OllamaBridge
except ImportError:
    OllamaBridge = None

# Import del riconoscimento vocale
try:
    from Artificial_Intelligence.Riconoscimento_Vocale.managers.speech_recognition_manager import (
        SpeechRecognitionThread,
        ensure_vosk_model_available
    )
except ImportError:
    SpeechRecognitionThread = None
    ensure_vosk_model_available = None

# Import per funzionalità multimediali
try:
    from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
    from PyQt6.QtMultimediaWidgets import QVideoWidget
    MULTIMEDIA_AVAILABLE = True
except ImportError:
    QMediaPlayer = None
    QAudioOutput = None
    QVideoWidget = None
    MULTIMEDIA_AVAILABLE = False

# Import per OCR
try:
    import pytesseract
    from PIL import Image
    OCR_AVAILABLE = True
except ImportError:
    pytesseract = None
    Image = None
    OCR_AVAILABLE = False

# Classe per gestire l'area di lavoro con supporto al drop
class WorkAreaWidget(QWidget):
    def __init__(self, settings):
        super().__init__()
        self.settings = settings
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        """Accetta il drag se contiene testo o dati del widget."""
        if event.mimeData().hasText() or event.mimeData().hasFormat("application/x-draggable-widget"):
            event.acceptProposedAction()
            # Accetta sia MoveAction che CopyAction
            event.setDropAction(Qt.DropAction.CopyAction)

    def dropEvent(self, event):
        """Gestisce il drop creando un nuovo widget trascinabile."""
        try:
            from UI.draggable_text_widget import DraggableTextWidget

            # Ottieni il testo dal drop
            if event.mimeData().hasText():
                text = event.mimeData().text()
            else:
                return

            if text and text.strip():
                # Crea un nuovo widget trascinabile con tutte le funzionalità
                widget = DraggableTextWidget(text, self.settings)
                # Aggiungi il widget al layout dell'area di lavoro
                self.layout().addWidget(widget)
                event.acceptProposedAction()

        except Exception as e:
            logging.error(f"Errore durante il drop nell'area di lavoro: {e}")


# Classe per gestire l'area pensierini con controllo duplicati
class PensieriniWidget(QWidget):
    def __init__(self, settings, pensierini_layout):
        super().__init__()
        self.settings = settings
        self.pensierini_layout = pensierini_layout
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        """Accetta il drag se contiene testo o dati del widget."""
        if event.mimeData().hasText() or event.mimeData().hasFormat("application/x-draggable-widget"):
            event.acceptProposedAction()
            # Accetta sia MoveAction che CopyAction
            event.setDropAction(Qt.DropAction.CopyAction)

    def dropEvent(self, event):
        """Gestisce il drop controllando se esiste già un widget con lo stesso testo."""
        try:
            from UI.draggable_text_widget import DraggableTextWidget

            # Ottieni il testo dal drop
            if event.mimeData().hasText():
                text = event.mimeData().text()
            else:
                return

            if text and text.strip():
                # Controlla se esiste già un pensierino con lo stesso testo
                existing_widget = self._find_existing_widget(text.strip())
                if existing_widget is not None:
                    # Esiste già un pensierino con lo stesso testo - non creare duplicato
                    event.ignore()
                    return

                # Crea un nuovo widget trascinabile con tutte le funzionalità
                widget = DraggableTextWidget(text, self.settings)
                # Aggiungi il widget al layout dei pensierini
                self.pensierini_layout.addWidget(widget)
                event.acceptProposedAction()

        except Exception as e:
            logging.error(f"Errore durante il drop nell'area pensierini: {e}")

    def _find_existing_widget(self, text):
        """Cerca se esiste già un widget con lo stesso testo nei pensierini."""
        for i in range(self.pensierini_layout.count()):
            item = self.pensierini_layout.itemAt(i)
            if item:
                widget = item.widget()
                if widget and hasattr(widget, 'text_label'):
                    existing_text = widget.text_label.text().strip()
                    if existing_text == text:
                        return widget
        return None

# Classe MainWindow integrata da aircraft.py
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # Usa il sistema di configurazione globale invece di AppConfig locale
        from main_03_configurazione_e_opzioni import load_settings
        self.settings = load_settings()
        self.text_widgets = []

        # Inizializza il bridge Ollama per l'integrazione AI
        self.ollama_bridge = OllamaBridge() if OllamaBridge else None
        if self.ollama_bridge:
            self.ollama_bridge.responseReceived.connect(self._on_ai_response_received)
            self.ollama_bridge.errorOccurred.connect(self._on_ai_error_occurred)
            logging.info("Bridge Ollama inizializzato con successo")
        else:
            logging.warning("Bridge Ollama non disponibile - funzionalità AI limitata")

        self.setup_ui()
        logging.info("Applicazione avviata")

    def _on_ai_response_received(self, prompt, response):
        """Gestisce la risposta ricevuta da Ollama."""
        try:
            # Riabilita il pulsante di riformulazione se era disabilitato
            if hasattr(self, 'rephrase_button'):
                self.rephrase_button.setEnabled(True)
                self.rephrase_button.setText("🧠 Riformula intensamente")

            # Controlla se è una risposta di riformulazione
            if "Riformula intensamente" in prompt or "Riformulazione intensa" in prompt:
                # Mostra solo la riformulazione nei dettagli
                full_content = f"🧠 RIFORMULAZIONE COMPLETATA\n\n✨ Testo riformulato con intelligenza artificiale:\n\n{response}\n\n{'='*50}\n\n📊 Statistiche:\n• Testo originale: {len(self.full_text) if hasattr(self, 'full_text') else 0} caratteri\n• Testo riformulato: {len(response)} caratteri"
                self.show_text_in_details(full_content)

                # Log della riformulazione
                logging.info(f"Riformulazione AI completata: {len(response)} caratteri")

                # Mostra notifica di successo per riformulazione
                QMessageBox.information(self, "Riformulazione Completata",
                                      f"✅ Testo riformulato con successo!\n\n"
                                      f"🧠 Elaborazione AI completata\n"
                                      f"📝 Nuovo testo: {len(response)} caratteri")
            else:
                # Risposta AI normale (non riformulazione)
                full_content = f"📤 Richiesta:\n{prompt}\n\n{'='*50}\n\n🤖 Risposta AI (llama2:7b):\n\n{response}"
                self.show_text_in_details(full_content)

                # Log della risposta ricevuta
                logging.info(f"Risposta AI ricevuta per prompt: {prompt[:50]}... (lunghezza: {len(response)} caratteri)")

                # Mostra notifica di successo
                QMessageBox.information(self, "AI Risposta Ricevuta",
                                      f"Risposta AI ricevuta con successo!\n\n"
                                      f"Richiesta: {len(prompt)} caratteri\n"
                                      f"Risposta: {len(response)} caratteri")

        except Exception as e:
            logging.error(f"Errore nella gestione della risposta AI: {e}")
            QMessageBox.critical(self, "Errore AI", f"Errore nella risposta AI: {e}")
            # Riabilita il pulsante in caso di errore
            if hasattr(self, 'rephrase_button'):
                self.rephrase_button.setEnabled(True)
                self.rephrase_button.setText("🧠 Riformula intensamente")

    def _on_ai_error_occurred(self, error_msg):
        """Gestisce gli errori da Ollama."""
        logging.error(f"Errore AI: {error_msg}")
        QMessageBox.critical(self, "Errore AI", f"Errore dal servizio AI:\n{error_msg}")

    def setup_ui(self):
        self.setWindowTitle("CogniFlow")
        # Usa le dimensioni dalla configurazione globale
        window_width = self.settings.get('ui', {}).get('window_width', 1200)
        window_height = self.settings.get('ui', {}).get('window_height', 800)
        self.setGeometry(100, 100, window_width, window_height)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Applica stile globale colorato
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #f8f9fa, stop:1 #e9ecef);
            }

            QGroupBox {
                font-weight: bold;
                border: 2px solid;
                border-radius: 8px;
                margin-top: 6px;
                padding-top: 10px;
                background: rgba(255, 255, 255, 0.8);
            }

            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #2c3e50;
                font-weight: bold;
            }

            /* Colonna A - Pensierini (Verde) */
            QGroupBox#pensierini {
                border-color: #28a745;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(40, 167, 69, 0.1), stop:1 rgba(40, 167, 69, 0.05));
            }

            /* Colonna B - Area Lavoro (Giallo) */
            QGroupBox#work_area {
                border-color: #ffc107;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255, 193, 7, 0.1), stop:1 rgba(255, 193, 7, 0.05));
            }

            /* Colonna C - Dettagli (Viola) */
            QGroupBox#details {
                border-color: #6f42c1;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(111, 66, 193, 0.1), stop:1 rgba(111, 66, 193, 0.05));
            }

            /* Barra strumenti */
            QGroupBox#tools {
                border-color: #4a90e2;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(74, 144, 226, 0.1), stop:1 rgba(74, 144, 226, 0.05));
            }

            QPushButton {
                background-color: #4a90e2;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 18px;
                font-weight: bold;
                min-width: 120px;
                min-height: 40px;
                font-size: 14px;
                text-align: center;
            }

            QPushButton:hover {
                background-color: #357abd;
                border: 2px solid #2e5f8f;
            }

            QPushButton:pressed {
                background-color: #2e5f8f;
            }

            /* Pulsante Opzioni */
            QPushButton#options_button {
                background-color: #6c757d;
                min-width: 100px;
            }

            QPushButton#options_button:hover {
                background-color: #5a6268;
            }

            /* Pulsante Salva */
            QPushButton#save_button {
                background-color: #28a745;
                min-width: 100px;
            }

            QPushButton#save_button:hover {
                background-color: #218838;
            }

            /* Pulsante Carica */
            QPushButton#load_button {
                background-color: #ffc107;
                color: black;
                min-width: 100px;
            }

            QPushButton#load_button:hover {
                background-color: #e0a800;
            }

            /* Pulsante Aggiungi Pensierino */
            QPushButton#add_pensierino_button {
                background-color: #17a2b8;
                min-width: 140px;
            }

            QPushButton#add_pensierino_button:hover {
                background-color: #138496;
            }

            /* Pulsante AI */
            QPushButton#ai_button {
                background-color: #28a745;
                min-width: 130px;
            }

            QPushButton#ai_button:hover {
                background-color: #218838;
            }

            /* Pulsante Voce */
            QPushButton#voice_button {
                background-color: #9c27b0;
                min-width: 130px;
            }

            QPushButton#voice_button:hover {
                background-color: #7b1fa2;
            }

            /* Pulsante Media */
            QPushButton#media_button {
                background-color: #17a2b8;
                min-width: 130px;
            }

            QPushButton#media_button:hover {
                background-color: #138496;
            }

            /* Pulsante OCR */
            QPushButton#ocr_button {
                background-color: #28a745;
                min-width: 200px;
            }

            QPushButton#ocr_button:hover {
                background-color: #218838;
            }

            /* Pulsante Riconoscimento Faciale */
            QPushButton#face_button {
                background-color: #f8f9fa;
                color: #6c757d;
                border: 2px solid #dee2e6;
                border-radius: 6px;
                padding: 8px 12px;
                font-weight: bold;
                min-width: 180px;
                min-height: 35px;
            }

            QPushButton#face_button:hover {
                background-color: #e9ecef;
                border-color: #adb5bd;
            }

            QPushButton#face_button:checked {
                background-color: #d4edda;
                color: #155724;
                border: 2px solid #c3e6cb;
            }

            QPushButton#face_button:checked:hover {
                background-color: #c3e6cb;
                border-color: #8fd19e;
            }

            /* Pulsante Riconoscimento Gesti Mani */
            QPushButton#hand_button {
                background-color: #f8f9fa;
                color: #6c757d;
                border: 2px solid #dee2e6;
                border-radius: 6px;
                padding: 8px 12px;
                font-weight: bold;
                min-width: 150px;
                min-height: 35px;
            }

            QPushButton#hand_button:hover {
                background-color: #e9ecef;
                border-color: #adb5bd;
            }

            QPushButton#hand_button:checked {
                background-color: #d4edda;
                color: #155724;
                border: 2px solid #c3e6cb;
            }

            QPushButton#hand_button:checked:hover {
                background-color: #c3e6cb;
                border-color: #8fd19e;
            }

            /* Pulsante Log Footer */
            QPushButton#footer_log_button {
                background-color: #6f42c1;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 12px;
                font-weight: bold;
                font-size: 11px;
            }

            QPushButton#footer_log_button:hover {
                background-color: #5a359a;
            }

            QPushButton#footer_log_button:checked {
                background-color: #e8590c;
                border: 2px solid #d0390c;
            }

            /* Pulsante Pulisci */
            QPushButton#clean_button {
                background-color: #dc3545;
                min-width: 130px;
            }

            QPushButton#clean_button:hover {
                background-color: #c82333;
            }

            /* Pulsante Copia */
            QPushButton#copy_button {
                background-color: #007bff;
                min-width: 100px;
            }

            QPushButton#copy_button:hover {
                background-color: #0056b3;
            }

            QLineEdit {
                border: 2px solid #4a90e2;
                border-radius: 10px;
                padding: 12px 16px;
                font-size: 16px;
                font-weight: bold;
                text-align: center;
                background: rgba(255, 255, 255, 0.9);
            }

            QLineEdit:focus {
                border-color: #357abd;
                background-color: #f8f9fa;
                border-width: 3px;
            }

            QLineEdit::placeholder {
                color: #6c757d;
                font-style: italic;
            }

            QTextEdit {
                border: 1px solid #dee2e6;
                border-radius: 6px;
                background-color: rgba(255, 255, 255, 0.9);
                font-size: 16px;
                line-height: 1.4;
                padding: 8px;
                min-height: 80px;
                max-height: 120px;
            }

            QScrollArea {
                border: 1px solid #dee2e6;
                border-radius: 6px;
                background-color: rgba(248, 249, 250, 0.8);
            }

            /* Scrollbar styling */
            QScrollBar:vertical {
                background: rgba(255, 255, 255, 0.5);
                width: 12px;
                border-radius: 6px;
            }

            QScrollBar::handle:vertical {
                background: #4a90e2;
                border-radius: 6px;
                min-height: 30px;
            }

            QScrollBar::handle:vertical:hover {
                background: #357abd;
            }

            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                background: none;
            }

            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)

        main_layout = QVBoxLayout(central_widget)

        # Top bar
        top_layout = QHBoxLayout()
        self.options_button = QPushButton("⚙️ Opzioni")
        self.options_button.setObjectName("options_button")  # ID per CSS
        self.options_button.clicked.connect(self.open_settings)
        top_layout.addWidget(self.options_button)

        top_layout.addStretch()
        self.project_name_input = QLineEdit()
        self.project_name_input.setPlaceholderText("Nome progetto...")
        top_layout.addWidget(self.project_name_input)
        top_layout.addStretch()

        self.save_button = QPushButton("💾 Salva")
        self.save_button.setObjectName("save_button")  # ID per CSS
        self.save_button.clicked.connect(self.save_project)
        top_layout.addWidget(self.save_button)

        self.load_button = QPushButton("📂 Carica")
        self.load_button.setObjectName("load_button")  # ID per CSS
        self.load_button.clicked.connect(self.load_project)
        top_layout.addWidget(self.load_button)

        main_layout.addLayout(top_layout)

        # Main content with SPLITTER for resizable columns
        from PyQt6.QtWidgets import QSplitter

        # Create splitter for resizable columns
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.main_splitter.setHandleWidth(8)  # Thicker handles for easier dragging
        self.main_splitter.setStyleSheet("""
            QSplitter::handle {
                background: #4a90e2;
                border: 1px solid #357abd;
                border-radius: 4px;
            }
            QSplitter::handle:hover {
                background: #357abd;
            }
            QSplitter::handle:pressed {
                background: #2e5f8f;
            }
        """)

        # Column A: Pensierini
        self.column_a_group = QGroupBox("📝 Pensierini")
        self.column_a_group.setObjectName("pensierini")  # ID per CSS
        self.column_a_group.setMinimumWidth(200)  # Minimum width to prevent collapse
        column_a_layout = QVBoxLayout(self.column_a_group)
        self.pensierini_scroll = QScrollArea()
        self.pensierini_scroll.setWidgetResizable(True)
        self.pensierini_widget = PensieriniWidget(self.settings, None)  # Layout sarà impostato dopo
        self.pensierini_layout = QVBoxLayout(self.pensierini_widget)
        self.pensierini_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        # Aggiorna il riferimento al layout nel widget pensierini
        self.pensierini_widget.pensierini_layout = self.pensierini_layout
        self.pensierini_scroll.setWidget(self.pensierini_widget)
        column_a_layout.addWidget(self.pensierini_scroll)
        self.main_splitter.addWidget(self.column_a_group)

        # Column B: Work Area
        self.column_b_group = QGroupBox("📋 Area di Lavoro")
        self.column_b_group.setObjectName("work_area")  # ID per CSS
        self.column_b_group.setMinimumWidth(200)  # Minimum width to prevent collapse
        column_b_layout = QVBoxLayout(self.column_b_group)
        self.setup_work_area(column_b_layout)
        self.main_splitter.addWidget(self.column_b_group)

        # Column C: Details
        self.column_c_group = QGroupBox("🔍 Dettagli")
        self.column_c_group.setObjectName("details")  # ID per CSS
        self.column_c_group.setMinimumWidth(300)  # Minimum width for details
        self.column_c_group.setMinimumHeight(600)  # Altezza minima aumentata significativamente
        column_c_layout = QVBoxLayout(self.column_c_group)
        self.details_scroll = QScrollArea()
        self.details_scroll.setWidgetResizable(True)
        self.details_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.details_widget = QWidget()
        self.details_layout = QVBoxLayout(self.details_widget)
        self.details_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.details_scroll.setWidget(self.details_widget)
        column_c_layout.addWidget(self.details_scroll)
        self.main_splitter.addWidget(self.column_c_group)

        # Set initial proportions (balanced 3-equal parts)
        self.main_splitter.setSizes([333, 333, 334])  # Roughly equal thirds

        main_layout.addWidget(self.main_splitter, 1)

        # Bottom tools
        tools_group = QGroupBox("🔧 Strumenti")
        tools_group.setObjectName("tools")  # ID per CSS
        tools_layout = QVBoxLayout(tools_group)

        self.input_text_area = QTextEdit()
        self.input_text_area.setPlaceholderText("Scrivi qui, ( premi INVIO per creare un pensierino - Premi INVIO di destra per tornare a capo )")
        self.input_text_area.setMaximumHeight(100)
        # Installa event filter per intercettare Invio
        self.input_text_area.installEventFilter(self)
        tools_layout.addWidget(self.input_text_area)

        buttons_layout = QHBoxLayout()
        self.add_pensierino_button = QPushButton("➕ Aggiungi Pensierino")
        self.add_pensierino_button.setObjectName("add_pensierino_button")  # ID per CSS
        self.add_pensierino_button.clicked.connect(self.add_text_from_input_area)
        buttons_layout.addWidget(self.add_pensierino_button)

        self.ai_button = QPushButton("🧠 Chiedi ad A.I. !")
        self.ai_button.setObjectName("ai_button")  # ID per CSS
        self.ai_button.clicked.connect(self.handle_ai_button)
        buttons_layout.addWidget(self.ai_button)

        self.voice_button = QPushButton("🎤 Trascrivi la mia voce")
        self.voice_button.setObjectName("voice_button")  # ID per CSS
        self.voice_button.clicked.connect(self.handle_voice_button)
        buttons_layout.addWidget(self.voice_button)

        self.media_button = QPushButton("📁 Carica Media")
        self.media_button.setObjectName("media_button")  # ID per CSS
        self.media_button.clicked.connect(self.handle_media_button)
        buttons_layout.addWidget(self.media_button)

        self.ocr_button = QPushButton("📄 Trascrizione di Documenti-OCR")
        self.ocr_button.setObjectName("ocr_button")  # ID per CSS
        self.ocr_button.clicked.connect(self.handle_ocr_button)
        buttons_layout.addWidget(self.ocr_button)

        # Pulsante Riconoscimento Faciale
        self.face_button = QPushButton("❌ Riconoscimento Faciale")
        self.face_button.setObjectName("face_button")  # ID per CSS
        self.face_button.setCheckable(True)
        self.face_button.clicked.connect(self.handle_face_recognition)
        buttons_layout.addWidget(self.face_button)

        # Pulsante Riconoscimento Gesti Mani
        self.hand_button = QPushButton("❌ Abilita Gesti Mani")
        self.hand_button.setObjectName("hand_button")  # ID per CSS
        self.hand_button.setCheckable(True)
        self.hand_button.clicked.connect(self.handle_hand_gestures)
        buttons_layout.addWidget(self.hand_button)

        self.clean_button = QPushButton("🧹 Pulisci")
        self.clean_button.setObjectName("clean_button")  # ID per CSS
        self.clean_button.clicked.connect(self.handle_clean_button)
        buttons_layout.addWidget(self.clean_button)

        buttons_layout.addStretch()
        tools_layout.addLayout(buttons_layout)
        main_layout.addWidget(tools_group)

        # Footer con pulsante log in basso a destra (alzato)
        footer_layout = QHBoxLayout()
        footer_layout.addStretch()  # Spazio a sinistra

        self.log_button = QPushButton("📋 Log")
        self.log_button.setObjectName("footer_log_button")
        self.log_button.setCheckable(True)
        self.log_button.clicked.connect(self.handle_log_toggle)
        self.log_button.setFixedSize(120, 35)
        footer_layout.addWidget(self.log_button)

        # Aggiungi spaziatura sotto per alzare il pulsante
        footer_layout.setContentsMargins(0, 0, 0, 8)  # Margine inferiore di 8px

        main_layout.addLayout(footer_layout)

    def setup_work_area(self, layout):
        self.work_area_scroll = QScrollArea()
        self.work_area_scroll.setWidgetResizable(True)
        self.work_area_widget = WorkAreaWidget(self.settings)
        self.work_area_layout = QVBoxLayout(self.work_area_widget)
        self.work_area_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.work_area_scroll.setWidget(self.work_area_widget)
        layout.addWidget(self.work_area_scroll)

    def eventFilter(self, obj, event):
        """Event filter per intercettare eventi della tastiera."""
        from PyQt6.QtCore import Qt, QEvent

        # Gestisci solo eventi della tastiera per l'area di testo
        if obj == self.input_text_area and event.type() == QEvent.Type.KeyPress:
            # Se è Invio senza Shift, aggiungi pensierino
            if event.key() == Qt.Key.Key_Return and not event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                if self.input_text_area.toPlainText().strip():
                    self.add_text_from_input_area()
                return True  # Consuma l'evento (non propagarlo)

        # Per tutti gli altri casi, lascia che l'evento venga gestito normalmente
        return super().eventFilter(obj, event)

    def add_text_from_input_area(self):
        text = self.input_text_area.toPlainText().strip()
        if text and DraggableTextWidget:
            widget = DraggableTextWidget(text, self.settings)
            self.pensierini_layout.addWidget(widget)
            self.input_text_area.clear()
            logging.info(f"Aggiunto pensierino: {text[:50]}...")

    def handle_ai_button(self):
        """Gestisce la funzione AI: invia richiesta a Ollama e mostra risposta."""
        text = self.input_text_area.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "Testo Vuoto", "Inserisci del testo prima di usare la funzione AI.")
            return

        # Controlla se il bridge Ollama è disponibile
        if not self.ollama_bridge:
            QMessageBox.critical(self, "AI Non Disponibile",
                               "Il servizio AI non è disponibile. Verifica che Ollama sia installato e funzionante.")
            return

        # Verifica connessione con Ollama
        if not self.ollama_bridge.checkConnection():
            QMessageBox.critical(self, "Connessione AI Fallita",
                               "Impossibile connettersi al servizio AI Ollama.\n"
                               "Assicurati che Ollama sia in esecuzione con: ollama serve")
            return

        try:
            # Crea pensierino con testo troncato per mostrare la richiesta
            truncated_text = text[:20] + "..." if len(text) > 20 else text

            if DraggableTextWidget:
                # Aggiungi pensierino alla colonna A con indicatore AI
                ai_pensierino_text = f"🤖 {truncated_text}"
                pensierino_widget = DraggableTextWidget(ai_pensierino_text, self.settings)
                self.pensierini_layout.addWidget(pensierino_widget)

            # Mostra richiesta originale nei dettagli
            self.show_text_in_details(f"📤 Richiesta AI:\n\n{text}\n\n⏳ Attendo risposta...")

            # Invia richiesta a Ollama con modello di default
            default_model = "llama2:7b"  # Modello raccomandato
            self.ollama_bridge.sendPrompt(text, default_model)

            # Log dell'invio richiesta
            logging.info(f"Richiesta AI inviata: {text[:50]}... (modello: {default_model})")

        except Exception as e:
            logging.error(f"Errore nell'invio richiesta AI: {e}")
            QMessageBox.critical(self, "Errore AI", f"Errore nell'invio della richiesta AI:\n{str(e)}")
            return

        # Pulisci area di input solo dopo aver inviato con successo
        self.input_text_area.clear()

    def show_text_in_details(self, full_text):
        """Mostra il testo completo nei dettagli con paginazione di 250 caratteri."""
        # Pulisci dettagli esistenti
        self._clear_details()

        # Crea widget per mostrare testo con paginazione
        self.create_paginated_text_widget(full_text)

    def create_paginated_text_widget(self, full_text):
        """Crea un widget con testo paginato per i dettagli."""
        from PyQt6.QtWidgets import QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QWidget

        # Widget contenitore
        container = QWidget()
        layout = QVBoxLayout(container)

        # Testo corrente
        self.current_page = 0
        self.page_size = 250
        self.full_text = full_text
        self.total_pages = (len(full_text) + self.page_size - 1) // self.page_size

        # TextEdit per il testo (permette navigazione con cursore)
        self.details_text_label = QTextEdit()
        self.details_text_label.setReadOnly(True)
        # Imposta altezza minima per mostrare circa 10 righe
        self.details_text_label.setMinimumHeight(300)  # Circa 10 righe con font 16px
        # Imposta size policy per espansione massima
        from PyQt6.QtWidgets import QSizePolicy
        self.details_text_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        # Rimuovi entrambe le scrollbar per massimizzare lo spazio
        self.details_text_label.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.details_text_label.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.details_text_label.setStyleSheet("""
            QTextEdit {
                background: rgba(221, 160, 221, 0.9); /* Viola chiaro per il testo */
                border: 2px solid #6f42c1;
                border-radius: 8px;
                padding-top: 20px;
                padding-bottom: 20px;
                padding-left: 15px;
                padding-right: 15px;
                font-size: 16px;
                line-height: 1.4;
                color: #333;
            }

            /* Pulsante Riformula - Verde */
            QPushButton#rephrase_button {
                background-color: #28a745;
                color: white;
                border: 2px solid #1e7e34;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
                min-height: 35px;
                min-width: 160px;
            }

            QPushButton#rephrase_button:hover {
                background-color: #218838;
                border-color: #1c7430;
            }

            /* Pulsanti navigazione - Blu */
            QPushButton#back_button, QPushButton#forward_button {
                background-color: #007bff;
                color: white;
                border: 2px solid #0056b3;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
                min-height: 35px;
            }

            QPushButton#back_button:hover, QPushButton#forward_button:hover {
                background-color: #0056b3;
                border-color: #004085;
            }

            /* Etichetta pagina - Arancione */
            QPushButton#page_info_label {
                background-color: #fd7e14;
                color: white;
                border: 2px solid #e8590c;
                border-radius: 4px;
                padding: 2px 8px;
                font-weight: bold;
                font-size: 12px;
                min-width: 50px;
                max-width: 60px;
            }

            QPushButton#page_info_label:hover {
                background-color: #e8590c;
                border-color: #d0390c;
            }


        """)

        # Pulsante per tornare indietro
        self.back_button = QPushButton("⬅️ Pagina precedente")
        self.back_button.setObjectName("back_button")
        self.back_button.clicked.connect(self.show_prev_page)

        # Pulsante per andare avanti
        self.forward_button = QPushButton("➡️ Prossima pagina")
        self.forward_button.setObjectName("forward_button")
        self.forward_button.clicked.connect(self.show_next_page)

        # Pulsante per riformulare intensamente
        self.rephrase_button = QPushButton("🧠 Riformula intensamente")
        self.rephrase_button.setObjectName("rephrase_button")
        self.rephrase_button.setStyleSheet("""
            QPushButton {
                background-color: #17a2b8;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: bold;
                min-height: 35px;
                min-width: 160px;
            }
            QPushButton:hover {
                background-color: #138496;
            }
            QPushButton:disabled {
                background-color: #adb5bd;
                color: #6c757d;
            }
        """)
        self.rephrase_button.clicked.connect(self.handle_rephrase_button)

        # Layout principale per controlli (verticale)
        main_controls_layout = QVBoxLayout()
        # Imposta size policy per mantenere i controlli compatti
        from PyQt6.QtWidgets import QSizePolicy
        main_controls_layout.setSizeConstraint(QVBoxLayout.SizeConstraint.SetFixedSize)

        # Prima riga: pulsante copia, riformula con numero pagina accanto
        rephrase_layout = QHBoxLayout()
        rephrase_layout.addStretch()

        # Pulsante copia
        self.copy_button = QPushButton("📋 Copia")
        self.copy_button.setObjectName("copy_button")
        self.copy_button.clicked.connect(self.handle_copy_button)
        self.copy_button.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border: 2px solid #0056b3;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
                min-height: 35px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #0056b3;
                border-color: #004085;
            }
        """)
        rephrase_layout.addWidget(self.copy_button)

        rephrase_layout.addWidget(self.rephrase_button)

        # Pulsante pagina non cliccabile (più compatto)
        self.page_info_label = QPushButton("Pag. 1")
        self.page_info_label.setObjectName("page_info_label")
        self.page_info_label.setEnabled(False)  # Non cliccabile
        self.page_info_label.setStyleSheet("""
            QPushButton {
                color: #495057;
                font-weight: bold;
                font-size: 12px;
                padding: 2px 8px;
                background: rgba(255, 255, 255, 0.8);
                border: 1px solid #dee2e6;
                border-radius: 4px;
                min-width: 50px;
                max-width: 60px;
                text-align: center;
                margin-left: 5px;
            }
        """)
        rephrase_layout.addWidget(self.page_info_label)
        rephrase_layout.addStretch()
        main_controls_layout.addLayout(rephrase_layout)

        # Seconda riga: controlli di navigazione (pulsanti indietro e avanti affiancati)
        navigation_layout = QHBoxLayout()

        # Pulsante indietro
        navigation_layout.addWidget(self.back_button)

        navigation_layout.addStretch()

        # Pulsante avanti accanto a quello indietro
        navigation_layout.addWidget(self.forward_button)

        main_controls_layout.addLayout(navigation_layout)

        layout.addWidget(self.details_text_label)
        layout.addLayout(main_controls_layout)  # Pulsanti direttamente sotto il testo

        # Aggiungi al layout dei dettagli
        self.details_layout.addWidget(container)

        # Mostra prima pagina
        self.update_page_display()

    def show_prev_page(self):
        """Mostra la pagina precedente del testo."""
        if self.current_page > 0:
            self.current_page -= 1
            self.update_page_display()

    def show_prev_page_2(self):
        """Mostra la pagina precedente di 2 posizioni."""
        if self.current_page > 1:
            self.current_page -= 2
        elif self.current_page > 0:
            self.current_page = 0
        self.update_page_display()

    def show_next_page(self):
        """Mostra la pagina successiva del testo o torna all'inizio."""
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
        else:
            # Ritorna all'inizio
            self.current_page = 0
        self.update_page_display()

    def update_page_display(self):
        """Aggiorna la visualizzazione della pagina corrente."""
        start = self.current_page * self.page_size
        end = min(start + self.page_size, len(self.full_text))
        current_text = self.full_text[start:end]

        # Rimuovi l'indicatore di pagina dal testo (ora mostrato nei controlli)
        display_text = current_text
        self.details_text_label.setPlainText(display_text)

        # Aggiorna etichetta pagina corrente (massimo 11 caratteri)
        current_page_num = self.current_page + 1
        self.page_info_label.setText(f"Pag. {current_page_num}")

        # Aggiorna testi dei pulsanti
        if self.current_page < self.total_pages - 1:
            self.forward_button.setText("➡️ Prossima pagina")
        else:
            self.forward_button.setText("🔄 Ritorna all'inizio")

        # Aggiorna stato pulsanti navigazione
        self.back_button.setEnabled(self.current_page > 0)
        self.forward_button.setEnabled(True)  # Sempre abilitato (per tornare all'inizio)

    def _clear_details(self):
        """Pulisce la colonna dettagli."""
        try:
            while self.details_layout.count():
                item = self.details_layout.takeAt(0)
                if item:
                    widget = item.widget()
                    if widget and hasattr(widget, 'deleteLater'):
                        widget.deleteLater()
        except Exception as e:
            logging.error(f"Errore pulizia dettagli: {e}")



    def handle_voice_button(self):
        """Avvia il riconoscimento vocale utilizzando il modulo Riconoscimento_Vocale."""
        if not SpeechRecognitionThread:
            QMessageBox.critical(self, "Errore", "Modulo di riconoscimento vocale non disponibile.\n\n"
                                               "Assicurati che le librerie 'vosk' e 'pyaudio' siano installate.")
            return

        # Disabilita il pulsante durante il riconoscimento
        self.voice_button.setEnabled(False)
        self.voice_button.setText("🎤 In ascolto...")

        # Ottieni il modello Vosk dalle impostazioni
        vosk_model = self.settings.get('vosk_model', 'vosk-model-it-0.22')

        # Se il modello non è configurato, usa quello italiano di default
        if not vosk_model or vosk_model == 'auto':
            vosk_model = 'vosk-model-it-0.22'

        # Verifica che il modello esista e scaricalo se necessario
        import os
        model_path = os.path.join("Artificial_Intelligence", "Riconoscimento_Vocale", "models", "vosk_models", vosk_model)
        if not os.path.exists(model_path):
            if ensure_vosk_model_available:
                # Mostra dialog di progresso per il download
                progress_msg = QMessageBox(self)
                progress_msg.setWindowTitle("Download Modello")
                progress_msg.setText("🔄 Preparazione download modello...")
                progress_msg.setStandardButtons(QMessageBox.StandardButton.Cancel)
                progress_msg.show()

                def progress_callback(message):
                    progress_msg.setText(message)
                    QApplication.processEvents()  # Aggiorna l'interfaccia

                # Tenta di scaricare il modello
                if not ensure_vosk_model_available(vosk_model, progress_callback):
                    progress_msg.close()
                    QMessageBox.critical(self, "Download Fallito",
                                       f"Impossibile scaricare il modello '{vosk_model}'.\n\n"
                                       "Verifica la connessione internet e riprova.")
                    self.voice_button.setEnabled(True)
                    self.voice_button.setText("🎤 Trascrivi la mia voce")
                    return

                progress_msg.close()
                QMessageBox.information(self, "Download Completato",
                                      f"✅ Modello '{vosk_model}' scaricato con successo!")
            else:
                QMessageBox.warning(self, "Funzione Download Non Disponibile",
                                  f"Il modello Vosk '{vosk_model}' non è stato trovato.\n\n"
                                  f"Percorso: {model_path}\n\n"
                                  "La funzione di download automatico non è disponibile.")
                self.voice_button.setEnabled(True)
                self.voice_button.setText("🎤 Trascrivi la mia voce")
                return

        try:
            # Crea il thread di riconoscimento vocale con callback
            self.speech_thread = SpeechRecognitionThread(vosk_model, text_callback=self._on_voice_recognized)

            # Connetti i segnali come fallback
            self.speech_thread.recognized_text.connect(self._on_voice_recognized)
            self.speech_thread.recognition_error.connect(self._on_voice_error)
            self.speech_thread.stopped_by_silence.connect(self._on_voice_stopped_by_silence)
            self.speech_thread.finished.connect(self._on_voice_finished)

            # Avvia il riconoscimento
            self.speech_thread.start()

            QMessageBox.information(self, "Riconoscimento Vocale",
                                  "🎤 Riconoscimento vocale avviato!\n\n"
                                  "Parla chiaramente nel microfono.\n"
                                  "Il testo riconosciuto verrà aggiunto direttamente ai pensierini.\n"
                                  "Il riconoscimento si fermerà automaticamente dopo 3 secondi di silenzio.")

        except Exception as e:
            QMessageBox.critical(self, "Errore Avvio", f"Errore nell'avvio del riconoscimento vocale:\n{str(e)}")
            self.voice_button.setEnabled(True)
            self.voice_button.setText("🎤 Trascrivi la mia voce")

    def _on_voice_recognized(self, text):
        """Callback quando viene riconosciuto del testo vocale."""
        logging.info(f"🎤 _on_voice_recognized chiamata con testo: '{text}'")

        if text and text.strip():
            logging.info(f"📝 Testo valido ricevuto: '{text.strip()}'")

            # Inserisci il testo direttamente nella colonna dei pensierini
            if hasattr(self, 'pensierini_layout') and self.pensierini_layout:
                logging.info("✅ pensierini_layout disponibile")

                # Crea un nuovo pensierino con il testo riconosciuto
                if DraggableTextWidget:
                    try:
                        widget = DraggableTextWidget(f"🎤 {text.strip()}", self.settings)
                        self.pensierini_layout.addWidget(widget)
                        logging.info(f"✅ Widget creato e aggiunto ai pensierini: {text[:50]}...")
                    except Exception as e:
                        logging.error(f"❌ Errore creazione widget: {e}")
                        # Fallback: inserisci nell'area di testo
                        current_text = self.input_text_area.toPlainText()
                        if current_text:
                            self.input_text_area.setPlainText(f"{current_text}\n{text.strip()}")
                        else:
                            self.input_text_area.setPlainText(text.strip())
                else:
                    logging.warning("⚠️ DraggableTextWidget non disponibile, uso fallback")
                    # Fallback: inserisci nell'area di testo
                    current_text = self.input_text_area.toPlainText()
                    if current_text:
                        self.input_text_area.setPlainText(f"{current_text}\n{text.strip()}")
                    else:
                        self.input_text_area.setPlainText(text.strip())
            else:
                logging.error("❌ pensierini_layout non disponibile")

            # Mostra notifica di successo
            QMessageBox.information(self, "Testo Riconosciuto",
                                  f"✅ Testo riconosciuto con successo!\n\n"
                                  f"📝 \"{text.strip()[:100]}{'...' if len(text.strip()) > 100 else ''}\"\n\n"
                                  f"💭 Aggiunto ai pensierini!")
        else:
            logging.warning(f"⚠️ Testo vuoto o None ricevuto: '{text}'")

    def _on_voice_error(self, error_msg):
        """Callback per gestire errori del riconoscimento vocale."""
        QMessageBox.warning(self, "Errore Riconoscimento", f"Errore durante il riconoscimento vocale:\n\n{error_msg}")
        self._reset_voice_button()

    def _on_voice_stopped_by_silence(self):
        """Callback quando il riconoscimento si ferma per silenzio."""
        QMessageBox.information(self, "Riconoscimento Completato",
                              "🎤 Riconoscimento vocale completato!\n\n"
                              "Il sistema si è fermato automaticamente dopo 3 secondi di silenzio.")
        self._reset_voice_button()

    def _on_voice_finished(self):
        """Callback quando il thread di riconoscimento finisce."""
        self._reset_voice_button()

    def _reset_voice_button(self):
        """Riporta il pulsante voce allo stato normale."""
        if hasattr(self, 'voice_button'):
            self.voice_button.setEnabled(True)
            self.voice_button.setText("🎤 Trascrivi la mia voce")

    def handle_copy_button(self):
        """Copia tutto il testo dei dettagli negli appunti."""
        if not hasattr(self, 'full_text') or not self.full_text:
            QMessageBox.warning(self, "Nessun Contenuto", "Non c'è contenuto da copiare nei dettagli.")
            return

        try:
            # Ottieni gli appunti dell'applicazione
            clipboard = QApplication.clipboard()
            if clipboard:
                clipboard.setText(self.full_text)
            else:
                QMessageBox.critical(self, "Errore Appunti", "Impossibile accedere agli appunti del sistema.")
                return

            # Mostra notifica di successo
            QMessageBox.information(self, "Copia Completata",
                                  f"✅ Testo copiato negli appunti!\n\n"
                                  f"📝 {len(self.full_text)} caratteri copiati")

            logging.info(f"Testo copiato negli appunti: {len(self.full_text)} caratteri")

        except Exception as e:
            logging.error(f"Errore durante la copia: {e}")
            QMessageBox.critical(self, "Errore Copia", f"Errore durante la copia del testo:\n{str(e)}")

    def handle_rephrase_button(self):
        """Gestisce la riformulazione intensa del contenuto nei dettagli usando LLM."""
        if not hasattr(self, 'full_text') or not self.full_text:
            QMessageBox.warning(self, "Nessun Contenuto", "Non c'è contenuto da riformulare nei dettagli.")
            return

        # Controlla se il bridge Ollama è disponibile
        if not self.ollama_bridge:
            QMessageBox.critical(self, "AI Non Disponibile",
                               "Il servizio AI non è disponibile. Verifica che Ollama sia installato e funzionante.")
            return

        # Verifica connessione con Ollama
        if not self.ollama_bridge.checkConnection():
            QMessageBox.critical(self, "Connessione AI Fallita",
                               "Impossibile connettersi al servizio AI Ollama.\n"
                               "Assicurati che Ollama sia in esecuzione con: ollama serve")
            return

        # Disabilita il pulsante durante l'elaborazione
        if hasattr(self, 'rephrase_button'):
            self.rephrase_button.setEnabled(False)
            self.rephrase_button.setText("⏳ Riformulazione...")

        try:
            # Crea prompt per riformulazione intensa
            prompt = f"""Riformula intensamente il seguente testo in modo più elegante, chiaro e professionale.
Mantieni il significato originale ma usa un linguaggio più sofisticato e fluido.
Se è un'analisi o una descrizione, rendila più dettagliata e approfondita.
Se è una domanda, riformulala in modo più preciso e formale.

Testo originale:
{self.full_text}

Riformulazione intensa:"""

            # Mostra stato di elaborazione nei dettagli
            processing_text = f"🧠 RIFORMULAZIONE IN CORSO\n\n⏳ Elaborazione del testo con intelligenza artificiale...\n\nTesto originale ({len(self.full_text)} caratteri):\n{self.full_text[:200]}{'...' if len(self.full_text) > 200 else ''}"
            self.show_text_in_details(processing_text)

            # Invia richiesta a Ollama con modello di default
            default_model = "llama2:7b"  # Modello raccomandato
            self.ollama_bridge.sendPrompt(prompt, default_model)

            logging.info(f"Richiesta riformulazione inviata: {len(self.full_text)} caratteri (modello: {default_model})")

        except Exception as e:
            logging.error(f"Errore nell'invio richiesta riformulazione: {e}")
            QMessageBox.critical(self, "Errore AI", f"Errore nell'invio della richiesta AI:\n{str(e)}")
            # Riabilita il pulsante in caso di errore
            if hasattr(self, 'rephrase_button'):
                self.rephrase_button.setEnabled(True)
                self.rephrase_button.setText("🧠 Riformula intensamente")

    def handle_media_button(self):
        """Gestisce il caricamento di file multimediali (audio/video)."""
        try:
            # Apri dialog per selezionare file
            file_dialog = QFileDialog(self)
            file_dialog.setWindowTitle("Seleziona file multimediale")
            file_dialog.setNameFilter("File multimediali (*.mp3 *.wav *.mp4 *.avi *.mkv *.mov);;Audio (*.mp3 *.wav);;Video (*.mp4 *.avi *.mkv *.mov);;Tutti i file (*)")

            if file_dialog.exec() == QFileDialog.DialogCode.Accepted:
                selected_files = file_dialog.selectedFiles()
                if selected_files:
                    file_path = selected_files[0]
                    self.process_media_file(file_path)

        except Exception as e:
            logging.error(f"Errore caricamento file multimediale: {e}")
            QMessageBox.critical(self, "Errore", f"Errore durante il caricamento del file:\n{str(e)}")

    def process_media_file(self, file_path):
        """Elabora il file multimediale selezionato."""
        import os
        from pathlib import Path

        file_name = os.path.basename(file_path)
        file_ext = Path(file_path).suffix.lower()

        # Determina il tipo di file
        audio_extensions = ['.mp3', '.wav', '.flac', '.aac', '.ogg']
        video_extensions = ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv']

        if file_ext in audio_extensions:
            self.create_audio_widget(file_path, file_name)
        elif file_ext in video_extensions:
            self.create_video_widget(file_path, file_name)
        else:
            # File generico - mostra icona semplice
            self.create_generic_media_widget(file_path, file_name)

    def create_audio_widget(self, file_path, file_name):
        """Crea un widget per file audio con controlli multimediali."""
        try:
            if not MULTIMEDIA_AVAILABLE:
                raise ImportError("Funzionalità multimediali non disponibili")

            from PyQt6.QtCore import QUrl

            # Crea widget contenitore
            audio_widget = QWidget()
            audio_layout = QVBoxLayout(audio_widget)

            # Header con nome file e icona
            header_layout = QHBoxLayout()
            header_layout.addWidget(QLabel(f"🎵 {file_name}"))
            header_layout.addStretch()
            audio_layout.addLayout(header_layout)

            # Controlli multimediali
            controls_layout = QHBoxLayout()

            # Pulsanti play/pausa/stop
            self.play_button = QPushButton("▶️ Play")
            self.play_button.clicked.connect(lambda: self.toggle_audio_playback(file_path))
            controls_layout.addWidget(self.play_button)

            self.pause_button = QPushButton("⏸️ Pausa")
            self.pause_button.clicked.connect(self.pause_audio)
            controls_layout.addWidget(self.pause_button)

            self.stop_button = QPushButton("⏹️ Stop")
            self.stop_button.clicked.connect(self.stop_audio)
            controls_layout.addWidget(self.stop_button)

            # Slider per posizione
            self.position_slider = QSlider(Qt.Orientation.Horizontal)
            self.position_slider.setRange(0, 100)
            controls_layout.addWidget(self.position_slider)

            # Etichetta durata
            self.duration_label = QLabel("00:00 / 00:00")
            controls_layout.addWidget(self.duration_label)

            # Inizializza variabili per controlli
            self.current_position = 0
            self.total_duration = 0

            audio_layout.addLayout(controls_layout)

            # Placeholder per analizzatore spettro (implementazione futura)
            spectrum_label = QLabel("🎵 Analizzatore Spettro - In sviluppo")
            spectrum_label.setStyleSheet("color: #666; font-style: italic; padding: 10px;")
            audio_layout.addWidget(spectrum_label)

            # Inizializza media player
            self.media_player = QMediaPlayer()
            self.audio_output = QAudioOutput()
            self.media_player.setAudioOutput(self.audio_output)
            self.media_player.setSource(QUrl.fromLocalFile(file_path))

            # Connetti segnali
            self.media_player.positionChanged.connect(self.update_position)
            self.media_player.durationChanged.connect(self.update_duration)
            self.position_slider.sliderMoved.connect(self.set_position)

            # Aggiungi alla colonna pensierini
            if DraggableTextWidget:
                # Crea un wrapper per rendere trascinabile
                wrapper_widget = DraggableTextWidget(f"🎵 Audio: {file_name}", self.settings)
                # Sostituisci il contenuto con il widget audio
                wrapper_layout = QVBoxLayout(wrapper_widget)
                wrapper_layout.addWidget(audio_widget)
                self.pensierini_layout.addWidget(wrapper_widget)

            QMessageBox.information(self, "File Audio Caricato",
                                  f"✅ File audio '{file_name}' caricato con successo!\n\n"
                                  f"🎵 Controlli multimediali disponibili\n"
                                  f"📊 Analizzatore spettro in sviluppo")

        except ImportError as e:
            QMessageBox.warning(self, "Funzionalità Limitata",
                              f"Alcune funzionalità audio potrebbero non essere disponibili:\n{str(e)}\n\n"
                              f"Il file è stato comunque aggiunto come elemento generico.")
            self.create_generic_media_widget(file_path, file_name)

    def create_video_widget(self, file_path, file_name):
        """Crea un widget semplice per file video."""
        try:
            # Crea widget semplice con icona video
            video_widget = QWidget()
            video_layout = QVBoxLayout(video_widget)

            # Icona e nome file
            icon_label = QLabel("🎥")
            icon_label.setStyleSheet("font-size: 48px; color: #dc3545;")
            video_layout.addWidget(icon_label, alignment=Qt.AlignmentFlag.AlignCenter)

            name_label = QLabel(file_name)
            name_label.setStyleSheet("font-weight: bold; color: #333;")
            video_layout.addWidget(name_label, alignment=Qt.AlignmentFlag.AlignCenter)

            # Nota che è un video
            type_label = QLabel("(File Video)")
            type_label.setStyleSheet("color: #666; font-style: italic;")
            video_layout.addWidget(type_label, alignment=Qt.AlignmentFlag.AlignCenter)

            # Aggiungi alla colonna pensierini
            if DraggableTextWidget:
                wrapper_widget = DraggableTextWidget(f"🎥 Video: {file_name}", self.settings)
                wrapper_layout = QVBoxLayout(wrapper_widget)
                wrapper_layout.addWidget(video_widget)
                self.pensierini_layout.addWidget(wrapper_widget)

            QMessageBox.information(self, "File Video Caricato",
                                  f"✅ File video '{file_name}' caricato con successo!")

        except Exception as e:
            logging.error(f"Errore creazione widget video: {e}")
            self.create_generic_media_widget(file_path, file_name)

    def create_generic_media_widget(self, file_path, file_name):
        """Crea un widget generico per file non riconosciuti."""
        try:
            # Crea widget semplice con icona file
            generic_widget = QWidget()
            generic_layout = QVBoxLayout(generic_widget)

            # Icona file generica
            icon_label = QLabel("📄")
            icon_label.setStyleSheet("font-size: 48px; color: #6c757d;")
            generic_layout.addWidget(icon_label, alignment=Qt.AlignmentFlag.AlignCenter)

            name_label = QLabel(file_name)
            name_label.setStyleSheet("font-weight: bold; color: #333;")
            generic_layout.addWidget(name_label, alignment=Qt.AlignmentFlag.AlignCenter)

            # Aggiungi alla colonna pensierini
            if DraggableTextWidget:
                wrapper_widget = DraggableTextWidget(f"📄 File: {file_name}", self.settings)
                wrapper_layout = QVBoxLayout(wrapper_widget)
                wrapper_layout.addWidget(generic_widget)
                self.pensierini_layout.addWidget(wrapper_widget)

            QMessageBox.information(self, "File Caricato",
                                  f"✅ File '{file_name}' caricato con successo!")

        except Exception as e:
            logging.error(f"Errore creazione widget generico: {e}")
            QMessageBox.critical(self, "Errore", f"Errore durante la creazione del widget:\n{str(e)}")

    def handle_ocr_button(self):
        """Gestisce la trascrizione OCR da documenti."""
        try:
            if not OCR_AVAILABLE:
                QMessageBox.warning(self, "OCR Non Disponibile",
                                  "La funzionalità OCR richiede pytesseract e PIL.\n\n"
                                  "Installa con: pip install pytesseract pillow\n\n"
                                  "Inoltre assicurati che Tesseract-OCR sia installato sul sistema.")
                return

            # Apri dialog per selezionare immagine/documento
            file_dialog = QFileDialog(self)
            file_dialog.setWindowTitle("Seleziona documento per OCR")
            file_dialog.setNameFilter("Immagini e documenti (*.png *.jpg *.jpeg *.bmp *.tiff *.pdf);;Immagini (*.png *.jpg *.jpeg *.bmp *.tiff);;PDF (*.pdf);;Tutti i file (*)")

            if file_dialog.exec() == QFileDialog.DialogCode.Accepted:
                selected_files = file_dialog.selectedFiles()
                if selected_files:
                    file_path = selected_files[0]
                    self.process_ocr_file(file_path)

        except Exception as e:
            logging.error(f"Errore caricamento file OCR: {e}")
            QMessageBox.critical(self, "Errore", f"Errore durante il caricamento del file:\n{str(e)}")

    def process_ocr_file(self, file_path):
        """Elabora il file per l'OCR."""
        import os
        from pathlib import Path

        file_name = os.path.basename(file_path)
        file_ext = Path(file_path).suffix.lower()

        try:
            # Mostra progresso
            progress_msg = QMessageBox(self)
            progress_msg.setWindowTitle("OCR in corso")
            progress_msg.setText("🔍 Elaborazione OCR in corso...")
            progress_msg.setStandardButtons(QMessageBox.StandardButton.Cancel)
            progress_msg.show()

            # Esegui OCR
            if file_ext.lower() == '.pdf':
                # Per PDF, dovremmo estrarre le immagini prima
                text = self.extract_text_from_pdf(file_path)
            else:
                # Per immagini
                text = self.extract_text_from_image(file_path)

            progress_msg.close()

            if text and text.strip():
                # Mostra il testo estratto nei dettagli
                ocr_content = f"📄 OCR - Trascrizione da: {file_name}\n\n{'='*50}\n\n{text}\n\n{'='*50}\n\n📊 Statistiche OCR:\n• Caratteri estratti: {len(text)}\n• Parole: {len(text.split())}\n• Righe: {len(text.split(chr(10)))}"
                self.show_text_in_details(ocr_content)

                # Crea anche un pensierino con il testo estratto
                if DraggableTextWidget:
                    ocr_pensierino_text = f"📄 OCR: {file_name[:30]}... ({len(text)} caratteri)"
                    pensierino_widget = DraggableTextWidget(ocr_pensierino_text, self.settings)
                    self.pensierini_layout.addWidget(pensierino_widget)

                QMessageBox.information(self, "OCR Completato",
                                      f"✅ Testo estratto con successo!\n\n"
                                      f"📄 File: {file_name}\n"
                                      f"📝 Caratteri: {len(text)}\n"
                                      f"📊 Parole: {len(text.split())}")
            else:
                QMessageBox.warning(self, "OCR Fallito",
                                  "Nessun testo rilevato nel documento.\n\n"
                                  "Possibili cause:\n"
                                  "• Immagine di bassa qualità\n"
                                  "• Testo non chiaramente leggibile\n"
                                  "• Orientamento del documento\n"
                                  "• Carattere non supportato")

        except Exception as e:
            if 'progress_msg' in locals():
                progress_msg.close()
            logging.error(f"Errore OCR: {e}")
            QMessageBox.critical(self, "Errore OCR", f"Errore durante l'elaborazione OCR:\n{str(e)}")

    def extract_text_from_image(self, image_path):
        """Estrae testo da un'immagine usando pytesseract."""
        try:
            # Apri l'immagine
            image = Image.open(image_path)

            # Configurazione OCR ottimale
            custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyzàèéìòùÀÈÉÌÒÙ .,!?-()[]{}:;"\'\n'

            # Esegui OCR
            text = pytesseract.image_to_string(image, lang='ita+eng', config=custom_config)

            return text.strip()

        except Exception as e:
            logging.error(f"Errore estrazione testo da immagine: {e}")
            raise

    def extract_text_from_pdf(self, pdf_path):
        """Estrae testo da un PDF (placeholder per implementazione futura)."""
        # Per ora restituiamo un messaggio che OCR su PDF non è ancora implementato
        return "📄 OCR per PDF non ancora implementato.\n\n" \
               "Converti prima il PDF in immagini per utilizzare l'OCR.\n\n" \
               "Funzionalità futura: estrazione automatica immagini da PDF."

    def handle_face_recognition(self):
        """Gestisce il toggle per il riconoscimento facciale."""
        try:
            if self.face_button.isChecked():
                # Abilita riconoscimento facciale
                self.face_button.setText("✅ Riconoscimento Faciale")
                QMessageBox.information(self, "Funzione in Sviluppo",
                                      "🔧 Riconoscimento Faciale\n\n"
                                      "📋 Stato: ABILITATO\n\n"
                                      "⚠️ In Manutenzione - WIP Work in progress\n\n"
                                      "Questa funzione sarà disponibile nelle prossime versioni.")
            else:
                # Disabilita riconoscimento facciale
                self.face_button.setText("❌ Riconoscimento Faciale")
                QMessageBox.information(self, "Funzione Disabilitata",
                                      "🔧 Riconoscimento Faciale\n\n"
                                      "📋 Stato: DISABILITATO\n\n"
                                      "La funzione è stata disabilitata.")

        except Exception as e:
            logging.error(f"Errore toggle riconoscimento facciale: {e}")
            QMessageBox.critical(self, "Errore", f"Errore durante la gestione del riconoscimento facciale:\n{str(e)}")

    def handle_hand_gestures(self):
        """Gestisce il toggle per il riconoscimento gesti mani."""
        try:
            if self.hand_button.isChecked():
                # Abilita riconoscimento gesti mani
                self.hand_button.setText("✅ Abilita Gesti Mani")
                QMessageBox.information(self, "Funzione in Sviluppo",
                                      "🔧 Riconoscimento Gesti Mani\n\n"
                                      "📋 Stato: ABILITATO\n\n"
                                      "⚠️ In Manutenzione - WIP Work in progress\n\n"
                                      "Questa funzione sarà disponibile nelle prossime versioni.")
            else:
                # Disabilita riconoscimento gesti mani
                self.hand_button.setText("❌ Abilita Gesti Mani")
                QMessageBox.information(self, "Funzione Disabilitata",
                                      "🔧 Riconoscimento Gesti Mani\n\n"
                                      "📋 Stato: DISABILITATO\n\n"
                                      "La funzione è stata disabilitata.")

        except Exception as e:
            logging.error(f"Errore toggle riconoscimento gesti mani: {e}")
            QMessageBox.critical(self, "Errore", f"Errore durante la gestione del riconoscimento gesti mani:\n{str(e)}")

    def handle_log_toggle(self):
        """Gestisce il toggle per visualizzare errori e warning dal log."""
        try:
            if self.log_button.isChecked():
                # Attiva visualizzazione log - apri finestra
                self.show_log_window()
                self.log_button.setText("📋 Log ON")
            else:
                # Disattiva visualizzazione log - chiudi finestra
                self.hide_log_window()
                self.log_button.setText("📋 Log")

        except Exception as e:
            logging.error(f"Errore toggle log: {e}")
            QMessageBox.critical(self, "Errore Log", f"Errore durante la gestione del log:\n{str(e)}")

    def show_log_window(self):
        """Mostra una finestra separata con errori e warning dal log."""
        try:
            # Crea finestra log se non esiste
            if not hasattr(self, 'log_window') or self.log_window is None:
                self.log_window = QWidget()
                self.log_window.setWindowTitle("📋 Log Errori e Warning")
                self.log_window.setFixedSize(600, 400)
                self.log_window.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)

                # Layout finestra
                layout = QVBoxLayout(self.log_window)

                # Titolo
                title = QLabel("📋 Monitor Log - Errori e Warning")
                title.setStyleSheet("font-size: 14px; font-weight: bold; margin-bottom: 10px;")
                layout.addWidget(title)

                # Area testo per il log
                self.log_text_area = QTextEdit()
                self.log_text_area.setReadOnly(True)
                self.log_text_area.setStyleSheet("""
                    QTextEdit {
                        background-color: #f8f9fa;
                        border: 1px solid #dee2e6;
                        border-radius: 4px;
                        font-family: monospace;
                        font-size: 10px;
                        line-height: 1.3;
                    }
                """)
                layout.addWidget(self.log_text_area)

                # Pulsanti
                buttons_layout = QHBoxLayout()
                buttons_layout.addStretch()

                refresh_button = QPushButton("🔄 Aggiorna")
                refresh_button.clicked.connect(self.refresh_log_content)
                buttons_layout.addWidget(refresh_button)

                clear_button = QPushButton("🧹 Pulisci Log")
                clear_button.clicked.connect(self.clear_log_file)
                buttons_layout.addWidget(clear_button)

                close_button = QPushButton("❌ Chiudi")
                close_button.clicked.connect(self.hide_log_window)
                buttons_layout.addWidget(close_button)

                layout.addLayout(buttons_layout)

            # Carica contenuto log
            self.refresh_log_content()

            # Mostra finestra
            self.log_window.show()

        except Exception as e:
            logging.error(f"Errore creazione finestra log: {e}")
            QMessageBox.critical(self, "Errore Finestra Log",
                               f"Errore durante la creazione della finestra log:\n{str(e)}")
            self.log_button.setChecked(False)

    def refresh_log_content(self):
        """Aggiorna il contenuto del log nella finestra."""
        try:
            if not hasattr(self, 'log_text_area'):
                return

            # Ottieni il percorso del file di log
            log_config = get_config()
            log_file = log_config.get_setting('files.log_file', 'Save/LOG/app.log')

            if not os.path.exists(log_file):
                self.log_text_area.setPlainText(f"📁 File log non trovato:\n{log_file}")
                return

            # Leggi il file di log
            with open(log_file, 'r', encoding='utf-8') as f:
                log_content = f.read()

            # Filtra solo errori e warning
            lines = log_content.split('\n')
            filtered_lines = []

            for line in lines:
                line_lower = line.lower()
                if ('error' in line_lower or
                    'warning' in line_lower or
                    'critical' in line_lower or
                    'exception' in line_lower):
                    filtered_lines.append(line)

            if not filtered_lines:
                display_text = f"📋 LOG ERRORI E WARNING\n\n" \
                              f"✅ Nessun errore o warning trovato nel log!\n\n" \
                              f"📁 File log: {log_file}\n" \
                              f"📊 Righe totali nel log: {len(lines)}\n" \
                              f"🔄 Ultimo aggiornamento: {datetime.now().strftime('%H:%M:%S')}"
            else:
                display_text = f"📋 LOG ERRORI E WARNING\n\n" \
                              f"🔍 Trovati {len(filtered_lines)} errori/warning:\n\n" \
                              f"{'='*60}\n\n" \
                              f"{chr(10).join(filtered_lines[-50:])}\n\n" \
                              f"{'='*60}\n\n" \
                              f"📁 File log: {log_file}\n" \
                              f"📊 Errori/warning totali: {len(filtered_lines)}\n" \
                              f"📈 Mostrati ultimi 50\n" \
                              f"🔄 Ultimo aggiornamento: {datetime.now().strftime('%H:%M:%S')}"

            self.log_text_area.setPlainText(display_text)

        except Exception as e:
            logging.error(f"Errore aggiornamento log: {e}")
            if hasattr(self, 'log_text_area'):
                self.log_text_area.setPlainText(f"❌ Errore lettura log:\n{str(e)}")

    def clear_log_file(self):
        """Pulisce il file di log."""
        try:
            reply = QMessageBox.question(self, "Conferma Pulizia Log",
                                       "Sei sicuro di voler pulire il file di log?\n\n"
                                       "Questa azione rimuoverà tutti gli errori e warning registrati.",
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

            if reply == QMessageBox.StandardButton.Yes:
                log_config = get_config()
                log_file = log_config.get_setting('files.log_file', 'Save/LOG/app.log')

                # Svuota il file di log
                with open(log_file, 'w', encoding='utf-8') as f:
                    f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] INFO Log pulito dall'utente\n")

                self.refresh_log_content()
                QMessageBox.information(self, "Log Pulito", "✅ File di log pulito con successo!")

        except Exception as e:
            logging.error(f"Errore pulizia log: {e}")
            QMessageBox.critical(self, "Errore Pulizia Log",
                               f"Errore durante la pulizia del log:\n{str(e)}")

    def hide_log_window(self):
        """Nasconde la finestra del log."""
        try:
            if hasattr(self, 'log_window') and self.log_window:
                self.log_window.hide()
                self.log_button.setChecked(False)
                self.log_button.setText("📋 Log")

        except Exception as e:
            logging.error(f"Errore nascondendo finestra log: {e}")

    def toggle_audio_playback(self, file_path):
        """Alterna play/pausa per l'audio."""
        if hasattr(self, 'media_player'):
            if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
                self.media_player.pause()
                self.play_button.setText("▶️ Play")
            else:
                self.media_player.play()
                self.play_button.setText("⏸️ Pausa")

    def pause_audio(self):
        """Mette in pausa l'audio."""
        if hasattr(self, 'media_player'):
            self.media_player.pause()
            if hasattr(self, 'play_button'):
                self.play_button.setText("▶️ Play")

    def stop_audio(self):
        """Ferma l'audio."""
        if hasattr(self, 'media_player'):
            self.media_player.stop()
            if hasattr(self, 'play_button'):
                self.play_button.setText("▶️ Play")

    def update_position(self, position):
        """Aggiorna la posizione del slider."""
        if hasattr(self, 'position_slider'):
            self.position_slider.setValue(position)

    def update_duration(self, duration):
        """Aggiorna la durata totale."""
        if hasattr(self, 'position_slider'):
            self.position_slider.setRange(0, duration)
        if hasattr(self, 'duration_label'):
            # Converti millisecondi in formato MM:SS
            total_seconds = duration // 1000
            minutes = total_seconds // 60
            seconds = total_seconds % 60
            self.duration_label.setText(f"00:00 / {minutes:02d}:{seconds:02d}")

    def set_position(self, position):
        """Imposta la posizione dell'audio."""
        if hasattr(self, 'media_player'):
            self.media_player.setPosition(position)

    def handle_clean_button(self):
        """Gestisce la pulizia di tutti i widget con conferma utente."""
        # Mostra finestra di conferma
        reply = QMessageBox.question(
            self,
            "Conferma Pulizia",
            "Sei sicuro di voler cancellare tutto?\n\n"
            "Questa azione rimuoverà tutti i pensierini e il contenuto dell'area di lavoro.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No  # Default: No
        )

        # Se l'utente non conferma, annulla l'operazione
        if reply != QMessageBox.StandardButton.Yes:
            return

        # Procedi con la pulizia
        try:
            while self.pensierini_layout.count():
                item = self.pensierini_layout.takeAt(0)
                if item:
                    try:
                        widget = item.widget()
                        if widget and hasattr(widget, 'deleteLater') and callable(getattr(widget, 'deleteLater', None)):
                            widget.deleteLater()
                    except (AttributeError, TypeError):
                        pass
            while self.work_area_layout.count():
                item = self.work_area_layout.takeAt(0)
                if item:
                    try:
                        widget = item.widget()
                        if widget and hasattr(widget, 'deleteLater') and callable(getattr(widget, 'deleteLater', None)):
                            widget.deleteLater()
                    except (AttributeError, TypeError):
                        pass
            logging.info("Area pulita")
        except Exception as e:
            logging.error(f"Errore pulizia area: {e}")

    def save_project(self):
        """Salva il progetto corrente (colonne 1 e 2)."""
        # Prevent multiple saves by disabling the button
        self.save_button.setEnabled(False)
        self.save_button.setText("💾 Salvataggio...")

        try:
            # Ottieni il nome del progetto
            project_name = self.project_name_input.text().strip()
            if not project_name:
                project_name = f"progetto_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            # Crea directory progetti se non esiste
            projects_dir = "Save/mia_dispenda_progetti"
            if not os.path.exists(projects_dir):
                os.makedirs(projects_dir, exist_ok=True)

            # Prepara dati da salvare
            project_data = {
                "metadata": {
                    "name": project_name,
                    "created": datetime.now().isoformat(),
                    "version": "1.0"
                },
                "pensierini": [],  # Colonna 1
                "workspace": []    # Colonna 2
            }

            # Salva pensierini dalla colonna 1
            for i in range(self.pensierini_layout.count()):
                item = self.pensierini_layout.itemAt(i)
                if item:
                    widget = item.widget()
                    if widget and hasattr(widget, 'text_label'):
                        text_label = getattr(widget, 'text_label', None)
                        if text_label and hasattr(text_label, 'text'):
                            text = text_label.text()
                            if text.strip():
                                project_data["pensierini"].append({
                                    "text": text,
                                    "order": i
                                })

            # Salva workspace dalla colonna 2
            for i in range(self.work_area_layout.count()):
                item = self.work_area_layout.itemAt(i)
                if item:
                    widget = item.widget()
                    if widget and hasattr(widget, 'text_label'):
                        text_label = getattr(widget, 'text_label', None)
                        if text_label and hasattr(text_label, 'text'):
                            text = text_label.text()
                            if text.strip():
                                project_data["workspace"].append({
                                    "text": text,
                                    "order": i
                                })

            # Salva file
            filename = f"{project_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            filepath = os.path.join(projects_dir, filename)

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(project_data, f, indent=2, ensure_ascii=False)

            QMessageBox.information(
                self, "Salvataggio Completato",
                f"Progetto '{project_name}' salvato con successo!\n\n"
                f"File: {filename}\n"
                f"Pensierini: {len(project_data['pensierini'])}\n"
                f"Workspace: {len(project_data['workspace'])}"
            )

            logging.info(f"Progetto salvato: {filepath}")

        except Exception as e:
            QMessageBox.critical(self, "Errore Salvataggio", f"Errore durante il salvataggio:\n{str(e)}")
            logging.error(f"Errore salvataggio progetto: {e}")
        finally:
            # Re-enable the button
            self.save_button.setEnabled(True)
            self.save_button.setText("💾 Salva")

    def load_project(self):
        """Carica un progetto salvato (colonne 1 e 2)."""
        try:
            # Crea directory progetti se non esiste
            projects_dir = "Save/mia_dispenda_progetti"
            if not os.path.exists(projects_dir):
                os.makedirs(projects_dir, exist_ok=True)
                QMessageBox.information(self, "Nessun Progetto", "Non ci sono progetti salvati.")
                return

            # Ottieni lista file progetti
            project_files = [f for f in os.listdir(projects_dir) if f.endswith('.json')]

            if not project_files:
                QMessageBox.information(self, "Nessun Progetto", "Non ci sono progetti salvati.")
                return

            # Crea dialog per selezione progetto
            from PyQt6.QtWidgets import QListWidget, QVBoxLayout, QDialog, QPushButton, QHBoxLayout

            dialog = QDialog(self)
            dialog.setWindowTitle("Seleziona Progetto da Caricare")
            dialog.resize(400, 300)

            layout = QVBoxLayout(dialog)

            # Lista progetti
            list_widget = QListWidget()
            for filename in sorted(project_files, reverse=True):
                try:
                    filepath = os.path.join(projects_dir, filename)
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    if data:
                        name = data.get('metadata', {}).get('name', filename)
                        created = data.get('metadata', {}).get('created', '')
                        pens_count = len(data.get('pensierini', []))
                        work_count = len(data.get('workspace', []))

                        display_text = f"{name} - {pens_count} pensierini, {work_count} workspace"
                        if created:
                            display_text += f" ({created[:19]})"

                        list_widget.addItem(display_text)
                        item = list_widget.item(list_widget.count() - 1)
                        if item and hasattr(item, 'setData'):
                            item.setData(Qt.ItemDataRole.UserRole, filepath)
                    else:
                        list_widget.addItem(filename)
                        item = list_widget.item(list_widget.count() - 1)
                        if item and hasattr(item, 'setData'):
                            item.setData(Qt.ItemDataRole.UserRole, os.path.join(projects_dir, filename))

                except Exception:
                    list_widget.addItem(filename)
                    item = list_widget.item(list_widget.count() - 1)
                    if item and hasattr(item, 'setData'):
                        item.setData(Qt.ItemDataRole.UserRole, os.path.join(projects_dir, filename))

            layout.addWidget(list_widget)

            # Pulsanti
            buttons_layout = QHBoxLayout()
            buttons_layout.addStretch()

            load_button = QPushButton("Carica")
            load_button.clicked.connect(dialog.accept)
            buttons_layout.addWidget(load_button)

            cancel_button = QPushButton("Annulla")
            cancel_button.clicked.connect(dialog.reject)
            buttons_layout.addWidget(cancel_button)

            layout.addLayout(buttons_layout)

            if dialog.exec() == QDialog.DialogCode.Accepted and list_widget.currentItem():
                current_item = list_widget.currentItem()
                if current_item and hasattr(current_item, 'data'):
                    selected_file = current_item.data(Qt.ItemDataRole.UserRole)
                else:
                    selected_file = None

                if selected_file:
                    # Conferma caricamento
                    reply = QMessageBox.question(
                        self, "Conferma Caricamento",
                        "Caricare questo progetto? I dati attuali verranno sostituiti.",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                    )

                    if reply == QMessageBox.StandardButton.Yes:
                        self._load_project_from_file(selected_file)
                else:
                    QMessageBox.warning(self, "Selezione Non Valida", "Seleziona un progetto valido da caricare.")

        except Exception as e:
            QMessageBox.critical(self, "Errore Caricamento", f"Errore durante il caricamento:\n{str(e)}")
            logging.error(f"Errore caricamento progetto: {e}")

    def _load_project_from_file(self, filepath):
        """Carica progetto da file specifico."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                project_data = json.load(f)

            if not project_data:
                raise ValueError("File progetto vuoto o corrotto")

            # Imposta nome progetto
            project_name = project_data.get('metadata', {}).get('name', 'Progetto Caricato')
            self.project_name_input.setText(project_name)

            # Pulisci colonne esistenti
            self._clear_columns()

            # Carica pensierini (colonna 1)
            pensierini_data = project_data.get('pensierini', [])
            for pensierino in pensierini_data:
                if isinstance(pensierino, dict):
                    text = pensierino.get('text', '')
                    if text.strip() and DraggableTextWidget:
                        widget = DraggableTextWidget(text, self.settings)
                        self.pensierini_layout.addWidget(widget)

            # Carica workspace (colonna 2)
            workspace_data = project_data.get('workspace', [])
            for work_item in workspace_data:
                if isinstance(work_item, dict):
                    text = work_item.get('text', '')
                    if text.strip() and DraggableTextWidget:
                        widget = DraggableTextWidget(text, self.settings)
                        self.work_area_layout.addWidget(widget)

            QMessageBox.information(
                self, "Caricamento Completato",
                f"Progetto '{project_name}' caricato con successo!\n\n"
                f"Pensierini: {len(pensierini_data)}\n"
                f"Workspace: {len(workspace_data)}"
            )

            logging.info(f"Progetto caricato: {filepath}")

        except Exception as e:
            QMessageBox.critical(self, "Errore Caricamento", f"Errore durante il caricamento del file:\n{str(e)}")
            logging.error(f"Errore caricamento file progetto: {e}")

    def _clear_columns(self):
        """Pulisce entrambe le colonne prima del caricamento."""
        try:
            # Pulisci colonna 1 (pensierini)
            while self.pensierini_layout.count():
                item = self.pensierini_layout.takeAt(0)
                if item:
                    widget = item.widget()
                    if widget and hasattr(widget, 'deleteLater') and callable(getattr(widget, 'deleteLater', None)):
                        widget.deleteLater()

            # Pulisci colonna 2 (workspace)
            while self.work_area_layout.count():
                item = self.work_area_layout.takeAt(0)
                if item:
                    widget = item.widget()
                    if widget and hasattr(widget, 'deleteLater') and callable(getattr(widget, 'deleteLater', None)):
                        widget.deleteLater()

            logging.info("Colonne pulite per caricamento progetto")

        except Exception as e:
            logging.error(f"Errore pulizia colonne: {e}")

    def open_settings(self):
        """Apre il dialog delle impostazioni."""
        if SettingsDialog is None:
            QMessageBox.critical(self, "Errore", "Modulo impostazioni non disponibile")
            return

        try:
            dialog = SettingsDialog(self)
            dialog.exec()
        except Exception as e:
            QMessageBox.critical(self, "Errore", f"Errore nell'apertura delle impostazioni: {e}")

def setup_logging():
    """Configura il sistema di logging."""
    log_config = get_config()
    log_file = log_config.get_setting('files.log_file', 'Save/LOG/app.log')

    # Assicura che la directory dei log esista
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )

def test_imports():
    """Test degli import critici."""
    print("🔍 Test degli import per Aircraft...")

    try:
        # Test import configurazione
        config = get_config()
        settings = load_settings()
        print(f"✓ Sistema configurazione caricato - Tema: {settings['application']['theme']}")

        # Test classe MainWindow (ora integrata in questo file)
        print("✓ Classe MainWindow disponibile")

        # Test import widget trascinabile
        from UI.draggable_text_widget import DraggableTextWidget
        print("✓ Modulo widget trascinabile importato")

        return True

    except ImportError as e:
        print(f"❌ Errore import: {e}")
        return False
    except Exception as e:
        print(f"❌ Errore generale: {e}")
        return False

def main():
    """Funzione principale per avviare la schermata aircraft."""
    print("✈️ Avvio Aircraft - Schermata principale...")

    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)

    # Test degli import
    if not test_imports():
        print("❌ Impossibile avviare Aircraft a causa di errori di import")
        sys.exit(1)

    try:
        # Carica configurazione
        config = get_config()
        settings = load_settings()

        # Crea applicazione Qt
        app = QApplication(sys.argv)
        app.setApplicationName(settings['application']['app_name'])
        app.setOrganizationName("DSA Aircraft")

        # Imposta icona se disponibile
        icon_path = "ICO-fonts-wallpaper/ICONA.ico"
        if os.path.exists(icon_path):
            from PyQt6.QtGui import QIcon
            app.setWindowIcon(QIcon(icon_path))
            logger.info(f"Icona caricata: {icon_path}")

        # Crea e mostra finestra principale (Aircraft)
        window = MainWindow()
        window.show()

        logger.info("✓ Aircraft avviata con successo")
        print("✅ Aircraft - Schermata principale avviata!")

        # Avvia event loop
        sys.exit(app.exec())

    except Exception as e:
        logger.error(f"Errore avvio Aircraft: {e}")
        print(f"❌ Errore avvio Aircraft: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()