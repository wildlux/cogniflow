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
    QScrollArea, QMessageBox, QFileDialog
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
            # Mostra richiesta e risposta nei dettagli con paginazione
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

            /* Colonna C - Dettagli (Rosso) */
            QGroupBox#details {
                border-color: #dc3545;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(220, 53, 69, 0.1), stop:1 rgba(220, 53, 69, 0.05));
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
                background-color: #6f42c1;
                min-width: 130px;
            }

            QPushButton#voice_button:hover {
                background-color: #5a359a;
            }

            /* Pulsante Pulisci */
            QPushButton#clean_button {
                background-color: #dc3545;
                min-width: 130px;
            }

            QPushButton#clean_button:hover {
                background-color: #c82333;
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

        # Main content
        content_layout = QHBoxLayout()

        # Column A: Pensierini
        self.column_a_group = QGroupBox("📝 Pensierini")
        self.column_a_group.setObjectName("pensierini")  # ID per CSS
        column_a_layout = QVBoxLayout(self.column_a_group)
        self.pensierini_scroll = QScrollArea()
        self.pensierini_scroll.setWidgetResizable(True)
        self.pensierini_widget = QWidget()
        self.pensierini_layout = QVBoxLayout(self.pensierini_widget)
        self.pensierini_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.pensierini_scroll.setWidget(self.pensierini_widget)
        column_a_layout.addWidget(self.pensierini_scroll)
        content_layout.addWidget(self.column_a_group, 3)

        # Column B: Work Area
        self.column_b_group = QGroupBox("📋 Area di Lavoro")
        self.column_b_group.setObjectName("work_area")  # ID per CSS
        column_b_layout = QVBoxLayout(self.column_b_group)
        self.setup_work_area(column_b_layout)
        content_layout.addWidget(self.column_b_group, 4)

        # Column C: Details
        self.column_c_group = QGroupBox("🔍 Dettagli")
        self.column_c_group.setObjectName("details")  # ID per CSS
        column_c_layout = QVBoxLayout(self.column_c_group)
        self.details_scroll = QScrollArea()
        self.details_scroll.setWidgetResizable(True)
        self.details_widget = QWidget()
        self.details_layout = QVBoxLayout(self.details_widget)
        self.details_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.details_scroll.setWidget(self.details_widget)
        column_c_layout.addWidget(self.details_scroll)
        content_layout.addWidget(self.column_c_group, 3)

        main_layout.addLayout(content_layout, 1)

        # Bottom tools
        tools_group = QGroupBox("🔧 Strumenti")
        tools_group.setObjectName("tools")  # ID per CSS
        tools_layout = QVBoxLayout(tools_group)

        self.input_text_area = QTextEdit()
        self.input_text_area.setPlaceholderText("Scrivi qui...")
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

        self.clean_button = QPushButton("🧹 Pulisci")
        self.clean_button.setObjectName("clean_button")  # ID per CSS
        self.clean_button.clicked.connect(self.handle_clean_button)
        buttons_layout.addWidget(self.clean_button)

        buttons_layout.addStretch()
        tools_layout.addLayout(buttons_layout)
        main_layout.addWidget(tools_group)

    def setup_work_area(self, layout):
        self.work_area_scroll = QScrollArea()
        self.work_area_scroll.setWidgetResizable(True)
        self.work_area_widget = QWidget()
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
        self.details_text_label.setStyleSheet("""
            QTextEdit {
                background: rgba(255, 255, 255, 0.9);
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 10px;
                font-size: 14px;
                line-height: 1.4;
                color: #333;
            }
        """)

        # Pulsante per tornare indietro
        self.back_button = QPushButton("⬅️ Pagina precedente")
        self.back_button.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: bold;
                min-height: 35px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
            QPushButton:disabled {
                background-color: #adb5bd;
                color: #6c757d;
            }
        """)
        self.back_button.clicked.connect(self.show_prev_page)

        # Pulsante per andare avanti
        self.forward_button = QPushButton("➡️ Prossima pagina")
        self.forward_button.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: bold;
                min-height: 35px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:disabled {
                background-color: #adb5bd;
                color: #6c757d;
            }
        """)
        self.forward_button.clicked.connect(self.show_next_page)

        # Layout per controlli
        controls_layout = QHBoxLayout()

        # Pulsante indietro
        controls_layout.addWidget(self.back_button)

        controls_layout.addStretch()

        # Centro: etichetta pagina corrente
        self.page_info_label = QLabel("Pagina 1")
        self.page_info_label.setStyleSheet("""
            QLabel {
                color: #495057;
                font-weight: bold;
                font-size: 14px;
                padding: 0 15px;
                background: rgba(255, 255, 255, 0.8);
                border-radius: 6px;
                min-width: 80px;
                text-align: center;
            }
        """)
        controls_layout.addWidget(self.page_info_label)

        controls_layout.addStretch()

        # Pulsante avanti
        controls_layout.addWidget(self.forward_button)

        layout.addWidget(self.details_text_label)
        layout.addLayout(controls_layout)

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

        # Aggiorna etichetta pagina corrente
        current_page_num = self.current_page + 1
        self.page_info_label.setText(f"Pagina {current_page_num}")

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

    def show_prev_page(self):
        """Mostra la pagina precedente del testo."""
        if self.current_page > 0:
            self.current_page -= 1
            self.update_page_display()

    def show_next_page(self):
        """Mostra la pagina successiva del testo o torna all'inizio."""
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
        else:
            # Ritorna all'inizio
            self.current_page = 0
        self.update_page_display()

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
                        if widget and hasattr(widget, 'deleteLater'):
                            widget.deleteLater()
                    except (AttributeError, TypeError):
                        pass
            while self.work_area_layout.count():
                item = self.work_area_layout.takeAt(0)
                if item:
                    try:
                        widget = item.widget()
                        if widget and hasattr(widget, 'deleteLater'):
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