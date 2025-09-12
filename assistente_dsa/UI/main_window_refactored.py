#!/usr/bin/env python3
"""
Main Window Refactored - Versione modulare della finestra principale
Separazione della logica UI dal controller di business
"""

import json
import logging
import os
import sys
from datetime import datetime
from typing import Dict, Any, Optional

from PyQt6.QtCore import Qt, QTimer, QObject, pyqtSignal
from PyQt6.QtGui import QFontDatabase, QFont
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QHBoxLayout,
    QLineEdit,
    QTextEdit,
    QGroupBox,
    QScrollArea,
    QMessageBox,
    QFileDialog,
    QSlider,
    QDialog,
    QSplitter,
    QGridLayout,
    QFrame,
)

# Import dei componenti UI esistenti
from .draggable_text_widget import DraggableTextWidget
from .settings_dialog import SettingsDialog

# Import del controller (quando sarà disponibile)
try:
    # Prova importazione relativa
    from ..controllers.cogniflow_controller import CogniFlowController
    CONTROLLER_AVAILABLE = True
except ImportError:
    try:
        # Fallback: importazione assoluta
        from controllers.cogniflow_controller import CogniFlowController
        CONTROLLER_AVAILABLE = True
    except ImportError:
        CogniFlowController = None
        CONTROLLER_AVAILABLE = False

# Import TTS per la pronuncia IPA
try:
    # Prova importazione relativa
    from ..Artificial_Intelligence.Sintesi_Vocale.managers.tts_manager import TTSThread
    TTS_AVAILABLE = True
except ImportError:
    try:
        # Fallback: importazione assoluta
        from Artificial_Intelligence.Sintesi_Vocale.managers.tts_manager import TTSThread
        TTS_AVAILABLE = True
    except ImportError:
        TTSThread = None
        TTS_AVAILABLE = False
        logging.warning(
            "Sistema TTS non disponibile - funzionalità di pronuncia IPA limitata"
        )

# Import del sistema di configurazione
try:
    # Prova importazione relativa
    from ..main_03_configurazione_e_opzioni import get_config, load_settings
except ImportError:
    try:
        # Fallback: importazione assoluta
        from main_03_configurazione_e_opzioni import get_config, load_settings
    except ImportError as e:
        logging.error(f"❌ Impossibile importare configurazione: {e}")
        logging.error("💡 Assicurati di eseguire dal launcher principale")
        raise

# Altri import esistenti...
try:
    # Prova importazione relativa
    from ..Artificial_Intelligence.Ollama.ollama_bridge import OllamaBridge
except ImportError:
    try:
        # Fallback: importazione assoluta
        from Artificial_Intelligence.Ollama.ollama_bridge import OllamaBridge
    except ImportError:
        OllamaBridge = None

try:
    # Prova importazione relativa
    from ..Artificial_Intelligence.Riconoscimento_Vocale.managers.speech_recognition_manager import (
        SpeechRecognitionThread,
        AudioFileTranscriptionThread,
        ensure_vosk_model_available,
    )
except ImportError:
    try:
        # Fallback: importazione assoluta
        from Artificial_Intelligence.Riconoscimento_Vocale.managers.speech_recognition_manager import (
            SpeechRecognitionThread,
            AudioFileTranscriptionThread,
            ensure_vosk_model_available,
        )
    except ImportError:
        SpeechRecognitionThread = None
        AudioFileTranscriptionThread = None
        ensure_vosk_model_available = None

# Import del sistema di errori user-friendly
try:
    from .user_friendly_errors import show_user_friendly_error, show_success_message
except ImportError:

    def show_user_friendly_error(parent, error, context=""):
        QMessageBox.critical(parent, "Errore", f"Errore: {str(error)}")

    def show_success_message(parent, operation, details=""):
        QMessageBox.information(
            parent, "Successo", f"Operazione completata: {operation}"
        )


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


