#!/usr/bin/env python3
"""
Main 01 Aircraft - Launcher per la schermata principale
Richiama la porta aerei per avviare l'interfaccia principale
"""

import json
import logging
import os
import sys
from datetime import datetime
from PyQt6.QtCore import Qt, QTimer, QEvent, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFontDatabase, QFont, QColor, QShortcut, QKeySequence
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel,
    QPushButton, QHBoxLayout, QLineEdit, QTextEdit, QGroupBox,
    QScrollArea, QMessageBox, QFileDialog, QSlider, QDialog, QSplitter, QGridLayout, QFrame, QToolBox
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

# Import del sistema di errori user-friendly
try:
    from UI.user_friendly_errors import show_user_friendly_error, show_success_message  # type: ignore
except ImportError:
    # Fallback se il modulo non è disponibile
    def show_user_friendly_error(parent, error, context=""):
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.critical(parent, "Errore", "Errore: {str(error)}")

    def show_success_message(parent, operation, details=""):
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.information(parent, "Successo", "Operazione completata: {operation}")

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

    def dragEnterEvent(self, a0):
        """Accetta il drag se contiene testo o dati del widget."""
        if a0 is not None and hasattr(a0, 'mimeData'):
            mime_data = a0.mimeData()
            if mime_data and (mime_data.hasText() or mime_data.hasFormat("application/x-draggable-widget")):
                a0.acceptProposedAction()
                # Accetta sia MoveAction che CopyAction
                a0.setDropAction(Qt.DropAction.CopyAction)

    def dropEvent(self, a0):
        """Gestisce il drop creando un nuovo widget trascinabile."""
        try:
            from UI.draggable_text_widget import DraggableTextWidget

            # Ottieni il testo dal drop
            text = ""
            if a0 is not None and hasattr(a0, 'mimeData'):
                mime_data = a0.mimeData()
                if mime_data and mime_data.hasText():
                    text = mime_data.text()
                else:
                    return
            else:
                return

            if text and text.strip():
                # Crea un nuovo widget trascinabile con tutte le funzionalità
                widget = DraggableTextWidget(text, self.settings)
                # Aggiungi il widget al layout dell'area di lavoro
                self.widget_layout.addWidget(widget)
                a0.acceptProposedAction()

        except Exception:
            logging.error("Errore durante il drop nell'area di lavoro: {e}")


# Classe per gestire l'area pensierini con controllo duplicati
class PensieriniWidget(QWidget):
    def __init__(self, settings, pensierini_layout):
        super().__init__()
        self.settings = settings
        # Initialize pensierini_layout properly
        if pensierini_layout is None:
            self.pensierini_layout = QVBoxLayout()
        else:
            self.pensierini_layout = pensierini_layout
        self.setAcceptDrops(True)

        # Il layout sarà impostato esternamente, non creare automaticamente

    def dragEnterEvent(self, a0):
        """Accetta il drag se contiene testo o dati del widget."""
        try:
            if a0 and hasattr(a0, 'mimeData') and a0.mimeData():
                mime_data = a0.mimeData()
                if mime_data and (mime_data.hasText() or mime_data.hasFormat("application/x-draggable-widget")):
                    if hasattr(a0, 'acceptProposedAction'):
                        a0.acceptProposedAction()
                    if hasattr(a0, 'setDropAction'):
                        a0.setDropAction(Qt.DropAction.CopyAction)
        except Exception:
            logging.error("Errore in dragEnterEvent: {e}")

    def dropEvent(self, a0):
        """Gestisce il drop controllando se esiste già un widget con lo stesso testo."""
        try:
            from UI.draggable_text_widget import DraggableTextWidget

            # Ottieni il testo dal drop
            text = ""
            if a0 and hasattr(a0, 'mimeData') and a0.mimeData():
                mime_data = a0.mimeData()
                if mime_data and mime_data.hasText():
                    text = mime_data.text()
                else:
                    return
            else:
                return

            if text and text.strip():
                # Controlla se esiste già un pensierino con lo stesso testo
                existing_widget = self._find_existing_widget(text.strip())
                if existing_widget is not None:
                    # Esiste già un pensierino con lo stesso testo - non creare duplicato
                    if hasattr(a0, 'ignore'):
                        a0.ignore()
                    return

                # Crea un nuovo widget trascinabile con tutte le funzionalità
                widget = DraggableTextWidget(text, self.settings)
                # Aggiungi il widget al layout dei pensierini
                if hasattr(self, 'pensierini_layout') and self.pensierini_layout:
                    self.pensierini_layout.addWidget(widget)
                if hasattr(a0, 'acceptProposedAction'):
                    a0.acceptProposedAction()

        except Exception:
            logging.error("Errore durante il drop nell'area pensierini: {e}")

    def _find_existing_widget(self, text):
        """Cerca se esiste già un widget con lo stesso testo nei pensierini."""
        try:
            if not hasattr(self, 'pensierini_layout') or not self.pensierini_layout:
                return None

            for i in range(self.pensierini_layout.count()):
                item = self.pensierini_layout.itemAt(i)
                if item:
                    widget = item.widget()
                    if widget:
                        text_label = getattr(widget, 'text_label', None)
                        if text_label and hasattr(text_label, 'text'):
                            existing_text = text_label.text().strip()
                            if existing_text == text:
                                return widget
        except Exception:
            logging.error("Errore in _find_existing_widget: {e}")
        return None

