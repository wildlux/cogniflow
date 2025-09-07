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
from PyQt6.QtGui import QFontDatabase
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel,
    QPushButton, QHBoxLayout, QLineEdit, QTextEdit, QGroupBox,
    QScrollArea, QMessageBox, QFileDialog, QSlider, QDialog, QSplitter, QGridLayout, QFrame
)

# Import TTS per la pronuncia IPA
try:
    from Artificial_Intelligence.Sintesi_Vocale.managers.tts_manager import TTSThread
    TTS_AVAILABLE = True
except ImportError:
    TTSThread = None
    TTS_AVAILABLE = False
    logging.warning("Sistema TTS non disponibile - funzionalità di pronuncia IPA limitata")

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
        AudioFileTranscriptionThread,
        ensure_vosk_model_available
    )
except ImportError:
    SpeechRecognitionThread = None
    AudioFileTranscriptionThread = None
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

        # Inizializza il layout per il widget
        self.widget_layout = QVBoxLayout(self)
        self.widget_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.setLayout(self.widget_layout)

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
                self.widget_layout.addWidget(widget)
                event.acceptProposedAction()

        except Exception as e:
            logging.error(f"Errore durante il drop nell'area di lavoro: {e}")


# Classe per gestire l'area pensierini con controllo duplicati
class PensieriniWidget(QWidget):
    def __init__(self, settings, pensierini_layout):
        super().__init__()
        self.settings = settings
        self.pensierini_layout = pensierini_layout  # Inizialmente None, sarà impostato dopo
        self.setAcceptDrops(True)

        # Il layout sarà impostato esternamente, non creare automaticamente

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

        # Variabili di stato per il footer
        self.tutor_session_active = False  # Stato sessione tutor
        self.screen_sharing_active = False  # Stato condivisione schermo

        # Variabili di stato per l'interfaccia
        self.tools_expanded = True  # Stato espansione dei sottogruppi

        # Inizializza il bridge Ollama per l'integrazione AI
        self.ollama_bridge = OllamaBridge() if OllamaBridge else None
        if self.ollama_bridge:
            self.ollama_bridge.responseReceived.connect(self._on_ai_response_received)
            self.ollama_bridge.errorOccurred.connect(self._on_ai_error_occurred)
            logging.info("Bridge Ollama inizializzato con successo")
        else:
            logging.warning("Bridge Ollama non disponibile - funzionalità AI limitata")

        # Carica il font OpenDyslexic per la dislessia
        self.load_dyslexic_font()

        self.setup_ui()

        # Tools panel always visible

        # Timer per aggiornare lo status del footer ogni minuto
        from PyQt6.QtCore import QTimer
        self.footer_timer = QTimer()
        self.footer_timer.timeout.connect(self.update_footer_status)
        self.footer_timer.start(60000)  # Aggiorna ogni 60 secondi

        logging.info("Applicazione avviata")

    def load_dyslexic_font(self):
        """Carica il font OpenDyslexic per la dislessia."""
        try:
            # Percorso del font OpenDyslexic
            font_path = os.path.join(os.path.dirname(__file__), "ICO-fonts-wallpaper", "OpenDyslexic-Regular.otf")

            if os.path.exists(font_path):
                # Carica il font nell'applicazione
                font_id = QFontDatabase.addApplicationFont(font_path)
                if font_id != -1:
                    # Ottieni il nome del font caricato
                    font_families = QFontDatabase.applicationFontFamilies(font_id)
                    if font_families:
                        loaded_font_name = font_families[0]
                        logging.info(f"✅ Font OpenDyslexic caricato con successo: {loaded_font_name}")
                        print(f"🎨 Font per dislessia caricato: {loaded_font_name}")
                        print(f"📖 Font disponibile per la lettura facilitata: {loaded_font_name}")
                    else:
                        logging.warning("⚠️ Font OpenDyslexic caricato ma nome non disponibile")
                else:
                    logging.error("❌ Errore nel caricamento del font OpenDyslexic")
            else:
                logging.warning(f"⚠️ File font OpenDyslexic non trovato: {font_path}")

        except Exception as e:
            logging.error(f"❌ Errore caricamento font OpenDyslexic: {e}")

        # Stato fullscreen
        self.is_fullscreen = False
        self.original_width = 0   # Per salvare la larghezza originale
        self.original_height = 0  # Per salvare l'altezza originale
        self.original_x = 0       # Per salvare la posizione X originale
        self.original_y = 0       # Per salvare la posizione Y originale

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

    def update_footer_status(self):
        """Aggiorna le informazioni di stato nel footer."""
        try:
            from datetime import datetime
            current_time = datetime.now().strftime("%H:%M:%S")
            status_text = f"🕐 {current_time} | 👤 Sessione attiva | 📊 Sistema operativo"
            self.status_footer_label.setText(status_text)
        except Exception as e:
            logging.error(f"Errore nell'aggiornamento del footer: {e}")
            self.status_footer_label.setText("📊 Stato: Sistema attivo")

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

             /* Sottogruppi nella barra strumenti - Migliorata leggibilità */
             QGroupBox#transcription_subgroup {
                 border-color: #17a2b8;
                 background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                     stop:0 rgba(248, 249, 250, 0.95), stop:1 rgba(241, 243, 244, 0.98));
                 margin-top: 5px;
                 padding-top: 5px;
                 color: #2c3e50;
             }

             QGroupBox#ai_media_subgroup {
                 border-color: #28a745;
                 background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                     stop:0 rgba(248, 249, 250, 0.95), stop:1 rgba(241, 243, 244, 0.98));
                 margin-top: 5px;
                 padding-top: 5px;
                 color: #2c3e50;
             }

             QGroupBox#recognition_subgroup {
                 border-color: #20b2aa;
                 background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                     stop:0 rgba(248, 249, 250, 0.95), stop:1 rgba(241, 243, 244, 0.98));
                 margin-top: 3px;
                 padding-top: 3px;
                 font-size: 13px;
                 color: #2c3e50;
             }

             QGroupBox#recognition_subgroup::title {
                 color: #155724;
                 font-weight: bold;
                 font-size: 12px;
             }

             QGroupBox#utilities_subgroup {
                 border-color: #ffc107;
                 background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                     stop:0 rgba(248, 249, 250, 0.95), stop:1 rgba(241, 243, 244, 0.98));
                 margin-top: 5px;
                 padding-top: 5px;
                 color: #2c3e50;
             }

             QGroupBox#knowledge_subgroup {
                 border-color: #20b2aa;
                 background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                     stop:0 rgba(248, 249, 250, 0.95), stop:1 rgba(241, 243, 244, 0.98));
                 margin-top: 5px;
                 padding-top: 5px;
                 color: #2c3e50;
             }

             QGroupBox#iot_subgroup {
                 border-color: #6f42c1;
                 background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                     stop:0 rgba(248, 249, 250, 0.95), stop:1 rgba(241, 243, 244, 0.98));
                 margin-top: 5px;
                 padding-top: 5px;
                 color: #2c3e50;
             }

            QPushButton {
                background-color: #4a90e2;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: bold;
                min-width: 120px;
                min-height: 32px;
                font-size: 13px;
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
                color: black;
                min-width: 130px;
            }

            QPushButton#ai_button:hover {
                background-color: #218838;
            }

            /* Pulsante Voce */
            QPushButton#voice_button {
                background-color: #9c27b0;
                color: black;
                min-width: 130px;
            }

            QPushButton#voice_button:hover {
                background-color: #7b1fa2;
            }

             /* Pulsante Media */
             QPushButton#media_button {
                 background-color: #17a2b8;
                 color: black;
                 min-width: 130px;
             }

             QPushButton#media_button:hover {
                 background-color: #138496;
             }

             /* Pulsante IPA */
             QPushButton#ipa_button {
                 background-color: #6f42c1;
                 color: white;
                 min-width: 80px;
             }

             QPushButton#ipa_button:hover {
                 background-color: #5a359a;
             }

             /* Pulsante OCR */
             QPushButton#ocr_button {
                 background-color: #28a745;
                 color: black;
                 min-width: 200px;
             }

             QPushButton#ocr_button:hover {
                 background-color: #218838;
             }

             /* Pulsante Trascrizione Audio */
             QPushButton#audio_transcription_button {
                 background-color: #17a2b8;
                 color: black;
                 min-width: 200px;
             }

             QPushButton#audio_transcription_button:hover {
                 background-color: #138496;
             }

            /* Pulsante Riconoscimento Faciale */
            QPushButton#face_button {
                background-color: #f8f9fa;
                color: #6c757d;
                border: 2px solid #dee2e6;
                border-radius: 6px;
                padding: 6px 10px;
                font-weight: bold;
                min-width: 180px;
                min-height: 30px;
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
                padding: 6px 10px;
                font-weight: bold;
                min-width: 150px;
                min-height: 30px;
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
                color: black;
                border: none;
                border-radius: 8px;
                padding: 12px 18px;
                font-weight: bold;
                font-size: 14px;
                min-width: 80px;
                min-height: 40px;
                text-align: center;
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
                color: black;
                min-width: 130px;
            }

            QPushButton#clean_button:hover {
                background-color: #c82333;
            }

            /* Pulsante Log Footer */
            QPushButton#footer_log_button {
                background-color: #6f42c1;
                color: black;
                border: none;
                border-radius: 8px;
                padding: 12px 18px;
                font-weight: bold;
                font-size: 14px;
                min-width: 80px;
                min-height: 40px;
                text-align: center;
            }

            QPushButton#footer_log_button:hover {
                background-color: #5a359a;
            }

            QPushButton#footer_log_button:checked {
                background-color: #e8590c;
                border: 2px solid #d0390c;
            }

            /* Pulsanti delle materie nella sezione conoscenza */
            QPushButton#ipa_button,
            QPushButton#math_button,
            QPushButton#chemistry_button,
            QPushButton#physics_button,
            QPushButton#biology_button,
            QPushButton#italian_button,
            QPushButton#history_button,
            QPushButton#computer_science_button,
            QPushButton#os_scripting_button,
            QPushButton#astronomy_button,
            QPushButton#advanced_math_button,
            QPushButton#law_button,
            QPushButton#probability_stats_button,
            QPushButton#english_button,
            QPushButton#german_button,
            QPushButton#spanish_button,
            QPushButton#sicilian_button,
            QPushButton#japanese_button,
            QPushButton#chinese_button,
            QPushButton#russian_button {
                color: black;
            }

            /* Assicurati che tutti gli elementi di testo nella sezione strumenti abbiano colore nero */
            QGroupBox#transcription_subgroup,
            QGroupBox#ai_media_subgroup,
            QGroupBox#recognition_subgroup,
            QGroupBox#utilities_subgroup,
            QGroupBox#knowledge_subgroup,
            QGroupBox#iot_subgroup {
                color: #2c3e50;
            }

            /* Titoli dei gruppi */
            QGroupBox#transcription_subgroup::title,
            QGroupBox#ai_media_subgroup::title,
            QGroupBox#utilities_subgroup::title,
            QGroupBox#knowledge_subgroup::title,
            QGroupBox#iot_subgroup::title {
                color: #2c3e50;
                font-weight: bold;
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
                background: transparent;
                border: none;
                border-radius: 0px;
            }
            QSplitter::handle:hover {
                background: rgba(74, 144, 226, 0.3);
            }
            QSplitter::handle:pressed {
                background: rgba(74, 144, 226, 0.5);
            }
        """)

        # Column A: Pensierini
        self.column_a_group = QGroupBox("📝 Contenuti pensierini creativi (A)")
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
        self.column_b_group = QGroupBox("🎯 Area di Lavoro (B)")
        self.column_b_group.setObjectName("work_area")  # ID per CSS
        self.column_b_group.setMinimumWidth(200)  # Minimum width to prevent collapse
        column_b_layout = QVBoxLayout(self.column_b_group)
        self.setup_work_area(column_b_layout)
        self.main_splitter.addWidget(self.column_b_group)

        # Column C: Details
        self.column_c_group = QGroupBox("Lavagna risposta Interattiva & AI")
        self.column_c_group.setObjectName("details")  # ID per CSS
        self.column_c_group.setMinimumWidth(300)  # Minimum width for details
        self.column_c_group.setMinimumHeight(600)  # Altezza minima aumentata significativamente
        column_c_layout = QVBoxLayout(self.column_c_group)
        self.details_scroll = QScrollArea()
        self.details_scroll.setWidgetResizable(True)
        self.details_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.details_widget = QWidget()
        self.details_widget.setObjectName("details_widget")
        self.details_layout = QVBoxLayout(self.details_widget)
        self.details_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.details_scroll.setWidget(self.details_widget)
        column_c_layout.addWidget(self.details_scroll)
        self.main_splitter.addWidget(self.column_c_group)

        # Set initial proportions (balanced 3-equal parts)
        self.main_splitter.setSizes([333, 333, 334])  # Roughly equal thirds

        # main_splitter will be added to vertical_splitter later

        # Bottom tools
        tools_group = QGroupBox("🔧 Strumenti")
        tools_group.setObjectName("tools")  # ID per CSS
        tools_layout = QVBoxLayout(tools_group)

        # Riga input testo + pulsante aggiungi pensierino
        input_row_layout = QHBoxLayout()
        self.input_text_area = QTextEdit()
        self.input_text_area.setPlaceholderText("Scrivi qui, ( premi INVIO per creare un pensierino - Premi INVIO di destra per tornare a capo )")
        self.input_text_area.setFixedHeight(35)  # Altezza esatta del pulsante "Aggiungi Pensierino"
        # Installa event filter per intercettare Invio
        self.input_text_area.installEventFilter(self)
        input_row_layout.addWidget(self.input_text_area)

        self.add_pensierino_button = QPushButton("➕ Aggiungi Pensierino")
        self.add_pensierino_button.setObjectName("add_pensierino_button")
        self.add_pensierino_button.clicked.connect(self.add_text_from_input_area)
        input_row_layout.addWidget(self.add_pensierino_button)

        tools_layout.addLayout(input_row_layout)

        # Crea un widget contenitore per gli strumenti
        self.tools_container = QWidget()
        self.tools_container.setObjectName("tools_container")
        self.tools_container.setStyleSheet("""
            QWidget {
                border: 2px solid #4a90e2;
                border-radius: 8px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(74, 144, 226, 0.1), stop:1 rgba(74, 144, 226, 0.05));
            }
        """)

        # Layout per il contenitore degli strumenti
        tools_container_layout = QVBoxLayout(self.tools_container)
        tools_container_layout.setContentsMargins(10, 10, 10, 10)

        # Contenitore principale per i sottogruppi
        subgroups_container = QHBoxLayout()
        subgroups_container.setSpacing(10)

        # === SOTTOGRUPPO 1: TRASCRIZIONE ===
        self.transcription_group = QGroupBox("🎤 Trascrizione")
        self.transcription_group.setObjectName("transcription_subgroup")
        transcription_layout = QHBoxLayout(self.transcription_group)
        transcription_layout.setSpacing(15)
        transcription_layout.setContentsMargins(10, 15, 10, 15)

        # Colonna sinistra
        left_column = QWidget()
        left_column.setObjectName("transcription_left_column")
        left_layout = QVBoxLayout(left_column)
        left_layout.setSpacing(8)
        left_layout.setContentsMargins(0, 0, 0, 0)

        self.voice_button = QPushButton("🎤 Voce → Testo")
        self.voice_button.setObjectName("voice_button")
        self.voice_button.clicked.connect(self.handle_voice_button)
        left_layout.addWidget(self.voice_button)

        self.audio_transcription_button = QPushButton("🎵 Audio → Testo")
        self.audio_transcription_button.setObjectName("audio_transcription_button")
        self.audio_transcription_button.clicked.connect(self.handle_audio_transcription_button)
        left_layout.addWidget(self.audio_transcription_button)

        self.ocr_button = QPushButton("📄 Documenti OCR→ Testo")
        self.ocr_button.setObjectName("ocr_button")
        self.ocr_button.clicked.connect(self.handle_ocr_button)
        left_layout.addWidget(self.ocr_button)

        self.graphics_tablet_button = QPushButton("🎨 Tavoletta grafica")
        self.graphics_tablet_button.setObjectName("graphics_tablet_button")
        self.graphics_tablet_button.clicked.connect(self.handle_graphics_tablet_button)
        left_layout.addWidget(self.graphics_tablet_button)

        transcription_layout.addWidget(left_column)
        transcription_layout.addStretch()
        subgroups_container.addWidget(self.transcription_group)

        # === SOTTOGRUPPO 2: AI E MEDIA ===
        self.ai_media_group = QGroupBox("🤖 AI & Media")
        self.ai_media_group.setObjectName("ai_media_subgroup")
        self.ai_media_group.setMaximumWidth(280)
        ai_media_layout = QVBoxLayout(self.ai_media_group)
        ai_media_layout.setSpacing(8)
        ai_media_layout.setContentsMargins(8, 10, 8, 10)

        self.ai_button = QPushButton("🧠 Chiedi ad A.I.")
        self.ai_button.setObjectName("ai_button")
        self.ai_button.clicked.connect(self.handle_ai_button)
        ai_media_layout.addWidget(self.ai_button)

        # Sottogruppo riconoscimento
        recognition_group = QGroupBox("👁️ Riconoscimento")
        recognition_group.setObjectName("recognition_subgroup")
        recognition_layout = QVBoxLayout(recognition_group)
        recognition_layout.setSpacing(6)
        recognition_layout.setContentsMargins(5, 8, 5, 8)

        self.face_button = QPushButton("❌ Faccia/e")
        self.face_button.setObjectName("face_button")
        self.face_button.setCheckable(True)
        self.face_button.clicked.connect(self.handle_face_recognition)
        recognition_layout.addWidget(self.face_button)

        self.hand_button = QPushButton("❌ Gesti")
        self.hand_button.setObjectName("hand_button")
        self.hand_button.setCheckable(True)
        self.hand_button.clicked.connect(self.handle_hand_gestures)
        recognition_layout.addWidget(self.hand_button)

        ai_media_layout.addWidget(recognition_group)
        subgroups_container.addWidget(self.ai_media_group)

        # === SOTTOGRUPPO 3: CONOSCENZA ===
        self.knowledge_group = QGroupBox("🌍 Esplora il Mondo della Conoscenza")
        self.knowledge_group.setObjectName("knowledge_subgroup")
        knowledge_layout = QGridLayout(self.knowledge_group)
        knowledge_layout.setSpacing(10)
        knowledge_layout.setContentsMargins(10, 10, 10, 10)

        # Griglia 4x5 per i pulsanti delle materie
        buttons_data = [
            ("📝 IPA", "ipa_button", self.handle_ipa_button),
            ("🔢 Matematica", "math_button", self.handle_math_button),
            ("⚗️ Chimica", "chemistry_button", self.handle_chemistry_button),
            ("⚛️ Fisica", "physics_button", self.handle_physics_button),
            ("🧬 Biologia", "biology_button", self.handle_biology_button),
            ("🇮🇹 Italiano", "italian_button", self.handle_italian_button),
            ("📚 Storia", "history_button", self.handle_history_button),
            ("💻 Informatica", "computer_science_button", self.handle_computer_science_button),
            ("🖥️ Sistemi", "os_scripting_button", self.handle_os_scripting_button),
            ("🌌 Astronomia", "astronomy_button", self.handle_astronomy_button),
            ("📐 Mat. Superiori", "advanced_math_button", self.handle_advanced_math_button),
            ("⚖️ Diritto", "law_button", self.handle_law_button),
            ("📊 Statistica", "probability_stats_button", self.handle_probability_stats_button),
            ("🇺🇸 Inglese", "english_button", self.handle_english_button),
            ("🇩🇪 Tedesco", "german_button", self.handle_german_button),
            ("🇪🇸 Spagnolo", "spanish_button", self.handle_spanish_button),
            ("🏛️ Siciliano", "sicilian_button", self.handle_sicilian_button),
            ("🇯🇵 Giapponese", "japanese_button", self.handle_japanese_button),
            ("🇨🇳 Cinese", "chinese_button", self.handle_chinese_button),
            ("🇷🇺 Russo", "russian_button", self.handle_russian_button),
        ]

        for i, (text, obj_name, handler) in enumerate(buttons_data):
            button = QPushButton(text)
            button.setObjectName(obj_name)
            button.clicked.connect(handler)
            row, col = divmod(i, 5)
            knowledge_layout.addWidget(button, row, col)

        subgroups_container.addWidget(self.knowledge_group)

        # === SOTTOGRUPPO 4: UTILITÀ ===
        self.utilities_group = QGroupBox("⚙️ Utilità")
        self.utilities_group.setObjectName("utilities_subgroup")
        utilities_layout = QVBoxLayout(self.utilities_group)

        self.media_button = QPushButton("📁 Carica Media")
        self.media_button.setObjectName("media_button")
        self.media_button.clicked.connect(self.handle_media_button)
        utilities_layout.addWidget(self.media_button)

        self.clean_button = QPushButton("🧹 Pulisci")
        self.clean_button.setObjectName("clean_button")
        self.clean_button.clicked.connect(self.handle_clean_button)
        utilities_layout.addWidget(self.clean_button)

        self.log_button = QPushButton("📋 Log")
        self.log_button.setObjectName("footer_log_button")
        self.log_button.setCheckable(True)
        self.log_button.clicked.connect(self.handle_log_toggle)
        utilities_layout.addWidget(self.log_button)

        subgroups_container.addWidget(self.utilities_group)

        # === SOTTOGRUPPO 5: IOT ===
        self.iot_group = QGroupBox("🔗 Periferiche esterne IOT")
        self.iot_group.setObjectName("iot_subgroup")
        self.iot_group.setMaximumWidth(250)
        iot_layout = QVBoxLayout(self.iot_group)
        iot_layout.setSpacing(8)
        iot_layout.setContentsMargins(8, 10, 8, 10)

        self.arduino_button = QPushButton("🔌 Risposta Arduino")
        self.arduino_button.setObjectName("arduino_button")
        self.arduino_button.clicked.connect(self.handle_arduino_button)
        iot_layout.addWidget(self.arduino_button)

        self.circuit_button = QPushButton("⚡ Circuito elettrico")
        self.circuit_button.setObjectName("circuit_button")
        self.circuit_button.clicked.connect(self.handle_circuit_button)
        iot_layout.addWidget(self.circuit_button)

        self.screen_share_button = QPushButton("📺 Condividi schermo")
        self.screen_share_button.setObjectName("screen_share_button")
        self.screen_share_button.clicked.connect(self.handle_screen_share_button)
        iot_layout.addWidget(self.screen_share_button)

        self.collab_button = QPushButton("🤝 Collabora Online")
        self.collab_button.setObjectName("collab_button")
        self.collab_button.clicked.connect(self.handle_collab_button)
        iot_layout.addWidget(self.collab_button)

        # Aggiungi stili CSS per i pulsanti IoT con testo nero
        self.setStyleSheet(self.styleSheet() + """
            QPushButton#arduino_button,
            QPushButton#circuit_button,
            QPushButton#screen_share_button,
            QPushButton#collab_button {
                color: black;
            }
        """)

        subgroups_container.addWidget(self.iot_group)



        # Aggiungi il contenitore dei sottogruppi al layout del contenitore
        tools_container_layout.addLayout(subgroups_container)

        # Aggiungi il contenitore degli strumenti al layout principale
        tools_layout.addWidget(self.tools_container)

        # Create vertical splitter for adjustable tools panel height
        from PyQt6.QtWidgets import QSplitter
        vertical_splitter = QSplitter(Qt.Orientation.Vertical)
        vertical_splitter.setHandleWidth(8)
        vertical_splitter.setStyleSheet("""
            QSplitter::handle {
                background: transparent;
                border: none;
                border-radius: 0px;
            }
            QSplitter::handle:hover {
                background: rgba(74, 144, 226, 0.3);
            }
            QSplitter::handle:pressed {
                background: rgba(74, 144, 226, 0.5);
            }
        """)

        vertical_splitter.addWidget(self.main_splitter)
        vertical_splitter.addWidget(tools_group)
        vertical_splitter.setSizes([600, 200])  # Default proportions: more space for main content

        main_layout.addWidget(vertical_splitter, 1)

        # Footer con informazioni di stato
        footer_layout = QHBoxLayout()
        footer_layout.addStretch()  # Spazio a sinistra

        # Label per informazioni di stato in basso a destra
        self.status_footer_label = QLabel()
        self.status_footer_label.setObjectName("status_footer_label")
        self.status_footer_label.setStyleSheet("""
            QLabel#status_footer_label {
                color: #495057;
                font-size: 11px;
                padding: 6px 12px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255, 255, 255, 0.95), stop:1 rgba(248, 249, 250, 0.95));
                border-radius: 8px;
                border: 1px solid #dee2e6;
                font-weight: bold;
                text-align: center;
                min-height: 20px;
            }
        """)
        self.update_footer_status()  # Aggiorna le informazioni di stato
        footer_layout.addWidget(self.status_footer_label)

        main_layout.addLayout(footer_layout)

    def setup_work_area(self, layout):
        self.work_area_scroll = QScrollArea()
        self.work_area_scroll.setWidgetResizable(True)
        self.work_area_widget = WorkAreaWidget(self.settings)
        # Salva riferimento al layout per altri metodi
        self.work_area_layout = self.work_area_widget.widget_layout
        self.work_area_scroll.setWidget(self.work_area_widget)
        layout.addWidget(self.work_area_scroll)

    # === FUNZIONI PLACEHOLDER PER LE MATERIE SCOLASTICHE ===
    def handle_ipa_button(self):
        """Gestisce il pulsante IPA - Funzionalità in sviluppo."""
        QMessageBox.information(self, "📝 IPA",
                              "🔤 Funzionalità IPA in Sviluppo\n\n"
                              "📚 Questa sezione sarà dedicata a:\n"
                              "• Pronuncia fonetica internazionale\n"
                              "• Simboli IPA interattivi\n"
                              "• Esercizi di pronuncia\n"
                              "• Dizionario fonetico\n\n"
                              "⚠️ Funzionalità attualmente in fase di implementazione")

    def handle_math_button(self):
        """Gestisce il pulsante Matematica - Funzionalità in sviluppo."""
        QMessageBox.information(self, "🔢 Matematica",
                              "📚 Funzionalità Matematica in Sviluppo\n\n"
                              "🧮 Questa sezione sarà dedicata a:\n"
                              "• Calcoli matematici interattivi\n"
                              "• Risoluzione di equazioni\n"
                              "• Geometria e algebra\n"
                              "• Statistica e probabilità\n\n"
                              "⚠️ Funzionalità attualmente in fase di implementazione")

    def handle_history_button(self):
        """Gestisce il pulsante Storia - Funzionalità in sviluppo."""
        QMessageBox.information(self, "📚 Storia",
                              "🏛️ Funzionalità Storia in Sviluppo\n\n"
                              "📜 Questa sezione sarà dedicata a:\n"
                              "• Linee temporali interattive\n"
                              "• Eventi storici importanti\n"
                              "• Biografie di personaggi storici\n"
                              "• Mappe storiche\n\n"
                              "⚠️ Funzionalità attualmente in fase di implementazione")

    def handle_italian_button(self):
        """Gestisce il pulsante Italiano - Funzionalità in sviluppo."""
        QMessageBox.information(self, "🇮🇹 Italiano",
                              "📖 Funzionalità Italiano in Sviluppo\n\n"
                              "✍️ Questa sezione sarà dedicata a:\n"
                              "• Grammatica italiana\n"
                              "• Analisi del testo\n"
                              "• Letteratura italiana\n"
                              "• Ortografia e sintassi\n\n"
                              "⚠️ Funzionalità attualmente in fase di implementazione")

    def handle_chemistry_button(self):
        """Gestisce il pulsante Chimica - Funzionalità in sviluppo."""
        QMessageBox.information(self, "⚗️ Chimica",
                              "🧪 Funzionalità Chimica in Sviluppo\n\n"
                              "🔬 Questa sezione sarà dedicata a:\n"
                              "• Tavola periodica interattiva\n"
                              "• Reazioni chimiche\n"
                              "• Struttura molecolare\n"
                              "• Esperimenti virtuali\n\n"
                              "⚠️ Funzionalità attualmente in fase di implementazione")

    def handle_physics_button(self):
        """Gestisce il pulsante Fisica - Funzionalità in sviluppo."""
        QMessageBox.information(self, "⚛️ Fisica",
                              "🔭 Funzionalità Fisica in Sviluppo\n\n"
                              "⚡ Questa sezione sarà dedicata a:\n"
                              "• Leggi della fisica\n"
                              "• Meccanica e termodinamica\n"
                              "• Elettricità e magnetismo\n"
                              "• Fisica quantistica\n\n"
                              "⚠️ Funzionalità attualmente in fase di implementazione")

    def handle_biology_button(self):
        """Gestisce il pulsante Scienza dei 5 Regni - Funzionalità in sviluppo."""
        QMessageBox.information(self, "🧬 Scienza dei 5 Regni",
                              "🌿 Funzionalità Biologia in Sviluppo\n\n"
                              "🦠 Questa sezione sarà dedicata a:\n"
                              "• Classificazione dei 5 regni\n"
                              "• Anatomia e fisiologia\n"
                              "• Ecologia e ambiente\n"
                              "• Genetica e evoluzione\n\n"
                              "⚠️ Funzionalità attualmente in fase di implementazione")

    def handle_astronomy_button(self):
        """Gestisce il pulsante Astronomia - Funzionalità in sviluppo."""
        QMessageBox.information(self, "🌌 Astronomia",
                              "🪐 Funzionalità Astronomia in Sviluppo\n\n"
                              "🌟 Questa sezione sarà dedicata a:\n"
                              "• Sistema solare\n"
                              "• Stelle e galassie\n"
                              "• Cosmologia\n"
                              "• Osservazione astronomica\n\n"
                              "⚠️ Funzionalità attualmente in fase di implementazione")

    def handle_computer_science_button(self):
        """Gestisce il pulsante Informatica - Funzionalità in sviluppo."""
        QMessageBox.information(self, "💻 Informatica",
                              "🖥️ Funzionalità Informatica in Sviluppo\n\n"
                              "💾 Questa sezione sarà dedicata a:\n"
                              "• Programmazione e algoritmi\n"
                              "• Strutture dati\n"
                              "• Reti e sicurezza informatica\n"
                              "• Intelligenza artificiale\n\n"
                              "⚠️ Funzionalità attualmente in fase di implementazione")

    def handle_os_scripting_button(self):
        """Gestisce il pulsante Sistemi Operativi e Script - Funzionalità in sviluppo."""
        QMessageBox.information(self, "🖥️ Sistemi Operativi e Script",
                              "🔧 Funzionalità Sistemi Operativi in Sviluppo\n\n"
                              "⚙️ Questa sezione sarà dedicata a:\n"
                              "• Sistemi operativi (Linux, Windows, macOS)\n"
                              "• Scripting (Bash, PowerShell, Python)\n"
                              "• Automazione processi\n"
                              "• Amministrazione sistemi\n\n"
                              "⚠️ Funzionalità attualmente in fase di implementazione")

    def handle_advanced_math_button(self):
        """Gestisce il pulsante Matematica delle Superiori - Funzionalità in sviluppo."""
        QMessageBox.information(self, "📐 Matematica delle Superiori",
                              "🔬 Funzionalità Matematica Avanzata in Sviluppo\n\n"
                              "📊 Questa sezione sarà dedicata a:\n"
                              "• Analisi matematica\n"
                              "• Geometria analitica\n"
                              "• Algebra lineare\n"
                              "• Calcolo differenziale e integrale\n\n"
                              "⚠️ Funzionalità attualmente in fase di implementazione")

    def handle_law_button(self):
        """Gestisce il pulsante Diritto - Funzionalità in sviluppo."""
        QMessageBox.information(self, "⚖️ Diritto",
                              "📋 Funzionalità Diritto in Sviluppo\n\n"
                              "🏛️ Questa sezione sarà dedicata a:\n"
                              "• Diritto civile e penale\n"
                              "• Diritto costituzionale\n"
                              "• Diritto internazionale\n"
                              "• Casi giuridici e sentenze\n\n"
                              "⚠️ Funzionalità attualmente in fase di implementazione")

    def handle_probability_stats_button(self):
        """Gestisce il pulsante Calcolo Probabilità e Statistica - Funzionalità in sviluppo."""
        QMessageBox.information(self, "📊 Probabilità e Statistica",
                              "📈 Funzionalità Statistica in Sviluppo\n\n"
                              "🔢 Questa sezione sarà dedicata a:\n"
                              "• Teoria delle probabilità\n"
                              "• Statistica descrittiva\n"
                              "• Inferenza statistica\n"
                              "• Analisi dati e modelli\n\n"
                              "⚠️ Funzionalità attualmente in fase di implementazione")

    def handle_english_button(self):
        """Gestisce il pulsante Inglese - Funzionalità in sviluppo."""
        QMessageBox.information(self, "🇺🇸 Inglese",
                              "📚 Funzionalità Inglese in Sviluppo\n\n"
                              "🇬🇧 Questa sezione sarà dedicata a:\n"
                              "• Grammatica inglese\n"
                              "• Vocabolario e frasi comuni\n"
                              "• Pronuncia e fonetica\n"
                              "• Letteratura inglese\n\n"
                              "⚠️ Funzionalità attualmente in fase di implementazione")

    def handle_german_button(self):
        """Gestisce il pulsante Tedesco - Funzionalità in sviluppo."""
        QMessageBox.information(self, "🇩🇪 Tedesco",
                              "📚 Funzionalità Tedesco in Sviluppo\n\n"
                              "🇩🇪 Questa sezione sarà dedicata a:\n"
                              "• Grammatica tedesca\n"
                              "• Vocabolario essenziale\n"
                              "• Pronuncia corretta\n"
                              "• Cultura germanica\n\n"
                              "⚠️ Funzionalità attualmente in fase di implementazione")

    def handle_spanish_button(self):
        """Gestisce il pulsante Spagnolo - Funzionalità in sviluppo."""
        QMessageBox.information(self, "🇪🇸 Spagnolo",
                              "📚 Funzionalità Spagnolo in Sviluppo\n\n"
                              "🇪🇸 Questa sezione sarà dedicata a:\n"
                              "• Grammatica spagnola\n"
                              "• Vocabolario e espressioni\n"
                              "• Pronuncia e accenti\n"
                              "• Letteratura ispanica\n\n"
                              "⚠️ Funzionalità attualmente in fase di implementazione")

    def handle_sicilian_button(self):
        """Gestisce il pulsante Siciliano - Funzionalità in sviluppo."""
        QMessageBox.information(self, "🏛️ Siciliano",
                              "📚 Funzionalità Siciliano in Sviluppo\n\n"
                              "🇮🇹 Questa sezione sarà dedicata a:\n"
                              "• Grammatica siciliana\n"
                              "• Vocabolario regionale\n"
                              "• Pronuncia tradizionale\n"
                              "• Letteratura siciliana\n\n"
                              "⚠️ Funzionalità attualmente in fase di implementazione")

    def handle_japanese_button(self):
        """Gestisce il pulsante Giapponese - Funzionalità in sviluppo."""
        QMessageBox.information(self, "🇯🇵 Giapponese",
                              "📚 Funzionalità Giapponese in Sviluppo\n\n"
                              "🇯🇵 Questa sezione sarà dedicata a:\n"
                              "• Hiragana e Katakana\n"
                              "• Kanji essenziali\n"
                              "• Grammatica giapponese\n"
                              "• Cultura tradizionale\n\n"
                              "⚠️ Funzionalità attualmente in fase di implementazione")

    def handle_chinese_button(self):
        """Gestisce il pulsante Cinese - Funzionalità in sviluppo."""
        QMessageBox.information(self, "🇨🇳 Cinese",
                              "📚 Funzionalità Cinese in Sviluppo\n\n"
                              "🇨🇳 Questa sezione sarà dedicata a:\n"
                              "• Caratteri cinesi semplificati\n"
                              "• Pinyin e pronuncia\n"
                              "• Grammatica cinese\n"
                              "• Cultura cinese\n\n"
                              "⚠️ Funzionalità attualmente in fase di implementazione")

    def handle_russian_button(self):
        """Gestisce il pulsante Russo - Funzionalità in sviluppo."""
        QMessageBox.information(self, "🇷🇺 Russo",
                              "📚 Funzionalità Russo in Sviluppo\n\n"
                              "🇷🇺 Questa sezione sarà dedicata a:\n"
                              "• Alfabeto cirillico\n"
                              "• Grammatica russa\n"
                              "• Vocabolario essenziale\n"
                              "• Letteratura russa\n\n"
                              "⚠️ Funzionalità attualmente in fase di implementazione")

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
        self.details_text_label.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
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
                padding: 6px 14px;
                font-weight: bold;
                min-height: 30px;
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

    def handle_audio_transcription_button(self):
        """Gestisce la trascrizione di file audio in testo."""
        try:
            if not AudioFileTranscriptionThread:
                QMessageBox.critical(self, "Errore", "Modulo di trascrizione audio non disponibile.\n\n"
                                                   "Assicurati che le librerie 'vosk' e 'wave' siano installate.")
                return

            # Apri dialog per selezionare file audio
            file_dialog = QFileDialog(self)
            file_dialog.setWindowTitle("Seleziona file audio per trascrizione")
            file_dialog.setNameFilter("File audio (*.wav *.mp3 *.flac *.aac *.ogg);;WAV (*.wav);;MP3 (*.mp3);;FLAC (*.flac);;AAC (*.aac);;OGG (*.ogg);;Tutti i file (*)")
            file_dialog.setFileMode(QFileDialog.FileMode.ExistingFile)

            if file_dialog.exec() == QFileDialog.DialogCode.Accepted:
                selected_files = file_dialog.selectedFiles()
                if selected_files:
                    audio_file_path = selected_files[0]
                    self.transcribe_audio_file(audio_file_path)

        except Exception as e:
            logging.error(f"Errore caricamento file audio: {e}")
            QMessageBox.critical(self, "Errore", f"Errore durante il caricamento del file:\n{str(e)}")

    def transcribe_audio_file(self, audio_file_path):
        """Trascrive un file audio in testo."""
        import os
        from pathlib import Path

        file_name = os.path.basename(audio_file_path)
        file_ext = Path(audio_file_path).suffix.lower()

        # Verifica formato supportato
        supported_formats = ['.wav', '.mp3', '.flac', '.aac', '.ogg']
        if file_ext not in supported_formats:
            QMessageBox.warning(self, "Formato Non Supportato",
                              f"Il formato '{file_ext}' non è attualmente supportato.\n\n"
                              f"Formati supportati: {', '.join(supported_formats)}\n\n"
                              f"Converti il file in uno dei formati supportati.")
            return

        try:
            # Mostra progresso
            progress_msg = QMessageBox(self)
            progress_msg.setWindowTitle("Trascrizione Audio")
            progress_msg.setText("🔄 Preparazione trascrizione...")
            progress_msg.setStandardButtons(QMessageBox.StandardButton.Cancel)
            progress_msg.show()

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
                    progress_msg.setText("🔄 Scaricamento modello necessario...")

                    def progress_callback(message):
                        progress_msg.setText(message)
                        QApplication.processEvents()  # Aggiorna l'interfaccia

                    # Tenta di scaricare il modello
                    if not ensure_vosk_model_available(vosk_model, progress_callback):
                        progress_msg.close()
                        QMessageBox.critical(self, "Download Fallito",
                                           f"Impossibile scaricare il modello '{vosk_model}'.\n\n"
                                           "Verifica la connessione internet e riprova.")
                        return

                    progress_msg.close()
                    QMessageBox.information(self, "Download Completato",
                                          f"✅ Modello '{vosk_model}' scaricato con successo!")
                else:
                    progress_msg.close()
                    QMessageBox.warning(self, "Funzione Download Non Disponibile",
                                      f"Il modello Vosk '{vosk_model}' non è stato trovato.\n\n"
                                      f"Percorso: {model_path}\n\n"
                                      "La funzione di download automatico non è disponibile.")
                    return

            progress_msg.close()

            # Mostra messaggio di inizio trascrizione
            QMessageBox.information(self, "Trascrizione Avviata",
                                  f"🎵 Avvio trascrizione del file:\n{file_name}\n\n"
                                  f"📝 Il testo trascritto verrà aggiunto ai pensierini.\n"
                                  f"⏳ L'operazione potrebbe richiedere alcuni minuti...")

            # Crea il thread di trascrizione
            self.audio_transcription_thread = AudioFileTranscriptionThread(
                audio_file_path,
                vosk_model,
                text_callback=self._on_audio_transcription_completed
            )

            # Connetti i segnali
            self.audio_transcription_thread.transcription_progress.connect(self._on_transcription_progress)
            self.audio_transcription_thread.transcription_completed.connect(self._on_audio_transcription_completed)
            self.audio_transcription_thread.transcription_error.connect(self._on_transcription_error)

            # Avvia la trascrizione
            self.audio_transcription_thread.start()

        except Exception as e:
            if 'progress_msg' in locals():
                progress_msg.close()
            logging.error(f"Errore avvio trascrizione: {e}")
            QMessageBox.critical(self, "Errore Avvio", f"Errore nell'avvio della trascrizione:\n{str(e)}")

    def _on_transcription_progress(self, message):
        """Gestisce gli aggiornamenti di progresso della trascrizione."""
        logging.info(f"Progresso trascrizione: {message}")
        # Potrebbe essere utile mostrare un dialog di progresso più dettagliato in futuro

    def _on_audio_transcription_completed(self, text):
        """Callback quando la trascrizione è completata."""
        logging.info(f"🎵 Trascrizione completata: '{text[:100]}...'")

        if text and text.strip():
            # Mostra il testo trascritto nei dettagli
            transcription_content = f"🎵 Trascrizione Audio Completata\n\n{'='*50}\n\n{text}\n\n{'='*50}\n\n📊 Statistiche Trascrizione:\n• Caratteri: {len(text)}\n• Parole: {len(text.split())}\n• Righe: {len(text.split(chr(10)))}"
            self.show_text_in_details(transcription_content)

            # Crea anche un pensierino con il testo trascritto
            if DraggableTextWidget:
                transcription_pensierino_text = f"🎵 Trascrizione: {text[:50]}... ({len(text)} caratteri)"
                pensierino_widget = DraggableTextWidget(transcription_pensierino_text, self.settings)
                self.pensierini_layout.addWidget(pensierino_widget)

            QMessageBox.information(self, "Trascrizione Completata",
                                  f"✅ Trascrizione completata con successo!\n\n"
                                  f"🎵 File audio elaborato\n"
                                  f"📝 Caratteri: {len(text)}\n"
                                  f"📊 Parole: {len(text.split())}")
        else:
            QMessageBox.warning(self, "Trascrizione Vuota",
                              "La trascrizione non ha prodotto testo.\n\n"
                              "Possibili cause:\n"
                              "• File audio di bassa qualità\n"
                              "• Audio senza parlato\n"
                              "• Problemi di riconoscimento")

    def _on_transcription_error(self, error_msg):
        """Gestisce gli errori della trascrizione."""
        logging.error(f"Errore trascrizione: {error_msg}")
        QMessageBox.critical(self, "Errore Trascrizione", f"Errore durante la trascrizione:\n\n{error_msg}")

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

    def _ipa_to_pronunciation_text(self, symbol):
        """Converte un simbolo IPA in testo pronunciabile per il TTS."""
        # Mappa dei simboli IPA a testi pronunciabili in italiano
        ipa_mapping = {
            # Vocali
            '[i]': 'i come in mìle',
            '[e]': 'e come in mèta',
            '[ɛ]': 'e aperta come in mèta',
            '[a]': 'a come in casa',
            '[ɔ]': 'o aperta come in còrso',
            '[o]': 'o come in còrso',
            '[u]': 'u come in cùpa',

            # Consonanti
            '[p]': 'p come in pane',
            '[b]': 'b come in buono',
            '[t]': 't come in tavolo',
            '[d]': 'd come in dono',
            '[k]': 'c come in cane',
            '[g]': 'g come in gatto',
            '[f]': 'f come in fare',
            '[v]': 'v come in vino',
            '[s]': 's come in sole',
            '[z]': 's sonora come in rosa',
            '[ʃ]': 'sc come in scena',
            '[ʒ]': 'j francese come in jour',
            '[m]': 'm come in mamma',
            '[n]': 'n come in nonna',
            '[ɲ]': 'gn come in gnomo',
            '[l]': 'l come in luna',
            '[ʎ]': 'gl come in gli',
            '[r]': 'r come in rosa',
            '[ʁ]': 'r francese come in rouge',

            # Simboli speciali
            '[ˈ]': 'accento principale',
            '[ˌ]': 'accento secondario',
            '[.]': 'sillaba',
            '[:]': 'lunga',
            '[̯]': 'semi vocale',
            '[̃]': 'nasale',

            # Altri simboli comuni
            '[t͡s]': 'z come in grazie',
            '[d͡z]': 'z sonora come in zero',
            '[t͡ʃ]': 'c come in cena',
            '[d͡ʒ]': 'g come in giro',
        }

        # Rimuovi le parentesi quadre se presenti
        clean_symbol = symbol.strip('[]')

        # Cerca corrispondenza esatta
        if symbol in ipa_mapping:
            return ipa_mapping[symbol]

        # Cerca corrispondenza senza parentesi
        bracketed_symbol = f'[{clean_symbol}]'
        if bracketed_symbol in ipa_mapping:
            return ipa_mapping[bracketed_symbol]

        # Se non trovato, restituisci il simbolo pulito
        return clean_symbol

    def keyPressEvent(self, event):
        """Gestisce gli eventi della tastiera per scorciatoie."""
        from PyQt6.QtCore import Qt

        # Controlla la combinazione Ctrl+F per toggle fullscreen
        if event.key() == Qt.Key.Key_F and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self.toggle_fullscreen()
            event.accept()  # Segnala che l'evento è stato gestito
        else:
            # Passa l'evento al gestore predefinito
            super().keyPressEvent(event)

    def toggle_fullscreen(self):
        """Attiva/disattiva la modalità fullscreen preservando esattamente le dimensioni originali."""
        try:
            if self.is_fullscreen:
                # Esci dalla modalità fullscreen
                self.showNormal()

                # Piccola pausa per permettere alla finestra di stabilizzarsi
                from PyQt6.QtCore import QTimer
                QTimer.singleShot(10, self._restore_original_size)

                self.is_fullscreen = False
                logging.info("Uscito dalla modalità fullscreen")
            else:
                # Salva le dimensioni attuali prima di entrare in fullscreen
                if not self.is_fullscreen:
                    self.original_width = self.width()
                    self.original_height = self.height()
                    self.original_x = self.x()
                    self.original_y = self.y()
                    logging.info(f"Salvata dimensione originale: {self.original_width}x{self.original_height} at ({self.original_x}, {self.original_y})")

                # Entra in modalità fullscreen
                self.showFullScreen()
                self.is_fullscreen = True
                logging.info("Entrato in modalità fullscreen")

        except Exception as e:
            logging.error(f"Errore toggle fullscreen: {e}")
            QMessageBox.critical(self, "Errore Fullscreen",
                               f"Errore durante il cambio modalità schermo:\n{str(e)}")

    def _restore_original_size(self):
        """Ripristina le dimensioni originali dopo l'uscita dal fullscreen."""
        try:
            if self.original_width > 0 and self.original_height > 0:
                # Forza le dimensioni esatte originali
                self.resize(self.original_width, self.original_height)

                # Posiziona la finestra nella posizione originale (se valida)
                if self.original_x >= 0 and self.original_y >= 0:
                    self.move(self.original_x, self.original_y)

                # Forza l'aggiornamento della geometria
                self.updateGeometry()

                # Assicurati che la finestra sia in primo piano
                self.raise_()
                self.activateWindow()

                logging.info(f"Ripristinate dimensioni originali: {self.original_width}x{self.original_height} at ({self.original_x}, {self.original_y})")
            else:
                logging.warning("Nessuna dimensione originale da ripristinare")

        except Exception as e:
            logging.error(f"Errore ripristino dimensioni: {e}")

    def handle_log_toggle(self):
        """Gestisce il toggle del pulsante log per mostrare/nascondere il contenuto del log nei dettagli."""
        try:
            if self.log_button.isChecked():
                # Salva il contenuto attuale dei dettagli prima di sovrascriverlo
                if hasattr(self, 'full_text'):
                    self.previous_details_content = self.full_text

                # Mostra il contenuto del log nei dettagli
                self.show_log_content()
                self.log_button.setText("📋 Log ✓")
            else:
                # Nasconde il contenuto del log (torna alla visualizzazione precedente o pulisce)
                if hasattr(self, 'previous_details_content'):
                    self.show_text_in_details(self.previous_details_content)
                    delattr(self, 'previous_details_content')
                else:
                    self._clear_details()
                self.log_button.setText("📋 Log")

        except Exception as e:
            logging.error(f"Errore toggle log: {e}")
            QMessageBox.critical(self, "Errore Log", f"Errore durante il toggle del log:\n{str(e)}")

    def show_log_content(self):
        """Mostra il contenuto del log nei dettagli."""
        try:
            from main_03_configurazione_e_opzioni import get_config
            import os
            from datetime import datetime

            # Ottieni il percorso del file di log
            log_config = get_config()
            log_file = log_config.get_setting('files.log_file', 'Save/LOG/app.log')

            if not os.path.exists(log_file):
                log_content = f"📁 File log non trovato:\n{log_file}"
            else:
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
                    log_content = f"📋 LOG ERRORI E WARNING\n\n" \
                                  f"✅ Nessun errore o warning trovato nel log!\n\n" \
                                  f"📁 File log: {log_file}\n" \
                                  f"📊 Righe totali nel log: {len(lines)}\n" \
                                  f"🔄 Ultimo aggiornamento: {datetime.now().strftime('%H:%M:%S')}"
                else:
                    log_content = f"📋 LOG ERRORI E WARNING\n\n" \
                                  f"🔍 Trovati {len(filtered_lines)} errori/warning:\n\n" \
                                  f"{'='*60}\n\n" \
                                  f"{chr(10).join(filtered_lines[-50:])}\n\n" \
                                  f"{'='*60}\n\n" \
                                  f"📁 File log: {log_file}\n" \
                                  f"📊 Righe totali nel log: {len(lines)}\n" \
                                  f"🔄 Ultimo aggiornamento: {datetime.now().strftime('%H:%M:%S')}"

            # Mostra il contenuto nei dettagli
            self.show_text_in_details(log_content)

        except Exception as e:
            logging.error(f"Errore lettura log: {e}")
            error_content = f"❌ Errore lettura log:\n{str(e)}"
            self.show_text_in_details(error_content)

    # def show_log_window(self):
    #     """Metodo disabilitato - funzionalità log spostata in alto come label di stato."""
    #     pass

    # def refresh_log_content(self):
    #     """Metodo disabilitato - funzionalità log spostata in alto come label di stato."""
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

    # def clear_log_file(self):
    #     """Metodo disabilitato - funzionalità log spostata in alto come label di stato."""
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
        """Nasconde la visualizzazione del log nei dettagli."""
        try:
            # Nasconde il contenuto del log nei dettagli
            if hasattr(self, 'log_button'):
                self.log_button.setChecked(False)
                self.log_button.setText("📋 Log")
                # Torna alla visualizzazione precedente o pulisce
                if hasattr(self, 'previous_details_content'):
                    self.show_text_in_details(self.previous_details_content)
                else:
                    self._clear_details()

        except Exception as e:
            logging.error(f"Errore nascondendo log: {e}")

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

    def handle_ipa_button(self):
        """Mostra un dialog con pulsanti interattivi per i simboli IPA e area clipboard."""
        try:
            # Crea il dialog IPA
            ipa_dialog = QDialog(self)
            ipa_dialog.setWindowTitle("📝 Simboli IPA - Alfabeto Fonetico Internazionale")
            ipa_dialog.setFixedSize(1200, 1000)  # Aumentato l'altezza per vedere nasalizzazione e suggerimento
            ipa_dialog.setStyleSheet("""
                QDialog {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #f8f9fa, stop:1 #e9ecef);
                    border: 2px solid #6f42c1;
                    border-radius: 10px;
                }
                QLabel {
                    font-size: 14px;
                    color: #333;
                    padding: 5px;
                }
                QLabel.title {
                    font-size: 18px;
                    font-weight: bold;
                    color: #6f42c1;
                    margin-bottom: 10px;
                }
                QLabel.section {
                    font-size: 14px;
                    font-weight: bold;
                    color: #495057;
                    margin-top: 15px;
                    margin-bottom: 5px;
                }
                QLabel.clipboard_title {
                    font-size: 14px;
                    font-weight: bold;
                    color: #28a745;
                    margin-top: 10px;
                    margin-bottom: 5px;
                }
                QPushButton.ipa_symbol {
                    background-color: #e9ecef;
                    color: #495057;
                    border: 2px solid #dee2e6;
                    border-radius: 8px;
                    padding: 10px 14px;
                    font-weight: bold;
                    font-size: 14px;
                    font-family: "Courier New", monospace;
                    min-width: 65px;
                    min-height: 45px;
                }
                QPushButton.ipa_symbol:hover {
                    background-color: #6f42c1;
                    color: white;
                    border-color: #5a359a;
                }
                QPushButton.ipa_symbol:pressed {
                    background-color: #5a359a;
                    border-color: #4a2e7a;
                }
                QPushButton.control {
                    background-color: #6f42c1;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 10px 18px;
                    font-weight: bold;
                    min-width: 120px;
                    font-size: 14px;
                }
                QPushButton.control:hover {
                    background-color: #5a359a;
                }
                QPushButton.clipboard_btn {
                    background-color: #28a745;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 8px 16px;
                    font-weight: bold;
                    min-width: 100px;
                    font-size: 12px;
                }
                QPushButton.clipboard_btn:hover {
                    background-color: #218838;
                }

                QScrollArea {
                    border: 1px solid #dee2e6;
                    border-radius: 6px;
                    background-color: rgba(255, 255, 255, 0.8);
                }
                QTextEdit {
                    border: 2px solid #28a745;
                    border-radius: 8px;
                    background-color: rgba(255, 255, 255, 0.95);
                    font-family: "Courier New", monospace;
                    font-size: 14px;
                    padding: 10px;
                    min-height: 120px;
                }
                QSplitter::handle {
                    background-color: #6f42c1;
                    height: 4px;
                }
                QSplitter::handle:hover {
                    background-color: #5a359a;
                }
            """)

            # Layout principale con splitter
            main_layout = QVBoxLayout(ipa_dialog)

            # Titolo
            title = QLabel("📝 Simboli IPA Interattivi con Clipboard")
            title.setObjectName("title")
            main_layout.addWidget(title)

            # Descrizione
            desc = QLabel("Clicca sui simboli IPA per copiarli negli appunti. Tutto quello che copi appare anche nell'area clipboard qui sotto per un riscontro immediato.")
            desc.setWordWrap(True)
            main_layout.addWidget(desc)

            # Splitter per dividere pulsanti e clipboard
            splitter = QSplitter(Qt.Orientation.Vertical)
            main_layout.addWidget(splitter)

            # Widget superiore: pulsanti IPA
            top_widget = QWidget()
            top_layout = QVBoxLayout(top_widget)

            # Scroll area per contenere tutti i pulsanti
            scroll_area = QScrollArea()
            scroll_widget = QWidget()
            scroll_layout = QVBoxLayout(scroll_widget)

            # VOCALI ITALIANE
            vocali_label = QLabel("🔤 VOCALI ITALIANE")
            vocali_label.setObjectName("section")
            scroll_layout.addWidget(vocali_label)

            vocali_layout = QHBoxLayout()
            vocali_data = [
                ("[i]", "mìle"),
                ("[e]", "mèta"),
                ("[ɛ]", "mèta"),
                ("[a]", "casa"),
                ("[ɔ]", "còrso"),
                ("[o]", "còrso"),
                ("[u]", "cùpa")
            ]

            for symbol, example in vocali_data:
                # Pulsante principale del simbolo (copia negli appunti)
                btn = QPushButton(f"{symbol}\n{example}")
                btn.setObjectName("ipa_symbol")
                btn.setToolTip(f"Esempio: '{example}' → trascrizione fonetica con {symbol}")
                btn.clicked.connect(lambda checked, s=symbol: self.copy_single_ipa_symbol_with_clipboard(s, ipa_dialog))
                vocali_layout.addWidget(btn)

            vocali_layout.addStretch()
            scroll_layout.addLayout(vocali_layout)

            # CONSONANTI
            consonanti_label = QLabel("🔤 CONSONANTI")
            consonanti_label.setObjectName("section")
            scroll_layout.addWidget(consonanti_label)

            # Prima riga consonanti
            cons1_layout = QHBoxLayout()
            cons1_data = [
                ("[p]", "pane"),
                ("[b]", "bene"),
                ("[t]", "tavolo"),
                ("[d]", "dado"),
                ("[k]", "casa"),
                ("[g]", "gatto"),
                ("[f]", "fame"),
                ("[v]", "vino")
            ]

            for symbol, example in cons1_data:
                # Pulsante principale del simbolo (copia negli appunti)
                btn = QPushButton(f"{symbol}\n{example}")
                btn.setObjectName("ipa_symbol")
                btn.setToolTip(f"Esempio: '{example}' → trascrizione fonetica con {symbol}")
                btn.clicked.connect(lambda checked, s=symbol: self.copy_single_ipa_symbol_with_clipboard(s, ipa_dialog))
                cons1_layout.addWidget(btn)

            cons1_layout.addStretch()
            scroll_layout.addLayout(cons1_layout)

            # Seconda riga consonanti
            cons2_layout = QHBoxLayout()
            cons2_data = [
                ("[s]", "sasso"),
                ("[z]", "rosa"),
                ("[ʃ]", "scena"),
                ("[ʒ]", "Gange"),
                ("[m]", "mamma"),
                ("[n]", "nono"),
                ("[ɲ]", "gnomo"),
                ("[l]", "luna")
            ]

            for symbol, example in cons2_data:
                # Pulsante principale del simbolo (copia negli appunti)
                btn = QPushButton(f"{symbol}\n{example}")
                btn.setObjectName("ipa_symbol")
                btn.setToolTip(f"Esempio: '{example}' → trascrizione fonetica con {symbol}")
                btn.clicked.connect(lambda checked, s=symbol: self.copy_single_ipa_symbol_with_clipboard(s, ipa_dialog))
                cons2_layout.addWidget(btn)

            cons2_layout.addStretch()
            scroll_layout.addLayout(cons2_layout)

            # Terza riga consonanti
            cons3_layout = QHBoxLayout()
            cons3_data = [
                ("[ʎ]", "gli"),
                ("[r]", "raro"),
                ("[ʁ]", "r francese")
            ]

            for symbol, example in cons3_data:
                # Pulsante principale del simbolo (copia negli appunti)
                btn = QPushButton(f"{symbol}\n{example}")
                btn.setObjectName("ipa_symbol")
                btn.setToolTip(f"Esempio: '{example}' → trascrizione fonetica con {symbol}")
                btn.clicked.connect(lambda checked, s=symbol: self.copy_single_ipa_symbol_with_clipboard(s, ipa_dialog))
                cons3_layout.addWidget(btn)

            cons3_layout.addStretch()
            scroll_layout.addLayout(cons3_layout)

            # SIMBOLI SPECIALI
            speciali_label = QLabel("🔤 SIMBOLI SPECIALI")
            speciali_label.setObjectName("section")
            scroll_layout.addWidget(speciali_label)

            speciali_layout = QHBoxLayout()
            speciali_data = [
                ("[ˈ]", "accento primario"),
                ("[ˌ]", "accento secondario"),
                ("[.]", "separatore sillabe"),
                ("[:]", "vocale lunga"),
                ("[̯]", "semivocale"),
                ("[̃]", "nasalizzazione")
            ]

            for symbol, example in speciali_data:
                # Pulsante principale del simbolo (copia negli appunti)
                btn = QPushButton(f"{symbol}\n{example}")
                btn.setObjectName("ipa_symbol")
                if symbol == "[ˈ]":
                    btn.setToolTip("Esempio: 'grazie' → [ˈɡrat.t͡sje] (accento primario sulla prima sillaba)")
                else:
                    btn.setToolTip(f"Esempio pratico con {symbol}: {example}")
                btn.clicked.connect(lambda checked, s=symbol: self.copy_single_ipa_symbol_with_clipboard(s, ipa_dialog))
                speciali_layout.addWidget(btn)

            speciali_layout.addStretch()
            scroll_layout.addLayout(speciali_layout)

            # SPIEGAZIONE
            info_label = QLabel("💡 Guida all'utilizzo:\n\n"
                               "• Utilizza questi simboli per trascrivere correttamente la pronuncia delle parole italiane\n"
                               "• Passa il mouse sui pulsanti per vedere esempi pratici di utilizzo\n"
                               "• Clicca sui simboli per copiarli negli appunti\n"
                               "• Tutto quello che copi appare automaticamente nel clipboard sottostante\n\n"
                               "🔍 Suggerimento: Inizia con le vocali e consonanti più comuni!")
            info_label.setObjectName("section")
            info_label.setWordWrap(True)
            info_label.setStyleSheet("font-size: 14px; color: #28a745; margin-top: 25px; margin-bottom: 15px; "
                                   "background-color: rgba(40, 167, 69, 0.1); padding: 15px; border-radius: 8px; "
                                   "border: 1px solid rgba(40, 167, 69, 0.3);")
            scroll_layout.addWidget(info_label)

            # Imposta lo scroll
            scroll_area.setWidget(scroll_widget)
            scroll_area.setWidgetResizable(True)
            scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            top_layout.addWidget(scroll_area)

            # Aggiungi il top_widget al splitter
            splitter.addWidget(top_widget)

            # Widget inferiore: area clipboard
            bottom_widget = QWidget()
            bottom_layout = QVBoxLayout(bottom_widget)

            # Titolo clipboard
            clipboard_title = QLabel("📋 CLIPBOARD - Tutto quello che copi")
            clipboard_title.setObjectName("clipboard_title")
            bottom_layout.addWidget(clipboard_title)

            # Area di testo per il clipboard
            self.clipboard_text = QTextEdit()
            self.clipboard_text.setPlaceholderText("Qui appariranno tutti i simboli IPA che copi...\n\nInizia cliccando sui pulsanti sopra! 🎵")
            self.clipboard_text.setReadOnly(False)  # Permetti modifica manuale
            bottom_layout.addWidget(self.clipboard_text)

            # Tutti i pulsanti di controllo su una sola riga
            all_buttons_layout = QHBoxLayout()

            # Pulsanti clipboard
            clear_clipboard_btn = QPushButton("🧹 Pulisci")
            clear_clipboard_btn.setObjectName("clipboard_btn")
            clear_clipboard_btn.clicked.connect(self.clear_clipboard)
            all_buttons_layout.addWidget(clear_clipboard_btn)

            copy_clipboard_btn = QPushButton("📋 Copia Tutto")
            copy_clipboard_btn.setObjectName("clipboard_btn")
            copy_clipboard_btn.clicked.connect(self.copy_clipboard_content)
            all_buttons_layout.addWidget(copy_clipboard_btn)

            select_all_btn = QPushButton("📝 Seleziona Tutto")
            select_all_btn.setObjectName("clipboard_btn")
            select_all_btn.clicked.connect(lambda: self.clipboard_text.selectAll())
            all_buttons_layout.addWidget(select_all_btn)

            # Separatore visivo
            all_buttons_layout.addStretch()

            # Pulsanti principali
            copy_all_symbols_btn = QPushButton("📚 Copia Tutti i Simboli")
            copy_all_symbols_btn.setObjectName("control")
            copy_all_symbols_btn.clicked.connect(lambda: self.copy_all_ipa_symbols())
            all_buttons_layout.addWidget(copy_all_symbols_btn)

            # Pulsante per abilitare/disabilitare TTS
            self.tts_enabled = True  # Stato iniziale: TTS abilitato
            tts_toggle_btn = QPushButton("🔊 TTS ON")
            tts_toggle_btn.setObjectName("control")
            tts_toggle_btn.clicked.connect(lambda: self.toggle_tts(tts_toggle_btn))
            all_buttons_layout.addWidget(tts_toggle_btn)

            close_button = QPushButton("❌ Chiudi")
            close_button.setObjectName("control")
            close_button.clicked.connect(ipa_dialog.close)
            all_buttons_layout.addWidget(close_button)

            # Aggiungi i pulsanti al layout del bottom_widget
            bottom_layout.addLayout(all_buttons_layout)

            # Aggiungi il bottom_widget al splitter
            splitter.addWidget(bottom_widget)

            # Imposta le proporzioni del splitter (70% pulsanti, 30% clipboard)
            splitter.setSizes([700, 300])

            # Inizializza clipboard vuoto
            self.clipboard_text.clear()

            # Mostra il dialog
            ipa_dialog.exec()

        except Exception as e:
            logging.error(f"Errore apertura dialog IPA: {e}")
            QMessageBox.critical(self, "Errore", f"Errore nell'apertura della guida IPA:\n{str(e)}")

    def copy_single_ipa_symbol_with_clipboard(self, symbol, dialog):
        """Copia un singolo simbolo IPA negli appunti e aggiungilo al clipboard del dialog. Se TTS è abilitato, pronuncia anche il simbolo."""
        try:
            # Copia negli appunti di sistema
            clipboard = QApplication.clipboard()
            if clipboard:
                clipboard.setText(symbol)

            # Aggiungi al clipboard del dialog
            current_text = self.clipboard_text.toPlainText()
            if current_text and not current_text.endswith(' '):
                self.clipboard_text.setPlainText(current_text + symbol)
            else:
                self.clipboard_text.setPlainText(current_text + symbol)

            # Scorri automaticamente alla fine
            cursor = self.clipboard_text.textCursor()
            cursor.movePosition(cursor.MoveOperation.End)
            self.clipboard_text.setTextCursor(cursor)

            # Se TTS è abilitato, pronuncia il simbolo
            if hasattr(self, 'tts_enabled') and self.tts_enabled:
                try:
                    # Converti il simbolo IPA in testo pronunciabile
                    pronunciation_text = self._ipa_to_pronunciation_text(symbol)

                    if pronunciation_text and TTS_AVAILABLE and TTSThread:
                        # Crea e avvia il thread TTS
                        tts_thread = TTSThread(
                            text=pronunciation_text,
                            engine_name='pyttsx3',  # Usa pyttsx3 per velocità
                            voice_or_lang='it',     # Voce italiana
                            speed=0.8,              # Più lento per chiarezza
                            pitch=1.0
                        )

                        # Connetti segnali
                        tts_thread.started_reading.connect(lambda: logging.info(f"🔊 Pronunciando simbolo IPA: {symbol}"))
                        tts_thread.finished_reading.connect(lambda: logging.info(f"✅ Pronuncia simbolo IPA completata: {symbol}"))
                        tts_thread.error_occurred.connect(lambda err: logging.error(f"❌ Errore pronuncia simbolo IPA {symbol}: {err}"))

                        # Avvia la pronuncia
                        tts_thread.start()

                        # Salva riferimento per evitare garbage collection
                        if not hasattr(self, '_tts_threads'):
                            self._tts_threads = []
                        self._tts_threads.append(tts_thread)

                except Exception as tts_error:
                    logging.warning(f"Errore TTS per simbolo IPA {symbol}: {tts_error}")
                    # Non mostrare errori TTS per non interrompere l'esperienza utente

            # Rimossa la notifica popup per un'esperienza più fluida

        except Exception as e:
            logging.error(f"Errore copia simbolo IPA: {e}")
            QMessageBox.critical(dialog, "Errore Copia", f"Errore durante la copia:\n{str(e)}")

    def clear_clipboard(self):
        """Pulisce l'area clipboard."""
        try:
            self.clipboard_text.clear()
            self.clipboard_text.setPlaceholderText("Clipboard pulito! 🎵\n\nInizia cliccando sui pulsanti sopra!")
        except Exception as e:
            logging.error(f"Errore pulizia clipboard: {e}")

    def copy_clipboard_content(self):
        """Copia tutto il contenuto del clipboard negli appunti di sistema."""
        try:
            content = self.clipboard_text.toPlainText()
            if content.strip():
                clipboard = QApplication.clipboard()
                if clipboard:
                    clipboard.setText(content)
                    QMessageBox.information(self, "Clipboard Copiato",
                                          f"✅ Tutto il contenuto del clipboard copiato negli appunti!\n\n"
                                          f"📝 {len(content)} caratteri copiati")
            else:
                QMessageBox.warning(self, "Clipboard Vuoto",
                                  "Il clipboard è vuoto. Clicca prima sui simboli IPA per riempirlo!")
        except Exception as e:
            logging.error(f"Errore copia clipboard: {e}")
            QMessageBox.critical(self, "Errore Copia", f"Errore durante la copia:\n{str(e)}")

    def pronounce_ipa_symbol(self, symbol, dialog=None):
        """Pronuncia un simbolo IPA e lo aggiunge al clipboard del dialog."""
        try:
            # Prima copia il simbolo nel clipboard (se dialog è fornito)
            if dialog and hasattr(self, 'clipboard_text'):
                # Copia negli appunti di sistema
                clipboard = QApplication.clipboard()
                if clipboard:
                    clipboard.setText(symbol)

                # Aggiungi al clipboard del dialog
                current_text = self.clipboard_text.toPlainText()
                if current_text and not current_text.endswith(' '):
                    self.clipboard_text.setPlainText(current_text + symbol)
                else:
                    self.clipboard_text.setPlainText(current_text + symbol)

                # Scorri automaticamente alla fine
                cursor = self.clipboard_text.textCursor()
                cursor.movePosition(cursor.MoveOperation.End)
                self.clipboard_text.setTextCursor(cursor)

            # Controlla se TTS è abilitato
            if not hasattr(self, 'tts_enabled') or not self.tts_enabled:
                QMessageBox.information(self, "TTS Disabilitato",
                                      "🔇 La sintesi vocale è attualmente disabilitata.\n\n"
                                      "Clicca sul pulsante '🔇 TTS OFF' per riabilitarla.")
                return

            if not TTS_AVAILABLE or not TTSThread:
                QMessageBox.warning(self, "TTS Non Disponibile",
                                  "Il sistema di sintesi vocale non è disponibile.\n\n"
                                  "Assicurati che le librerie 'pyttsx3' e 'gtts' siano installate.")
                return

            # Converti il simbolo IPA in testo pronunciabile
            pronunciation_text = self._ipa_to_pronunciation_text(symbol)

            if not pronunciation_text:
                QMessageBox.warning(self, "Simbolo Non Supportato",
                                  f"Il simbolo '{symbol}' non ha una pronuncia definita.")
                return

            # Crea e avvia il thread TTS
            # Converti il simbolo IPA in testo pronunciabile
            pronunciation_text = self._ipa_to_pronunciation_text(symbol)

            if not pronunciation_text:
                QMessageBox.warning(self, "Simbolo Non Supportato",
                                  f"Il simbolo '{symbol}' non ha una pronuncia definita.")
                return

            # Crea e avvia il thread TTS
            tts_thread = TTSThread(
                text=pronunciation_text,
                engine_name='pyttsx3',  # Usa pyttsx3 per velocità
                voice_or_lang='it',     # Voce italiana
                speed=0.8,              # Più lento per chiarezza
                pitch=1.0
            )

            # Connetti segnali
            tts_thread.started_reading.connect(lambda: logging.info(f"🔊 Pronunciando: {symbol}"))
            tts_thread.finished_reading.connect(lambda: logging.info(f"✅ Pronuncia completata: {symbol}"))
            tts_thread.error_occurred.connect(lambda err: logging.error(f"❌ Errore pronuncia {symbol}: {err}"))

            # Avvia la pronuncia
            tts_thread.start()

            # Salva riferimento per evitare garbage collection
            if not hasattr(self, '_tts_threads'):
                self._tts_threads = []
            self._tts_threads.append(tts_thread)

        except Exception as e:
            logging.error(f"Errore integrato pronuncia+copia IPA {symbol}: {e}")
            QMessageBox.critical(self, "Errore Integrato", f"Errore durante copia e pronuncia:\n{str(e)}")
            logging.error(f"Errore copia simbolo IPA: {e}")
            QMessageBox.critical(self, "Errore Copia", f"Errore durante la copia:\n{str(e)}")

    def copy_all_ipa_symbols(self):
        """Copia tutti i simboli IPA negli appunti."""
        try:
            all_symbols = """
VOCALI: [i] [e] [ɛ] [a] [ɔ] [o] [u]
CONSONANTI: [p] [b] [t] [d] [k] [g] [f] [v] [s] [z] [ʃ] [ʒ] [m] [n] [ɲ] [l] [ʎ] [r] [ʁ]
SPECIALI: [ˈ] [ˌ] [.] [:] [̯] [̃]

ESEMPI:
"casa" → [ˈka.za]
"pasta" → [ˈpas.ta]
"telefono" → [teˈlɛ.fo.no]
"grazie" → [ˈɡrat.t͡sje]
"occhio" → [ˈɔk.kjo]
            """

            clipboard = QApplication.clipboard()
            if clipboard:
                clipboard.setText(all_symbols.strip())
                QMessageBox.information(self, "Guida Completa Copiata",
                                      "✅ Tutti i simboli IPA copiati negli appunti!\n\n"
                                      "Ora hai a disposizione la guida completa per le trascrizioni fonetiche.")
        except Exception as e:
            logging.error(f"Errore copia tutti i simboli IPA: {e}")
            QMessageBox.critical(self, "Errore Copia", f"Errore durante la copia:\n{str(e)}")

    def copy_ipa_symbols(self, content):
        """Copia il contenuto IPA negli appunti."""
        try:
            clipboard = QApplication.clipboard()
            if clipboard:
                clipboard.setText(content)
                QMessageBox.information(self, "Copia Completata",
                                      "✅ Contenuto IPA copiato negli appunti!\n\n"
                                      "Ora puoi incollarlo dove necessario.")
            else:
                QMessageBox.warning(self, "Errore Appunti",
                                  "Impossibile accedere agli appunti del sistema.")
        except Exception as e:
            logging.error(f"Errore copia IPA: {e}")
            QMessageBox.critical(self, "Errore Copia", f"Errore durante la copia:\n{str(e)}")

    def toggle_tts(self, button):
        """Abilita/disabilita la sintesi vocale per i simboli IPA."""
        try:
            self.tts_enabled = not self.tts_enabled

            if self.tts_enabled:
                button.setText("🔊 TTS ON")
                button.setStyleSheet("""
                    QPushButton {
                        background-color: #28a745;
                        color: white;
                        border: none;
                        border-radius: 6px;
                        padding: 10px 18px;
                        font-weight: bold;
                        min-width: 120px;
                        font-size: 14px;
                    }
                    QPushButton:hover {
                        background-color: #218838;
                    }
                """)
                QMessageBox.information(self, "TTS Abilitato",
                                      "🔊 Sintesi vocale abilitata!\n\n"
                                      "Ora puoi cliccare sui pulsanti 🔊 accanto ai simboli IPA per sentirne la pronuncia.")
            else:
                button.setText("🔇 TTS OFF")
                button.setStyleSheet("""
                    QPushButton {
                        background-color: #dc3545;
                        color: white;
                        border: none;
                        border-radius: 6px;
                        padding: 10px 18px;
                        font-weight: bold;
                        min-width: 120px;
                        font-size: 14px;
                    }
                    QPushButton:hover {
                        background-color: #c82333;
                    }
                """)
                QMessageBox.information(self, "TTS Disabilitato",
                                      "🔇 Sintesi vocale disabilitata!\n\n"
                                      "I pulsanti 🔊 sono ora disattivati per risparmiare risorse.")

        except Exception as e:
            logging.error(f"Errore toggle TTS: {e}")
            QMessageBox.critical(self, "Errore TTS", f"Errore durante il cambio stato TTS:\n{str(e)}")

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

    def update_status_label(self):
        """Metodo deprecato - lo status è ora gestito dal pulsante log."""
        # Il pulsante log ha sostituito il label di stato
        pass



    def update_footer_status(self):
        """Aggiorna il label di stato nel footer con data, utente, sessione tutor e condivisione schermo."""
        from datetime import datetime
        import getpass

        try:
            # Data attuale
            current_date = datetime.now().strftime("%d/%m/%Y %H:%M")

            # Nome utente (da sistema)
            username = getpass.getuser()

            # Stato sessione tutor
            tutor_session = "Sì" if self.tutor_session_active else "No"

            # Stato condivisione schermo
            screen_sharing = "Sì" if self.screen_sharing_active else "No"

            # Aggiorna il testo del label nel footer
            status_text = f"📅 {current_date} | 👤 {username} | 🎓 Tutor: {tutor_session} | 🖥️ Condivisione: {screen_sharing}"
            if hasattr(self, 'status_footer_label'):
                self.status_footer_label.setText(status_text)

        except Exception as e:
            logging.error(f"Errore aggiornamento footer status: {e}")
            if hasattr(self, 'status_footer_label'):
                self.status_footer_label.setText("Status non disponibile")

    def set_tutor_session_status(self, active: bool):
        """Imposta lo stato della sessione tutor e aggiorna il footer."""
        self.tutor_session_active = active
        self.update_footer_status()

    def set_screen_sharing_status(self, active: bool):
        """Imposta lo stato della condivisione schermo e aggiorna il footer."""
        self.screen_sharing_active = active
        self.update_footer_status()

    def closeEvent(self, event):
        """Gestisce la chiusura dell'applicazione."""
        # Ferma il timer del footer
        if hasattr(self, 'footer_timer'):
            self.footer_timer.stop()

        # Chiama il metodo originale
        super().closeEvent(event)

    def handle_arduino_button(self):
        """Gestisce il pulsante Risposta Arduino - Funzionalità in sviluppo."""
        QMessageBox.information(self, "🔌 Risposta Arduino",
                              "🤖 Funzionalità Arduino in Sviluppo\n\n"
                              "⚙️ Questa sezione sarà dedicata a:\n"
                              "• Programmazione Arduino interattiva\n"
                              "• Simulazione circuiti elettronici\n"
                              "• Controllo dispositivi IoT\n"
                              "• Progetti maker e robotica\n\n"
                              "⚠️ Funzionalità attualmente in fase di implementazione")

    def handle_circuit_button(self):
        """Gestisce il pulsante Circuito elettrico - Funzionalità in sviluppo."""
        QMessageBox.information(self, "⚡ Circuito elettrico",
                              "🔌 Funzionalità Circuiti Elettrici in Sviluppo\n\n"
                              "⚡ Questa sezione sarà dedicata a:\n"
                              "• Simulazione circuiti elettrici\n"
                              "• Analisi componenti elettronici\n"
                              "• Progettazione schemi elettrici\n"
                              "• Calcoli elettrici interattivi\n\n"
                              "⚠️ Funzionalità attualmente in fase di implementazione")

    def handle_graphics_tablet_button(self):
        """Gestisce il pulsante Tavoletta grafica - Funzionalità in sviluppo."""
        QMessageBox.information(self, "🎨 Tavoletta grafica",
                              "🖼️ Funzionalità Tavoletta Grafica in Sviluppo\n\n"
                              "🎨 Questa sezione sarà dedicata a:\n"
                              "• Disegno digitale interattivo\n"
                              "• Editing immagini avanzato\n"
                              "• Strumenti artistici digitali\n"
                              "• Creazione grafica professionale\n\n"
                              "⚠️ Funzionalità attualmente in fase di implementazione")

    def handle_screen_share_button(self):
        """Gestisce il pulsante Condividi schermo - Funzionalità in sviluppo."""
        QMessageBox.information(self, "📺 Condividi schermo",
                              "🎬 Funzionalità Condivisione Schermo in Sviluppo\n\n"
                              "📺 Questa sezione sarà dedicata a:\n"
                              "• Condivisione schermo con VLC\n"
                              "• Streaming video in tempo reale\n"
                              "• Registrazione sessioni di lavoro\n"
                              "• Condivisione contenuti multimediali\n\n"
                              "⚠️ Funzionalità attualmente in fase di implementazione")

    def handle_collab_button(self):
        """Gestisce il pulsante Collabora Online - Funzionalità in sviluppo."""
        QMessageBox.information(self, "🤝 Collabora Online",
                              "🌐 Funzionalità Collaborazione Online in Sviluppo\n\n"
                              "🤝 Questa sezione sarà dedicata a:\n"
                              "• Collaborazione in tempo reale\n"
                              "• Condivisione progetti online\n"
                              "• Lavoro di squadra remoto\n"
                              "• Sincronizzazione contenuti\n\n"
                              "⚠️ Funzionalità attualmente in fase di implementazione")



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