class UIManager(QObject):
    """
    Gestore dell'interfaccia utente - separa la logica UI dalla business logic
    """

    # Segnali per comunicazione con il controller
    button_clicked = pyqtSignal(str, dict)  # button_name, data
    text_input_submitted = pyqtSignal(str)  # text
    settings_requested = pyqtSignal()

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.logger = logging.getLogger(__name__)

        # Riferimenti ai widget principali
        self.text_widgets = []
        self.current_project_name = ""

        # Stato dell'interfaccia
        self.tutor_session_active = False
        self.screen_sharing_active = False
        self.tools_expanded = True

    def setup_ui(self):
        """Configura l'interfaccia utente"""
        self.main_window.setWindowTitle("CogniFlow - Refactored")
        settings = load_settings()

        # Dimensioni finestra
        window_width = settings.get("ui", {}).get("window_width", 1200)
        window_height = settings.get("ui", {}).get("window_height", 800)
        self.main_window.setGeometry(100, 100, window_width, window_height)

        # Widget centrale
        central_widget = QWidget()
        self.main_window.setCentralWidget(central_widget)

        # Applica stili
        self._apply_styles(settings)

        # Layout principale
        main_layout = QVBoxLayout(central_widget)

        # Top bar
        self._create_top_bar(main_layout)

        # Contenuto principale
        self._create_main_content(main_layout, settings)

        # Footer
        self._create_footer(main_layout)

        # Timer per aggiornamenti periodici
        self._setup_timers()

    def _apply_styles(self, settings):
        """Applica gli stili all'interfaccia"""
        # Carica colori dalle impostazioni
        colors = settings.get("colors", {})
        button_text_colors = colors.get("button_text_colors", {})
        button_border_colors = colors.get("button_border_colors", {})
        button_background_colors = colors.get("button_background_colors", {})

        # Carica preferenze font
        main_font_size = settings.get("fonts", {}).get("main_font_size", 13)
        pensierini_font_size = settings.get("fonts", {}).get("pensierini_font_size", 12)

        # CSS dinamico
        style_sheet = f"""
            QMainWindow {{
                background: #f8f9fa;
                font-size: {main_font_size}px;
            }}

            QPushButton {{
                background-color: transparent;
                color: {button_text_colors.get('options_button', '#000000')};
                border: 2px solid {button_border_colors.get('general_border', '#357abd')};
                border-radius: 10px;
                padding: 12px 16px;
                font-weight: bold;
                min-width: 140px;
                min-height: 40px;
                font-size: {main_font_size + 1}px;
            }}

            QPushButton:hover {{
                background-color: rgba(74, 144, 226, 0.1);
                border-color: #357abd;
            }}

            /* Altri stili per pulsanti specifici... */
        """

        self.main_window.setStyleSheet(style_sheet)

    def _create_top_bar(self, parent_layout):
        """Crea la barra superiore"""
        top_layout = QHBoxLayout()

        # Pulsante Opzioni
        self.options_button = QPushButton("⚙️ Opzioni")
        self.options_button.clicked.connect(
            lambda: self.button_clicked.emit("options", {})
        )
        top_layout.addWidget(self.options_button)

        # Pulsante Toggle Tools
        self.toggle_tools_button = QPushButton("🔧 Ingranaggi")
        self.toggle_tools_button.setCheckable(True)
        self.toggle_tools_button.clicked.connect(
            lambda: self.button_clicked.emit("toggle_tools", {})
        )
        top_layout.addWidget(self.toggle_tools_button)

        top_layout.addStretch()

        # Input nome progetto
        self.project_name_input = QLineEdit()
        self.project_name_input.setPlaceholderText("Nome progetto...")
        top_layout.addWidget(self.project_name_input)
        top_layout.addStretch()

        # Pulsanti Salva/Carica
        self.save_button = QPushButton("💾 Salva")
        self.save_button.clicked.connect(lambda: self.button_clicked.emit("save", {}))
        top_layout.addWidget(self.save_button)

        self.load_button = QPushButton("📂 Carica")
        self.load_button.clicked.connect(lambda: self.button_clicked.emit("load", {}))
        top_layout.addWidget(self.load_button)

        parent_layout.addLayout(top_layout)

    def _create_main_content(self, parent_layout, settings):
        """Crea il contenuto principale con splitter"""
        # Splitter principale
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)

        # Colonna A: Pensierini
        self.column_a_group = QGroupBox("📝 Contenuti pensierini creativi (A)")
        column_a_layout = QVBoxLayout(self.column_a_group)
        self.pensierini_scroll = QScrollArea()
        self.pensierini_scroll.setWidgetResizable(True)
        self.pensierini_widget = PensieriniWidget(settings, None)
        self.pensierini_layout = QVBoxLayout(self.pensierini_widget)
        self.pensierini_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.pensierini_widget.pensierini_layout = self.pensierini_layout
        self.pensierini_scroll.setWidget(self.pensierini_widget)
        column_a_layout.addWidget(self.pensierini_scroll)
        self.main_splitter.addWidget(self.column_a_group)

        # Colonna B: Work Area
        self.column_b_group = QGroupBox("🎯 Area di Lavoro (B)")
        column_b_layout = QVBoxLayout(self.column_b_group)
        self._setup_work_area(column_b_layout)
        self.main_splitter.addWidget(self.column_b_group)

        # Colonna C: Details
        self.column_c_group = QGroupBox("Lavagna risposta Interattiva & AI")
        column_c_layout = QVBoxLayout(self.column_c_group)
        self.details_scroll = QScrollArea()
        self.details_scroll.setWidgetResizable(True)
        self.details_widget = QWidget()
        self.details_layout = QVBoxLayout(self.details_widget)
        self.details_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.details_scroll.setWidget(self.details_widget)
        column_c_layout.addWidget(self.details_scroll)
        self.main_splitter.addWidget(self.column_c_group)

        # Imposta proporzioni
        self.main_splitter.setSizes([333, 333, 334])

        # Aggiungi allo splitter verticale
        self.vertical_splitter = QSplitter(Qt.Orientation.Vertical)
        self.vertical_splitter.addWidget(self.main_splitter)

        # Area input pensierini
        self._create_input_area()

        parent_layout.addWidget(self.vertical_splitter, 1)

    def _create_input_area(self):
        """Crea l'area di input per i pensierini"""
        pensierini_input_group = QGroupBox("✏️ Creazione Pensierini")
        pensierini_input_group.setMinimumHeight(80)
        pensierini_input_group.setMaximumHeight(100)
        pensierini_layout = QVBoxLayout(pensierini_input_group)
        pensierini_layout.setContentsMargins(10, 20, 10, 10)

        input_row_layout = QHBoxLayout()
        input_row_layout.setSpacing(10)

        self.input_text_area = QTextEdit()
        self.input_text_area.setPlaceholderText(
            "Scrivi qui, ( premi INVIO per creare un pensierino - Premi INVIO di destra per tornare a capo )"
        )
        self.input_text_area.setFixedHeight(35)
        self.input_text_area.installEventFilter(self.main_window)
        input_row_layout.addWidget(self.input_text_area, 4)

        self.add_pensierino_button = QPushButton("➕ Aggiungi Pensierino")
        self.add_pensierino_button.clicked.connect(
            lambda: self.button_clicked.emit("add_pensierino", {})
        )
        input_row_layout.addWidget(self.add_pensierino_button, 1)

        pensierini_layout.addLayout(input_row_layout)
        self.vertical_splitter.addWidget(pensierini_input_group)

    def _setup_work_area(self, layout):
        """Configura l'area di lavoro"""
        self.work_area_scroll = QScrollArea()
        self.work_area_scroll.setWidgetResizable(True)
        self.work_area_widget = WorkAreaWidget(self.main_window.settings)
        self.work_area_layout = self.work_area_widget.widget_layout
        self.work_area_scroll.setWidget(self.work_area_widget)
        layout.addWidget(self.work_area_scroll)

    def _create_footer(self, parent_layout):
        """Crea il footer con informazioni di stato"""
        footer_layout = QHBoxLayout()
        footer_layout.addStretch()

        self.status_footer_label = QLabel()
        self.status_footer_label.setObjectName("status_footer_label")

        footer_font_size = (
            self.main_window.settings.get("fonts", {}).get("main_font_size", 13) - 2
        )
        self.status_footer_label.setStyleSheet(
            f"""
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
        """
        )

        self.update_footer_status()
        footer_layout.addWidget(self.status_footer_label)
        parent_layout.addLayout(footer_layout)

    def _setup_timers(self):
        """Configura i timer per aggiornamenti periodici"""
        self.footer_timer = QTimer()
        self.footer_timer.timeout.connect(self.update_footer_status)
        self.footer_timer.start(60000)  # Aggiorna ogni 60 secondi

    def update_footer_status(self):
        """Aggiorna le informazioni di stato nel footer"""
        try:
            current_time = datetime.now().strftime("%H:%M:%S")
            status_text = (
                f"🕐 {current_time} | 👤 Sessione attiva | 📊 Sistema operativo"
            )
            self.status_footer_label.setText(status_text)
        except Exception as e:
            logging.error(f"Errore nell'aggiornamento del footer: {e}")
            self.status_footer_label.setText("📊 Stato: Sistema attivo")

    def show_text_in_details(self, full_text: str):
        """Mostra testo nei dettagli"""
        # Implementazione semplificata
        self._clear_details()

        # Crea widget per mostrare testo
        from PyQt6.QtWidgets import QTextEdit

        text_widget = QTextEdit()
        text_widget.setReadOnly(True)
        text_widget.setPlainText(full_text)
        self.details_layout.addWidget(text_widget)

    def _clear_details(self):
        """Pulisce la colonna dettagli"""
        try:
            while self.details_layout.count():
                item = self.details_layout.takeAt(0)
                if item:
                    widget = item.widget()
                    if widget:
                        widget.deleteLater()
        except Exception as e:
            logging.error(f"Errore pulizia dettagli: {e}")

    def add_text_widget(self, text: str):
        """Aggiunge un widget di testo all'area di lavoro"""
        if DraggableTextWidget and text.strip():
            widget = DraggableTextWidget(text, self.main_window.settings)
            self.work_area_layout.addWidget(widget)
            self.text_widgets.append(widget)
            logging.info(f"Aggiunto widget di testo: {text[:50]}...")

    def get_input_text(self) -> str:
        """Ottiene il testo dall'area di input"""
        return self.input_text_area.toPlainText().strip()

    def clear_input_text(self):
        """Pulisce l'area di input"""
        self.input_text_area.clear()

    def set_project_name(self, name: str):
        """Imposta il nome del progetto"""
        self.current_project_name = name
        self.project_name_input.setText(name)

    def get_project_name(self) -> str:
        """Ottiene il nome del progetto"""
        return self.project_name_input.text().strip()