# Classe MainWindow integrata da aircraft.py


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
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

        # Imposta un font sicuro e standard per evitare artefatti
        self.set_safe_font()

        self.setup_ui()

        # Tools panel always visible

        # Timer per aggiornare lo status del footer ogni minuto
        from PyQt6.QtCore import QTimer
        self.footer_timer = QTimer()
        self.footer_timer.timeout.connect(self.update_footer_status)
        self.footer_timer.start(60000)  # Aggiorna ogni 60 secondi

        logging.info("Applicazione avviata")

        # Log delle metriche iniziali dopo che l'UI è stata configurata
        QTimer.singleShot(1000, lambda: self.log_ui_metrics("INITIAL_SETUP"))

    def log_ui_metrics(self, context=""):
        """Registra le metriche dell'interfaccia per il debug."""
        try:
            # Dimensioni finestra principale
            window_size = self.size()
            window_pos = self.pos()

            # Posizioni e dimensioni dei pulsanti nella top bar
            buttons_info = {}
            try:
                if hasattr(self, 'options_button') and self.options_button is not None:
                    pos = self.options_button.pos()
                    size = self.options_button.size()
                    buttons_info['options_button'] = {
                        'pos': (pos.x(), pos.y()),
                        'size': (size.width(), size.height())
                    }
            except Exception as e:
                print(f"Error getting options_button metrics: {e}")

            try:
                if hasattr(self, 'toggle_tools_button') and self.toggle_tools_button is not None:
                    pos = self.toggle_tools_button.pos()
                    size = self.toggle_tools_button.size()
                    buttons_info['toggle_tools_button'] = {
                        'pos': (pos.x(), pos.y()),
                        'size': (size.width(), size.height())
                    }
            except Exception as e:
                print(f"Error getting toggle_tools_button metrics: {e}")

            try:
                if hasattr(self, 'save_button') and self.save_button is not None:
                    pos = self.save_button.pos()
                    size = self.save_button.size()
                    buttons_info['save_button'] = {
                        'pos': (pos.x(), pos.y()),
                        'size': (size.width(), size.height())
                    }
            except Exception as e:
                print(f"Error getting save_button metrics: {e}")

            try:
                if hasattr(self, 'load_button') and self.load_button is not None:
                    pos = self.load_button.pos()
                    size = self.load_button.size()
                    buttons_info['load_button'] = {
                        'pos': (pos.x(), pos.y()),
                        'size': (size.width(), size.height())
                    }
            except Exception as e:
                print(f"Error getting load_button metrics: {e}")

            # Dimensioni del layout principale
            main_layout_geometry = None
            try:
                if hasattr(self, 'centralWidget') and self.centralWidget():
                    cw = self.centralWidget()
                    if cw:
                        geom = cw.geometry()
                        main_layout_geometry = (geom.x(), geom.y(), geom.width(), geom.height())
            except Exception as e:
                print(f"Error getting central widget geometry: {e}")

            # Dimensioni dello splitter verticale
            splitter_sizes = None
            if hasattr(self, 'vertical_splitter'):
                splitter_sizes = self.vertical_splitter.sizes()

            metrics = {
                'context': context,
                'timestamp': datetime.now().isoformat(),
                'window': {
                    'size': (window_size.width(), window_size.height()),
                    'pos': (window_pos.x(), window_pos.y())
                },
                'buttons': buttons_info,
                'main_layout': main_layout_geometry,
                'splitter_sizes': splitter_sizes
            }

            # Salva in un file di log per analisi
            import json
            import os
            log_dir = os.path.join(os.path.dirname(__file__), "debug_logs")
            os.makedirs(log_dir, exist_ok=True)
            log_file = os.path.join(log_dir, "ui_metrics.jsonl")

            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(metrics, ensure_ascii=False) + '\n')

            print(f"📊 UI Metrics logged - Context: {context}")
            print(f"   Window size: {window_size.width()}x{window_size.height()}")
            print(f"   Window pos: {window_pos.x()}, {window_pos.y()}")

            for btn_name, btn_data in buttons_info.items():
                print(f"   {btn_name}: pos={btn_data['pos']}, size={btn_data['size']}")

            if splitter_sizes:
                print(f"   Splitter sizes: {splitter_sizes}")

        except Exception as e:
            print(f"❌ Error logging UI metrics: {e}")

    def create_unified_tools_section(self):
        """Crea la sezione unificata per pensierini e strumenti con layout orizzontale"""
        # Contenitore principale per la sezione unificata
        unified_section = QWidget()
        unified_layout = QVBoxLayout(unified_section)
        unified_layout.setContentsMargins(5, 5, 5, 5)

        # QSplitter orizzontale per pensierini + strumenti
        tools_splitter = QSplitter(Qt.Orientation.Horizontal)
        tools_splitter.setHandleWidth(4)
        tools_splitter.setStyleSheet("""
            QSplitter::handle {
                background: rgba(108, 117, 125, 0.4);
                border: 1px solid rgba(108, 117, 125, 0.6);
                border-radius: 2px;
            }
            QSplitter::handle:hover {
                background: rgba(74, 144, 226, 0.6);
                border-color: rgba(74, 144, 226, 0.8);
            }
        """)

        # === Colonna unica: Strumenti con input pensierini in basso ===
        tools_section = self.create_unified_tools_section_content()
        tools_splitter.addWidget(tools_section)

        # Imposta proporzioni: 100% strumenti (input pensierini ora dentro)
        tools_splitter.setSizes([1])

        unified_layout.addWidget(tools_splitter)
        return unified_section

    def create_pensierini_input_section(self):
        """Crea la sezione input pensierini"""
        pensierini_group = QGroupBox("✏️ Creazione Pensierini")
        pensierini_group.setMinimumHeight(150)
        pensierini_group.setMaximumHeight(150)

        layout = QVBoxLayout(pensierini_group)
        layout.setContentsMargins(8, 15, 8, 8)

        # Campo di testo in alto (occupa tutto lo spazio disponibile)
        self.input_text_area.setFixedHeight(60)  # Più alto per migliore usabilità
        layout.addWidget(self.input_text_area)

        # Riga pulsanti in basso
        buttons_row = QHBoxLayout()
        buttons_row.setSpacing(8)

        self.add_pensierino_button.setFixedHeight(32)
        buttons_row.addWidget(self.add_pensierino_button, 1)

        # Pulsante pulisci
        self.clear_pensierini_button = QPushButton("🧹 Pulisci Tutto")
        self.clear_pensierini_button.setFixedHeight(32)
        self.clear_pensierini_button.setObjectName("clear_pensierini_button")
        self.clear_pensierini_button.clicked.connect(self.clear_all_pensierini_with_confirmation)
        buttons_row.addWidget(self.clear_pensierini_button, 1)

        layout.addLayout(buttons_row)

        return pensierini_group

    def clear_column_a(self):
        """Pulisce la colonna A (pensierini)"""
        try:
            # Per ora, mostriamo solo un messaggio informativo
            # La pulizia effettiva dei pensierini richiede l'implementazione specifica
            print("✅ Colonna A (pensierini) - pulizia pianificata")
            QMessageBox.information(self, "Info Pulizia", "La pulizia della colonna A sarà implementata nella prossima versione.")
        except Exception as e:
            print(f"⚠️ Errore pulizia colonna A: {e}")

    def clear_column_b(self):
        """Pulisce la colonna B (area di lavoro)"""
        try:
            if hasattr(self, 'work_area_layout') and self.work_area_layout:
                # Rimuove tutti i widget dalla colonna B in modo sicuro
                count = self.work_area_layout.count()
                for i in range(count - 1, -1, -1):  # Scorri al contrario per sicurezza
                    item = self.work_area_layout.itemAt(i)
                    if item:
                        widget = item.widget()
                        if widget:
                            self.work_area_layout.removeItem(item)
                            widget.setVisible(False)  # Nasconde invece di eliminare
                print("✅ Colonna B (area di lavoro) pulita")
        except Exception as e:
            print(f"⚠️ Errore pulizia colonna B: {e}")

    def clear_column_c(self):
        """Pulisce la colonna C (dettagli)"""
        try:
            if hasattr(self, 'details_layout') and self.details_layout:
                # Rimuove tutti i widget dalla colonna C in modo sicuro
                count = self.details_layout.count()
                for i in range(count - 1, -1, -1):  # Scorri al contrario per sicurezza
                    item = self.details_layout.itemAt(i)
                    if item:
                        widget = item.widget()
                        if widget:
                            self.details_layout.removeItem(item)
                            widget.setVisible(False)  # Nasconde invece di eliminare
                print("✅ Colonna C (dettagli) pulita")
        except Exception as e:
            print(f"⚠️ Errore pulizia colonna C: {e}")

    def clear_input_text(self):
        """Pulisce il campo di input testo"""
        if hasattr(self, 'input_text_area'):
            self.input_text_area.clear()
            print("✅ Campo di input testo pulito")

    def clear_all_pensierini_with_confirmation(self):
        """Pulisce tutto (input + colonne A, B, C) con conferma"""
        reply = QMessageBox.question(
            self,
            "Conferma Pulizia Totale",
            "⚠️ ATTENZIONE: Questa azione pulirà:\n\n"
            "• Il campo di input testo\n"
            "• Tutti i pensierini (Colonna A)\n"
            "• L'area di lavoro (Colonna B)\n"
            "• I dettagli (Colonna C)\n\n"
            "Questa operazione è IRREVERSIBILE.\n\n"
            "Vuoi continuare?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Procedi con la pulizia
            self.clear_input_text()
            self.clear_column_a()
            self.clear_column_b()
            self.clear_column_c()

            QMessageBox.information(
                self,
                "Pulizia Completata",
                "✅ Tutto è stato pulito con successo!\n\n"
                "• Campo di input: VUOTO\n"
                "• Colonna A: VUOTA\n"
                "• Colonna B: VUOTA\n"
                "• Colonna C: VUOTA"
            )
        else:
            print("❌ Pulizia annullata dall'utente")

    def create_unified_tools_section_content(self):
        """Crea il contenuto unificato di tutti gli strumenti con schede e area risultati"""
        # Prima creo tutti i pulsanti necessari
        self._create_subject_buttons()

        tools_group = QGroupBox("🛠️ Strumenti e Assistenza")
        tools_group.setMinimumHeight(200)

        layout = QVBoxLayout(tools_group)
        layout.setContentsMargins(8, 15, 8, 8)

        # QSplitter orizzontale per schede + area risultati
        tools_splitter = QSplitter(Qt.Orientation.Horizontal)

        # Colonna sinistra: Schede con tutti gli strumenti
        tabs_widget = self.create_tools_tabs()
        tools_splitter.addWidget(tabs_widget)

        # Colonna destra: Area risultati/visualizzazione - REMOVED

        # Imposta proporzioni: 100% schede (risultati rimossi)
        tools_splitter.setSizes([1])

        layout.addWidget(tools_splitter)

        # Aggiungi sezione input pensierini in basso
        pensierini_input_section = self.create_pensierini_input_section()
        layout.addWidget(pensierini_input_section)

        return tools_group



    def _create_subject_buttons(self):
        """Crea i pulsanti delle materie e li restituisce come lista"""
        # Dati dei pulsanti delle materie
        buttons_data = [
            ("📝 IPA", "ipa_button", self.handle_ipa_button),
            ("🔢 Matematica", "math_button", self.handle_math_button),
            ("⚗️ Chimica", "chemistry_button", self.handle_chemistry_button),
            ("⚛️ Fisica", "physics_button", self.handle_physics_button),
            ("🧬 Biologia", "biology_button", self.handle_biology_button),
            ("🇮🇹 Italiano", "italian_button", self.handle_italian_button),
            ("📚 Storia", "history_button", self.handle_history_button),
            ("💻 Info", "computer_science_button", self.handle_computer_science_button),
            ("🖥️ Sistemi", "os_scripting_button", self.handle_os_scripting_button),
            ("🌌 Astronomia", "astronomy_button", self.handle_astronomy_button),
            ("📐 Mat.Sup.", "advanced_math_button", self.handle_advanced_math_button),
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

        # Crea i pulsanti e li salva come attributi della classe
        subject_buttons = []
        for text, obj_name, handler in buttons_data:
            button = QPushButton(text)
            button.setObjectName(obj_name)
            button.clicked.connect(handler)
            setattr(self, obj_name, button)
            subject_buttons.append(button)

        return subject_buttons

    def create_tools_tabs(self):
        """Crea il widget con schede per tutti gli strumenti"""
        from PyQt6.QtWidgets import QTabWidget

        tabs = QTabWidget()
        # tabs.setTabPosition(QTabWidget.TabPosition.West)  # Commentato per layout orizzontale
        tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #dee2e6;
                border-radius: 6px;
                background: rgba(255, 255, 255, 0.95);
            }

            QTabBar::tab {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ffffff, stop:1 #f8f9fa);
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 8px 16px;
                margin-right: 2px;
                color: #495057;
                font-weight: bold;
                font-size: 12px;
                min-width: 80px;
            }

            QTabBar::tab:selected {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #e3f2fd, stop:1 #bbdefb);
                border-color: #2196f3;
                color: #1976d2;
            }

            QTabBar::tab:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f8f9ff, stop:1 #e8f4fd);
                border-color: #64b5f6;
            }
        """)

        # Scheda 1: Trascrizione
        transcription_tab = self.create_transcription_tab()
        tabs.addTab(transcription_tab, "🎤 Trascrizione")

        # Scheda 2: AI & Media
        ai_media_tab = self.create_ai_media_tab()
        tabs.addTab(ai_media_tab, "🧠 AI & Media")

        # Scheda 3: Materie
        subjects_tab = self.create_subjects_tab()
        tabs.addTab(subjects_tab, "📚 Materie")

        # Scheda 4: Utilità
        utilities_tab = self.create_utilities_tab()
        tabs.addTab(utilities_tab, "🛠️ Utilità")

        # Scheda 5: IoT
        iot_tab = self.create_iot_tab()
        tabs.addTab(iot_tab, "🔌 IoT")

        return tabs

    def create_transcription_tab(self):
        """Crea la scheda Trascrizione"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(8)
        layout.setContentsMargins(10, 15, 10, 10)

        layout.addWidget(self.voice_button)
        layout.addWidget(self.audio_transcription_button)
        layout.addWidget(self.ocr_button)
        layout.addWidget(self.graphics_tablet_button)

        layout.addStretch()  # Spazio flessibile
        return widget

    def create_ai_media_tab(self):
        """Crea la scheda AI & Media"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(8)
        layout.setContentsMargins(10, 15, 10, 10)

        layout.addWidget(self.ai_button)

        # Gruppo riconoscimento
        recognition_group = QGroupBox("👁️ Riconoscimento")
        recognition_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 11px;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                margin-top: 8px;
                padding-top: 10px;
                background: rgba(255, 255, 255, 0.8);
            }
        """)
        recognition_layout = QVBoxLayout(recognition_group)
        recognition_layout.addWidget(self.face_button)
        recognition_layout.addWidget(self.hand_button)
        layout.addWidget(recognition_group)

        layout.addStretch()
        return widget

    def create_subjects_tab(self):
        """Crea la scheda Materie"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 15, 10, 10)

        # Scroll area per le materie
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        subjects_widget = QWidget()
        subjects_layout = QGridLayout(subjects_widget)
        subjects_layout.setSpacing(4)
        subjects_layout.setContentsMargins(5, 5, 5, 5)

        # Aggiungi pulsanti materie in griglia
        subject_buttons = self._create_subject_buttons()
        for i, button in enumerate(subject_buttons):
            row, col = divmod(i, 4)  # 4 colonne invece di 5 per adattarsi meglio
            subjects_layout.addWidget(button, row, col)

        scroll.setWidget(subjects_widget)
        layout.addWidget(scroll)
        return widget

    def create_utilities_tab(self):
        """Crea la scheda Utilità"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(8)
        layout.setContentsMargins(10, 15, 10, 10)

        layout.addWidget(self.media_button)
        layout.addWidget(self.clean_button)
        layout.addWidget(self.log_button)

        layout.addStretch()
        return widget

    def create_iot_tab(self):
        """Crea la scheda IoT"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(8)
        layout.setContentsMargins(10, 15, 10, 10)

        layout.addWidget(self.arduino_button)
        layout.addWidget(self.circuit_button)
        layout.addWidget(self.screen_share_button)
        layout.addWidget(self.collab_button)

        layout.addStretch()
        return widget



    def _create_all_buttons(self):
        """Crea tutti i pulsanti necessari per il nuovo layout unificato"""
        # Crea pulsanti di trascrizione
        self.voice_button = QPushButton("🎤 Voce → Testo")
        self.voice_button.setObjectName("voice_button")
        self.voice_button.setMinimumWidth(140)
        self.voice_button.clicked.connect(self.handle_voice_button)

        self.audio_transcription_button = QPushButton("🎵 Audio → Testo")
        self.audio_transcription_button.setObjectName("audio_transcription_button")
        self.audio_transcription_button.setMinimumWidth(140)
        self.audio_transcription_button.clicked.connect(self.handle_audio_transcription_button)

        self.ocr_button = QPushButton("📄 OCR → Testo")
        self.ocr_button.setObjectName("ocr_button")
        self.ocr_button.setMinimumWidth(140)
        self.ocr_button.clicked.connect(self.handle_ocr_button)

        self.graphics_tablet_button = QPushButton("🎨 Tavoletta")
        self.graphics_tablet_button.setObjectName("graphics_tablet_button")
        self.graphics_tablet_button.setMinimumWidth(140)
        self.graphics_tablet_button.clicked.connect(self.handle_graphics_tablet_button)

        # Crea pulsanti AI e media
        self.ai_button = QPushButton("🧠 Chiedi ad A.I.")
        self.ai_button.setObjectName("ai_button")
        self.ai_button.setMinimumWidth(140)
        self.ai_button.clicked.connect(self.handle_ai_button)

        self.face_button = QPushButton("❌ Faccia/e")
        self.face_button.setObjectName("face_button")
        self.face_button.setMinimumWidth(140)
        self.face_button.setCheckable(True)
        self.face_button.clicked.connect(self.handle_face_recognition)

        self.hand_button = QPushButton("❌ Gesti")
        self.hand_button.setObjectName("hand_button")
        self.hand_button.setMinimumWidth(140)
        self.hand_button.setCheckable(True)
        self.hand_button.clicked.connect(self.handle_hand_gestures)

        # Crea pulsanti utilità
        self.media_button = QPushButton("📁 Carica Media")
        self.media_button.setObjectName("media_button")
        self.media_button.setMinimumWidth(140)
        self.media_button.clicked.connect(self.handle_media_button)

        self.clean_button = QPushButton("🧹 Pulisci")
        self.clean_button.setObjectName("clean_button")
        self.clean_button.setMinimumWidth(140)
        self.clean_button.clicked.connect(self.handle_clean_button)

        self.log_button = QPushButton("📋 Log")
        self.log_button.setObjectName("footer_log_button")
        self.log_button.setMinimumWidth(140)
        self.log_button.setCheckable(True)
        self.log_button.clicked.connect(self.handle_log_toggle)

        # Crea pulsanti IoT
        self.arduino_button = QPushButton("🔌 Arduino")
        self.arduino_button.setObjectName("arduino_button")
        self.arduino_button.setMinimumWidth(140)
        self.arduino_button.clicked.connect(self.handle_arduino_button)

        self.circuit_button = QPushButton("⚡ Circuito")
        self.circuit_button.setObjectName("circuit_button")
        self.circuit_button.setMinimumWidth(140)
        self.circuit_button.clicked.connect(self.handle_circuit_button)

        self.screen_share_button = QPushButton("📺 Condividi")
        self.screen_share_button.setObjectName("screen_share_button")
        self.screen_share_button.setMinimumWidth(140)
        self.screen_share_button.clicked.connect(self.handle_screen_share_button)

        self.collab_button = QPushButton("🤝 Collabora")
        self.collab_button.setObjectName("collab_button")
        self.collab_button.setMinimumWidth(140)
        self.collab_button.clicked.connect(self.handle_collab_button)

    def toggle_tools_panel(self):
        """Mostra/nasconde il pannello degli strumenti nel nuovo layout unificato."""
        # Log metriche PRIMA del toggle
        self.log_ui_metrics("BEFORE_TOGGLE")

        if self.tools_group.isVisible():
            # Nasconde la sezione unificata strumenti
            self.tools_group.setVisible(False)
            # Ricalcola le proporzioni per dare più spazio al contenuto principale
            current_sizes = self.vertical_splitter.sizes()
            main_content_size = current_sizes[0]  # Contenuto principale
            tools_size = current_sizes[1]         # Sezione strumenti
            total_current = main_content_size + tools_size
            # Distribuisci tutto lo spazio al contenuto principale
            self.vertical_splitter.setSizes([total_current, 0])

            # Aggiorna il testo del pulsante
            if hasattr(self, 'toggle_tools_button'):
                self.toggle_tools_button.setText("🔧 Visualizza Ingranaggi")

            # Salva nelle preferenze
            self.settings['ui'] = self.settings.get('ui', {})
            self.settings['ui']['tools_panel_visible'] = False
        else:
            # Mostra la sezione unificata strumenti
            self.tools_group.setVisible(True)
            # Ripristina proporzioni bilanciate
            current_sizes = self.vertical_splitter.sizes()
            main_content_size = current_sizes[0]  # Contenuto principale
            tools_size = current_sizes[1]         # Sezione strumenti
            total_current = main_content_size + tools_size
            # 70% contenuto principale, 30% sezione strumenti
            main_new = int(total_current * 0.7)
            tools_new = total_current - main_new
            self.vertical_splitter.setSizes([main_new, tools_new])

            # Aggiorna il testo del pulsante
            if hasattr(self, 'toggle_tools_button'):
                self.toggle_tools_button.setText("🔧 Nascondi Ingranaggi")

            # Salva nelle preferenze
            self.settings['ui'] = self.settings.get('ui', {})
            self.settings['ui']['tools_panel_visible'] = True

        # Log metriche DOPO il toggle
        QTimer.singleShot(100, lambda: self.log_ui_metrics("AFTER_TOGGLE"))

        # Salva le impostazioni
        from main_03_configurazione_e_opzioni import save_settings
        save_settings(self.settings)

    def set_safe_font(self):
        """Imposta un font sicuro e standard per evitare artefatti di rendering, usando le preferenze utente."""
        try:
            # Ottieni le preferenze font dalle impostazioni utente
            user_font_family = self.settings.get('fonts', {}).get('main_font_family', 'Arial')
            user_font_size = self.settings.get('fonts', {}).get('main_font_size', 12)

            # Lista di font sicuri e standard, ordinati per priorità
            safe_fonts = [
                user_font_family,  # Prima priorità: font scelto dall'utente
                'Segoe UI',      # Windows moderno
                'SF Pro Display',  # macOS moderno
                'Ubuntu',        # Linux moderno
                'Arial',         # Universale
                'Helvetica',     # Universale
                'DejaVu Sans',   # Linux comune
                'Liberation Sans',  # Linux comune
                'Verdana',       # Windows comune
                'Tahoma'         # Windows comune
            ]

            # Trova il primo font disponibile
            available_fonts = QFontDatabase.families()
            selected_font = None

            for font_name in safe_fonts:
                if font_name in available_fonts:
                    selected_font = font_name
                    break

            if selected_font:
                # Imposta il font sicuro con dimensione dalle preferenze utente
                safe_font = QFont(selected_font, user_font_size)
                safe_font.setWeight(QFont.Weight.Normal)
                safe_font.setStyleHint(QFont.StyleHint.System)  # Hint per sistema
                QApplication.setFont(safe_font)
                logging.info(f"✅ Font sicuro impostato: {selected_font} ({user_font_size}pt)")
            else:
                # Fallback al font di sistema con dimensione utente
                system_font = QApplication.font()
                system_font.setPointSize(user_font_size)
                QApplication.setFont(system_font)
                logging.info(f"✅ Font di sistema impostato come fallback ({user_font_size}pt)")

        except Exception as e:
            logging.error(f"❌ Errore impostazione font sicuro: {e}")
            # Assicurati che ci sia sempre un font valido
            try:
                system_font = QApplication.font()
                system_font.setPointSize(12)
                QApplication.setFont(system_font)
            except BaseException:
                pass  # Se anche questo fallisce, lascia il default di Qt

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

            # Controlla se è una risposta di riformulazione
            if "Riformula intensamente" in prompt or "Riformulazione intensa" in prompt:
                # Mostra la riformulazione nell'area risultati
                full_content = "🧠 RIFORMULAZIONE COMPLETATA\n\n✨ Testo riformulato con intelligenza artificiale:\n\n{response}\n\n{'=' * 50}\n\n📊 Statistiche:\n• Testo originale: {len(self.full_text) if hasattr(self, 'full_text') else 0} caratteri\n• Testo riformulato: {len(response)} caratteri"

                # Log della riformulazione
                logging.info("Riformulazione AI completata: {len(response)} caratteri")

                # Mostra anche nei dettagli per compatibilità
                self.show_text_in_details(full_content)
            else:
                # Risposta AI normale (non riformulazione)
                full_content = "📤 Richiesta:\n{prompt}\n\n{'=' * 50}\n\n🤖 Risposta AI (llama2:7b):\n\n{response}"

                # Log della risposta ricevuta
                logging.info("Risposta AI ricevuta per prompt: {prompt[:50]}... (lunghezza: {len(response)} caratteri)")

                # Mostra anche nei dettagli per compatibilità
                self.show_text_in_details(full_content)

        except Exception as e:
            logging.error(f"Errore nella gestione della risposta AI: {e}")
            error_msg = f"❌ Errore nella gestione della risposta AI:\n{str(e)}"
            show_user_friendly_error(self, e, "risposta AI")
            # Riabilita il pulsante in caso di errore
            if hasattr(self, 'rephrase_button'):
                self.rephrase_button.setEnabled(True)

    def _on_ai_error_occurred(self, error_msg):
        """Gestisce gli errori da Ollama."""
        logging.error("Errore AI: {error_msg}")
        # Crea un'eccezione per il sistema user-friendly
        ai_error = Exception("Errore dal servizio AI: {error_msg}")
        show_user_friendly_error(self, ai_error, "servizio AI")

    def update_footer_status_old(self):
        """Aggiorna le informazioni di stato nel footer - versione precedente."""
        try:
            from datetime import datetime
            current_time = datetime.now().strftime("%H:%M:%S")
            status_text = "🕐 {current_time} | 👤 Sessione attiva | 📊 Sistema operativo"
        except Exception:
            logging.error("Errore nell'aggiornamento del footer: {e}")

    def setup_ui(self):

        # Usa le dimensioni dalla configurazione globale
        window_width = self.settings.get('ui', {}).get('window_width', 1200)
        window_height = self.settings.get('ui', {}).get('window_height', 800)


        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Applica stile globale con font sicuro
        # Carica colori dalle impostazioni centralizzate
        colors = self.settings.get('colors', {})
        button_text_colors = colors.get('button_text_colors', {})
        button_border_colors = colors.get('button_border_colors', {})
        button_background_colors = colors.get('button_background_colors', {})
        button_hover_colors = colors.get('button_hover_colors', {})
        button_pressed_colors = colors.get('button_pressed_colors', {})

        # Carica preferenze font dalle impostazioni
        main_font_size = self.settings.get('fonts', {}).get('main_font_size', 13)
        pensierini_font_size = self.settings.get('fonts', {}).get('pensierini_font_size', 12)

        # CSS dinamico basato sulle impostazioni colori - REMOVED

        main_layout = QVBoxLayout(central_widget)

        # Top bar
        top_layout = QHBoxLayout()
        self.options_button = QPushButton("⚙️ Opzioni")
        self.options_button.setObjectName("options_button")  # ID per CSS
        self.options_button.clicked.connect(self.open_settings)
        top_layout.addWidget(self.options_button)

        # Pulsante per mostrare/nascondere il pannello strumenti (spostato in basso)

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
        self.main_splitter.setHandleWidth(8)  # Increased divider width for better visibility
        self.main_splitter.setStyleSheet("""
            QSplitter::handle {
                background: rgba(108, 117, 125, 0.4);
                border: 1px solid rgba(108, 117, 125, 0.6);
                border-radius: 2px;
            }
            QSplitter::handle:hover {
                background: rgba(74, 144, 226, 0.6);
                border-color: rgba(74, 144, 226, 0.8);
            }
            QSplitter::handle:pressed {
                background: rgba(74, 144, 226, 0.8);
                border-color: rgba(74, 144, 226, 1.0);
            }
        """)

        # Column A: Pensierini
        self.column_a_group = QGroupBox("📝 Contenuti pensierini creativi (A)")
        self.column_a_group.setObjectName("pensierini")  # ID per CSS
        self.column_a_group.setMinimumWidth(250)  # Improved minimum width for better usability
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
        self.column_b_group.setMinimumWidth(280)  # Improved minimum width for work area
        column_b_layout = QVBoxLayout(self.column_b_group)
        self.setup_work_area(column_b_layout)
        self.main_splitter.addWidget(self.column_b_group)

        # Column C: Details
        self.column_c_group = QGroupBox("Lavagna risposta Interattiva & AI")
        self.column_c_group.setObjectName("details")  # ID per CSS
        self.column_c_group.setMinimumWidth(300)  # Minimum width for details
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

        # Accordion per la creazione pensierini
        self.pensierini_toolbox = QToolBox()
        self.pensierini_toolbox.setObjectName("pensierini_toolbox")
        self.pensierini_toolbox.setMinimumHeight(120)  # Ottimizzato per compattezza
        self.pensierini_toolbox.setMaximumHeight(160)  # Limite ragionevole per evitare spreco
        self.pensierini_toolbox.setStyleSheet("""
            QToolBox {
                background: rgba(255, 255, 255, 0.95);
                border: 1px solid #dee2e6;
                border-radius: 6px;
                font-weight: bold;
                font-size: 12px;
            }

            QToolBox::tab {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ffffff, stop:1 #f8f9fa);
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 6px 12px;
                margin: 1px;
                color: #495057;
                font-weight: bold;
                min-height: 16px;
                font-size: 12px;
            }

            QToolBox::tab:selected {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #e8f5e8, stop:1 #c8e6c9);
                border-color: #4caf50;
                color: #2e7d32;
            }

            QToolBox::tab:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f8fff8, stop:1 #e8f5e8);
                border-color: #81c784;
            }
        """)

        # Crea la pagina per l'input dei pensierini
        pensierini_page = QWidget()
        pensierini_page.setObjectName("pensierini_page")
        pensierini_layout = QVBoxLayout(pensierini_page)
        pensierini_layout.setContentsMargins(10, 15, 10, 10)

        # Riga input testo + pulsante aggiungi pensierino
        input_row_layout = QHBoxLayout()
        input_row_layout.setSpacing(10)  # Spazio tra elementi

        self.input_text_area = QTextEdit()
        self.input_text_area.setPlaceholderText("Scrivi qui, ( premi INVIO per creare un pensierino - Premi INVIO di destra per tornare a capo )")
        self.input_text_area.setFixedHeight(35)  # Altezza esatta del pulsante "Aggiungi Pensierino"
        # Rimuovi limite di larghezza massima per permettere espansione
        # Installa event filter per intercettare Invio
        self.input_text_area.installEventFilter(self)
        input_row_layout.addWidget(self.input_text_area, 4)  # Stretch factor 4 (80% circa)

        self.add_pensierino_button = QPushButton("➕ Aggiungi Pensierino")
        self.add_pensierino_button.setObjectName("add_pensierino_button")
        self.add_pensierino_button.setMaximumWidth(150)  # Larghezza massima ridotta
        self.add_pensierino_button.clicked.connect(self.add_text_from_input_area)
        input_row_layout.addWidget(self.add_pensierino_button, 1)  # Stretch factor 1 (20% circa)

        pensierini_layout.addLayout(input_row_layout)

        # Aggiungi la pagina al QToolBox (mantenuto per compatibilità ma non utilizzato nel nuovo layout)
        self.pensierini_toolbox.addItem(pensierini_page, "✏️ Crea Pensierini")
        self.pensierini_toolbox.setCurrentIndex(0)  # Espandi per default

        # ===========================================
        # === SEZIONE STRUMENTI AVANZATI ===
        # ===========================================
        # Nota: Il QToolBox tradizionale è stato sostituito dal nuovo layout unificato
        # Questo codice è mantenuto per compatibilità ma non viene utilizzato

        # Crea QToolBox (Accordion) per gli strumenti - MANTENUTO PER COMPATIBILITÀ
        self.tools_toolbox = QToolBox()
        self.tools_toolbox.setObjectName("tools_toolbox")
        self.tools_toolbox.setMinimumHeight(320)
        self.tools_toolbox.setStyleSheet("""
            QToolBox {
                background: rgba(255, 255, 255, 0.95);
                border: 1px solid #dee2e6;
                border-radius: 6px;
                font-weight: bold;
                font-size: 13px;
            }

            QToolBox::tab {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ffffff, stop:1 #f8f9fa);
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 8px 16px;
                margin: 1px;
                color: #495057;
                font-weight: bold;
                min-height: 18px;
                font-size: 13px;
            }

            QToolBox::tab:selected {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #e3f2fd, stop:1 #bbdefb);
                border-color: #2196f3;
                color: #1976d2;
            }

            QToolBox::tab:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f8f9ff, stop:1 #e8f4fd);
                border-color: #64b5f6;
            }

            QToolBox QScrollArea {
                border: none;
                background: transparent;
            }
        """)

        # Crea le pagine per il QToolBox (Accordion)
        # Ogni categoria avrà la sua pagina espandibile

        # === PAGINA 1: TRASCRIZIONE ===
        # Contiene: Voce→Testo, Audio→Testo, OCR→Testo, Tavoletta Grafica
        transcription_page = QWidget()
        transcription_page.setObjectName("transcription_page")
        transcription_layout = QVBoxLayout(transcription_page)
        transcription_layout.setSpacing(10)
        transcription_layout.setContentsMargins(12, 20, 12, 15)

        # Add buttons directly to vertical layout
        self.voice_button = QPushButton("🎤 Voce → Testo")
        self.voice_button.setObjectName("voice_button")
        self.voice_button.setMinimumWidth(140)
        self.voice_button.clicked.connect(self.handle_voice_button)
        transcription_layout.addWidget(self.voice_button)

        self.audio_transcription_button = QPushButton("🎵 Audio → Testo")
        self.audio_transcription_button.setObjectName("audio_transcription_button")
        self.audio_transcription_button.setMinimumWidth(140)
        self.audio_transcription_button.clicked.connect(self.handle_audio_transcription_button)
        transcription_layout.addWidget(self.audio_transcription_button)

        self.ocr_button = QPushButton("📄 OCR → Testo")
        self.ocr_button.setObjectName("ocr_button")
        self.ocr_button.setMinimumWidth(140)
        self.ocr_button.clicked.connect(self.handle_ocr_button)
        transcription_layout.addWidget(self.ocr_button)

        self.graphics_tablet_button = QPushButton("🎨 Tavoletta")
        self.graphics_tablet_button.setObjectName("graphics_tablet_button")
        self.graphics_tablet_button.setMinimumWidth(140)
        self.graphics_tablet_button.clicked.connect(self.handle_graphics_tablet_button)
        transcription_layout.addWidget(self.graphics_tablet_button)

        # === PAGINA 2: AI E MEDIA ===
        # Contiene: AI, Riconoscimento (Faccia, Gesti)
        ai_media_page = QWidget()
        ai_media_page.setObjectName("ai_media_page")
        ai_media_layout = QVBoxLayout(ai_media_page)
        ai_media_layout.setSpacing(10)
        ai_media_layout.setContentsMargins(12, 20, 12, 15)

        self.ai_button = QPushButton("🧠 Chiedi ad A.I.")
        self.ai_button.setObjectName("ai_button")
        self.ai_button.setMinimumWidth(140)
        self.ai_button.clicked.connect(self.handle_ai_button)
        ai_media_layout.addWidget(self.ai_button)

        # Sottogruppo riconoscimento
        recognition_group = QGroupBox("👁️ Riconoscimento")
        recognition_group.setObjectName("recognition_subgroup")
        recognition_group.setStyleSheet("""
            QGroupBox#recognition_subgroup {
                font-weight: bold;
                font-size: 12px;
                color: #495057;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                margin-top: 8px;
                padding-top: 15px;
                background: rgba(255, 255, 255, 0.7);
                min-height: 80px;
            }

            QGroupBox#recognition_subgroup::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 2px 6px;
                color: #6c757d;
                font-weight: bold;
                background: rgba(248, 249, 250, 0.8);
                border-radius: 3px;
            }
        """)
        recognition_layout = QVBoxLayout(recognition_group)
        recognition_layout.setSpacing(8)
        recognition_layout.setContentsMargins(8, 20, 8, 8)

        self.face_button = QPushButton("❌ Faccia/e")
        self.face_button.setObjectName("face_button")
        self.face_button.setMinimumWidth(140)
        self.face_button.setCheckable(True)
        self.face_button.clicked.connect(self.handle_face_recognition)
        recognition_layout.addWidget(self.face_button)

        self.hand_button = QPushButton("❌ Gesti")
        self.hand_button.setObjectName("hand_button")
        self.hand_button.setMinimumWidth(140)
        self.hand_button.setCheckable(True)
        self.hand_button.clicked.connect(self.handle_hand_gestures)
        recognition_layout.addWidget(self.hand_button)

        ai_media_layout.addWidget(recognition_group)

        # === PAGINA 3: CONOSCENZA ===
        # Contiene: Griglia 4x5 con 20 materie scolastiche
        knowledge_page = QWidget()
        knowledge_page.setObjectName("knowledge_page")
        knowledge_layout = QGridLayout(knowledge_page)
        knowledge_layout.setSpacing(8)
        knowledge_layout.setContentsMargins(15, 25, 15, 15)

        # Griglia 4x5 per i pulsanti delle materie
        buttons_data = [
            ("📝 IPA", "ipa_button", self.handle_ipa_button),
            ("🔢 Matematica", "math_button", self.handle_math_button),
            ("⚗️ Chimica", "chemistry_button", self.handle_chemistry_button),
            ("⚛️ Fisica", "physics_button", self.handle_physics_button),
            ("🧬 Biologia", "biology_button", self.handle_biology_button),
            ("🇮🇹 Italiano", "italian_button", self.handle_italian_button),
            ("📚 Storia", "history_button", self.handle_history_button),
            ("💻 Info", "computer_science_button", self.handle_computer_science_button),
            ("🖥️ Sistemi", "os_scripting_button", self.handle_os_scripting_button),
            ("🌌 Astronomia", "astronomy_button", self.handle_astronomy_button),
            ("📐 Mat.Sup.", "advanced_math_button", self.handle_advanced_math_button),
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

        # === PAGINA 4: UTILITÀ ===
        # Contiene: Carica Media, Pulisci, Log
        utilities_page = QWidget()
        utilities_page.setObjectName("utilities_page")
        utilities_layout = QVBoxLayout(utilities_page)
        utilities_layout.setSpacing(10)
        utilities_layout.setContentsMargins(12, 20, 12, 15)

        self.media_button = QPushButton("📁 Carica Media")
        self.media_button.setObjectName("media_button")
        self.media_button.setMinimumWidth(140)
        self.media_button.clicked.connect(self.handle_media_button)
        utilities_layout.addWidget(self.media_button)

        self.clean_button = QPushButton("🧹 Pulisci")
        self.clean_button.setObjectName("clean_button")
        self.clean_button.setMinimumWidth(140)
        self.clean_button.clicked.connect(self.handle_clean_button)
        utilities_layout.addWidget(self.clean_button)

        self.log_button = QPushButton("📋 Log")
        self.log_button.setObjectName("footer_log_button")
        self.log_button.setMinimumWidth(140)
        self.log_button.setCheckable(True)
        self.log_button.clicked.connect(self.handle_log_toggle)
        utilities_layout.addWidget(self.log_button)

        # === PAGINA 5: IOT ===
        # Contiene: Arduino, Circuito, Condividi Schermo, Collabora
        iot_page = QWidget()
        iot_page.setObjectName("iot_page")
        iot_layout = QVBoxLayout(iot_page)
        iot_layout.setSpacing(10)
        iot_layout.setContentsMargins(12, 20, 12, 15)

        self.arduino_button = QPushButton("🔌 Arduino")
        self.arduino_button.setObjectName("arduino_button")
        self.arduino_button.setMinimumWidth(140)
        self.arduino_button.clicked.connect(self.handle_arduino_button)
        iot_layout.addWidget(self.arduino_button)

        self.circuit_button = QPushButton("⚡ Circuito")
        self.circuit_button.setObjectName("circuit_button")
        self.circuit_button.setMinimumWidth(140)
        self.circuit_button.clicked.connect(self.handle_circuit_button)
        iot_layout.addWidget(self.circuit_button)

        self.screen_share_button = QPushButton("📺 Condividi")
        self.screen_share_button.setObjectName("screen_share_button")
        self.screen_share_button.setMinimumWidth(140)
        self.screen_share_button.clicked.connect(self.handle_screen_share_button)
        iot_layout.addWidget(self.screen_share_button)

        self.collab_button = QPushButton("🤝 Collabora")
        self.collab_button.setObjectName("collab_button")
        self.collab_button.setMinimumWidth(140)
        self.collab_button.clicked.connect(self.handle_collab_button)
        iot_layout.addWidget(self.collab_button)

        # ===========================================
        # === AGGIUNGI PAGINE AL QTOOLBOX ===
        # ===========================================

        # Aggiungi tutte le pagine al QToolBox con i titoli appropriati
        self.tools_toolbox.addItem(transcription_page, "🎤 Trascrizione")
        self.tools_toolbox.addItem(ai_media_page, "🧠 AI & Media")
        self.tools_toolbox.addItem(knowledge_page, "📚 Materie")
        self.tools_toolbox.addItem(utilities_page, "🛠️ Utilità")
        self.tools_toolbox.addItem(iot_page, "🔌 IoT")

        # Imposta la pagina iniziale espansa (Trascrizione)
        self.tools_toolbox.setCurrentIndex(0)

        # Prima creo tutti i pulsanti necessari per il nuovo layout
        self._create_all_buttons()

        # Create unified vertical splitter with 2 rows: main content + unified tools section
        from PyQt6.QtWidgets import QSplitter
        vertical_splitter = QSplitter(Qt.Orientation.Vertical)
        vertical_splitter.setHandleWidth(6)  # Slightly wider for better visibility
        vertical_splitter.setStyleSheet("""
            QSplitter::handle {
                background: rgba(74, 144, 226, 0.4);
                border: 1px solid rgba(74, 144, 226, 0.6);
                border-radius: 3px;
            }
            QSplitter::handle:hover {
                background: rgba(74, 144, 226, 0.6);
                border-color: rgba(74, 144, 226, 0.8);
            }
            QSplitter::handle:pressed {
                background: rgba(74, 144, 226, 0.8);
                border-color: rgba(74, 144, 226, 1.0);
            }
        """)

        # ROW 1: Main content (columns A, B, C)
        vertical_splitter.addWidget(self.main_splitter)

        # ROW 2: Unified section containing pensierini + tools
        unified_tools_section = self.create_unified_tools_section()
        vertical_splitter.addWidget(unified_tools_section)

        # Save reference to vertical_splitter
        self.vertical_splitter = vertical_splitter
        self.tools_group = unified_tools_section  # For toggle compatibility

        # Set minimum window size
        self.setMinimumSize(1000, 850)

        # Check preferences for initial tools panel state
        tools_visible = self.settings.get('ui', {}).get('tools_panel_visible', True)
        if tools_visible:
            vertical_splitter.setSizes([450, 450])  # 50% main content, 50% unified tools
            if hasattr(self, 'toggle_tools_button'):
                self.toggle_tools_button.setChecked(True)
                self.toggle_tools_button.setText("🔧 Nascondi Ingranaggi")
        else:
            vertical_splitter.setSizes([800, 50])  # Hide tools section when not visible
            self.tools_group.setVisible(False)
            if hasattr(self, 'toggle_tools_button'):
                self.toggle_tools_button.setChecked(False)
                self.toggle_tools_button.setText("🔧 Visualizza Ingranaggi")

        # Add vertical splitter to main layout
        main_layout.addWidget(vertical_splitter, 1)

        # Footer con informazioni di stato
        footer_layout = QHBoxLayout()

        # Pulsante per mostrare/nascondere il pannello strumenti (in basso a sinistra)
        self.toggle_tools_button = QPushButton("🔧 Ingranaggi")
        self.toggle_tools_button.setObjectName("toggle_tools_button")
        self.toggle_tools_button.setCheckable(True)
        self.toggle_tools_button.setMinimumHeight(32)  # Altezza ridotta per il footer
        self.toggle_tools_button.clicked.connect(self.toggle_tools_panel)
        footer_layout.addWidget(self.toggle_tools_button)

        footer_layout.addStretch()  # Spazio centrale

        # Label per informazioni di stato in basso a destra
        self.status_footer_label = QLabel()
        self.status_footer_label.setObjectName("status_footer_label")

        # Usa dimensione font dalle preferenze per il footer (un po' più piccola)
        footer_font_size = self.settings.get('fonts', {}).get('main_font_size', 13) - 2
        self.status_footer_label.setStyleSheet(f"""
            QLabel#status_footer_label {{
                color: #495057;
                font-size: {footer_font_size}px;
                padding: 6px 12px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255, 255, 255, 0.95), stop:1 rgba(248, 249, 250, 0.95));
                border-radius: 8px;
                border: 1px solid #dee2e6;
                font-weight: bold;
                text-align: center;
                min-height: 20px;
            }}
        """)
        self.update_footer_status()  # Aggiorna le informazioni di stato
        footer_layout.addWidget(self.status_footer_label)

        # Spazio tra status_footer_label e click_status_label
        footer_layout.addSpacing(15)

        # Mouse click tracking label accanto alla data (a destra)
        self.click_status_label = QLabel("Clicca su un elemento...")
        self.click_status_label.setObjectName("click_status_label")
        click_font_size = self.settings.get('fonts', {}).get('main_font_size', 13) - 1
        self.click_status_label.setStyleSheet(f"""
            QLabel#click_status_label {{
                color: #666;
                font-size: {click_font_size}px;
                padding: 5px 10px;
                background: rgba(255, 255, 255, 0.8);
                border-radius: 5px;
                border: 1px solid #ddd;
                font-weight: normal;
                text-align: left;
                min-height: 20px;
                max-width: 200px;
            }}
        """)
        footer_layout.addWidget(self.click_status_label)

        main_layout.addLayout(footer_layout)

        # Install event filter to capture mouse clicks
        QTimer.singleShot(100, self._install_event_filters)

        # Apply modern UI improvements
        QTimer.singleShot(200, self._apply_modern_ui_styles)

    def _apply_modern_ui_styles(self):
        """Applica stili moderni e miglioramenti all'interfaccia utente."""
        try:
            # Stili moderni per l'intera applicazione
            modern_css = """
                /* Stili base moderni */
                QWidget {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #f8f9fa, stop:1 #e9ecef);
                    color: #212529;
                }

                /* Miglioramenti per i GroupBox */
                QGroupBox {
                    font-weight: bold;
                    font-size: 14px;
                    color: #495057;
                    border: 2px solid #dee2e6;
                    border-radius: 8px;
                    margin-top: 12px;
                    padding-top: 20px;
                    background: rgba(255, 255, 255, 0.8);
                }

                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 12px;
                    padding: 4px 8px;
                    color: #495057;
                    font-weight: bold;
                    background: rgba(255, 255, 255, 0.9);
                    border-radius: 4px;
                }

                /* Stili specifici per il nuovo layout con schede */
                QGroupBox#pensierini_group {
                    font-size: 12px;
                    font-weight: bold;
                    margin-top: 6px;
                    padding-top: 12px;
                    min-height: 80px;
                    border: 1px solid #dee2e6;
                    border-radius: 6px;
                }

                /* Area risultati */
                QGroupBox#results_group {
                    font-size: 13px;
                    font-weight: bold;
                    margin-top: 6px;
                    padding-top: 12px;
                    border: 2px solid #28a745;
                    border-radius: 6px;
                    background: rgba(255, 255, 255, 0.95);
                }

                QGroupBox#results_group QTextEdit {
                    background: rgba(240, 255, 240, 0.9);
                    border: 1px solid #28a745;
                    border-radius: 4px;
                    font-family: 'Segoe UI', Arial, sans-serif;
                }

                /* Pulsanti compatti nelle schede */
                QTabWidget QPushButton {
                    min-height: 32px;
                    font-size: 11px;
                    padding: 6px 12px;
                    margin: 2px;
                    border-radius: 4px;
                }

                /* Griglia delle materie nelle schede */
                QScrollArea QPushButton {
                    min-width: 90px;
                    max-width: 130px;
                    font-size: 10px;
                    padding: 4px 6px;
                    margin: 1px;
                }

                /* Miglioramenti per le schede */
                QTabWidget {
                    background: rgba(255, 255, 255, 0.95);
                    border-radius: 6px;
                }

                QTabWidget::tab-bar {
                    alignment: left;
                }

                /* Splitter migliorato per il layout unificato */
                QSplitter::handle:vertical {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 rgba(74, 144, 226, 0.3),
                        stop:1 rgba(74, 144, 226, 0.5));
                    border: 1px solid rgba(74, 144, 226, 0.6);
                    border-radius: 2px;
                }

                QSplitter::handle:vertical:hover {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 rgba(74, 144, 226, 0.6),
                        stop:1 rgba(74, 144, 226, 0.8));
                    border-color: rgba(74, 144, 226, 0.8);
                }

                QSplitter::handle:horizontal {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 rgba(74, 144, 226, 0.3),
                        stop:1 rgba(74, 144, 226, 0.5));
                    border: 1px solid rgba(74, 144, 226, 0.6);
                    border-radius: 2px;
                }

                QSplitter::handle:horizontal:hover {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 rgba(74, 144, 226, 0.6),
                        stop:1 rgba(74, 144, 226, 0.8));
                    border-color: rgba(74, 144, 226, 0.8);
                }

                /* Stili moderni per tutti i pulsanti */
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #ffffff, stop:1 #f8f9fa);
                    border: 2px solid #dee2e6;
                    border-radius: 6px;
                    padding: 8px 16px;
                    font-weight: 500;
                    font-size: 13px;
                    color: #495057;
                    min-height: 32px;
                    transition: all 0.3s ease;
                }

                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #e3f2fd, stop:1 #bbdefb);
                    border-color: #2196f3;
                    color: #1976d2;
                    transform: translateY(-1px);
                    box-shadow: 0 4px 8px rgba(33, 150, 243, 0.2);
                }

                QPushButton:pressed {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #bbdefb, stop:1 #90caf9);
                    transform: translateY(0px);
                    box-shadow: 0 2px 4px rgba(33, 150, 243, 0.3);
                }

                QPushButton:disabled {
                    background: #f5f5f5;
                    color: #9e9e9e;
                    border-color: #e0e0e0;
                    opacity: 0.6;
                }

                /* Pulsanti speciali nella top bar */
                QPushButton#options_button, QPushButton#toggle_tools_button,
                QPushButton#save_button, QPushButton#load_button {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #ffffff, stop:1 #f8f9fa);
                    border: 2px solid #6c757d;
                    font-weight: bold;
                    min-width: 100px;
                }

                QPushButton#options_button:hover {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #fff3cd, stop:1 #ffeaa7);
                    border-color: #ffc107;
                    color: #856404;
                }

                QPushButton#toggle_tools_button:hover {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #d1ecf1, stop:1 #bee5eb);
                    border-color: #17a2b8;
                    color: #0c5460;
                }

                QPushButton#save_button:hover {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #d4edda, stop:1 #c3e6cb);
                    border-color: #28a745;
                    color: #155724;
                }

                QPushButton#load_button:hover {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #f8d7da, stop:1 #f5c6cb);
                    border-color: #dc3545;
                    color: #721c24;
                }

                /* Miglioramenti per le aree di testo */
                QTextEdit, QLineEdit {
                    border: 2px solid #ced4da;
                    border-radius: 6px;
                    padding: 8px 12px;
                    background: #ffffff;
                    font-size: 13px;
                    selection-background-color: #007bff;
                    transition: border-color 0.3s ease;
                }

                QTextEdit:focus, QLineEdit:focus {
                    border-color: #007bff;
                    box-shadow: 0 0 0 3px rgba(0, 123, 255, 0.1);
                }

                /* Miglioramenti per gli scroll area */
                QScrollArea {
                    border: 1px solid #dee2e6;
                    border-radius: 6px;
                    background: rgba(255, 255, 255, 0.8);
                }

                QScrollBar:vertical {
                    background: #f8f9fa;
                    width: 12px;
                    border-radius: 6px;
                    margin: 2px;
                }

                QScrollBar::handle:vertical {
                    background: #dee2e6;
                    border-radius: 6px;
                    min-height: 30px;
                    transition: background 0.3s ease;
                }

                QScrollBar::handle:vertical:hover {
                    background: #adb5bd;
                }

                QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                    border: none;
                    background: none;
                }

                /* Miglioramenti per i splitter */
                QSplitter::handle {
                    background: rgba(108, 117, 125, 0.3);
                    border-radius: 3px;
                    transition: background 0.3s ease;
                }

                QSplitter::handle:hover {
                    background: rgba(108, 117, 125, 0.6);
                }

                /* Stili per il footer */
                QLabel#status_footer_label {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 rgba(255, 255, 255, 0.95), stop:1 rgba(248, 249, 250, 0.95));
                    border: 1px solid #dee2e6;
                    border-radius: 8px;
                    font-weight: 500;
                    color: #495057;
                }

                QLabel#click_status_label {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 rgba(255, 255, 255, 0.9), stop:1 rgba(248, 249, 250, 0.9));
                    border: 1px solid #dee2e6;
                    border-radius: 6px;
                    font-weight: 500;
                    color: #495057;
                    transition: all 0.3s ease;
                }

                QLabel#click_status_label:hover {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 rgba(220, 237, 255, 0.9), stop:1 rgba(187, 222, 251, 0.9));
                    border-color: #2196f3;
                }
            """

                # Applica gli stili moderni
            self.setStyleSheet(self.styleSheet() + modern_css)

            # Aggiungi animazioni per alcuni elementi
            self._add_animations()

            # Aggiungi tooltip informativi
            self._add_tooltips()

            # Aggiungi scorciatoie da tastiera
            self._add_keyboard_shortcuts()

            logging.info("✅ Stili moderni applicati con successo")

        except Exception as e:
            logging.error(f"❌ Errore nell'applicazione degli stili moderni: {e}")

    def _add_animations(self):
        """Aggiunge animazioni fluide per migliorare l'esperienza utente."""
        try:
            # Animazione per il pulsante toggle tools
            if hasattr(self, 'toggle_tools_button'):
                self.toggle_animation = QPropertyAnimation(self.toggle_tools_button, b"geometry")
                self.toggle_animation.setDuration(300)
                self.toggle_animation.setEasingCurve(QEasingCurve.Type.OutCubic)

            # Animazione per il click status label
            if hasattr(self, 'click_status_label'):
                self.click_label_animation = QPropertyAnimation(self.click_status_label, b"windowOpacity")
                self.click_label_animation.setDuration(200)
                self.click_label_animation.setStartValue(0.7)
                self.click_label_animation.setEndValue(1.0)
                self.click_label_animation.setEasingCurve(QEasingCurve.Type.InOutQuad)

        except Exception as e:
            logging.error(f"❌ Errore nell'aggiunta delle animazioni: {e}")

    def _add_tooltips(self):
        """Aggiunge tooltip informativi per migliorare l'usabilità."""
        try:
            # Tooltip per i pulsanti della top bar
            if hasattr(self, 'options_button'):
                self.options_button.setToolTip("⚙️ Configura le impostazioni dell'applicazione\n"
                                             "Personalizza colori, font e preferenze")

            if hasattr(self, 'toggle_tools_button'):
                self.toggle_tools_button.setToolTip("🔧 Mostra/Nasconde il pannello degli strumenti\n"
                                                  "Contiene tutte le funzionalità avanzate")

            if hasattr(self, 'save_button'):
                self.save_button.setToolTip("💾 Salva il progetto corrente\n"
                                          "Salva tutti i pensierini e le impostazioni")

            if hasattr(self, 'load_button'):
                self.load_button.setToolTip("📂 Carica un progetto salvato\n"
                                          "Ripristina pensierini e impostazioni precedenti")

            # Tooltip per i pulsanti di input
            if hasattr(self, 'add_pensierino_button'):
                self.add_pensierino_button.setToolTip("➕ Aggiungi un nuovo pensierino\n"
                                                    "Crea un elemento trascinabile con il testo inserito")

            # Tooltip per i pulsanti degli strumenti
            if hasattr(self, 'voice_button'):
                self.voice_button.setToolTip("🎤 Riconoscimento vocale\n"
                                           "Converte la voce in testo usando Vosk\n"
                                           "Premi e parla chiaramente nel microfono")

            if hasattr(self, 'audio_transcription_button'):
                self.audio_transcription_button.setToolTip("🎵 Trascrizione file audio\n"
                                                         "Converte file audio in testo\n"
                                                         "Supporta vari formati audio")

            if hasattr(self, 'ocr_button'):
                self.ocr_button.setToolTip("📄 Riconoscimento ottico caratteri\n"
                                         "Estrae testo dalle immagini\n"
                                         "Supporta screenshot e file immagine")

            if hasattr(self, 'ai_button'):
                self.ai_button.setToolTip("🧠 Chiedi all'Intelligenza Artificiale\n"
                                        "Invia richieste a Ollama AI\n"
                                        "Ottieni risposte intelligenti e riformulazioni")

            if hasattr(self, 'face_button'):
                self.face_button.setToolTip("❌ Riconoscimento facciale\n"
                                          "Attiva/disattiva il riconoscimento facce\n"
                                          "Funzionalità in sviluppo")

            if hasattr(self, 'hand_button'):
                self.hand_button.setToolTip("❌ Riconoscimento gesti\n"
                                          "Attiva/disattiva il riconoscimento gesti\n"
                                          "Funzionalità in sviluppo")

            # Tooltip per i pulsanti delle materie
            subject_tooltips = {
                'ipa_button': "📝 Fonetica Internazionale\nPronuncia e simboli IPA",
                'math_button': "🔢 Matematica\nCalcoli e formule matematiche",
                'chemistry_button': "⚗️ Chimica\nReazioni e composti chimici",
                'physics_button': "⚛️ Fisica\nLeggi fisiche e meccanica",
                'biology_button': "🧬 Biologia\nScienze della vita e organismi",
                'italian_button': "🇮🇹 Italiano\nGrammatica e letteratura italiana",
                'history_button': "📚 Storia\nEventi storici e civiltà",
                'computer_science_button': "💻 Informatica\nProgrammazione e algoritmi",
                'astronomy_button': "🌌 Astronomia\nStelle, pianeti e universo",
                'advanced_math_button': "📐 Matematica Avanzata\nAnalisi e geometria",
                'law_button': "⚖️ Diritto\nLeggi e giurisprudenza",
                'english_button': "🇺🇸 Inglese\nLingua e letteratura inglese",
                'spanish_button': "🇪🇸 Spagnolo\nLingua e cultura ispanica",
                'german_button': "🇩🇪 Tedesco\nLingua e letteratura tedesca",
                'japanese_button': "🇯🇵 Giapponese\nLingua e cultura giapponese",
                'chinese_button': "🇨🇳 Cinese\nLingua e cultura cinese",
                'russian_button': "🇷🇺 Russo\nLingua e letteratura russa"
            }

            # Applica i tooltip alle materie
            for button_name, tooltip in subject_tooltips.items():
                if hasattr(self, button_name):
                    button = getattr(self, button_name)
                    button.setToolTip(f"{tooltip}\nFunzionalità in sviluppo")

            # Tooltip per gli altri pulsanti
            if hasattr(self, 'media_button'):
                self.media_button.setToolTip("📁 Carica file multimediali\n"
                                           "Immagini, audio, video e documenti")

            if hasattr(self, 'clean_button'):
                self.clean_button.setToolTip("🧹 Pulisci tutto\n"
                                           "Rimuovi tutti i pensierini e resetta l'area di lavoro")

            if hasattr(self, 'log_button'):
                self.log_button.setToolTip("📋 Mostra/Nasconde il pannello log\n"
                                         "Visualizza i messaggi di sistema e debug")

            # Tooltip per i controlli di navigazione
            if hasattr(self, 'back_button'):
                self.back_button.setToolTip("⬅️ Pagina precedente\n"
                                          "Torna alla pagina precedente del testo")

            if hasattr(self, 'forward_button'):
                self.forward_button.setToolTip("➡️ Pagina successiva\n"
                                             "Vai alla pagina successiva del testo")

            if hasattr(self, 'copy_button'):
                self.copy_button.setToolTip("📋 Copia tutto il testo\n"
                                          "Copia il contenuto completo negli appunti")

            if hasattr(self, 'rephrase_button'):
                self.rephrase_button.setToolTip("🧠 Riformula intensamente\n"
                                              "Usa AI per migliorare e riformulare il testo")

            # Tooltip per le aree di input
            if hasattr(self, 'input_text_area'):
                self.input_text_area.setToolTip("Scrivi qui il testo per creare pensierini\n"
                                              "Premi INVIO per creare un pensierino\n"
                                              "Premi Shift+INVIO per andare a capo")

            if hasattr(self, 'project_name_input'):
                self.project_name_input.setToolTip("Nome del progetto corrente\n"
                                                "Viene usato per salvare/caricare progetti")

            logging.info("✅ Tooltip informativi aggiunti con successo")

        except Exception as e:
            logging.error(f"❌ Errore nell'aggiunta dei tooltip: {e}")

    def _add_keyboard_shortcuts(self):
        """Aggiunge scorciatoie da tastiera per migliorare l'usabilità."""
        try:
            # Scorciatoie principali
            QShortcut(QKeySequence("Ctrl+S"), self).activated.connect(self.save_project)
            QShortcut(QKeySequence("Ctrl+O"), self).activated.connect(self.load_project)
            QShortcut(QKeySequence("Ctrl+N"), self).activated.connect(self._new_project)
            QShortcut(QKeySequence("F1"), self).activated.connect(self._show_help)
            QShortcut(QKeySequence("Ctrl+T"), self).activated.connect(self.toggle_tools_panel)
            QShortcut(QKeySequence("Ctrl+L"), self).activated.connect(self._toggle_log_panel)

            # Scorciatoie per funzioni comuni
            QShortcut(QKeySequence("F2"), self).activated.connect(self._focus_input_area)
            QShortcut(QKeySequence("F3"), self).activated.connect(self._focus_search)
            QShortcut(QKeySequence("Ctrl+Return"), self).activated.connect(self.add_text_from_input_area)

            # Scorciatoie per navigazione
            QShortcut(QKeySequence("Ctrl+1"), self).activated.connect(lambda: self._focus_column(0))
            QShortcut(QKeySequence("Ctrl+2"), self).activated.connect(lambda: self._focus_column(1))
            QShortcut(QKeySequence("Ctrl+3"), self).activated.connect(lambda: self._focus_column(2))

            # Scorciatoie per funzioni AI e media
            QShortcut(QKeySequence("Ctrl+A"), self).activated.connect(self.handle_ai_button)
            QShortcut(QKeySequence("Ctrl+V"), self).activated.connect(self.handle_voice_button)
            QShortcut(QKeySequence("Ctrl+M"), self).activated.connect(self.handle_media_button)

            logging.info("✅ Scorciatoie da tastiera aggiunte con successo")

        except Exception as e:
            logging.error(f"❌ Errore nell'aggiunta delle scorciatoie: {e}")

    def _new_project(self):
        """Crea un nuovo progetto (resetta tutto)."""
        try:
            reply = QMessageBox.question(self, "Nuovo Progetto",
                                       "Vuoi creare un nuovo progetto?\n"
                                       "Tutti i pensierini non salvati andranno persi.",
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

            if reply == QMessageBox.StandardButton.Yes:
                # Pulisci tutti i pensierini
                self._clear_all_pensierini()
                # Reset nome progetto
                if hasattr(self, 'project_name_input'):
                    self.project_name_input.clear()
                # Reset area di lavoro
                self._clear_work_area()
                # Reset dettagli
                self._clear_details()

                QMessageBox.information(self, "Nuovo Progetto",
                                      "✅ Nuovo progetto creato con successo!")

        except Exception as e:
            logging.error(f"Errore nella creazione del nuovo progetto: {e}")

    def _show_help(self):
        """Mostra la finestra di aiuto con tutte le scorciatoie."""
        help_text = """
        <h2>🎯 Guida Rapida - CogniFlow</h2>

        <h3>🔥 Scorciatoie Principali</h3>
        <ul>
        <li><b>Ctrl+S</b> - Salva progetto</li>
        <li><b>Ctrl+O</b> - Carica progetto</li>
        <li><b>Ctrl+N</b> - Nuovo progetto</li>
        <li><b>F1</b> - Mostra questa guida</li>
        <li><b>Ctrl+T</b> - Mostra/Nasconde strumenti</li>
        </ul>

        <h3>⚡ Scorciatoie di Input</h3>
        <ul>
        <li><b>F2</b> - Focus sull'area di input</li>
        <li><b>Ctrl+Return</b> - Aggiungi pensierino</li>
        <li><b>Ctrl+A</b> - Chiedi all'AI</li>
        <li><b>Ctrl+V</b> - Riconoscimento vocale</li>
        </ul>

        <h3>🎨 Navigazione</h3>
        <ul>
        <li><b>Ctrl+1</b> - Focus colonna pensierini</li>
        <li><b>Ctrl+2</b> - Focus area di lavoro</li>
        <li><b>Ctrl+3</b> - Focus colonna dettagli</li>
        </ul>

        <h3>🎯 Mouse Tracking</h3>
        <p>Il sistema traccia tutti gli eventi del mouse in basso a sinistra:</p>
        <ul>
        <li>👆 SINISTRO/DESTRO/CENTRALE - Click dei pulsanti</li>
        <li>👇 RELEASE - Rilascio pulsanti</li>
        <li>👆👆 DOUBLE_CLICK - Doppio click</li>
        <li>🌀 SU/GIÙ - Rotella del mouse</li>
        </ul>

        <h3>💡 Suggerimenti</h3>
        <ul>
        <li>Passa il mouse sui pulsanti per vedere i tooltip</li>
        <li>Usa Invio nell'area di input per creare pensierini</li>
        <li>Trascina i pensierini nell'area di lavoro</li>
        <li>Usa Ctrl+T per nascondere/mostrare gli strumenti</li>
        </ul>
        """

        QMessageBox.information(self, "🎯 Guida CogniFlow", help_text)

    def _toggle_log_panel(self):
        """Mostra/Nasconde il pannello log."""
        if hasattr(self, 'log_button'):
            self.log_button.click()

    def _focus_input_area(self):
        """Imposta il focus sull'area di input."""
        if hasattr(self, 'input_text_area'):
            self.input_text_area.setFocus()

    def _focus_search(self):
        """Imposta il focus sulla barra di ricerca (se presente)."""
        # Placeholder per futura implementazione
        pass

    def _focus_column(self, column_index):
        """Imposta il focus su una colonna specifica."""
        try:
            if column_index == 0 and hasattr(self, 'pensierini_scroll'):
                self.pensierini_scroll.setFocus()
            elif column_index == 1 and hasattr(self, 'work_area_scroll'):
                self.work_area_scroll.setFocus()
            elif column_index == 2 and hasattr(self, 'details_scroll'):
                self.details_scroll.setFocus()
        except Exception as e:
            logging.error(f"Errore nel focus della colonna {column_index}: {e}")

    def _clear_all_pensierini(self):
        """Pulisce tutti i pensierini dalla colonna A."""
        try:
            if hasattr(self, 'pensierini_layout') and self.pensierini_layout:
                while self.pensierini_layout.count():
                    item = self.pensierini_layout.takeAt(0)
                    if item:
                        widget = item.widget()
                        if widget and hasattr(widget, 'deleteLater'):
                            widget.deleteLater()
        except Exception as e:
            logging.error(f"Errore nella pulizia dei pensierini: {e}")

    def _clear_work_area(self):
        """Pulisce l'area di lavoro."""
        try:
            if hasattr(self, 'work_area_layout') and self.work_area_layout:
                while self.work_area_layout.count():
                    item = self.work_area_layout.takeAt(0)
                    if item:
                        widget = item.widget()
                        if widget and hasattr(widget, 'deleteLater'):
                            widget.deleteLater()
        except Exception as e:
            logging.error(f"Errore nella pulizia dell'area di lavoro: {e}")

    def _install_event_filters(self):
        """Install event filters for mouse click tracking."""
        try:
            # Install on central widget if available
            central = self.centralWidget()
            if central is not None:
                central.installEventFilter(self)
            else:
                # Fallback: install on main window
                self.installEventFilter(self)
        except Exception as e:
            logging.error(f"Errore installazione event filter: {e}")

    def setup_work_area(self, layout):
        self.work_area_scroll = QScrollArea()
        self.work_area_scroll.setWidgetResizable(True)
        self.work_area_widget = WorkAreaWidget(self.settings)
        # Salva riferimento al layout per altri metodi
        self.work_area_layout = self.work_area_widget.widget_layout
        self.work_area_scroll.setWidget(self.work_area_widget)
        layout.addWidget(self.work_area_scroll)

    # === FUNZIONI PLACEHOLDER PER LE MATERIE SCOLASTICHE ===
    def handle_ipa_button_placeholder(self):
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

    def eventFilter(self, a0, a1):
        """Event filter per intercettare eventi della tastiera e del mouse."""
        from PyQt6.QtCore import Qt, QEvent

        # Handle all mouse events for tracking
        try:
            if a1 and hasattr(a1, 'type'):
                event_type = getattr(a1, 'type', lambda: None)()

                # Handle mouse button press events
                if event_type == QEvent.Type.MouseButtonPress:
                    event_button = getattr(a1, 'button', lambda: None)()
                    self._handle_mouse_event(a0, "PRESS", event_button)

                # Handle mouse button release events
                elif event_type == QEvent.Type.MouseButtonRelease:
                    event_button = getattr(a1, 'button', lambda: None)()
                    self._handle_mouse_event(a0, "RELEASE", event_button)

                # Handle mouse double click events
                elif event_type == QEvent.Type.MouseButtonDblClick:
                    event_button = getattr(a1, 'button', lambda: None)()
                    self._handle_mouse_event(a0, "DOUBLE_CLICK", event_button)

                # Handle mouse wheel events
                elif event_type == QEvent.Type.Wheel:
                    delta = getattr(a1, 'angleDelta', lambda: None)()
                    if delta:
                        if hasattr(delta, 'y'):
                            direction = "SU" if delta.y() > 0 else "GIÙ"
                            self._handle_mouse_wheel(a0, direction)

        except Exception:
            logging.error("Errore in eventFilter mouse handling: {e}")

        # Gestisci solo eventi della tastiera per l'area di testo
        try:
            if (a0 == self.input_text_area
                    and a1 and hasattr(a1, 'type') and hasattr(a1, 'key') and hasattr(a1, 'modifiers')):

                # Se è Invio senza Shift, aggiungi pensierino
                try:
                    # Usa getattr per accedere ai metodi in modo sicuro
                    event_type = getattr(a1, 'type', lambda: None)()
                    event_key = getattr(a1, 'key', lambda: None)()
                    event_modifiers = getattr(a1, 'modifiers', lambda: None)()

                    if (event_type == QEvent.Type.KeyPress
                        and event_key == Qt.Key.Key_Return
                        and event_modifiers is not None
                            and not event_modifiers & Qt.KeyboardModifier.ShiftModifier):
                        if hasattr(self, 'input_text_area') and self.input_text_area:
                            text = self.input_text_area.toPlainText().strip()
                            if text:
                                self.add_text_from_input_area()
                        return True  # Consuma l'evento (non propagarlo)
                except (AttributeError, TypeError):
                    pass  # Se l'evento non ha i metodi richiesti, ignora
                    if hasattr(self, 'input_text_area') and self.input_text_area:
                        text = self.input_text_area.toPlainText().strip()
                        if text:
                            self.add_text_from_input_area()
                    return True  # Consuma l'evento (non propagarlo)
        except Exception:
            logging.error("Errore in eventFilter keyboard handling: {e}")

        # Per tutti gli altri casi, lascia che l'evento venga gestito normalmente
        return super().eventFilter(a0, a1)

    def _handle_mouse_event(self, widget, event_type, button):
        """Gestisce tutti gli eventi del mouse per identificare l'elemento e il tipo di evento."""
        try:
            if not hasattr(self, 'click_status_label'):
                return

            # Get widget information
            widget_name = ""
            widget_type = ""

            if hasattr(widget, 'objectName') and widget.objectName():
                widget_name = widget.objectName()

            widget_type = type(widget).__name__

            # Identify the mouse button
            button_name = self._get_button_name(button)

            # Identify the type of widget
            widget_icon = self._get_widget_icon(widget_name, widget_type)

            # Create event description
            event_icon = self._get_event_icon(event_type)

            # Format the display text
            if widget_name:
                info = f"{event_icon} {button_name} su {widget_icon} {widget_name}"
            else:
                info = f"{event_icon} {button_name} su {widget_icon} {widget_type}"

            # Update the status label with animation
            self.click_status_label.setText(info)

            # Trigger animation if available
            if hasattr(self, 'click_label_animation'):
                self.click_label_animation.start()

        except Exception as e:
            logging.error(f"Errore in _handle_mouse_event: {e}")
            if hasattr(self, 'click_status_label'):
                self.click_status_label.setText("❌ Errore evento mouse")

    def _handle_mouse_wheel(self, widget, direction):
        """Gestisce gli eventi della rotella del mouse."""
        try:
            if not hasattr(self, 'click_status_label'):
                return

            # Get widget information
            widget_name = ""
            if hasattr(widget, 'objectName') and widget.objectName():
                widget_name = widget.objectName()

            widget_type = type(widget).__name__
            widget_icon = self._get_widget_icon(widget_name, widget_type)

            # Create wheel event description
            if widget_name:
                info = f"🌀 Rotella {direction} su {widget_icon} {widget_name}"
            else:
                info = f"🌀 Rotella {direction} su {widget_icon} {widget_type}"

            # Update the status label
            self.click_status_label.setText(info)

        except Exception as e:
            logging.error(f"Errore in _handle_mouse_wheel: {e}")
            if hasattr(self, 'click_status_label'):
                self.click_status_label.setText("❌ Errore rotella mouse")

    def _get_button_name(self, button):
        """Restituisce il nome del pulsante del mouse."""
        try:
            if button == Qt.MouseButton.LeftButton:
                return "SINISTRO"
            elif button == Qt.MouseButton.RightButton:
                return "DESTRO"
            elif button == Qt.MouseButton.MiddleButton:
                return "CENTRALE"
            elif button == Qt.MouseButton.BackButton:
                return "INDIETRO"
            elif button == Qt.MouseButton.ForwardButton:
                return "AVANTI"
            elif button == Qt.MouseButton.TaskButton:
                return "TASK"
            elif button == Qt.MouseButton.ExtraButton4:
                return "EXTRA4"
            elif button == Qt.MouseButton.ExtraButton5:
                return "EXTRA5"
            else:
                return f"PULSANTE_{button}"
        except:
            return "SCONOSCIUTO"

    def _get_event_icon(self, event_type):
        """Restituisce l'icona per il tipo di evento."""
        if event_type == "PRESS":
            return "👆"
        elif event_type == "RELEASE":
            return "👇"
        elif event_type == "DOUBLE_CLICK":
            return "👆👆"
        else:
            return "❓"

    def _get_widget_icon(self, widget_name, widget_type):
        """Restituisce l'icona per il tipo di widget."""
        if 'button' in widget_name.lower() or widget_type == 'QPushButton':
            return "🔘"
        elif 'checkbox' in widget_name.lower() or widget_type == 'QCheckBox':
            return "☑️"
        elif 'lineedit' in widget_name.lower() or widget_type == 'QLineEdit':
            return "📝"
        elif 'textedit' in widget_name.lower() or widget_type == 'QTextEdit':
            return "📄"
        elif 'combobox' in widget_name.lower() or widget_type == 'QComboBox':
            return "📋"
        elif 'slider' in widget_name.lower() or widget_type == 'QSlider':
            return "🎚️"
        elif 'groupbox' in widget_name.lower() or widget_type == 'QGroupBox':
            return "📁"
        elif 'scrollarea' in widget_name.lower() or widget_type == 'QScrollArea':
            return "📜"
        elif 'splitter' in widget_name.lower() or widget_type == 'QSplitter':
            return "📏"
        else:
            return "📦"

    def _handle_mouse_click(self, widget):
        """Gestisce i click del mouse per identificare l'elemento cliccato (legacy method)."""
        # This method is kept for backward compatibility but now uses the new system
        self._handle_mouse_event(widget, "PRESS", Qt.MouseButton.LeftButton)

    def add_text_from_input_area(self):
        text = self.input_text_area.toPlainText().strip()
        if text and DraggableTextWidget:
            widget = DraggableTextWidget(text, self.settings)
            self.pensierini_layout.addWidget(widget)
            self.input_text_area.clear()
            logging.info("Aggiunto pensierino: {text[:50]}...")

    def handle_ai_button(self):
        """Gestisce la funzione AI: invia richiesta a Ollama e mostra risposta."""
        text = self.input_text_area.toPlainText().strip()
        if not text:
            return

        # Controlla se il bridge Ollama è disponibile
        if not self.ollama_bridge:
            return

        # Verifica connessione con Ollama
        if not self.ollama_bridge.checkConnection():
            return

        try:
            # Crea pensierino con testo troncato per mostrare la richiesta
            truncated_text = text[:20] + "..." if len(text) > 20 else text

            if DraggableTextWidget:
                # Aggiungi pensierino alla colonna A con indicatore AI
                ai_pensierino_text = "🤖 {truncated_text}"
                pensierino_widget = DraggableTextWidget(ai_pensierino_text, self.settings)
                self.pensierini_layout.addWidget(pensierino_widget)

            # Mostra richiesta nell'area risultati

            # Invia richiesta a Ollama con modello di default
            default_model = "llama2:7b"  # Modello raccomandato
            self.ollama_bridge.sendPrompt(text, default_model)

            # Log dell'invio richiesta
            logging.info("Richiesta AI inviata: {text[:50]}... (modello: {default_model})")

        except Exception as e:
            logging.error("Errore nell'invio richiesta AI: {e}")
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

        # Carica preferenze font dalle impostazioni
        main_font_size = self.settings.get('fonts', {}).get('main_font_size', 13)
        page_button_font_size = main_font_size - 1  # Un po' più piccolo per il pulsante pagina

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
        self.details_text_label.setMinimumHeight(300)  # Circa 10 righe con font personalizzato
        # Imposta size policy per espansione massima
        from PyQt6.QtWidgets import QSizePolicy
        self.details_text_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        # Rimuovi entrambe le scrollbar per massimizzare lo spazio
        self.details_text_label.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.details_text_label.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # Usa dimensione font dalle preferenze per i dettagli
        details_font_size = main_font_size + 3  # Un po' più grande per i dettagli
        self.details_text_label.setStyleSheet(f"""
            QTextEdit {{
                background: rgba(221, 160, 221, 0.9); /* Viola chiaro per il testo */
                border: 2px solid #6f42c1;
                border-radius: 8px;
                padding-top: 20px;
                padding-bottom: 20px;
                padding-left: 15px;
                padding-right: 15px;
                font-size: {details_font_size}px;
                line-height: 1.4;
                color: #333;
            }}

            /* Pulsante Riformula - Verde */
            QPushButton#rephrase_button {{
                background-color: #28a745;
                color: white;
                border: 2px solid #1e7e34;
                border-radius: 6px;
                padding: 6px 14px;
                font-weight: bold;
                min-height: 30px;
                min-width: 160px;
                font-size: {main_font_size}px;
            }}

            QPushButton#rephrase_button:hover {{
                background-color: #218838;
                border-color: #1c7430;
            }}

            /* Pulsanti navigazione - Blu */
            QPushButton#back_button, QPushButton#forward_button {{
                background-color: #007bff;
                color: white;
                border: 2px solid #0056b3;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
                min-height: 35px;
                font-size: {main_font_size}px;
            }}

            QPushButton#back_button:hover, QPushButton#forward_button:hover {{
                background-color: #0056b3;
                border-color: #004085;
            }}

            /* Etichetta pagina - Arancione */
            QPushButton#page_info_label {{
                background-color: #fd7e14;
                color: white;
                border: 2px solid #e8590c;
                border-radius: 4px;
                padding: 2px 8px;
                font-weight: bold;
                font-size: {page_button_font_size}px;
                min-width: 50px;
                max-width: 60px;
            }}

            QPushButton#page_info_label:hover {{
                background-color: #e8590c;
                border-color: #d0390c;
            }}


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

        # Usa dimensione font dalle preferenze per il pulsante riformula
        rephrase_button_font_size = self.settings.get('fonts', {}).get('main_font_size', 13)
        self.rephrase_button.setStyleSheet(f"""
            QPushButton {{
                background-color: #17a2b8;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: bold;
                min-height: 35px;
                min-width: 160px;
                font-size: {rephrase_button_font_size}px;
            }}
            QPushButton:hover {{
                background-color: #138496;
            }}
            QPushButton:disabled {{
                background-color: #adb5bd;
                color: #6c757d;
            }}
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
        self.copy_button.setStyleSheet(f"""
            QPushButton {{
                background-color: #007bff;
                color: white;
                border: 2px solid #0056b3;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
                min-height: 35px;
                min-width: 100px;
                font-size: {main_font_size}px;
            }}
            QPushButton:hover {{
                background-color: #0056b3;
                border-color: #004085;
            }}
        """)
        rephrase_layout.addWidget(self.copy_button)

        rephrase_layout.addWidget(self.rephrase_button)

        # Pulsante pagina non cliccabile (più compatto)
        self.page_info_label = QPushButton("Pag. 1")
        self.page_info_label.setObjectName("page_info_label")
        self.page_info_label.setEnabled(False)  # Non cliccabile

        # Usa dimensione font dalle preferenze per il pulsante pagina
        page_button_font_size = self.settings.get('fonts', {}).get('main_font_size', 13) - 1  # Un po' più piccolo per il pulsante pagina
        self.page_info_label.setStyleSheet(f"""
            QPushButton {{
                color: #495057;
                font-weight: bold;
                font-size: {page_button_font_size}px;
                padding: 2px 8px;
                background: rgba(255, 255, 255, 0.8);
                border: 1px solid #dee2e6;
                border-radius: 4px;
                min-width: 50px;
                max-width: 60px;
                text-align: center;
                margin-left: 5px;
            }}
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

        # Usa QSplitter per rendere resizable la sezione testo e controlli
        details_splitter = QSplitter(Qt.Orientation.Vertical)
        details_splitter.setHandleWidth(3)
        details_splitter.setStyleSheet("""
            QSplitter::handle {
                background: rgba(108, 117, 125, 0.3);
                border-radius: 2px;
            }
            QSplitter::handle:hover {
                background: rgba(108, 117, 125, 0.6);
            }
        """)

        # Widget contenitore per il testo
        text_container = QWidget()
        text_layout = QVBoxLayout(text_container)
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.addWidget(self.details_text_label)
        details_splitter.addWidget(text_container)

        # Widget contenitore per i controlli
        controls_container = QWidget()
        controls_layout = QVBoxLayout(controls_container)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.addLayout(main_controls_layout)
        details_splitter.addWidget(controls_container)

        # Imposta proporzioni iniziali (80% testo, 20% controlli)
        details_splitter.setSizes([400, 100])

        layout.addWidget(details_splitter)

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
        self.page_info_label.setText("Pag. {current_page_num}")

        # Aggiorna testi dei pulsanti
        if self.current_page < self.total_pages - 1:
            pass
        else:
            pass

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
        except Exception:
            logging.error("Errore pulizia dettagli: {e}")

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
                                         "Impossibile scaricare il modello '{vosk_model}'.\n\n"
                                         "Verifica la connessione internet e riprova.")
                    self.voice_button.setEnabled(True)
                    self.voice_button.setText("🎤 Trascrivi la mia voce")
                    return

                progress_msg.close()
                QMessageBox.information(self, "Download Completato",
                                        "✅ Modello '{vosk_model}' scaricato con successo!")
            else:
                QMessageBox.warning(self, "Funzione Download Non Disponibile",
                                    "Il modello Vosk '{vosk_model}' non è stato trovato.\n\n"
                                    "Percorso: {model_path}\n\n"
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
            show_user_friendly_error(self, e, "riconoscimento vocale")
            self.voice_button.setEnabled(True)
            self.voice_button.setText("🎤 Trascrivi la mia voce")

    def _on_voice_recognized(self, text):
        """Callback quando viene riconosciuto del testo vocale."""
        logging.info("🎤 _on_voice_recognized chiamata con testo: '{text}'")

        if text and text.strip():
            logging.info("📝 Testo valido ricevuto: '{text.strip()}'")

            # Inserisci il testo direttamente nella colonna dei pensierini
            if hasattr(self, 'pensierini_layout') and self.pensierini_layout:
                logging.info("✅ pensierini_layout disponibile")

                # Crea un nuovo pensierino con il testo riconosciuto
                if DraggableTextWidget:
                    try:
                        widget = DraggableTextWidget("🎤 {text.strip()}", self.settings)
                        self.pensierini_layout.addWidget(widget)
                        logging.info("✅ Widget creato e aggiunto ai pensierini: {text[:50]}...")
                    except Exception:
                        logging.error("❌ Errore creazione widget: {e}")
                        # Fallback: inserisci nell'area di testo
                        current_text = self.input_text_area.toPlainText()
                        if current_text:
                            self.input_text_area.setPlainText("{current_text}\n{text.strip()}")
                        else:
                            self.input_text_area.setPlainText(text.strip())
                else:
                    logging.warning("⚠️ DraggableTextWidget non disponibile, uso fallback")
                    # Fallback: inserisci nell'area di testo
                    current_text = self.input_text_area.toPlainText()
                    if current_text:
                        self.input_text_area.setPlainText("{current_text}\n{text.strip()}")
                    else:
                        self.input_text_area.setPlainText(text.strip())
            else:
                logging.error("❌ pensierini_layout non disponibile")

            # Mostra notifica di successo
            QMessageBox.information(self, "Testo Riconosciuto",
                                    "✅ Testo riconosciuto con successo!\n\n"
                                    "📝 \"{text.strip()[:100]}{'...' if len(text.strip()) > 100 else ''}\"\n\n"
                                    "💭 Aggiunto ai pensierini!")
        else:
            logging.warning("⚠️ Testo vuoto o None ricevuto: '{text}'")

    def _on_voice_error(self, error_msg):
        """Callback per gestire errori del riconoscimento vocale."""
        QMessageBox.warning(self, "Errore Riconoscimento", "Errore durante il riconoscimento vocale:\n\n{error_msg}")
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
                                    "✅ Testo copiato negli appunti!\n\n"
                                    "📝 {len(self.full_text)} caratteri copiati")

            logging.info("Testo copiato negli appunti: {len(self.full_text)} caratteri")

        except Exception:
            logging.error("Errore durante la copia: {e}")
            QMessageBox.critical(self, "Errore Copia", "Errore durante la copia del testo:\n{str(e)}")

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
            prompt = """Riformula intensamente il seguente testo in modo più elegante, chiaro e professionale.
Mantieni il significato originale ma usa un linguaggio più sofisticato e fluido.
Se è un'analisi o una descrizione, rendila più dettagliata e approfondita.
Se è una domanda, riformulala in modo più preciso e formale.

Testo originale:
{self.full_text}

Riformulazione intensa:"""

            # Mostra stato di elaborazione nei dettagli
            processing_text = "🧠 RIFORMULAZIONE IN CORSO\n\n⏳ Elaborazione del testo con intelligenza artificiale...\n\nTesto originale ({len(self.full_text)} caratteri):\n{self.full_text[:200]}{'...' if len(self.full_text) > 200 else ''}"
            self.show_text_in_details(processing_text)

            # Invia richiesta a Ollama con modello di default
            default_model = "llama2:7b"  # Modello raccomandato
            self.ollama_bridge.sendPrompt(prompt, default_model)

            logging.info("Richiesta riformulazione inviata: {len(self.full_text)} caratteri (modello: {default_model})")

        except Exception:
            logging.error("Errore nell'invio richiesta riformulazione: {e}")
            QMessageBox.critical(self, "Errore AI", "Errore nell'invio della richiesta AI:\n{str(e)}")
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

        except Exception:
            logging.error("Errore caricamento file multimediale: {e}")
            QMessageBox.critical(self, "Errore", "Errore durante il caricamento del file:\n{str(e)}")

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
            header_layout.addWidget(QLabel("🎵 {file_name}"))
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
            if QMediaPlayer and QAudioOutput:
                self.media_player = QMediaPlayer()
                self.audio_output = QAudioOutput()
                self.media_player.setAudioOutput(self.audio_output)
                self.media_player.setSource(QUrl.fromLocalFile(file_path))
            else:
                raise ImportError("QMediaPlayer non disponibile")

            # Connetti segnali
            self.media_player.positionChanged.connect(self.update_position)
            self.media_player.durationChanged.connect(self.update_duration)
            self.position_slider.sliderMoved.connect(self.set_position)

            # Aggiungi alla colonna pensierini
            if DraggableTextWidget:
                # Crea un wrapper per rendere trascinabile
                wrapper_widget = DraggableTextWidget("🎵 Audio: {file_name}", self.settings)
                # Sostituisci il contenuto con il widget audio
                wrapper_layout = QVBoxLayout(wrapper_widget)
                wrapper_layout.addWidget(audio_widget)
                self.pensierini_layout.addWidget(wrapper_widget)

            QMessageBox.information(self, "File Audio Caricato",
                                    "✅ File audio '{file_name}' caricato con successo!\n\n"
                                    "🎵 Controlli multimediali disponibili\n"
                                    "📊 Analizzatore spettro in sviluppo")

        except ImportError as e:
            QMessageBox.warning(self, "Funzionalità Limitata",
                                "Alcune funzionalità audio potrebbero non essere disponibili:\n{str(e)}\n\n"
                                "Il file è stato comunque aggiunto come elemento generico.")
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
                wrapper_widget = DraggableTextWidget("🎥 Video: {file_name}", self.settings)
                wrapper_layout = QVBoxLayout(wrapper_widget)
                wrapper_layout.addWidget(video_widget)
                self.pensierini_layout.addWidget(wrapper_widget)

            QMessageBox.information(self, "File Video Caricato",
                                    "✅ File video '{file_name}' caricato con successo!")

        except Exception:
            logging.error("Errore creazione widget video: {e}")
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
                wrapper_widget = DraggableTextWidget("📄 File: {file_name}", self.settings)
                wrapper_layout = QVBoxLayout(wrapper_widget)
                wrapper_layout.addWidget(generic_widget)
                self.pensierini_layout.addWidget(wrapper_widget)

            QMessageBox.information(self, "File Caricato",
                                    "✅ File '{file_name}' caricato con successo!")

        except Exception:
            logging.error("Errore creazione widget generico: {e}")
            QMessageBox.critical(self, "Errore", "Errore durante la creazione del widget:\n{str(e)}")

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

        except Exception:
            logging.error("Errore caricamento file OCR: {e}")
            QMessageBox.critical(self, "Errore", "Errore durante il caricamento del file:\n{str(e)}")

    def process_ocr_file(self, file_path):
        """Elabora il file per l'OCR."""
        import os
        from pathlib import Path

        file_name = os.path.basename(file_path)
        file_ext = Path(file_path).suffix.lower()

        progress_msg = None
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
                ocr_content = "📄 OCR - Trascrizione da: {file_name}\n\n{'=' * 50}\n\n{text}\n\n{'=' * 50}\n\n📊 Statistiche OCR:\n• Caratteri estratti: {len(text)}\n• Parole: {len(text.split())}\n• Righe: {len(text.split(chr(10)))}"
                self.show_text_in_details(ocr_content)

                # Crea anche un pensierino con il testo estratto
                if DraggableTextWidget:
                    ocr_pensierino_text = "📄 OCR: {file_name[:30]}... ({len(text)} caratteri)"
                    pensierino_widget = DraggableTextWidget(ocr_pensierino_text, self.settings)
                    self.pensierini_layout.addWidget(pensierino_widget)

                QMessageBox.information(self, "OCR Completato",
                                        "✅ Testo estratto con successo!\n\n"
                                        "📄 File: {file_name}\n"
                                        "📝 Caratteri: {len(text)}\n"
                                        "📊 Parole: {len(text.split())}")
            else:
                QMessageBox.warning(self, "OCR Fallito",
                                    "Nessun testo rilevato nel documento.\n\n"
                                    "Possibili cause:\n"
                                    "• Immagine di bassa qualità\n"
                                    "• Testo non chiaramente leggibile\n"
                                    "• Orientamento del documento\n"
                                    "• Carattere non supportato")

        except Exception:
            if progress_msg is not None:
                progress_msg.close()
            logging.error("Errore OCR: {e}")
            QMessageBox.critical(self, "Errore OCR", "Errore durante l'elaborazione OCR:\n{str(e)}")

    def extract_text_from_image(self, image_path):
        """Estrae testo da un'immagine usando pytesseract."""
        try:
            if not Image or not pytesseract:
                raise ImportError("PIL o pytesseract non disponibili")

            # Apri l'immagine
            image = Image.open(image_path)

            # Configurazione OCR ottimale
            custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyzàèéìòùÀÈÉÌÒÙ .,!?-()[]{}:;"\'\n'

            # Esegui OCR
            text = pytesseract.image_to_string(image, lang='ita+eng', config=custom_config)

            return text.strip()

        except Exception:
            logging.error("Errore estrazione testo da immagine: {e}")
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

        except Exception:
            logging.error("Errore caricamento file audio: {e}")
            QMessageBox.critical(self, "Errore", "Errore durante il caricamento del file:\n{str(e)}")

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
                                "Il formato '{file_ext}' non è attualmente supportato.\n\n"
                                "Formati supportati: {', '.join(supported_formats)}\n\n"
                                "Converti il file in uno dei formati supportati.")
            return

        progress_msg = None
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
                if ensure_vosk_model_available is not None:
                    # Mostra dialog di progresso per il download
                    progress_msg.setText("🔄 Scaricamento modello necessario...")

                    def progress_callback(message):
                        progress_msg.setText(message)
                        QApplication.processEvents()  # Aggiorna l'interfaccia

                    # Tenta di scaricare il modello
                    if not ensure_vosk_model_available(vosk_model, progress_callback):
                        progress_msg.close()
                        QMessageBox.critical(self, "Download Fallito",
                                             "Impossibile scaricare il modello '{vosk_model}'.\n\n"
                                             "Verifica la connessione internet e riprova.")
                        return

                    progress_msg.close()
                    QMessageBox.information(self, "Download Completato",
                                            "✅ Modello '{vosk_model}' scaricato con successo!")
                else:
                    progress_msg.close()
                    QMessageBox.warning(self, "Funzione Download Non Disponibile",
                                        "Il modello Vosk '{vosk_model}' non è stato trovato.\n\n"
                                        "Percorso: {model_path}\n\n"
                                        "La funzione di download automatico non è disponibile.")
                    return

            progress_msg.close()

            # Mostra messaggio di inizio trascrizione
            QMessageBox.information(self, "Trascrizione Avviata",
                                    "🎵 Avvio trascrizione del file:\n{file_name}\n\n"
                                    "📝 Il testo trascritto verrà aggiunto ai pensierini.\n"
                                    "⏳ L'operazione potrebbe richiedere alcuni minuti...")

            # Crea il thread di trascrizione
            if AudioFileTranscriptionThread:
                self.audio_transcription_thread = AudioFileTranscriptionThread(
                    audio_file_path,
                    vosk_model,
                    text_callback=self._on_audio_transcription_completed
                )
            else:
                raise ImportError("AudioFileTranscriptionThread non disponibile")

            # Connetti i segnali
            self.audio_transcription_thread.transcription_progress.connect(self._on_transcription_progress)
            self.audio_transcription_thread.transcription_completed.connect(self._on_audio_transcription_completed)
            self.audio_transcription_thread.transcription_error.connect(self._on_transcription_error)

            # Avvia la trascrizione
            self.audio_transcription_thread.start()

        except Exception:
            if progress_msg is not None:
                progress_msg.close()
            logging.error("Errore avvio trascrizione: {e}")
            QMessageBox.critical(self, "Errore Avvio", "Errore nell'avvio della trascrizione:\n{str(e)}")

    def _on_transcription_progress(self, message):
        """Gestisce gli aggiornamenti di progresso della trascrizione."""
        logging.info("Progresso trascrizione: {message}")
        # Potrebbe essere utile mostrare un dialog di progresso più dettagliato in futuro

    def _on_audio_transcription_completed(self, text):
        """Callback quando la trascrizione è completata."""
        logging.info("🎵 Trascrizione completata: '{text[:100]}...'")

        if text and text.strip():
            # Mostra il testo trascritto nei dettagli
            transcription_content = "🎵 Trascrizione Audio Completata\n\n{'=' * 50}\n\n{text}\n\n{'=' * 50}\n\n📊 Statistiche Trascrizione:\n• Caratteri: {len(text)}\n• Parole: {len(text.split())}\n• Righe: {len(text.split(chr(10)))}"
            self.show_text_in_details(transcription_content)

            # Crea anche un pensierino con il testo trascritto
            if DraggableTextWidget:
                transcription_pensierino_text = "🎵 Trascrizione: {text[:50]}... ({len(text)} caratteri)"
                pensierino_widget = DraggableTextWidget(transcription_pensierino_text, self.settings)
                self.pensierini_layout.addWidget(pensierino_widget)

            QMessageBox.information(self, "Trascrizione Completata",
                                    "✅ Trascrizione completata con successo!\n\n"
                                    "🎵 File audio elaborato\n"
                                    "📝 Caratteri: {len(text)}\n"
                                    "📊 Parole: {len(text.split())}")
        else:
            QMessageBox.warning(self, "Trascrizione Vuota",
                                "La trascrizione non ha prodotto testo.\n\n"
                                "Possibili cause:\n"
                                "• File audio di bassa qualità\n"
                                "• Audio senza parlato\n"
                                "• Problemi di riconoscimento")

    def _on_transcription_error(self, error_msg):
        """Gestisce gli errori della trascrizione."""
        logging.error("Errore trascrizione: {error_msg}")
        QMessageBox.critical(self, "Errore Trascrizione", "Errore durante la trascrizione:\n\n{error_msg}")

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

        except Exception:
            logging.error("Errore toggle riconoscimento facciale: {e}")
            QMessageBox.critical(self, "Errore", "Errore durante la gestione del riconoscimento facciale:\n{str(e)}")

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

        except Exception:
            logging.error("Errore toggle riconoscimento gesti mani: {e}")
            QMessageBox.critical(self, "Errore", "Errore durante la gestione del riconoscimento gesti mani:\n{str(e)}")

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

    def keyPressEvent(self, a0):
        """Gestisce gli eventi della tastiera per scorciatoie."""
        from PyQt6.QtCore import Qt

        try:
            # Controlla la combinazione Ctrl+F per toggle fullscreen
            if (a0 and hasattr(a0, 'key') and hasattr(a0, 'modifiers')
                    and a0.key() == Qt.Key.Key_F and a0.modifiers() & Qt.KeyboardModifier.ControlModifier):
                self.toggle_fullscreen()
                if hasattr(a0, 'accept'):
                    a0.accept()  # Segnala che l'evento è stato gestito
            else:
                # Passa l'evento al gestore predefinito
                super().keyPressEvent(a0)
        except Exception:
            logging.error("Errore in keyPressEvent: {e}")
            super().keyPressEvent(a0)

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
                    logging.info("Salvata dimensione originale: {self.original_width}x{self.original_height} at ({self.original_x}, {self.original_y})")

                # Entra in modalità fullscreen
                self.showFullScreen()
                self.is_fullscreen = True
                logging.info("Entrato in modalità fullscreen")

        except Exception:
            logging.error("Errore toggle fullscreen: {e}")
            QMessageBox.critical(self, "Errore Fullscreen",
                                 "Errore durante il cambio modalità schermo:\n{str(e)}")

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

                logging.info("Ripristinate dimensioni originali: {self.original_width}x{self.original_height} at ({self.original_x}, {self.original_y})")
            else:
                logging.warning("Nessuna dimensione originale da ripristinare")

        except Exception:
            logging.error("Errore ripristino dimensioni: {e}")

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

        except Exception:
            logging.error("Errore toggle log: {e}")
            QMessageBox.critical(self, "Errore Log", "Errore durante il toggle del log:\n{str(e)}")

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
                log_content = "📁 File log non trovato:\n{log_file}"
            else:
                # Leggi il file di log
                with open(log_file, 'r', encoding='utf-8') as f:
                    log_content = f.read()

                # Filtra solo errori e warning
                lines = log_content.split('\n')
                filtered_lines = []

                for line in lines:
                    line_lower = line.lower()
                    if ('error' in line_lower
                        or 'warning' in line_lower
                        or 'critical' in line_lower
                            or 'exception' in line_lower):
                        filtered_lines.append(line)

                if not filtered_lines:
                    log_content = "📋 LOG ERRORI E WARNING\n\n" \
                        "✅ Nessun errore o warning trovato nel log!\n\n" \
                        "📁 File log: {log_file}\n" \
                        "📊 Righe totali nel log: {len(lines)}\n" \
                        "🔄 Ultimo aggiornamento: {datetime.now().strftime('%H:%M:%S')}"
                else:
                    log_content = "📋 LOG ERRORI E WARNING\n\n" \
                        "🔍 Trovati {len(filtered_lines)} errori/warning:\n\n" \
                        "{'=' * 60}\n\n" \
                        "{chr(10).join(filtered_lines[-50:])}\n\n" \
                        "{'=' * 60}\n\n" \
                        "📁 File log: {log_file}\n" \
                        "📊 Righe totali nel log: {len(lines)}\n" \
                        "🔄 Ultimo aggiornamento: {datetime.now().strftime('%H:%M:%S')}"

            # Mostra il contenuto nei dettagli
            self.show_text_in_details(log_content)

        except Exception:
            logging.error("Errore lettura log: {e}")
            error_content = "❌ Errore lettura log:\n{str(e)}"
            self.show_text_in_details(error_content)

    # def show_log_window(self):
    #     """Metodo disabilitato - funzionalità log spostata in alto come label di stato."""
    #     pass

    # def refresh_log_content(self):
    #     """Metodo disabilitato - funzionalità log spostata in alto come label di stato."""
    #     pass

    # def clear_log_file(self):
    #     """Metodo disabilitato - funzionalità log spostata in alto come label di stato."""
        try:
            reply = QMessageBox.question(self, "Conferma Pulizia Log",
                                         "Sei sicuro di voler pulire il file di log?\n\n"
                                         "Questa azione rimuoverà tutti gli errori e warning registrati.",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

            if reply == QMessageBox.StandardButton.Yes:
                from main_03_configurazione_e_opzioni import get_config
                log_config = get_config()
                log_file = log_config.get_setting('files.log_file', 'Save/LOG/app.log')

                # Svuota il file di log
                with open(log_file, 'w', encoding='utf-8') as f:
                    f.write("[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] INFO Log pulito dall'utente\n")

                # Log pulito, non è necessario aggiornare la visualizzazione
                QMessageBox.information(self, "Log Pulito", "✅ File di log pulito con successo!")

        except Exception:
            logging.error("Errore pulizia log: {e}")
            QMessageBox.critical(self, "Errore Pulizia Log",
                                 "Errore durante la pulizia del log:\n{str(e)}")

    def hide_log_window(self):
        """Nasconde la visualizzazione del log nei dettagli."""
        try:
            # Nasconde il contenuto del log nei dettagli
            if hasattr(self, 'log_button'):
                self.log_button.setChecked(False)
                # Torna alla visualizzazione precedente o pulisce
                if hasattr(self, 'previous_details_content'):
                    self.show_text_in_details(self.previous_details_content)
                else:
                    self._clear_details()

        except Exception:
            logging.error("Errore nascondendo log: {e}")

    def toggle_audio_playback(self, file_path):
        """Alterna play/pausa per l'audio."""
        if hasattr(self, 'media_player') and self.media_player and QMediaPlayer:
            try:
                if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
                    self.media_player.pause()
                    if hasattr(self, 'play_button'):
                        self.play_button.setText("▶️ Play")
                else:
                    self.media_player.play()
                    if hasattr(self, 'play_button'):
                        self.play_button.setText("⏸️ Pausa")
            except Exception:
                logging.error("Errore toggle audio playback: {e}")

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
            self.duration_label.setText("00:00 / {minutes:02d}:{seconds:02d}")

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
                btn = QPushButton("{symbol}\n{example}")
                btn.setObjectName("ipa_symbol")
                btn.setToolTip("Esempio: '{example}' → trascrizione fonetica con {symbol}")
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
                btn = QPushButton("{symbol}\n{example}")
                btn.setObjectName("ipa_symbol")
                btn.setToolTip("Esempio: '{example}' → trascrizione fonetica con {symbol}")
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
                btn = QPushButton("{symbol}\n{example}")
                btn.setObjectName("ipa_symbol")
                btn.setToolTip("Esempio: '{example}' → trascrizione fonetica con {symbol}")
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
                btn = QPushButton("{symbol}\n{example}")
                btn.setObjectName("ipa_symbol")
                btn.setToolTip("Esempio: '{example}' → trascrizione fonetica con {symbol}")
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
                btn = QPushButton("{symbol}\n{example}")
                btn.setObjectName("ipa_symbol")
                if symbol == "[ˈ]":
                    btn.setToolTip("Esempio: 'grazie' → [ˈɡrat.t͡sje] (accento primario sulla prima sillaba)")
                else:
                    btn.setToolTip("Esempio pratico con {symbol}: {example}")
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

        except Exception:
            logging.error("Errore apertura dialog IPA: {e}")
            QMessageBox.critical(self, "Errore", "Errore nell'apertura della guida IPA:\n{str(e)}")

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
                        tts_thread.started_reading.connect(lambda: logging.info("🔊 Pronunciando simbolo IPA: {symbol}"))
                        tts_thread.finished_reading.connect(lambda: logging.info("✅ Pronuncia simbolo IPA completata: {symbol}"))
                        tts_thread.error_occurred.connect(lambda err: logging.error("❌ Errore pronuncia simbolo IPA {symbol}: {err}"))

                        # Avvia la pronuncia
                        tts_thread.start()

                        # Salva riferimento per evitare garbage collection
                        if not hasattr(self, '_tts_threads'):
                            self._tts_threads = []
                        self._tts_threads.append(tts_thread)

                except Exception as tts_error:
                    logging.warning("Errore TTS per simbolo IPA {symbol}: {tts_error}")
                    # Non mostrare errori TTS per non interrompere l'esperienza utente

            # Rimossa la notifica popup per un'esperienza più fluida

        except Exception:
            logging.error("Errore copia simbolo IPA: {e}")
            QMessageBox.critical(dialog, "Errore Copia", "Errore durante la copia:\n{str(e)}")

    def clear_clipboard(self):
        """Pulisce l'area clipboard."""
        try:
            self.clipboard_text.clear()
            self.clipboard_text.setPlaceholderText("Clipboard pulito! 🎵\n\nInizia cliccando sui pulsanti sopra!")
        except Exception:
            logging.error("Errore pulizia clipboard: {e}")

    def copy_clipboard_content(self):
        """Copia tutto il contenuto del clipboard negli appunti di sistema."""
        try:
            content = self.clipboard_text.toPlainText()
            if content.strip():
                clipboard = QApplication.clipboard()
                if clipboard:
                    clipboard.setText(content)
                    QMessageBox.information(self, "Clipboard Copiato",
                                            "✅ Tutto il contenuto del clipboard copiato negli appunti!\n\n"
                                            "📝 {len(content)} caratteri copiati")
            else:
                QMessageBox.warning(self, "Clipboard Vuoto",
                                    "Il clipboard è vuoto. Clicca prima sui simboli IPA per riempirlo!")
        except Exception:
            logging.error("Errore copia clipboard: {e}")
            QMessageBox.critical(self, "Errore Copia", "Errore durante la copia:\n{str(e)}")

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
                                    "Il simbolo '{symbol}' non ha una pronuncia definita.")
                return

            # Crea e avvia il thread TTS
            # Converti il simbolo IPA in testo pronunciabile
            pronunciation_text = self._ipa_to_pronunciation_text(symbol)

            if not pronunciation_text:
                QMessageBox.warning(self, "Simbolo Non Supportato",
                                    "Il simbolo '{symbol}' non ha una pronuncia definita.")
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
            tts_thread.started_reading.connect(lambda: logging.info("🔊 Pronunciando: {symbol}"))
            tts_thread.finished_reading.connect(lambda: logging.info("✅ Pronuncia completata: {symbol}"))
            tts_thread.error_occurred.connect(lambda err: logging.error("❌ Errore pronuncia {symbol}: {err}"))

            # Avvia la pronuncia
            tts_thread.start()

            # Salva riferimento per evitare garbage collection
            if not hasattr(self, '_tts_threads'):
                self._tts_threads = []
            self._tts_threads.append(tts_thread)

        except Exception:
            logging.error("Errore integrato pronuncia+copia IPA {symbol}: {e}")
            QMessageBox.critical(self, "Errore Integrato", "Errore durante copia e pronuncia:\n{str(e)}")
            logging.error("Errore copia simbolo IPA: {e}")
            QMessageBox.critical(self, "Errore Copia", "Errore durante la copia:\n{str(e)}")

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
        except Exception:
            logging.error("Errore copia tutti i simboli IPA: {e}")
            QMessageBox.critical(self, "Errore Copia", "Errore durante la copia:\n{str(e)}")

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
        except Exception:
            logging.error("Errore copia IPA: {e}")
            QMessageBox.critical(self, "Errore Copia", "Errore durante la copia:\n{str(e)}")

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

        except Exception:
            logging.error("Errore toggle TTS: {e}")
            QMessageBox.critical(self, "Errore TTS", "Errore durante il cambio stato TTS:\n{str(e)}")

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
        except Exception:
            logging.error("Errore pulizia area: {e}")

    def save_project(self):
        """Salva il progetto corrente (colonne 1 e 2)."""
        # Prevent multiple saves by disabling the button
        self.save_button.setEnabled(False)
        self.save_button.setText("💾 Salvataggio...")

        try:
            # Ottieni il nome del progetto
            project_name = self.project_name_input.text().strip()
            if not project_name:
                project_name = "progetto_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

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
            filename = "{project_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            filepath = os.path.join(projects_dir, filename)

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(project_data, f, indent=2, ensure_ascii=False)

            QMessageBox.information(
                self, "Salvataggio Completato",
                "Progetto '{project_name}' salvato con successo!\n\n"
                "File: {filename}\n"
                "Pensierini: {len(project_data['pensierini'])}\n"
                "Workspace: {len(project_data['workspace'])}"
            )

            logging.info("Progetto salvato: {filepath}")

        except Exception:
            QMessageBox.critical(self, "Errore Salvataggio", "Errore durante il salvataggio:\n{str(e)}")
            logging.error("Errore salvataggio progetto: {e}")
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

                        display_text = "{name} - {pens_count} pensierini, {work_count} workspace"
                        if created:
                            display_text += " ({created[:19]})"

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

        except Exception:
            QMessageBox.critical(self, "Errore Caricamento", "Errore durante il caricamento:\n{str(e)}")
            logging.error("Errore caricamento progetto: {e}")

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
                "Progetto '{project_name}' caricato con successo!\n\n"
                "Pensierini: {len(pensierini_data)}\n"
                "Workspace: {len(workspace_data)}"
            )

            logging.info("Progetto caricato: {filepath}")

        except Exception:
            QMessageBox.critical(self, "Errore Caricamento", "Errore durante il caricamento del file:\n{str(e)}")
            logging.error("Errore caricamento file progetto: {e}")

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

        except Exception:
            logging.error("Errore pulizia colonne: {e}")

    def open_settings(self):
        """Apre il dialog delle impostazioni."""
        if SettingsDialog is None:
            QMessageBox.critical(self, "Errore", "Modulo impostazioni non disponibile")
            return

        try:
            dialog = SettingsDialog(self)
            dialog.exec()
        except Exception:
            QMessageBox.critical(self, "Errore", "Errore nell'apertura delle impostazioni: {e}")

    def update_status_label(self):
        """Metodo deprecato - lo status è ora gestito dal pulsante log."""
        # Il pulsante log ha sostituito il label di stato
        pass

    def update_footer_status(self):
        """Aggiorna le informazioni di stato nel footer con design moderno e informazioni utili."""
        try:
            from datetime import datetime
            current_time = datetime.now().strftime("%H:%M:%S")

            # Conta elementi attivi
            pensierini_count = 0
            if hasattr(self, 'pensierini_layout') and self.pensierini_layout:
                pensierini_count = self.pensierini_layout.count()

            work_items_count = 0
            if hasattr(self, 'work_area_layout') and self.work_area_layout:
                work_items_count = self.work_area_layout.count()

            # Stato del sistema
            ai_status = "🟢" if (hasattr(self, 'ollama_bridge') and self.ollama_bridge) else "🔴"
            voice_status = "🟢" if SpeechRecognitionThread else "🔴"
            ocr_status = "🟢" if OCR_AVAILABLE else "🔴"

            # Messaggio dinamico basato sul contesto
            if pensierini_count > 0:
                status_text = f"🕐 {current_time} | 📝 {pensierini_count} pensierini | 🎯 {work_items_count} elementi | {ai_status} AI | {voice_status} Voce | {ocr_status} OCR"
            else:
                status_text = f"🕐 {current_time} | 🎨 CogniFlow pronto | Premi F1 per aiuto | {ai_status} AI | {voice_status} Voce | {ocr_status} OCR"

            if hasattr(self, 'status_footer_label'):
                self.status_footer_label.setText(status_text)

        except Exception as e:
            logging.error(f"Errore nell'aggiornamento del footer: {e}")
            if hasattr(self, 'status_footer_label'):
                self.status_footer_label.setText("🕐 Sistema attivo | Premi F1 per aiuto")

    def set_tutor_session_status(self, active: bool):
        """Imposta lo stato della sessione tutor e aggiorna il footer."""
        self.tutor_session_active = active
        self.update_footer_status()

    def set_screen_sharing_status(self, active: bool):
        """Imposta lo stato della condivisione schermo e aggiorna il footer."""
        self.screen_sharing_active = active
        self.update_footer_status()

    def closeEvent(self, a0):
        """Gestisce la chiusura dell'applicazione."""
        # Ferma il timer del footer
        if hasattr(self, 'footer_timer'):
            self.footer_timer.stop()

        # Chiama il metodo originale
        super().closeEvent(a0)

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
        print("✓ Sistema configurazione caricato - Tema: {settings['application']['theme']}")

        # Test classe MainWindow (ora integrata in questo file)
        print("✓ Classe MainWindow disponibile")

        # Test import widget trascinabile
        from UI.draggable_text_widget import DraggableTextWidget
        print("✓ Modulo widget trascinabile importato")

        return True

    except ImportError as e:
        print("❌ Errore import: {e}")
        return False
    except Exception:
        print("❌ Errore generale: {e}")
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
        print("Settings loaded successfully")

        # Crea applicazione Qt
        app = QApplication(sys.argv)
        app.setApplicationName(settings['application']['app_name'])
        app.setOrganizationName("DSA Aircraft")
        print("QApplication created successfully")

        # Imposta icona se disponibile
        icon_path = "ICO-fonts-wallpaper/ICONA.ico"
        if os.path.exists(icon_path):
            from PyQt6.QtGui import QIcon
            app.setWindowIcon(QIcon(icon_path))
            logger.info("Icona caricata: {icon_path}")

        print("About to create MainWindow...")
        # Crea e mostra finestra principale (Aircraft)
        window = MainWindow()
        print("MainWindow created successfully")
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