# Classi di supporto (spostate qui per modularità)
class WorkAreaWidget(QWidget):
    """Widget per l'area di lavoro con supporto al drop"""

    def __init__(self, settings):
        super().__init__()
        self.settings = settings
        self.setAcceptDrops(True)

        self.widget_layout = QVBoxLayout(self)
        self.widget_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.setLayout(self.widget_layout)

    def dragEnterEvent(self, event):
        """Accetta il drag se contiene testo o dati del widget."""
        if event.mimeData().hasText() or event.mimeData().hasFormat(
            "application/x-draggable-widget"
        ):
            event.acceptProposedAction()
            event.setDropAction(Qt.DropAction.CopyAction)

    def dropEvent(self, event):
        """Gestisce il drop creando un nuovo widget trascinabile."""
        try:
            if event.mimeData().hasText():
                text = event.mimeData().text()
                if text and text.strip():
                    from .draggable_text_widget import DraggableTextWidget

                    widget = DraggableTextWidget(text, self.settings)
                    self.widget_layout.addWidget(widget)
                    event.acceptProposedAction()
        except Exception as e:
            logging.error(f"Errore durante il drop nell'area di lavoro: {e}")


class PensieriniWidget(QWidget):
    """Widget per gestire l'area pensierini con controllo duplicati"""

    def __init__(self, settings, pensierini_layout):
        super().__init__()
        self.settings = settings
        self.pensierini_layout = pensierini_layout or QVBoxLayout()
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        """Accetta il drag se contiene testo o dati del widget."""
        try:
            mime_data = event.mimeData()
            if mime_data and (
                mime_data.hasText()
                or mime_data.hasFormat("application/x-draggable-widget")
            ):
                event.acceptProposedAction()
                event.setDropAction(Qt.DropAction.CopyAction)
        except Exception as e:
            logging.error(f"Errore in dragEnterEvent: {e}")

    def dropEvent(self, event):
        """Gestisce il drop controllando se esiste già un widget con lo stesso testo."""
        try:
            if event.mimeData().hasText():
                text = event.mimeData().text()
                if text and text.strip():
                    # Controlla duplicati (implementazione semplificata)
                    from .draggable_text_widget import DraggableTextWidget

                    widget = DraggableTextWidget(text, self.settings)
                    if self.pensierini_layout:
                        self.pensierini_layout.addWidget(widget)
                    event.acceptProposedAction()
        except Exception as e:
            logging.error(f"Errore durante il drop nell'area pensierini: {e}")


class MainWindowRefactored(QMainWindow):
    """
    Versione refactored della MainWindow che separa UI da business logic
    """

    def __init__(self):
        super().__init__()
        self.settings = load_settings()
        self.ui_manager = UIManager(self)

        # Inizializza il controller se disponibile
        self.controller = None
        if CONTROLLER_AVAILABLE:
            self.controller = CogniFlowController()
            self._connect_controller_signals()

        # Configura l'interfaccia
        self.ui_manager.setup_ui()

        # Configura segnali UI
        self._connect_ui_signals()

        logging.info("MainWindow Refactored inizializzata")

    def _connect_controller_signals(self):
        """Connette i segnali del controller"""
        if self.controller:
            self.controller.ai_response_received.connect(self._on_ai_response_received)
            self.controller.ai_error_occurred.connect(self._on_ai_error_occurred)
            self.controller.speech_recognized.connect(self._on_speech_recognized)
            self.controller.error_occurred.connect(self._on_error_occurred)

    def _connect_ui_signals(self):
        """Connette i segnali dell'UI manager"""
        self.ui_manager.button_clicked.connect(self._on_button_clicked)
        self.ui_manager.text_input_submitted.connect(self._on_text_input_submitted)
        self.ui_manager.settings_requested.connect(self._on_settings_requested)

    def _on_button_clicked(self, button_name: str, data: dict):
        """Gestisce i click dei pulsanti"""
        if button_name == "options":
            self._open_settings()
        elif button_name == "toggle_tools":
            self._toggle_tools_panel()
        elif button_name == "save":
            self._save_project()
        elif button_name == "load":
            self._load_project()
        elif button_name == "add_pensierino":
            self._add_pensierino()

    def _on_text_input_submitted(self, text: str):
        """Gestisce l'invio di testo"""
        if text.strip():
            self.ui_manager.add_text_widget(text)
            self.ui_manager.clear_input_text()

    def _on_ai_response_received(self, prompt: str, response: str):
        """Gestisce la risposta AI"""
        full_content = f"🤖 Risposta AI:\n\n{prompt}\n\n{'=' * 50}\n\n{response}"
        self.ui_manager.show_text_in_details(full_content)

    def _on_ai_error_occurred(self, error_msg: str):
        """Gestisce gli errori AI"""
        show_user_friendly_error(self, Exception(error_msg), "servizio AI")

    def _on_speech_recognized(self, text: str):
        """Gestisce il riconoscimento vocale"""
        self.ui_manager.input_text_area.setPlainText(text)

    def _on_error_occurred(self, error_type: str, message: str):
        """Gestisce gli errori generali"""
        show_user_friendly_error(self, Exception(message), error_type)

    def _open_settings(self):
        """Apre la finestra delle impostazioni"""
        if SettingsDialog:
            dialog = SettingsDialog(self)
            dialog.exec()

    def _toggle_tools_panel(self):
        """Mostra/nasconde il pannello degli strumenti"""
        # Implementazione semplificata
        pass

    def _save_project(self):
        """Salva il progetto corrente"""
        project_name = self.ui_manager.get_project_name()
        if not project_name:
            QMessageBox.warning(
                self,
                "Nome progetto mancante",
                "Inserisci un nome per il progetto prima di salvarlo.",
            )
            return

        # Raccogli i dati del progetto (implementazione semplificata)
        project_data = {
            "pensierini": [],
            "work_area": [],
            "timestamp": datetime.now().isoformat(),
        }

        if self.controller:
            success = self.controller.save_project(project_name, project_data)
        else:
            # Salvataggio manuale semplificato
            success = self._save_project_manual(project_name, project_data)

        if success:
            QMessageBox.information(
                self,
                "Salvataggio completato",
                f"Progetto '{project_name}' salvato con successo!",
            )
        else:
            QMessageBox.critical(
                self,
                "Errore salvataggio",
                "Errore durante il salvataggio del progetto.",
            )

    def _load_project(self):
        """Carica un progetto"""
        if self.controller:
            projects = self.controller.get_available_projects()
        else:
            projects = self._get_available_projects_manual()

        if not projects:
            QMessageBox.information(
                self, "Nessun progetto", "Non ci sono progetti salvati."
            )
            return

        project_name, ok = QInputDialog.getItem(
            self, "Carica progetto", "Seleziona progetto:", projects, 0, False
        )
        if ok and project_name:
            if self.controller:
                project_data = self.controller.load_project(project_name)
            else:
                project_data = self._load_project_manual(project_name)

            if project_data:
                self.ui_manager.set_project_name(project_name)
                QMessageBox.information(
                    self,
                    "Caricamento completato",
                    f"Progetto '{project_name}' caricato con successo!",
                )
            else:
                QMessageBox.critical(
                    self,
                    "Errore caricamento",
                    "Errore durante il caricamento del progetto.",
                )

    def _add_pensierino(self):
        """Aggiunge un pensierino"""
        text = self.ui_manager.get_input_text()
        if text.strip():
            self.ui_manager.add_text_widget(text)
            self.ui_manager.clear_input_text()

    def _save_project_manual(self, project_name: str, data: dict) -> bool:
        """Salvataggio manuale semplificato"""
        try:
            projects_dir = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "Save",
                "mia_dispenda_progetti",
            )
            os.makedirs(projects_dir, exist_ok=True)

            safe_name = "".join(
                c for c in project_name if c.isalnum() or c in (" ", "-", "_")
            ).rstrip()
            file_path = os.path.join(projects_dir, f"{safe_name}.json")

            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            return True
        except Exception as e:
            logging.error(f"Errore salvataggio manuale: {e}")
            return False

    def _load_project_manual(self, project_name: str) -> Optional[dict]:
        """Caricamento manuale semplificato"""
        try:
            projects_dir = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "Save",
                "mia_dispenda_progetti",
            )
            safe_name = "".join(
                c for c in project_name if c.isalnum() or c in (" ", "-", "_")
            ).rstrip()
            file_path = os.path.join(projects_dir, f"{safe_name}.json")

            if os.path.exists(file_path):
                with open(file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            return None
        except Exception as e:
            logging.error(f"Errore caricamento manuale: {e}")
            return None

    def _get_available_projects_manual(self) -> list:
        """Ottiene la lista dei progetti disponibili (manuale)"""
        try:
            projects_dir = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "Save",
                "mia_dispenda_progetti",
            )
            if os.path.exists(projects_dir):
                return [f[:-5] for f in os.listdir(projects_dir) if f.endswith(".json")]
            return []
        except Exception as e:
            logging.error(f"Errore recupero progetti: {e}")
            return []

    def eventFilter(self, obj, event):
        """Event filter per intercettare eventi della tastiera."""
        from PyQt6.QtCore import QEvent, Qt

        if (
            obj == self.ui_manager.input_text_area
            and event.type() == QEvent.Type.KeyPress
            and event.key() == Qt.Key.Key_Return
            and not event.modifiers() & Qt.KeyboardModifier.ShiftModifier
        ):
            text = self.ui_manager.get_input_text()
            if text:
                self._on_text_input_submitted(text)
            return True

        return super().eventFilter(obj, event)

    def closeEvent(self, event):
        """Gestisce la chiusura dell'applicazione"""
        if self.controller:
            self.controller.cleanup()
        event.accept()


# Import necessario per QInputDialog
from PyQt6.QtWidgets import QInputDialog
