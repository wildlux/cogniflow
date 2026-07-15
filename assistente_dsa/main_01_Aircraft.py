#!/usr/bin/env python3
"""
Main 01 Aircraft - Launcher per la schermata principale
Richiama la porta aerei per avviare l'interfaccia principale
"""

import json
import logging
import os
import sys
import importlib.util
from datetime import datetime

# Aggiungi il percorso del progetto ai path di sistema per gli import
project_root = os.path.dirname(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
from PyQt6.QtCore import (
    Qt,
    QTimer,
    QEvent,
    QPropertyAnimation,
    QEasingCurve,
    QDateTime,
    pyqtSignal,
    QObject,
    QPoint,
    QPointF,
    QRect,
)
from PyQt6.QtGui import (
    QFontDatabase,
    QFont,
    QFontMetrics,
    QColor,
    QRadialGradient,
    QShortcut,
    QKeySequence,
    QPainter,
    QPen,
    QMouseEvent,
    QImage,
    QTextCharFormat,
    QTextCursor,
    QBrush,
)
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
    QSizePolicy,
    QGroupBox,
    QScrollArea,
    QMessageBox,
    QFileDialog,
    QSlider,
    QDialog,
    QSplitter,
    QGridLayout,
    QFrame,
    QToolBox,
    QInputDialog,
)

# Import centralizzato delle dipendenze
try:
    helper_path = os.path.join(os.path.dirname(__file__), "0_HELPER_DEPENDENCY.py")
    spec = importlib.util.spec_from_file_location("helper_dependency", helper_path)
    if spec and spec.loader:
        helper_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(helper_module)
        print("✅ Helper dependency loaded successfully")
    else:
        print("⚠️  Could not load helper dependency")
except Exception as e:
    print(f"⚠️  Helper dependency not available: {e}")

# Import delle funzioni e classi necessarie con gestione errori
def safe_import(module_path, attr_name, default_value=None):
    """Import sicuro che restituisce un valore di default se l'import fallisce."""
    try:
        module = __import__(module_path, fromlist=[attr_name])
        return getattr(module, attr_name, default_value)
    except (ImportError, AttributeError) as e:
        print(f"⚠️  Import failed for {module_path}.{attr_name}: {e}")
        return default_value

# Import delle impostazioni e configurazione
load_settings = safe_import('core.config_module', 'load_settings', lambda: {})
get_config = safe_import('core.config_module', 'get_config', lambda: None)

# Import del bridge Ollama per AI
OllamaBridge = safe_import('Artificial_Intelligence.Ollama.ollama_bridge', 'OllamaBridge', None)

# Import dei componenti UI
DraggableTextWidget = safe_import('UI.draggable_text_widget', 'DraggableTextWidget', None)
SettingsDialog = safe_import('UI.settings_dialog', 'SettingsDialog', None)
show_user_friendly_error = safe_import('UI.user_friendly_errors', 'show_user_friendly_error', lambda *args, **kwargs: None)

# Import dei thread per riconoscimento vocale
SpeechRecognitionThread = safe_import('Artificial_Intelligence.Riconoscimento_Vocale.managers.speech_recognition_manager', 'SpeechRecognitionThread', None)

# Altre funzioni mancanti
ensure_vosk_model_available = safe_import('Artificial_Intelligence.Riconoscimento_Vocale.managers.speech_recognition_manager', 'ensure_vosk_model_available', lambda *args, **kwargs: False)
AudioFileTranscriptionThread = safe_import('Artificial_Intelligence.Riconoscimento_Vocale.managers.speech_recognition_manager', 'AudioFileTranscriptionThread', None)
TTSThread = safe_import('Artificial_Intelligence.Sintesi_Vocale.managers.tts_manager', 'TTSThread', None)

# Import per OCR
try:
    import pytesseract
    from PIL import Image
    OCR_AVAILABLE = True
except ImportError:
    pytesseract = None
    Image = None
    OCR_AVAILABLE = False
    print("⚠️  OCR functionality not available")

# Import per funzionalità multimediali
try:
    from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
    MULTIMEDIA_AVAILABLE = True
except ImportError:
    QMediaPlayer = None
    QAudioOutput = None
    MULTIMEDIA_AVAILABLE = False
    print("⚠️  Multimedia functionality not available")

# Controllo disponibilità TTS
try:
    from Artificial_Intelligence.Sintesi_Vocale.managers.tts_manager import TTSThread
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False
    print("⚠️  TTS functionality not available")

# Funzione di utilità mancante
def show_success_message(parent, title, message):
    """Mostra un messaggio di successo."""
    try:
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.information(parent, title, message)
    except:
        print(f"✅ {title}: {message}")

# Funzione di fallback per get_setting
def get_setting(key, default=None):
    """Ottiene un'impostazione con fallback."""
    try:
        settings = load_settings()
        return settings.get(key, default)
    except:
        return default

print("✅ Import process completed")

# Rimuovi la definizione di initialize_application da qui - sarà alla fine del file


class WebcamTestWindow(QMainWindow):
    """Finestra separata per il test della webcam con supporto gesture."""

    # Signals for hand gesture integration
    hand_position_signal = pyqtSignal(int, int)  # x, y coordinates
    gesture_detected_signal = pyqtSignal(str)  # gesture type

    # Signals for human detection (LIDAR-like)
    human_detected_signal = pyqtSignal(list)  # list of human bounding boxes
    human_position_signal = pyqtSignal(int, int)  # center position of primary human

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.setWindowTitle("🧪 Test Webcam - CogniFlow")
        self.setGeometry(100, 100, 800, 600)

        # Inizializza componenti
        self.webcam_active = False
        self.test_timer = None
        self.video_thread = None

        # Hand gesture state
        self.hand_x = 0
        self.hand_y = 0
        self.current_gesture = "none"
        self.is_dragging = False
        self.drag_start_pos = None
        self.button_original_pos = None

        # Visual feedback
        self.hover_highlight = False

        # Detection control states
        self.hands_enabled = False
        self.gestures_enabled = False
        self.expressions_enabled = False

        # Backend selection state
        self.current_backend = "opencv"  # Only OpenCV supported

        self.setup_ui()
        self.setup_connections()

        # Connect gesture signals
        self.hand_position_signal.connect(self.on_hand_position_update)
        self.gesture_detected_signal.connect(self.on_gesture_detected)

        # Connect human detection signals (LIDAR-like)
        self.human_detected_signal.connect(self.on_human_detected)
        self.human_position_signal.connect(self.on_human_position_update)

        # RITARDA L'AVVIO AUTOMATICO PER ASSICURARE CHE TUTTO SIA PRONTO
        from PyQt6.QtCore import QTimer

        QTimer.singleShot(100, self.start_webcam_automatically)  # Avvia dopo 100ms

        # ASSICURA CHE TUTTI I PULSANTI DI TRACCIAMENTO SIANO VISUALMENTE DISABILITATI
        self.face_tracking_btn.setChecked(False)
        self.left_hand_tracking_btn.setChecked(False)
        self.right_hand_tracking_btn.setChecked(False)
        self.human_detection_btn.setChecked(False)

        # Aggiorna l'aspetto dei pulsanti per riflettere lo stato disabilitato
        self.face_tracking_btn.repaint()
        self.left_hand_tracking_btn.repaint()
        self.right_hand_tracking_btn.repaint()
        self.human_detection_btn.repaint()

    def start_webcam_automatically(self):
        """Avvia automaticamente la webcam con tutti i tracciamenti disabilitati."""
        try:
            self.start_webcam_test()
            print("📹 Webcam avviata automaticamente con tracciamenti disabilitati")
        except Exception as e:
            print(f"❌ Errore avvio automatico webcam: {e}")
            self.status_label.setText("Status: Errore avvio automatico webcam")

    def setup_ui(self):
        """Configura l'interfaccia utente della finestra di test."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)

        # Titolo
        title_label = QLabel("🧪 Webcam Test Window - Gesture Control")
        title_label.setStyleSheet(
            """
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #2c3e50;
                margin-bottom: 10px;
            }
        """
        )
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # Splitter orizzontale per webcam e area di trascinamento
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.main_splitter.setHandleWidth(4)
        self.main_splitter.setStyleSheet(
            """
            QSplitter::handle {
                background: rgba(108, 117, 125, 0.4);
                border: 1px solid rgba(108, 117, 125, 0.6);
                border-radius: 2px;
            }
            QSplitter::handle:hover {
                background: rgba(74, 144, 226, 0.6);
                border-color: rgba(74, 144, 226, 0.8);
            }
        """
        )

        # === Colonna SINISTRA: Webcam ===
        self.setup_webcam_column()

        # === Colonna DESTRA: Area di trascinamento ===
        self.setup_drag_column()

        # Imposta proporzioni uguali per le due colonne
        self.main_splitter.setSizes([400, 400])

        layout.addWidget(self.main_splitter)

        # Pulsante semi-trasparente sovrapposto all'immagine webcam
        self.test_button = QPushButton("Pulsante di Prova")
        self.test_button.setStyleSheet(
            """
            QPushButton {
                background: rgba(255, 255, 255, 0.8);
                color: #333;
                border: 2px solid rgba(0, 123, 255, 0.9);
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
                padding: 8px 16px;
                z-index: 10;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.95);
                border-color: #007bff;
            }
            QPushButton:pressed {
                background: rgba(0, 123, 255, 0.2);
            }
        """
        )
        self.test_button.setFixedSize(160, 45)
        self.test_button.clicked.connect(self.on_test_button_clicked)

        # Posiziona il pulsante come figlio del container video per la sovrimpressione
        self.test_button.setParent(self.video_container)

        # Carica la posizione salvata o usa quella di default
        button_x, button_y = self.load_button_position()
        self.test_button.move(
            button_x, button_y
        )  # Posizione assoluta sopra l'immagine webcam
        self.test_button.raise_()  # Porta il pulsante in primo piano
        self.test_button.show()

        # Controlli
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(10)

        # Pulsante avvia test
        self.start_test_btn = QPushButton("▶️ Avvia Test")
        self.start_test_btn.setMinimumHeight(35)
        self.start_test_btn.setStyleSheet(
            """
            QPushButton {
                background: #28a745;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background: #218838;
            }
            QPushButton:pressed {
                background: #1e7e34;
            }
        """
        )
        controls_layout.addWidget(self.start_test_btn)

        # Pulsante ferma test
        self.stop_test_btn = QPushButton("⏹️ Ferma Test")
        self.stop_test_btn.setMinimumHeight(35)
        self.stop_test_btn.setEnabled(False)
        self.stop_test_btn.setStyleSheet(
            """
            QPushButton {
                background: #dc3545;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background: #c82333;
            }
            QPushButton:pressed {
                background: #bd2130;
            }
            QPushButton:disabled {
                background: #6c757d;
            }
        """
        )
        controls_layout.addWidget(self.stop_test_btn)

        # Pulsante cattura
        self.capture_btn = QPushButton("📸 Cattura")
        self.capture_btn.setMinimumHeight(35)
        self.capture_btn.setEnabled(False)
        self.capture_btn.setStyleSheet(
            """
            QPushButton {
                background: #007bff;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background: #0056b3;
            }
            QPushButton:pressed {
                background: #004085;
            }
            QPushButton:disabled {
                background: #6c757d;
            }
        """
        )
        controls_layout.addWidget(self.capture_btn)

        # Pulsanti controllo rilevamento
        self.hands_btn = QPushButton("🤚 Mani OFF")
        self.hands_btn.setMinimumHeight(35)
        self.hands_btn.setEnabled(False)
        self.hands_btn.setStyleSheet(
            """
            QPushButton {
                background: #17a2b8;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 12px;
                font-weight: bold;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background: #138496;
            }
            QPushButton:pressed {
                background: #117a8b;
            }
            QPushButton:disabled {
                background: #6c757d;
            }
        """
        )
        controls_layout.addWidget(self.hands_btn)

        self.gestures_btn = QPushButton("👋 Gesti OFF")
        self.gestures_btn.setMinimumHeight(35)
        self.gestures_btn.setEnabled(False)
        self.gestures_btn.setStyleSheet(
            """
            QPushButton {
                background: #ffc107;
                color: black;
                border: none;
                border-radius: 6px;
                font-size: 12px;
                font-weight: bold;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background: #e0a800;
            }
            QPushButton:pressed {
                background: #d39e00;
            }
            QPushButton:disabled {
                background: #6c757d;
            }
        """
        )
        controls_layout.addWidget(self.gestures_btn)

        self.expressions_btn = QPushButton("😊 Espressioni OFF")
        self.expressions_btn.setMinimumHeight(35)
        self.expressions_btn.setEnabled(False)
        self.expressions_btn.setStyleSheet(
            """
            QPushButton {
                background: #fd7e14;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 12px;
                font-weight: bold;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background: #e8590c;
            }
            QPushButton:pressed {
                background: #d8430b;
            }
            QPushButton:disabled {
                background: #6c757d;
            }
        """
        )
        controls_layout.addWidget(self.expressions_btn)




        controls_layout.addStretch()
        layout.addLayout(controls_layout)

        # === Controlli Tracciamento ===
        tracking_layout = QHBoxLayout()
        tracking_layout.setSpacing(8)

        # Etichetta sezione
        tracking_label = QLabel("🎯 Tracciamento:")
        tracking_label.setStyleSheet(
            """
            QLabel {
                font-size: 12px;
                font-weight: bold;
                color: #495057;
                padding: 5px;
            }
        """
        )
        tracking_layout.addWidget(tracking_label)

        # Pulsante traccia viso
        self.face_tracking_btn = QPushButton("👤 Traccia Viso")
        self.face_tracking_btn.setCheckable(True)
        self.face_tracking_btn.setChecked(False)
        self.face_tracking_btn.setMinimumHeight(30)
        self.face_tracking_btn.setStyleSheet(
            """
            QPushButton {
                background: #6c757d;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 11px;
                font-weight: bold;
                padding: 6px 10px;
            }
            QPushButton:hover {
                background: #5a6268;
            }
            QPushButton:checked {
                background: #28a745;
            }
            QPushButton:checked:hover {
                background: #218838;
            }
        """
        )
        tracking_layout.addWidget(self.face_tracking_btn)

        # Pulsante traccia mano sinistra
        self.left_hand_tracking_btn = QPushButton("✋ SX Traccia Mano")
        self.left_hand_tracking_btn.setCheckable(True)
        self.left_hand_tracking_btn.setChecked(False)
        self.left_hand_tracking_btn.setMinimumHeight(30)
        self.left_hand_tracking_btn.setStyleSheet(
            """
            QPushButton {
                background: #6c757d;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 11px;
                font-weight: bold;
                padding: 6px 10px;
            }
            QPushButton:hover {
                background: #5a6268;
            }
            QPushButton:checked {
                background: #007bff;
            }
            QPushButton:checked:hover {
                background: #0056b3;
            }
        """
        )
        tracking_layout.addWidget(self.left_hand_tracking_btn)

        # Pulsante traccia mano destra
        self.right_hand_tracking_btn = QPushButton("✋ DX Traccia Mano")
        self.right_hand_tracking_btn.setCheckable(True)
        self.right_hand_tracking_btn.setChecked(False)  # Disabilitato di default
        self.right_hand_tracking_btn.setMinimumHeight(30)
        self.right_hand_tracking_btn.setStyleSheet(
            """
            QPushButton {
                background: #6c757d;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 11px;
                font-weight: bold;
                padding: 6px 10px;
            }
            QPushButton:hover {
                background: #5a6268;
            }
            QPushButton:checked {
                background: #007bff;
            }
            QPushButton:checked:hover {
                background: #0056b3;
            }
        """
        )
        tracking_layout.addWidget(self.right_hand_tracking_btn)

        # Pulsante rilevamento umano (LIDAR-like)
        self.human_detection_btn = QPushButton("👤 Rilevamento Umano")
        self.human_detection_btn.setCheckable(True)
        self.human_detection_btn.setChecked(False)  # Disabilitato di default
        self.human_detection_btn.setMinimumHeight(30)
        self.human_detection_btn.setStyleSheet(
            """
            QPushButton {
                background: #6c757d;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 11px;
                font-weight: bold;
                padding: 6px 10px;
            }
            QPushButton:hover {
                background: #5a6268;
            }
            QPushButton:checked {
                background: #17a2b8;
            }
            QPushButton:checked:hover {
                background: #138496;
            }
        """
        )
        tracking_layout.addWidget(self.human_detection_btn)

        tracking_layout.addStretch()
        layout.addLayout(tracking_layout)

        # Status e informazioni
        self.status_label = QLabel("Status: Pronto per il test")
        self.status_label.setStyleSheet(
            """
            QLabel {
                font-size: 12px;
                color: #6c757d;
                padding: 5px;
                background: #f8f9fa;
                border-radius: 4px;
            }
        """
        )
        layout.addWidget(self.status_label)

        # Pulsante chiudi
        close_btn = QPushButton("❌ Chiudi Finestra")
        close_btn.setMinimumHeight(35)
        close_btn.setStyleSheet(
            """
            QPushButton {
                background: #6c757d;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background: #5a6268;
            }
            QPushButton:pressed {
                background: #545b62;
            }
        """
        )
        layout.addWidget(close_btn)
        close_btn.clicked.connect(self.close)

    def setup_connections(self):
        """Configura le connessioni dei segnali."""
        self.start_test_btn.clicked.connect(self.start_webcam_test)
        self.stop_test_btn.clicked.connect(self.stop_webcam_test)
        self.capture_btn.clicked.connect(self.capture_frame)
        self.test_button.clicked.connect(self.on_test_button_clicked)

        # Connessioni controlli tracciamento
        self.face_tracking_btn.clicked.connect(self.toggle_face_tracking)
        self.left_hand_tracking_btn.clicked.connect(self.toggle_left_hand_tracking)
        self.right_hand_tracking_btn.clicked.connect(self.toggle_right_hand_tracking)
        self.human_detection_btn.clicked.connect(self.toggle_human_detection)

        # Connessioni controlli rilevamento
        self.hands_btn.clicked.connect(self.toggle_hands)
        self.gestures_btn.clicked.connect(self.toggle_gestures)
        self.expressions_btn.clicked.connect(self.toggle_expressions)



    def on_hand_position_update(self, webcam_x, webcam_y):
        """Gestisce l'aggiornamento della posizione della mano."""
        # Map webcam coordinates to UI coordinates for video area
        ui_x, ui_y = self.map_webcam_to_ui_coordinates(webcam_x, webcam_y)

        self.hand_x = ui_x
        self.hand_y = ui_y

        # Map webcam coordinates to drag area coordinates
        drag_x, drag_y = self.map_webcam_to_drag_coordinates(webcam_x, webcam_y)

        # Update circle position in drag area
        if hasattr(self, "drag_circle"):
            # Keep circle within drag area bounds
            circle_size = self.drag_circle.size()
            drag_area_size = self.drag_area.size()

            bounded_x = max(
                0,
                min(
                    drag_x - circle_size.width() // 2,
                    drag_area_size.width() - circle_size.width(),
                ),
            )
            bounded_y = max(
                0,
                min(
                    drag_y - circle_size.height() // 2,
                    drag_area_size.height() - circle_size.height(),
                ),
            )

            self.drag_circle.move(bounded_x, bounded_y)

        # Check if hand is hovering over the test button
        button_rect = self.test_button.geometry()
        if button_rect.contains(ui_x, ui_y):
            if not self.hover_highlight:
                self.hover_highlight = True
                self.update_button_style()
        else:
            if self.hover_highlight:
                self.hover_highlight = False
                self.update_button_style()

        # Handle dragging if active
        if (
            self.is_dragging
            and self.drag_start_pos
            and self.button_original_pos is not None
        ):
            # Calculate movement delta
            delta_x = ui_x - self.drag_start_pos[0]
            delta_y = ui_y - self.drag_start_pos[1]

            # Update button position
            new_x = self.button_original_pos.x() + delta_x
            new_y = self.button_original_pos.y() + delta_y

            # Keep button within bounds
            new_x = max(
                0, min(new_x, self.video_container.width() - self.test_button.width())
            )
            new_y = max(
                0, min(new_y, self.video_container.height() - self.test_button.height())
            )

            self.test_button.move(new_x, new_y)

    def map_webcam_to_ui_coordinates(self, webcam_x, webcam_y):
        """Converte le coordinate dalla webcam alle coordinate dell'interfaccia utente."""
        # Use consistent webcam resolution for both mappings
        # This should match the resolution used by VideoThread
        webcam_width = 640
        webcam_height = 480

        # Get the actual size of the video display area
        video_size = self.video_area.size()
        ui_width = video_size.width()
        ui_height = video_size.height()

        # Calculate scale factors
        scale_x = ui_width / webcam_width
        scale_y = ui_height / webcam_height

        # Convert coordinates
        ui_x = int(webcam_x * scale_x)
        ui_y = int(webcam_y * scale_y)

        return ui_x, ui_y

    def map_webcam_to_drag_coordinates(self, webcam_x, webcam_y):
        """Converte le coordinate dalla webcam alle coordinate dell'area di trascinamento."""
        # Use the same webcam resolution as the video area for consistent mapping
        webcam_width = 640
        webcam_height = 480

        # Get the actual size of the drag area
        drag_size = self.drag_area.size()
        drag_width = drag_size.width()
        drag_height = drag_size.height()

        # Calculate scale factors
        scale_x = drag_width / webcam_width
        scale_y = drag_height / webcam_height

        # Convert coordinates
        drag_x = int(webcam_x * scale_x)
        drag_y = int(webcam_y * scale_y)

        return drag_x, drag_y

    def toggle_face_tracking(self):
        """Attiva/disattiva il tracciamento del viso."""
        enabled = self.face_tracking_btn.isChecked()
        if self.video_thread:
            self.video_thread.face_detection_enabled = enabled
            status = "ON" if enabled else "OFF"
            self.status_label.setText(f"Status: Tracciamento viso {status}")
            print(f"👤 Tracciamento viso: {status}")
        else:
            # Se video_thread non è disponibile, disabilita il pulsante e mostra messaggio
            self.face_tracking_btn.setChecked(False)
            self.status_label.setText(
                "Status: Avvia prima la webcam per abilitare i tracciamenti"
            )
            print("⚠️ Webcam non attiva - impossibile abilitare tracciamento viso")

    def toggle_left_hand_tracking(self):
        """Attiva/disattiva il tracciamento della mano sinistra."""
        enabled = self.left_hand_tracking_btn.isChecked()
        if self.video_thread:
            self.video_thread.left_hand_tracking_enabled = enabled
            status = "ON" if enabled else "OFF"
            self.status_label.setText(f"Status: Tracciamento mano sinistra {status}")
            print(f"✋ SX Tracciamento mano sinistra: {status}")
        else:
            # Se video_thread non è disponibile, disabilita il pulsante e mostra messaggio
            self.left_hand_tracking_btn.setChecked(False)
            self.status_label.setText(
                "Status: Avvia prima la webcam per abilitare i tracciamenti"
            )
            print(
                "⚠️ Webcam non attiva - impossibile abilitare tracciamento mano sinistra"
            )

    def toggle_right_hand_tracking(self):
        """Attiva/disattiva il tracciamento della mano destra."""
        enabled = self.right_hand_tracking_btn.isChecked()
        if self.video_thread:
            self.video_thread.right_hand_tracking_enabled = enabled
            status = "ON" if enabled else "OFF"
            self.status_label.setText(f"Status: Tracciamento mano destra {status}")
            print(f"✋ DX Tracciamento mano destra: {status}")
        else:
            # Se video_thread non è disponibile, disabilita il pulsante e mostra messaggio
            self.right_hand_tracking_btn.setChecked(False)
            self.status_label.setText(
                "Status: Avvia prima la webcam per abilitare i tracciamenti"
            )
            print(
                "⚠️ Webcam non attiva - impossibile abilitare tracciamento mano destra"
            )

    def toggle_human_detection(self):
        """Attiva/disattiva il rilevamento umano (LIDAR-like)."""
        enabled = self.human_detection_btn.isChecked()
        if self.video_thread:
            self.video_thread.human_detection_enabled = enabled
            status = "ON" if enabled else "OFF"
            self.status_label.setText(f"Status: Rilevamento umano {status}")
            print(f"👤 Rilevamento umano (LIDAR): {status}")
        else:
            # Se video_thread non è disponibile, disabilita il pulsante e mostra messaggio
            self.human_detection_btn.setChecked(False)
            self.status_label.setText(
                "Status: Avvia prima la webcam per abilitare i tracciamenti"
            )
            print("⚠️ Webcam non attiva - impossibile abilitare rilevamento umano")

    def on_gesture_detected(self, gesture):
        """Gestisce il rilevamento di un gesto."""
        self.current_gesture = gesture

        # Update status with more detailed information
        if gesture == "Closed Hand":
            if self.is_dragging:
                self.status_label.setText("Status: Trascinamento attivo - Closed Hand")
            else:
                self.status_label.setText(
                    "Status: Closed Hand rilevata - Pronto per trascinare"
                )
        elif gesture == "Open Hand":
            if self.is_dragging:
                self.status_label.setText("Status: Open Hand - Rilascia trascinamento")
            else:
                self.status_label.setText("Status: Open Hand rilevata")
        else:
            self.status_label.setText(f"Status: Gesto rilevato - {gesture}")

        # Handle drag gestures
        if gesture == "Closed Hand" and not self.is_dragging:
            # Start dragging if hand is over the button
            button_rect = self.test_button.geometry()
            if button_rect.contains(self.hand_x, self.hand_y):
                self.start_drag()
        elif gesture == "Open Hand" and self.is_dragging:
            # Stop dragging
            self.stop_drag()

    def start_drag(self):
        """Inizia il trascinamento del pulsante."""
        self.is_dragging = True
        self.drag_start_pos = (self.hand_x, self.hand_y)
        self.button_original_pos = self.test_button.pos()
        self.status_label.setText("Status: Trascinamento iniziato")
        print("🖱️ Trascinamento iniziato con gesto mano chiusa")

    def stop_drag(self):
        """Termina il trascinamento del pulsante."""
        if self.is_dragging:
            self.is_dragging = False
            self.drag_start_pos = None
            self.button_original_pos = None
            self.save_button_position()
            self.status_label.setText("Status: Trascinamento completato")
            print("🖱️ Trascinamento completato con gesto mano aperta")

    def on_video_thread_status(self, status):
        """Gestisce gli aggiornamenti di stato dal VideoThread."""
        self.status_label.setText(f"Status: {status}")

    def on_human_detected(self, humans):
        """Gestisce il rilevamento di umani (approccio LIDAR-like)."""
        if humans:
            self.status_label.setText(f"Status: {len(humans)} umano(i) rilevato(i)")
            print(f"👤 Rilevati {len(humans)} umani")
        else:
            self.status_label.setText("Status: Nessun umano rilevato")

    def on_human_position_update(self, human_x, human_y):
        """Gestisce l'aggiornamento della posizione dell'umano primario."""
        # Map human position to UI coordinates
        ui_x, ui_y = self.map_webcam_to_ui_coordinates(human_x, human_y)

        # Update status with human position
        self.status_label.setText(f"Status: Umano rilevato a ({ui_x}, {ui_y})")

        # Use human position for interaction (similar to hand tracking)
        # Check if human is hovering over the test button
        button_rect = self.test_button.geometry()
        if button_rect.contains(ui_x, ui_y):
            if not self.hover_highlight:
                self.hover_highlight = True
                self.update_button_style()
                print("👤 Umano sopra il pulsante")
        else:
            if self.hover_highlight:
                self.hover_highlight = False
                self.update_button_style()

    def update_webcam_feed_pixmap(self, pixmap):
        """Aggiorna il feed della webcam con il pixmap dal VideoThread."""
        if self.webcam_active and pixmap:
            # Scale pixmap to fit video area
            scaled_pixmap = pixmap.scaled(
                self.video_area.size(), Qt.AspectRatioMode.KeepAspectRatio
            )
            self.video_area.setPixmap(scaled_pixmap)

    def update_button_style(self):
        """Aggiorna lo stile del pulsante basato sullo stato."""
        base_style = """
            QPushButton {
                background: rgba(255, 255, 255, 0.8);
                color: #333;
                border: 2px solid rgba(0, 123, 255, 0.9);
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
                padding: 8px 16px;
                z-index: 10;
            }
        """

        if self.hover_highlight:
            style = (
                base_style
                + """
                QPushButton {
                    background: rgba(255, 255, 255, 0.95);
                    border-color: #28a745;
                    color: #155724;
                }
            """
            )
        elif self.is_dragging:
            style = (
                base_style
                + """
                QPushButton {
                    background: rgba(255, 193, 7, 0.9);
                    border-color: #856404;
                    color: #533f00;
                }
            """
            )
        else:
            style = (
                base_style
                + """
                QPushButton:hover {
                    background: rgba(255, 255, 255, 0.95);
                    border-color: #007bff;
                }
                QPushButton:pressed {
                    background: rgba(0, 123, 255, 0.2);
                }
            """
            )

        self.test_button.setStyleSheet(style)

    def on_test_button_clicked(self):
        """Gestisce il click del pulsante di prova."""
        print("🧪 Pulsante di prova cliccato!")
        self.status_label.setText("Status: Pulsante di prova attivato")
        # Puoi aggiungere qui altre azioni per il pulsante di prova

    def keyPressEvent(self, a0):
        """Gestisce gli eventi della tastiera per spostare il pulsante."""
        if hasattr(self, "test_button") and a0 is not None:
            current_pos = self.test_button.pos()
            step = 5  # Pixel per spostamento

            if a0.key() == Qt.Key.Key_Up:
                new_y = max(0, current_pos.y() - step)
                self.test_button.move(current_pos.x(), new_y)
                self.save_button_position()
            elif a0.key() == Qt.Key.Key_Down:
                # Limita il movimento verso il basso per non uscire dalla finestra
                max_y = self.height() - self.test_button.height() - 50
                new_y = min(max_y, current_pos.y() + step)
                self.test_button.move(current_pos.x(), new_y)
                self.save_button_position()
            elif a0.key() == Qt.Key.Key_Left:
                new_x = max(0, current_pos.x() - step)
                self.test_button.move(new_x, current_pos.y())
                self.save_button_position()
            elif a0.key() == Qt.Key.Key_Right:
                # Limita il movimento verso destra per non uscire dalla finestra
                max_x = self.width() - self.test_button.width() - 20
                new_x = min(max_x, current_pos.x() + step)
                self.test_button.move(new_x, current_pos.y())
                self.save_button_position()

        super().keyPressEvent(a0)

    def load_button_position(self):
        """Carica la posizione del pulsante dal file JSON."""
        try:
            settings_file = os.path.join(
                os.path.dirname(__file__), "button_position.json"
            )
            if os.path.exists(settings_file):
                with open(settings_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data.get("x", 10), data.get("y", 10)
        except Exception as e:
            print(f"Errore caricamento posizione pulsante: {e}")
        return 10, 10  # Posizione di default

    def save_button_position(self):
        """Salva la posizione del pulsante nel file JSON."""
        if hasattr(self, "test_button"):
            try:
                pos = self.test_button.pos()
                settings_file = os.path.join(
                    os.path.dirname(__file__), "button_position.json"
                )
                data = {
                    "x": pos.x(),
                    "y": pos.y(),
                    "timestamp": datetime.now().isoformat(),
                }
                with open(settings_file, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                print(f"✓ Posizione pulsante salvata: ({pos.x()}, {pos.y()})")
            except Exception as e:
                print(f"Errore salvataggio posizione pulsante: {e}")

    def resizeEvent(self, a0):
        """Gestisce il ridimensionamento della finestra per riposizionare il pulsante."""
        if hasattr(self, "test_button"):
            # Il pulsante è ora figlio del container video, quindi rimane sempre alla stessa posizione relativa
            # Non è necessario riposizionarlo manualmente dato che si muove con il container
            pass
        super().resizeEvent(a0)

    def start_webcam_test(self):
        """Avvia il test della webcam con VideoThread per gesture recognition."""
        try:
            # Check if VideoThread is available
            if not VIDEO_THREAD_AVAILABLE or VideoThread is None:
                self.status_label.setText("Status: VideoThread non disponibile")
                self.video_area.setText(
                    "❌ VideoThread non disponibile\n\nFunzionalità avanzate webcam limitate"
                )
                return

            self.webcam_active = True
            self.start_test_btn.setEnabled(False)
            self.stop_test_btn.setEnabled(True)
            self.capture_btn.setEnabled(True)
            # I nuovi pulsanti verranno abilitati in finalize_webcam_startup

            # Initialize VideoThread with gesture recognition enabled
            self.video_thread = VideoThread(main_window=self)

            # Verifica che il VideoThread sia stato creato correttamente
            if self.video_thread is None:
                self.status_label.setText("Status: Errore creazione VideoThread")
                self.video_area.setText("❌ Errore creazione VideoThread")
                return

            self.video_thread.change_pixmap_signal.connect(
                self.update_webcam_feed_pixmap
            )
            self.video_thread.status_signal.connect(self.on_video_thread_status)
            self.video_thread.human_position_signal.connect(
                self.on_hand_position_update
            )
            self.video_thread.gesture_detected_signal.connect(self.on_gesture_detected)

            # Connect human detection signals (LIDAR-like)
            self.video_thread.human_detected_signal.connect(self.human_detected_signal)
            self.video_thread.human_position_signal.connect(self.human_position_signal)

            # TUTTI I TRACCIAMENTI DISABILITATI PER DEFAULT
            self.video_thread.hand_detection_enabled = False
            self.video_thread.gesture_recognition_enabled = False
            self.video_thread.human_detection_enabled = (
                False  # Rilevamento umano disabilitato
            )

            # Forza tutti i controlli di tracciamento come disabilitati
            self.video_thread.face_detection_enabled = False
            self.video_thread.left_hand_tracking_enabled = False
            self.video_thread.right_hand_tracking_enabled = False
            self.video_thread.human_detection_enabled = False

            # Start the video thread
            self.video_thread.start()

            # Piccolo ritardo per assicurarsi che il thread sia operativo
            from PyQt6.QtCore import QTimer

            QTimer.singleShot(500, self.finalize_webcam_startup)  # 500ms di attesa

            self.status_label.setText("Status: Webcam attiva con gesture recognition")
            self.video_area.clear()  # Remove text, show video

            print("🧪 Test webcam avviato con VideoThread e gesture recognition")

        except Exception as e:
            self.status_label.setText(f"Status: Errore avvio webcam - {str(e)}")
            self.video_area.setText(f"❌ Errore avvio webcam:\n{str(e)}")
            print(f"❌ Errore avvio webcam: {e}")

    def finalize_webcam_startup(self):
        """Finalizza l'avvio della webcam dopo che il thread è operativo."""
        if self.video_thread and self.video_thread.isRunning():
            self.status_label.setText(
                "Status: Webcam attiva - tutti i tracciamenti disabilitati"
            )
            print(
                "✅ Webcam completamente operativa - tutti i tracciamenti disabilitati"
            )

            # Sincronizza i pulsanti con lo stato attuale
            self.face_tracking_btn.setChecked(False)
            self.left_hand_tracking_btn.setChecked(False)
            self.right_hand_tracking_btn.setChecked(False)
            self.human_detection_btn.setChecked(False)

            # Abilita i nuovi pulsanti di controllo rilevamento
            self.hands_btn.setEnabled(True)
            self.gestures_btn.setEnabled(True)
            self.expressions_btn.setEnabled(True)


        else:
            self.status_label.setText("Status: Webcam non avviata correttamente")
            print("⚠️ Webcam thread non è operativo")

    def stop_webcam_test(self):
        """Ferma il test della webcam con VideoThread."""
        try:
            self.webcam_active = False
            self.start_test_btn.setEnabled(True)
            self.stop_test_btn.setEnabled(False)
            self.capture_btn.setEnabled(False)
            # Disabilita i nuovi pulsanti di controllo rilevamento
            self.hands_btn.setEnabled(False)
            self.gestures_btn.setEnabled(False)
            self.expressions_btn.setEnabled(False)



            # Stop and cleanup VideoThread
            if self.video_thread:
                self.video_thread.stop()
                self.video_thread = None

            # Reset gesture state
            self.is_dragging = False
            self.drag_start_pos = None
            self.button_original_pos = None
            self.hover_highlight = False
            self.update_button_style()

            self.status_label.setText("Status: Test fermato")
            self.video_area.setText(
                "📹 Webcam Fermata\n\nClicca 'Avvia Test' per ricominciare"
            )

            print("🧪 Test webcam fermato")

        except Exception as e:
            print(f"❌ Errore arresto test webcam: {e}")
            self.status_label.setText(f"Status: Errore arresto - {str(e)}")

    def capture_frame(self):
        """Cattura un frame dalla webcam usando VideoThread."""
        try:
            if self.webcam_active and self.video_thread:
                import cv2
                import os
                from datetime import datetime

                # Get current frame from video thread
                # Since VideoThread processes frames internally, we'll capture from its cap
                if (
                    hasattr(self.video_thread, "cap")
                    and self.video_thread.cap
                    and self.video_thread.cap.isOpened()
                ):
                    ret, frame = self.video_thread.cap.read()
                    if ret:
                        # Flip frame horizontally for mirror effect
                        frame = cv2.flip(frame, 1)

                        # Generate filename with timestamp
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        screenshot_dir = os.path.join(
                            os.path.dirname(os.path.dirname(__file__)), "Screenshot"
                        )
                        os.makedirs(screenshot_dir, exist_ok=True)
                        filename = os.path.join(
                            screenshot_dir, f"webcam_capture_{timestamp}.png"
                        )

                        # Save the image
                        cv2.imwrite(filename, frame)

                        self.status_label.setText(
                            f"Status: Frame salvato - {os.path.basename(filename)}"
                        )
                        print(f"📸 Frame catturato e salvato: {filename}")

                        # Mostra messaggio di successo
                        if self.parent_window:
                            try:
                                show_success_message(
                                    self.parent_window,
                                    "Cattura frame",
                                    f"Frame salvato come {os.path.basename(filename)}",
                                )
                            except:
                                QMessageBox.information(
                                    self,
                                    "Successo",
                                    f"Frame catturato e salvato con successo",
                                )
                    else:
                        self.status_label.setText("Status: Errore cattura frame")
                        print("❌ Impossibile catturare il frame dalla webcam")
                else:
                    self.status_label.setText("Status: Webcam non pronta per cattura")
                    print("❌ Webcam non pronta per cattura")
            else:
                self.status_label.setText("Status: Webcam non attiva")
                print("❌ Webcam non attiva")

        except Exception as e:
            print(f"❌ Errore cattura frame: {e}")
            self.status_label.setText(f"Status: Errore cattura - {str(e)}")

    def setup_webcam_column(self):
        """Configura la colonna sinistra per il display della webcam."""
        # Container per la webcam
        self.video_container = QWidget()
        self.video_container.setStyleSheet(
            """
            QWidget {
                background: #000;
                border: 2px solid #333;
                border-radius: 8px;
            }
        """
        )

        video_layout = QVBoxLayout(self.video_container)
        video_layout.setContentsMargins(5, 5, 5, 5)

        # Etichetta per il video
        self.video_area = QLabel("📹 Webcam Feed\n\nClicca 'Avvia Test' per iniziare")
        self.video_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_area.setStyleSheet(
            """
            QLabel {
                color: #666;
                font-size: 16px;
                font-weight: bold;
                background: #111;
                border-radius: 4px;
                padding: 20px;
            }
        """
        )
        self.video_area.setMinimumSize(320, 240)

        video_layout.addWidget(self.video_area)
        self.main_splitter.addWidget(self.video_container)

    def setup_drag_column(self):
        """Configura la colonna destra per l'area di trascinamento."""
        # Container per l'area di trascinamento
        self.drag_container = QWidget()
        self.drag_container.setStyleSheet(
            """
            QWidget {
                background: #f8f9fa;
                border: 2px solid #dee2e6;
                border-radius: 8px;
            }
        """
        )

        drag_layout = QVBoxLayout(self.drag_container)
        drag_layout.setContentsMargins(5, 5, 5, 5)

        # Titolo area di trascinamento
        drag_title = QLabel("🎯 Drag Area")
        drag_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        drag_title.setStyleSheet(
            """
            QLabel {
                color: #495057;
                font-size: 14px;
                font-weight: bold;
                margin-bottom: 10px;
            }
        """
        )
        drag_layout.addWidget(drag_title)

        # Area di trascinamento con cerchio
        self.drag_area = QWidget()
        self.drag_area.setStyleSheet(
            """
            QWidget {
                background: #ffffff;
                border: 1px solid #ced4da;
                border-radius: 4px;
                min-height: 240px;
            }
        """
        )
        self.drag_area.setMinimumSize(320, 240)

        # Layout per l'area di trascinamento
        drag_area_layout = QVBoxLayout(self.drag_area)
        drag_area_layout.setContentsMargins(10, 10, 10, 10)

        # Cerchio trascinabile
        self.drag_circle = QLabel("●")
        self.drag_circle.setStyleSheet(
            """
            QLabel {
                color: #007bff;
                font-size: 40px;
                background: transparent;
                border: none;
            }
        """
        )
        self.drag_circle.setFixedSize(50, 50)
        self.drag_circle.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Posiziona il cerchio al centro inizialmente
        self.drag_circle.move(135, 95)  # Centro approssimativo dell'area 320x240

        # Aggiungi il cerchio come figlio dell'area di trascinamento
        self.drag_circle.setParent(self.drag_area)
        self.drag_circle.raise_()
        self.drag_circle.show()

        drag_layout.addWidget(self.drag_area)
        self.main_splitter.addWidget(self.drag_container)

    def closeEvent(self, a0):
        """Gestisce la chiusura della finestra."""
        self.stop_webcam_test()
        print("🧪 Finestra test webcam chiusa")
        if a0:
            a0.accept()

    def toggle_hands(self):
        """Attiva/disattiva il rilevamento delle mani."""
        if not self.webcam_active:
            return

        self.hands_enabled = not self.hands_enabled
        if self.hands_enabled:
            self.hands_btn.setText("🤚 Mani ON")
            self.hands_btn.setStyleSheet(
                """
                QPushButton {
                    background: #17a2b8;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    font-size: 12px;
                    font-weight: bold;
                    padding: 6px 12px;
                }
                QPushButton:hover {
                    background: #138496;
                }
                QPushButton:pressed {
                    background: #117a8b;
                }
            """
            )
            print("🤚 Rilevamento mani attivato")
        else:
            self.hands_btn.setText("🤚 Mani OFF")
            self.hands_btn.setStyleSheet(
                """
                QPushButton {
                    background: #6c757d;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    font-size: 12px;
                    font-weight: bold;
                    padding: 6px 12px;
                }
                QPushButton:hover {
                    background: #5a6268;
                }
                QPushButton:pressed {
                    background: #545b62;
                }
            """
            )
            print("🤚 Rilevamento mani disattivato")

        # TODO: Integrazione con VideoThread per toggle mani
        # if self.video_thread and hasattr(self.video_thread, 'toggle_hands'):
        #     self.video_thread.toggle_hands(self.hands_enabled)

    def toggle_gestures(self):
        """Attiva/disattiva il rilevamento dei gesti."""
        if not self.webcam_active:
            return

        self.gestures_enabled = not self.gestures_enabled
        if self.gestures_enabled:
            self.gestures_btn.setText("👋 Gesti ON")
            self.gestures_btn.setStyleSheet(
                """
                QPushButton {
                    background: #ffc107;
                    color: black;
                    border: none;
                    border-radius: 6px;
                    font-size: 12px;
                    font-weight: bold;
                    padding: 6px 12px;
                }
                QPushButton:hover {
                    background: #e0a800;
                }
                QPushButton:pressed {
                    background: #d39e00;
                }
            """
            )
            print("👋 Rilevamento gesti attivato")
        else:
            self.gestures_btn.setText("👋 Gesti OFF")
            self.gestures_btn.setStyleSheet(
                """
                QPushButton {
                    background: #6c757d;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    font-size: 12px;
                    font-weight: bold;
                    padding: 6px 12px;
                }
                QPushButton:hover {
                    background: #5a6268;
                }
                QPushButton:pressed {
                    background: #545b62;
                }
            """
            )
            print("👋 Rilevamento gesti disattivato")

        # TODO: Integrazione con VideoThread per toggle gesti
        # if self.video_thread and hasattr(self.video_thread, 'toggle_gestures'):
        #     self.video_thread.toggle_gestures(self.gestures_enabled)

    def toggle_expressions(self):
        """Attiva/disattiva il rilevamento delle espressioni."""
        if not self.webcam_active:
            return

        self.expressions_enabled = not self.expressions_enabled
        if self.expressions_enabled:
            self.expressions_btn.setText("😊 Espressioni ON")
            self.expressions_btn.setStyleSheet(
                """
                QPushButton {
                    background: #fd7e14;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    font-size: 12px;
                    font-weight: bold;
                    padding: 6px 12px;
                }
                QPushButton:hover {
                    background: #e8590c;
                }
                QPushButton:pressed {
                    background: #d8430b;
                }
            """
            )
            print("😊 Rilevamento espressioni attivato")
        else:
            self.expressions_btn.setText("😊 Espressioni OFF")
            self.expressions_btn.setStyleSheet(
                """
                QPushButton {
                    background: #6c757d;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    font-size: 12px;
                    font-weight: bold;
                    padding: 6px 12px;
                }
                QPushButton:hover {
                    background: #5a6268;
                }
                QPushButton:pressed {
                    background: #545b62;
                }
            """
            )
            print("😊 Rilevamento espressioni disattivato")

        # TODO: Integrazione con VideoThread per toggle espressioni
        # if self.video_thread and hasattr(self.video_thread, 'toggle_expressions'):
        #     self.video_thread.toggle_expressions(self.expressions_enabled)






# Import per OCR
try:
    import pytesseract
    from PIL import Image

    OCR_AVAILABLE = True
except ImportError:
    pytesseract = None
    Image = None
    OCR_AVAILABLE = False

# Import VideoThread for advanced webcam features
try:
    from Artificial_Intelligence.Video.visual_background import VideoThread

    VIDEO_THREAD_AVAILABLE = True
except ImportError:
    VideoThread = None
    VIDEO_THREAD_AVAILABLE = False
    logging.warning(
        "VideoThread non disponibile - funzionalità avanzate webcam limitate"
    )

# Import PyQt6 signals for hand gesture integration
from PyQt6.QtCore import pyqtSignal

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
        if a0 is not None and hasattr(a0, "mimeData"):
            mime_data = a0.mimeData()
            if mime_data and (
                mime_data.hasText()
                or mime_data.hasFormat("application/x-draggable-widget")
            ):
                a0.acceptProposedAction()

    def dragMoveEvent(self, a0):
        """Necessario perché Qt consenta il drop durante il movimento."""
        if a0 is not None and hasattr(a0, "mimeData"):
            mime_data = a0.mimeData()
            if mime_data and (
                mime_data.hasText()
                or mime_data.hasFormat("application/x-draggable-widget")
            ):
                a0.acceptProposedAction()

    def dropEvent(self, a0):
        """Gestisce il drop creando un nuovo widget trascinabile."""
        try:
            from UI.draggable_text_widget import DraggableTextWidget

            # Ottieni il testo dal drop
            text = ""
            if a0 is not None and hasattr(a0, "mimeData"):
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
            if a0 and hasattr(a0, "mimeData") and a0.mimeData():
                mime_data = a0.mimeData()
                if mime_data and (
                    mime_data.hasText()
                    or mime_data.hasFormat("application/x-draggable-widget")
                ):
                    if hasattr(a0, "acceptProposedAction"):
                        a0.acceptProposedAction()
        except Exception:
            logging.error("Errore in dragEnterEvent: {e}")

    def dragMoveEvent(self, a0):
        """Necessario perché Qt consenta il drop durante il movimento."""
        try:
            if a0 and hasattr(a0, "mimeData") and a0.mimeData():
                mime_data = a0.mimeData()
                if mime_data and (
                    mime_data.hasText()
                    or mime_data.hasFormat("application/x-draggable-widget")
                ):
                    a0.acceptProposedAction()
        except Exception:
            pass

    def dropEvent(self, a0):
        """Gestisce il drop controllando se esiste già un widget con lo stesso testo."""
        try:
            from UI.draggable_text_widget import DraggableTextWidget

            # Ottieni il testo dal drop
            text = ""
            if a0 and hasattr(a0, "mimeData") and a0.mimeData():
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
                    if hasattr(a0, "ignore"):
                        a0.ignore()
                    return

                # Crea un nuovo widget trascinabile con tutte le funzionalità
                widget = DraggableTextWidget(text, self.settings)
                # Aggiungi il widget al layout dei pensierini
                if hasattr(self, "pensierini_layout") and self.pensierini_layout:
                    self.pensierini_layout.addWidget(widget)
                if hasattr(a0, "acceptProposedAction"):
                    a0.acceptProposedAction()

        except Exception:
            logging.error("Errore durante il drop nell'area pensierini: {e}")

    def _find_existing_widget(self, text):
        """Cerca se esiste già un widget con lo stesso testo nei pensierini."""
        try:
            if not hasattr(self, "pensierini_layout") or not self.pensierini_layout:
                return None

            for i in range(self.pensierini_layout.count()):
                item = self.pensierini_layout.itemAt(i)
                if item:
                    widget = item.widget()
                    if widget:
                        text_label = getattr(widget, "text_label", None)
                        if text_label and hasattr(text_label, "text"):
                            existing_text = text_label.text().strip()
                            if existing_text == text:
                                return widget
        except Exception:
            logging.error("Errore in _find_existing_widget: {e}")
        return None


# Classe MainWindow integrata da aircraft.py


class HandCursorWidget(QWidget):
    """Cursore-gioco della mano: una bolla colorata con alone morbido.

    Verde = mano aperta, rosso = chiusa, blu = scorri. È volutamente grande
    e "giocoso" perché va vissuto come un gioco. I colori sono scelti
    dall'utente nelle Impostazioni (chiave `cursor.color_*`).
    """

    DEFAULT_COLORS = {
        "open": "#28a745",
        "closed": "#dc3545",
        "scroll": "#007bff",
    }
    SIZE = 52  # bolla grande: più facile da seguire, sembra un gioco

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setFixedSize(self.SIZE, self.SIZE)
        self.mode = "open"
        self.colors = {}
        self.reload_colors()
        self.hide()

    def reload_colors(self):
        """(Ri)legge i colori del cursore dalle Impostazioni."""
        self.colors = {}
        for mode, default in self.DEFAULT_COLORS.items():
            value = get_setting(f"cursor.color_{mode}", default)
            col = QColor(value)
            self.colors[mode] = col if col.isValid() else QColor(default)
        self.update()

    def set_mode(self, mode):
        if mode != self.mode and mode in self.DEFAULT_COLORS:
            self.mode = mode
            self.update()

    def set_closed(self, closed):
        self.set_mode("closed" if closed else "open")

    def paintEvent(self, a0):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        color = self.colors.get(self.mode, QColor(self.DEFAULT_COLORS[self.mode]))
        c = self.SIZE / 2

        # Alone morbido: sfumatura radiale che svanisce verso il bordo
        glow = QRadialGradient(c, c, c)
        g0 = QColor(color)
        g0.setAlpha(150 if self.mode == "closed" else 90)
        g1 = QColor(color)
        g1.setAlpha(0)
        glow.setColorAt(0.0, g0)
        glow.setColorAt(1.0, g1)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(glow)
        painter.drawEllipse(0, 0, self.SIZE, self.SIZE)

        # Bolla centrale con bordo pieno
        painter.setPen(QPen(color, 4))
        fill = QColor(color)
        fill.setAlpha({"open": 70, "closed": 160, "scroll": 120}[self.mode])
        painter.setBrush(fill)
        r = self.SIZE * 0.42
        painter.drawEllipse(int(c - r), int(c - r), int(2 * r), int(2 * r))

        # Lucciola/riflesso in alto a sinistra: dà l'aria di una bolla-gioco
        highlight = QColor(255, 255, 255, 180)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(highlight)
        painter.drawEllipse(int(c - r * 0.5), int(c - r * 0.6), int(r * 0.4), int(r * 0.4))

        if self.mode == "scroll":
            # Freccette su/giù per indicare la modalità scorrimento
            painter.setPen(QPen(QColor(255, 255, 255), 3))
            cx = int(c)
            painter.drawLine(cx, int(c - 12), cx, int(c + 12))
            painter.drawLine(cx - 6, int(c - 6), cx, int(c - 12))
            painter.drawLine(cx + 6, int(c - 6), cx, int(c - 12))
            painter.drawLine(cx - 6, int(c + 6), cx, int(c + 12))
            painter.drawLine(cx + 6, int(c + 6), cx, int(c + 12))
        painter.end()


class HandMouseController(QObject):
    """Trasforma posizione e gesti della mano in azioni mouse nella finestra.

    Mano chiusa = click / afferra un pensierino, mano aperta = rilascia.
    Non usa il puntatore di sistema (su Wayland QCursor.setPos non funziona):
    muove un cursore interno e invia eventi mouse sintetici ai widget.
    I pensierini non vengono trascinati via QDrag (bloccherebbe con eventi
    sintetici): al rilascio viene creata una copia nell'area di destinazione,
    la stessa semantica del dropEvent di WorkAreaWidget.
    """

    # Frame video consecutivi con lo stesso gesto prima di accettarlo
    # (~250 ms a 20 fps: filtra i gesti di passaggio ed evita click accidentali)
    GESTURE_CONFIRM_FRAMES = 5
    # Il segno "2" richiede più conferme: è uno stato di passaggio
    # quando la mano si apre o si chiude
    SCROLL_CONFIRM_FRAMES = 4
    # Peso della nuova posizione nello smussamento (anti-tremolio)
    SMOOTHING = 0.45
    # Pixel di scorrimento per pixel di movimento della mano
    SCROLL_GAIN = 2.0

    def __init__(self, main_window):
        super().__init__(main_window)
        self.win = main_window
        self.cursor = HandCursorWidget(main_window.centralWidget())
        self.frame_size = None  # (larghezza, altezza) del frame webcam
        self.pos = None  # posizione smussata in coordinate del centralWidget
        self.pressed = False
        self._last_gesture = None
        self._gesture_streak = 0
        self._press_target = None  # widget destinatario del click sintetico
        self._press_local = None
        self._grab_text = None  # testo del pensierino afferrato
        self._ghost = None  # etichetta fantasma durante il trascinamento
        self._scroll_target = None  # QAbstractScrollArea della sessione scorrimento
        self._scroll_prev = None  # ultima posizione mano durante lo scorrimento

    def set_frame_size(self, w, h):
        if w > 0 and h > 0:
            self.frame_size = (w, h)

    def stop(self):
        """Disattiva il controller e nasconde gli elementi visivi."""
        if self.pressed:
            self._release()
        self._end_scroll()
        self.cursor.hide()
        self.pos = None
        self._last_gesture = None
        self._gesture_streak = 0

    def on_hand_position(self, x, y):
        """Riceve la posizione della mano in coordinate frame webcam."""
        central = self.win.centralWidget()
        if central is None or not self.frame_size:
            return
        fw, fh = self.frame_size
        nx = max(0.0, min(1.0, x / fw))
        ny = max(0.0, min(1.0, y / fh))
        px = nx * central.width()
        py = ny * central.height()
        if self.pos is None:
            self.pos = [px, py]
        else:
            s = self.SMOOTHING
            self.pos[0] = self.pos[0] * (1 - s) + px * s
            self.pos[1] = self.pos[1] * (1 - s) + py * s

        cx, cy = int(self.pos[0]), int(self.pos[1])
        self.cursor.move(cx - self.cursor.width() // 2, cy - self.cursor.height() // 2)
        self.cursor.show()
        self.cursor.raise_()

        # Modalità scorrimento: il movimento della mano trascina le barre
        # (come tenere l'ascensore verticale e orizzontale)
        if self._scroll_target is not None:
            try:
                if self._scroll_prev is not None:
                    dx = cx - self._scroll_prev[0]
                    dy = cy - self._scroll_prev[1]
                    vsb = self._scroll_target.verticalScrollBar()
                    hsb = self._scroll_target.horizontalScrollBar()
                    if vsb is not None and vsb.maximum() > vsb.minimum():
                        vsb.setValue(vsb.value() + int(dy * self.SCROLL_GAIN))
                    if hsb is not None and hsb.maximum() > hsb.minimum():
                        hsb.setValue(hsb.value() + int(dx * self.SCROLL_GAIN))
                self._scroll_prev = (cx, cy)
            except RuntimeError:
                self._scroll_target = None  # area distrutta nel frattempo

        if self._ghost is not None:
            self._ghost.move(cx + 12, cy + 12)
            self._ghost.raise_()
            self.cursor.raise_()

    def on_gesture(self, gesture):
        """Riceve il gesto rilevato; con debounce per filtrare il rumore."""
        if gesture not in ("Open Hand", "Closed Hand", "Two Fingers", "OK Circle"):
            return
        if gesture == self._last_gesture:
            self._gesture_streak += 1
        else:
            self._last_gesture = gesture
            self._gesture_streak = 1

        needed = (
            self.SCROLL_CONFIRM_FRAMES
            if gesture == "Two Fingers"
            else self.GESTURE_CONFIRM_FRAMES
        )
        if self._gesture_streak != needed:
            return

        if gesture == "Two Fingers":
            if self._scroll_target is None:
                self._start_scroll()
        elif gesture == "Closed Hand":
            self._end_scroll()
            if not self.pressed:
                self._press()
        elif gesture == "Open Hand":
            self._end_scroll()
            if self.pressed:
                self._release()
        elif gesture == "OK Circle":
            # Gesto "O" (indice+pollice): richiesta di informazione se la mano
            # si trova sopra l'Area di Lavoro (B).
            self._end_scroll()
            if self._hand_over_work_area() and hasattr(
                self.win, "request_information_gesture"
            ):
                self.win.request_information_gesture()

    def _hand_over_work_area(self):
        """True se il cursore mano è sopra l'Area di Lavoro (colonna B)."""
        scroll = getattr(self.win, "work_area_scroll", None)
        if scroll is None or self.pos is None:
            return False
        central = self.win.centralWidget()
        if central is None:
            return False
        point = QPoint(int(self.pos[0]), int(self.pos[1]))
        global_pos = central.mapToGlobal(point)
        vp = scroll.viewport()
        return vp.rect().contains(vp.mapFromGlobal(global_pos))

    def _find_scroll_area(self, widget):
        """Risale la gerarchia cercando un'area di scorrimento."""
        from PyQt6.QtWidgets import QAbstractScrollArea

        central = self.win.centralWidget()
        w = widget
        while w is not None and w is not central:
            if isinstance(w, QAbstractScrollArea):
                return w
            w = w.parentWidget()
        return None

    def _start_scroll(self):
        """Entra in modalità scorrimento sull'area sotto il cursore."""
        if self.pos is None:
            return
        if self.pressed:
            self._release()

        central = self.win.centralWidget()
        point = QPoint(int(self.pos[0]), int(self.pos[1]))
        target = self._find_scroll_area(central.childAt(point))

        if target is None:
            # Fallback: area principale il cui viewport contiene il punto
            global_pos = central.mapToGlobal(point)
            for name in ("pensierini_scroll", "work_area_scroll", "details_scroll"):
                scroll = getattr(self.win, name, None)
                if scroll is not None:
                    vp = scroll.viewport()
                    if vp.rect().contains(vp.mapFromGlobal(global_pos)):
                        target = scroll
                        break
        if target is None:
            return

        self._scroll_target = target
        self._scroll_prev = (int(self.pos[0]), int(self.pos[1]))
        self.cursor.set_mode("scroll")

    def _end_scroll(self):
        """Esce dalla modalità scorrimento."""
        self._scroll_target = None
        self._scroll_prev = None
        if not self.pressed:
            self.cursor.set_mode("open")

    def _find_draggable(self, widget):
        """Risale la gerarchia cercando un DraggableTextWidget."""
        try:
            from UI.draggable_text_widget import DraggableTextWidget
        except ImportError:
            return None
        central = self.win.centralWidget()
        w = widget
        while w is not None and w is not central:
            if isinstance(w, DraggableTextWidget):
                return w
            w = w.parentWidget()
        return None

    def _press(self):
        if self.pos is None:
            return
        self.pressed = True
        self.cursor.set_closed(True)
        central = self.win.centralWidget()
        point = QPoint(int(self.pos[0]), int(self.pos[1]))
        child = central.childAt(point)
        if child is None or child in (self.cursor, self._ghost):
            return

        draggable = self._find_draggable(child)
        if draggable is not None and getattr(draggable, "text_label", None):
            # Afferra il pensierino: mostra un fantasma che segue la mano
            self._grab_text = draggable.text_label.text()
            self._ghost = QLabel(self._short_text(self._grab_text), central)
            self._ghost.setStyleSheet(
                "background: rgba(74, 144, 226, 0.85); color: white;"
                "border-radius: 6px; padding: 6px 10px; font-weight: bold;"
            )
            self._ghost.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
            self._ghost.adjustSize()
            self._ghost.move(point.x() + 12, point.y() + 12)
            self._ghost.show()
            self.cursor.raise_()
        else:
            # Click sintetico: premi ora, rilascia all'apertura della mano
            self._press_target = child
            self._press_local = child.mapFrom(central, point)
            self._send_mouse(
                child, QEvent.Type.MouseButtonPress, self._press_local, True
            )

    def _release(self):
        self.pressed = False
        self.cursor.set_closed(False)

        if self._grab_text is not None:
            self._drop_grabbed()
        elif self._press_target is not None:
            target, local = self._press_target, self._press_local
            self._press_target = None
            self._press_local = None
            try:
                self._send_mouse(target, QEvent.Type.MouseButtonRelease, local, False)
            except RuntimeError:
                pass  # il widget potrebbe essere stato distrutto nel frattempo

    def _drop_grabbed(self):
        """Rilascia il pensierino afferrato copiandolo nell'area sotto la mano."""
        text = self._grab_text
        self._grab_text = None
        if self._ghost is not None:
            self._ghost.deleteLater()
            self._ghost = None
        if not text or self.pos is None:
            return

        central = self.win.centralWidget()
        global_pos = central.mapToGlobal(QPoint(int(self.pos[0]), int(self.pos[1])))

        try:
            from UI.draggable_text_widget import DraggableTextWidget
        except ImportError:
            return

        # Nell'area di lavoro (B)? Stessa semantica del dropEvent: crea una copia
        work_scroll = getattr(self.win, "work_area_scroll", None)
        if work_scroll is not None:
            vp = work_scroll.viewport()
            if vp.rect().contains(vp.mapFromGlobal(global_pos)):
                widget = DraggableTextWidget(text, self.win.settings)
                self.win.work_area_layout.addWidget(widget)
                logging.info("Pensierino copiato nell'area di lavoro con la mano")
                return

        # Nell'area pensierini (A)? Aggiungi lì la copia
        pens_scroll = getattr(self.win, "pensierini_scroll", None)
        if pens_scroll is not None:
            vp = pens_scroll.viewport()
            if vp.rect().contains(vp.mapFromGlobal(global_pos)):
                widget = DraggableTextWidget(text, self.win.settings)
                self.win.pensierini_layout.addWidget(widget)
                logging.info("Pensierino copiato nell'area pensierini con la mano")

    def _send_mouse(self, widget, etype, local_pos, pressed):
        global_pos = widget.mapToGlobal(local_pos)
        event = QMouseEvent(
            etype,
            QPointF(local_pos),
            QPointF(global_pos),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton if pressed else Qt.MouseButton.NoButton,
            Qt.KeyboardModifier.NoModifier,
        )
        QApplication.sendEvent(widget, event)

    @staticmethod
    def _short_text(text, max_len=40):
        return text if len(text) <= max_len else text[: max_len - 1] + "…"


class FooterPensierinoEdit(QTextEdit):
    """Campo pensierino rapido multiriga che si espande verso l'alto.

    Invio invia, Shift+Invio va a capo. L'altezza cresce con il contenuto
    (da 1 riga fino a ``max_lines``); essendo nel footer, l'espansione si
    sviluppa visivamente verso l'alto.
    """

    send_requested = pyqtSignal()

    def __init__(self, *args, min_lines=1, max_lines=12, expand_to_fill=False, **kwargs):
        super().__init__(*args, **kwargs)
        self._min_lines = min_lines
        self._max_lines = max_lines
        self._expand_to_fill = expand_to_fill
        if expand_to_fill:
            # Riempie tutto lo spazio disponibile del contenitore
            self.setSizePolicy(
                QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
            )
            self.setMinimumHeight(
                int(min_lines * self._line_px() + self._chrome_px())
            )
        else:
            self.setSizePolicy(
                self.sizePolicy().horizontalPolicy(),
                QSizePolicy.Policy.Preferred,
            )
            self.document().documentLayout().documentSizeChanged.connect(
                lambda _=None: self._adjust_height()
            )
            self.textChanged.connect(self._adjust_height)
            self._adjust_height()

    def _line_px(self):
        return max(1, self.fontMetrics().lineSpacing())

    def _chrome_px(self):
        # Margini del documento + bordi/padding del frame
        doc_margin = int(self.document().documentMargin()) * 2
        frame = self.frameWidth() * 2 + 8
        return doc_margin + frame

    def _adjust_height(self):
        line = self._line_px()
        doc_h = self.document().size().height()
        content_lines = max(self._min_lines, int(round(doc_h / line)) if line else 1)
        content_lines = min(self._max_lines, content_lines)
        new_h = int(content_lines * line + self._chrome_px())
        if self.height() != new_h:
            self.setMinimumHeight(int(self._min_lines * line + self._chrome_px()))
            self.setMaximumHeight(int(self._max_lines * line + self._chrome_px()))
            self.setFixedHeight(new_h)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter) and not (
            event.modifiers() & Qt.KeyboardModifier.ShiftModifier
        ):
            self.send_requested.emit()
        else:
            super().keyPressEvent(event)


class AnalogClock(QWidget):
    """Orologio analogico che si aggiorna ogni secondo."""

    clicked = pyqtSignal()

    def __init__(self, parent=None, size=140):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self.setToolTip("Clicca per sentire l'ora")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self.update)
        self._timer.start(1000)

    def mousePressEvent(self, event):
        self.clicked.emit()
        event.accept()

    def paintEvent(self, event):
        from datetime import datetime

        now = datetime.now()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        side = min(self.width(), self.height())
        painter.translate(self.width() / 2, self.height() / 2)
        painter.scale(side / 200.0, side / 200.0)  # spazio logico -100..100

        # Quadrante
        painter.setPen(QPen(QColor("#495057"), 3))
        painter.setBrush(QColor("#ffffff"))
        painter.drawEllipse(QPointF(0, 0), 95, 95)

        # Tacche delle ore
        painter.setPen(QPen(QColor("#495057"), 3))
        for _ in range(12):
            painter.drawLine(0, -78, 0, -90)
            painter.rotate(30)
        # Tacche dei minuti
        painter.setPen(QPen(QColor("#adb5bd"), 1))
        for i in range(60):
            if i % 5:
                painter.drawLine(0, -86, 0, -90)
            painter.rotate(6)

        def _hand(angle, length, tail, width, color):
            pen = QPen(QColor(color), width)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(pen)
            painter.save()
            painter.rotate(angle)
            painter.drawLine(QPointF(0, tail), QPointF(0, -length))
            painter.restore()

        # Lancette (12 in alto = -y)
        _hand(30 * (now.hour % 12) + 0.5 * now.minute, 48, 12, 6, "#343a40")
        _hand(6 * now.minute + 0.1 * now.second, 70, 14, 4, "#343a40")
        _hand(6 * now.second, 82, 18, 1.5, "#e53935")

        # Perno centrale
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#e53935"))
        painter.drawEllipse(QPointF(0, 0), 4, 4)


class HandwritingCanvas(QWidget):
    """Superficie di disegno: si disegna solo tenendo premuto il tasto 'D'.

    Supporta pennelli di vario spessore, colori e forme (matita a mano libera,
    linea, rettangolo, ellisse, gomma). Con la tavoletta grafica lo spessore
    della matita segue la pressione.
    """

    def __init__(self, parent=None, width=720, height=300):
        super().__init__(parent)
        self.setMinimumSize(width, height)
        self.setCursor(Qt.CursorShape.CrossCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        # Tracciamento del mouse: con 'D' premuto si disegna anche solo muovendo
        # il cursore (utile col touchpad, senza dover tenere premuto un pulsante).
        self.setMouseTracking(True)
        self.image = QImage(width, height, QImage.Format.Format_RGB32)
        self.image.fill(Qt.GlobalColor.white)

        self.pen_color = QColor("#1a1a1a")
        self.pen_width = 3
        self.tool = "pencil"  # pencil, line, rect, ellipse, eraser
        # Trasparenza SOLO visiva: l'immagine di lavoro resta RGB su fondo
        # bianco (niente canale alfa in più), quindi salvataggi, OCR e invio
        # non cambiano. A schermo il foglio lascia intravedere lo sfondo.
        self.visual_opacity = 1.0

        self._last = None
        self._start = None
        self._preview_end = None
        self._draw_enabled = False  # True mentre si tiene premuto 'D'

        # Penna "in aria" (webcam): ultimo punto del tratto, posizione del
        # cursore mostrato sul canvas e stato del rubinetto dell'inchiostro
        self._air_last = None
        self._air_pos = None
        self._air_inking = False

    # --- Configurazione strumenti ---
    def set_color(self, color):
        self.pen_color = QColor(color)

    def set_width(self, width):
        self.pen_width = int(width)

    def set_tool(self, tool):
        self.tool = tool

    def set_visual_opacity(self, value):
        """Imposta la trasparenza del foglio a schermo (0.05..1.0)."""
        self.visual_opacity = max(0.05, min(1.0, float(value)))
        self.update()

    # --- Penna "in aria" (punta seguita dalla webcam) ---
    def air_pen_point(self, nx, ny, visible, inking=True):
        """Riceve la punta della penna dalla webcam e disegna sul canvas.

        Coordinate normalizzate (0..1) mappate sull'area del canvas.
        ``visible``: la punta è inquadrata (il cursore viene mostrato).
        ``inking``: il "rubinetto" dell'inchiostro è aperto e la punta
        traccia; se chiuso, il cursore si muove senza scrivere.
        Non richiede il tasto 'D': la penna fisica È il comando.
        """
        if not visible:
            self._air_last = None
            if self._air_pos is not None:
                self._air_pos = None
                self.update()
            return
        point = QPoint(
            int(nx * max(1, self.width() - 1)),
            int(ny * max(1, self.height() - 1)),
        )
        self._air_pos = point
        self._air_inking = bool(inking)
        if not inking:
            # Rubinetto chiuso: la punta si vede ma non lascia inchiostro
            self._air_last = None
        elif self._air_last is None:
            self._air_last = point
        else:
            painter = QPainter(self.image)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setPen(self._make_pen())
            painter.drawLine(self._air_last, point)
            painter.end()
            self._air_last = point
        self.update()

    def _make_pen(self, width=None):
        colore = QColor("#ffffff") if self.tool == "eraser" else self.pen_color
        spessore = width if width is not None else self.pen_width
        if self.tool == "eraser":
            spessore = max(spessore, self.pen_width) * 4
        return QPen(
            colore, spessore,
            Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin,
        )

    # --- Abilitazione con il tasto 'D' ---
    def enterEvent(self, event):
        self.setFocus()
        super().enterEvent(event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_D:
            # Ignora l'auto-repeat: resettare _last a ogni ripetizione
            # spezzerebbe il tratto (effetto tratteggio).
            if not event.isAutoRepeat():
                self._last = None  # nuovo tratto pulito al primo press
            self._draw_enabled = True
        else:
            super().keyPressEvent(event)

    def leaveEvent(self, event):
        # Interrompe il tratto quando il cursore esce dall'area
        self._last = None
        super().leaveEvent(event)

    def keyReleaseEvent(self, event):
        if event.key() == Qt.Key.Key_D and not event.isAutoRepeat():
            self._draw_enabled = False
            self._last = None
            self._start = None
            self._preview_end = None
            self.update()
        else:
            super().keyReleaseEvent(event)

    # --- Disegno ---
    def paintEvent(self, event):
        painter = QPainter(self)
        if self.visual_opacity < 1.0:
            painter.setOpacity(self.visual_opacity)
        painter.drawImage(0, 0, self.image)
        painter.setOpacity(1.0)
        # Foglio trasparente: bordo tratteggiato per vedere dove finisce
        if self.visual_opacity < 1.0:
            bordo = QPen(QColor(120, 120, 120, 160), 1, Qt.PenStyle.DashLine)
            painter.setPen(bordo)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(self.rect().adjusted(0, 0, -1, -1))
        # Anteprima della forma mentre la si traccia
        if self.tool in ("line", "rect", "ellipse") and self._start and self._preview_end:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setPen(self._make_pen())
            painter.setBrush(Qt.BrushStyle.NoBrush)
            self._paint_shape(painter, self._start, self._preview_end)
        # Cursore della penna "in aria": pieno = inchiostro aperto (scrive),
        # vuoto = rubinetto chiuso (la punta si muove senza tracciare).
        # Visibile anche con il foglio trasparente: è disegnato sopra.
        if self._air_pos is not None:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setPen(QPen(QColor("#e91e63"), 2))
            if self._air_inking:
                painter.setBrush(QBrush(self.pen_color))
            else:
                painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(self._air_pos, 8, 8)

    def _paint_shape(self, painter, a, b):
        if self.tool == "line":
            painter.drawLine(a, b)
        elif self.tool == "rect":
            painter.drawRect(QRect(a, b).normalized())
        elif self.tool == "ellipse":
            painter.drawEllipse(QRect(a, b).normalized())

    def resizeEvent(self, event):
        if self.width() > self.image.width() or self.height() > self.image.height():
            nuova = QImage(
                max(self.width(), self.image.width()),
                max(self.height(), self.image.height()),
                QImage.Format.Format_RGB32,
            )
            nuova.fill(Qt.GlobalColor.white)
            painter = QPainter(nuova)
            painter.drawImage(0, 0, self.image)
            painter.end()
            self.image = nuova
        super().resizeEvent(event)

    def _draw_to(self, point, width=None):
        if self._last is None:
            self._last = point
            return
        painter = QPainter(self.image)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(self._make_pen(width))
        painter.drawLine(self._last, point)
        painter.end()
        self._last = point
        self.update()

    def mousePressEvent(self, event):
        if not self._draw_enabled:
            return
        point = event.position().toPoint()
        if self.tool in ("pencil", "eraser"):
            self._last = point
        else:
            self._start = point
            self._preview_end = point

    def mouseMoveEvent(self, event):
        if not self._draw_enabled:
            return
        point = event.position().toPoint()
        if self.tool in ("pencil", "eraser"):
            # Con 'D' premuto disegna sia trascinando col pulsante sinistro
            # (mouse/touchpad) sia semplicemente muovendo il cursore.
            self._draw_to(point)
        elif self._start is not None:
            self._preview_end = point
            self.update()

    def mouseReleaseEvent(self, event):
        if not self._draw_enabled:
            return
        point = event.position().toPoint()
        if self.tool in ("pencil", "eraser"):
            self._last = None
        elif self._start is not None:
            painter = QPainter(self.image)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setPen(self._make_pen())
            painter.setBrush(Qt.BrushStyle.NoBrush)
            self._paint_shape(painter, self._start, point)
            painter.end()
            self._start = None
            self._preview_end = None
            self.update()

    def tabletEvent(self, event):
        # Con la tavoletta la matita segue la pressione; richiede sempre 'D'
        if not self._draw_enabled or self.tool not in ("pencil", "eraser"):
            event.accept()
            return
        point = event.position().toPoint()
        t = event.type()
        if t == QEvent.Type.TabletPress:
            self._last = point
        elif t == QEvent.Type.TabletMove:
            self._draw_to(point, width=max(1.0, event.pressure() * 6.0))
        elif t == QEvent.Type.TabletRelease:
            self._last = None
        event.accept()

    def clear(self):
        self.image.fill(Qt.GlobalColor.white)
        self.update()


class DrawingWidget(QWidget):
    """Canvas di disegno con barra strumenti: colori, pennelli e forme."""

    def __init__(self, parent=None, width=720, height=280, compact=False):
        super().__init__(parent)
        from PyQt6.QtWidgets import QComboBox

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self.canvas = HandwritingCanvas(width=width, height=height)

        toolbar = QHBoxLayout()
        toolbar.setSpacing(3)

        # Colori rapidi
        for nome, hexc in (
            ("Nero", "#1a1a1a"), ("Rosso", "#e53935"),
            ("Blu", "#1565c0"), ("Verde", "#2e7d32"), ("Arancio", "#e65100"),
        ):
            b = QPushButton()
            b.setFixedSize(22, 22)
            b.setStyleSheet(
                f"background:{hexc}; border:1px solid #999; border-radius:4px;"
            )
            b.setToolTip(f"Colore: {nome}")
            b.clicked.connect(lambda _=False, c=hexc: self.canvas.set_color(c))
            toolbar.addWidget(b)
        # Stile che sovrascrive il padding globale (8px 16px) che farebbe
        # sparire l'icona nei pulsanti stretti.
        tool_btn_style = (
            "QPushButton { padding:2px 0px; min-height:24px; font-size:14px;"
            " background:#ffffff; color:#2c3e50; border:1px solid #ccc;"
            " border-radius:4px; }"
            "QPushButton:hover { background:#eef4ff; border-color:#4a90e2; }"
        )
        color_btn = QPushButton("🎨")
        color_btn.setFixedWidth(34)
        color_btn.setStyleSheet(tool_btn_style)
        color_btn.setToolTip("Scegli un altro colore")
        color_btn.clicked.connect(self._pick_color)
        toolbar.addWidget(color_btn)

        toolbar.addSpacing(8)

        # Strumenti / forme
        for label, tool, tip in (
            ("✏️", "pencil", "Matita (mano libera)"),
            ("➖", "line", "Linea"),
            ("▭", "rect", "Rettangolo"),
            ("⬭", "ellipse", "Ellisse"),
            ("🧽", "eraser", "Gomma"),
        ):
            b = QPushButton(label)
            b.setFixedWidth(36)
            b.setStyleSheet(tool_btn_style)
            b.setToolTip(tip)
            b.clicked.connect(lambda _=False, t=tool: self.canvas.set_tool(t))
            toolbar.addWidget(b)

        toolbar.addSpacing(8)

        # Spessore pennello
        self.width_combo = QComboBox()
        for wpx in (2, 3, 5, 8, 12, 18):
            self.width_combo.addItem(f"{wpx}px", wpx)
        self.width_combo.setCurrentIndex(1)
        self.width_combo.setToolTip("Spessore del pennello")
        self.width_combo.currentIndexChanged.connect(
            lambda _i: self.canvas.set_width(self.width_combo.currentData())
        )
        toolbar.addWidget(self.width_combo)

        toolbar.addSpacing(8)

        # Trasparenza del foglio: effetto solo visivo, il disegno viene
        # sempre salvato/inviato su sfondo bianco.
        ghost_label = QLabel("👻")
        ghost_label.setToolTip("Trasparenza del foglio")
        toolbar.addWidget(ghost_label)
        self.opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.opacity_slider.setRange(5, 100)
        self.opacity_slider.setValue(100)
        self.opacity_slider.setFixedWidth(70)
        self.opacity_slider.setToolTip(
            "Trasparenza del foglio (solo a schermo: l'immagine resta "
            "su sfondo bianco quando la salvi o la invii)"
        )
        self.opacity_slider.valueChanged.connect(
            lambda v: self.canvas.set_visual_opacity(v / 100.0)
        )
        toolbar.addWidget(self.opacity_slider)

        toolbar.addSpacing(8)

        # Penna "in aria": la webcam segue la punta colorata di una penna
        # fisica. Punta in basso e visibile = disegna; punta nascosta
        # (penna girata o coperta) = sollevata dal foglio.
        self._pen_tracker = None
        self.air_pen_button = QPushButton("🖊️ Aria")
        self.air_pen_button.setCheckable(True)
        self.air_pen_button.setFixedWidth(60)
        self.air_pen_button.setStyleSheet(tool_btn_style)
        self.air_pen_button.setToolTip(
            "Disegna in aria con una penna vera: la webcam ne segue la punta "
            "colorata (tienila rivolta verso il basso). Nascondi la punta per "
            "sollevare la penna dal foglio. Non usare insieme allo sfondo "
            "webcam: la telecamera serve a una funzione alla volta."
        )
        self.air_pen_button.toggled.connect(self._toggle_air_pen)
        toolbar.addWidget(self.air_pen_button)

        self.air_color_combo = QComboBox()
        for nome, chiave in (
            ("Punta blu", "blu"), ("Punta verde", "verde"),
            ("Punta rossa", "rosso"), ("Punta gialla", "giallo"),
        ):
            self.air_color_combo.addItem(nome, chiave)
        self.air_color_combo.setToolTip(
            "Colore della punta/cappuccio della penna che la webcam deve seguire"
        )
        self.air_color_combo.currentIndexChanged.connect(
            lambda _i: self._set_air_pen_color()
        )
        toolbar.addWidget(self.air_color_combo)

        toolbar.addStretch()
        self.hint_label = QLabel("Tieni premuto  D  per disegnare")
        self.hint_label.setStyleSheet("color:#888; font-size:10px;")
        toolbar.addWidget(self.hint_label)

        layout.addLayout(toolbar)
        layout.addWidget(self.canvas, 1)

    def _toggle_air_pen(self, checked):
        """Avvia/ferma il tracciamento della penna via webcam."""
        if not checked:
            if self._pen_tracker is not None:
                self._pen_tracker.stop()
                self._pen_tracker = None
            self.canvas.air_pen_point(0.0, 0.0, False)
            self.hint_label.setText("Tieni premuto  D  per disegnare")
            return
        try:
            from Artificial_Intelligence.Video.pen_tracker import PenTrackerThread
        except ImportError:
            try:
                from assistente_dsa.Artificial_Intelligence.Video.pen_tracker import (
                    PenTrackerThread,
                )
            except ImportError as e:
                self.hint_label.setText(f"Penna in aria non disponibile: {e}")
                self.air_pen_button.setChecked(False)
                return
        self._pen_tracker = PenTrackerThread(
            color=self.air_color_combo.currentData() or "blu"
        )
        self._pen_tracker.pen_position.connect(self.canvas.air_pen_point)
        self._pen_tracker.status.connect(self.hint_label.setText)
        self._pen_tracker.start()

    def _set_air_pen_color(self):
        if self._pen_tracker is not None:
            self._pen_tracker.color = self.air_color_combo.currentData() or "blu"

    def _pick_color(self):
        from PyQt6.QtWidgets import QColorDialog

        c = QColorDialog.getColor(self.canvas.pen_color, self, "Scegli colore")
        if c.isValid():
            self.canvas.set_color(c.name())

    def clear(self):
        self.canvas.clear()


class RichTextInputWidget(QWidget):
    """Mini WordPad: campo di testo con barra per formattare il testo selezionato
    (grassetto, corsivo, sottolineato, dimensione, colore)."""

    def __init__(self, editor, parent=None):
        super().__init__(parent)
        self.editor = editor
        self.editor.setAcceptRichText(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        toolbar = QHBoxLayout()
        toolbar.setSpacing(3)

        def _btn(label, tip, slot, checkable=False, width=34, bold=False, italic=False):
            b = QPushButton(label)
            b.setToolTip(tip)
            b.setFixedWidth(width)
            b.setCheckable(checkable)
            extra = ""
            if bold:
                extra += "font-weight:bold;"
            if italic:
                extra += "font-style:italic;"
            # Padding piccolo per non far sparire il testo (lo stile globale usa
            # padding 8px 16px, troppo grande per questi pulsanti stretti).
            b.setStyleSheet(
                "QPushButton {"
                " background:#ffffff; color:#2c3e50;"
                " border:1px solid #ccc; border-radius:4px;"
                " padding:2px 0px; min-height:24px; font-size:13px;" + extra + " }"
                "QPushButton:hover { background:#eef4ff; border-color:#4a90e2; }"
                "QPushButton:checked { background:#d6e6ff; border-color:#2196f3;"
                " color:#1565c0; }"
            )
            b.clicked.connect(slot)
            toolbar.addWidget(b)
            return b

        self.bold_btn = _btn("B", "Grassetto", self._toggle_bold, checkable=True, bold=True)
        self.italic_btn = _btn("I", "Corsivo", self._toggle_italic, checkable=True, italic=True)
        self.underline_btn = _btn("U", "Sottolineato", self._toggle_underline, checkable=True)
        toolbar.addSpacing(8)
        _btn("A−", "Rimpicciolisci", lambda: self._change_size(-2), width=40)
        _btn("A+", "Ingrandisci", lambda: self._change_size(+2), width=40)
        toolbar.addSpacing(8)
        color_btn = QPushButton("🎨 Colore")
        color_btn.setToolTip("Colore del testo selezionato")
        color_btn.setStyleSheet(
            "QPushButton { padding:2px 8px; min-height:24px; color:#2c3e50;"
            " background:#ffffff; border:1px solid #ccc; border-radius:4px; }"
            "QPushButton:hover { background:#eef4ff; border-color:#4a90e2; }"
        )
        color_btn.clicked.connect(self._pick_color)
        toolbar.addWidget(color_btn)
        toolbar.addSpacing(8)

        # Scrittura con l'alfabeto manuale (dattilologia LIS): la webcam
        # riconosce la forma della mano e digita la lettera nel testo.
        self._sign_thread = None
        self.sign_btn = QPushButton("🤟 Segni")
        self.sign_btn.setCheckable(True)
        self.sign_btn.setToolTip(
            "Scrivi con l'alfabeto manuale (dattilologia): fai la lettera con "
            "la mano davanti alla webcam e tienila ferma ~1 secondo per "
            "scriverla. Mano aperta = spazio; per una lettera doppia nascondi "
            "un attimo la mano e rifai il segno. Supporta le lettere statiche "
            "(tutte tranne J e Z). Non usare insieme ad altre funzioni che "
            "occupano la webcam."
        )
        self.sign_btn.setStyleSheet(
            "QPushButton { padding:2px 8px; min-height:24px; color:#2c3e50;"
            " background:#ffffff; border:1px solid #ccc; border-radius:4px; }"
            "QPushButton:hover { background:#eef4ff; border-color:#4a90e2; }"
            "QPushButton:checked { background:#d6e6ff; border-color:#2196f3;"
            " color:#1565c0; }"
        )
        self.sign_btn.toggled.connect(self._toggle_sign_input)
        toolbar.addWidget(self.sign_btn)

        self.sign_hint = QLabel("")
        self.sign_hint.setStyleSheet("color:#888; font-size:10px;")
        toolbar.addWidget(self.sign_hint)
        toolbar.addStretch()

        layout.addLayout(toolbar)
        layout.addWidget(self.editor, 1)

    def _apply(self, fmt):
        cursor = self.editor.textCursor()
        cursor.mergeCharFormat(fmt)  # applica alla selezione
        self.editor.mergeCurrentCharFormat(fmt)  # e al testo che verrà digitato
        self.editor.setFocus()

    def _toggle_bold(self):
        fmt = QTextCharFormat()
        fmt.setFontWeight(
            QFont.Weight.Bold if self.bold_btn.isChecked() else QFont.Weight.Normal
        )
        self._apply(fmt)

    def _toggle_italic(self):
        fmt = QTextCharFormat()
        fmt.setFontItalic(self.italic_btn.isChecked())
        self._apply(fmt)

    def _toggle_underline(self):
        fmt = QTextCharFormat()
        fmt.setFontUnderline(self.underline_btn.isChecked())
        self._apply(fmt)

    def _change_size(self, delta):
        current = self.editor.currentCharFormat().fontPointSize()
        if not current or current <= 0:
            current = self.editor.font().pointSizeF()
        if not current or current <= 0:
            current = 12.0
        fmt = QTextCharFormat()
        fmt.setFontPointSize(max(6.0, current + delta))
        self._apply(fmt)

    def _pick_color(self):
        from PyQt6.QtWidgets import QColorDialog

        c = QColorDialog.getColor(QColor("#000000"), self, "Colore del testo")
        if c.isValid():
            fmt = QTextCharFormat()
            fmt.setForeground(QBrush(c))
            self._apply(fmt)

    def _toggle_sign_input(self, checked):
        """Avvia/ferma la scrittura con l'alfabeto manuale via webcam."""
        if not checked:
            if self._sign_thread is not None:
                self._sign_thread.stop()
                self._sign_thread = None
            self.sign_hint.setText("")
            return
        try:
            from Artificial_Intelligence.Video.sign_tracker import SignLanguageThread
        except ImportError:
            try:
                from assistente_dsa.Artificial_Intelligence.Video.sign_tracker import (
                    SignLanguageThread,
                )
            except ImportError as e:
                self.sign_hint.setText(f"Segni non disponibili: {e}")
                self.sign_btn.setChecked(False)
                return
        self._sign_thread = SignLanguageThread()
        self._sign_thread.letter_ready.connect(self._on_sign_letter)
        self._sign_thread.candidate.connect(self._on_sign_candidate)
        self._sign_thread.status.connect(self.sign_hint.setText)
        self._sign_thread.start()

    def _on_sign_letter(self, ch):
        """Scrive la lettera confermata dal segno nel punto del cursore."""
        cursor = self.editor.textCursor()
        cursor.insertText(ch)
        self.editor.setTextCursor(cursor)

    def _on_sign_candidate(self, letter, progress):
        """Anteprima: lettera che la webcam sta vedendo e conferma in corso."""
        if not letter:
            self.sign_hint.setText("🤟 mostra una lettera alla webcam")
            return
        dots = round(progress * 5)
        self.sign_hint.setText(f"🤟 {letter}  {'●' * dots}{'○' * (5 - dots)}")


class HandwritingTabletDialog(QDialog):
    """Tavoletta per esercitarsi a scrivere il proprio nome/cognome a mano."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("✍️ Tavoletta - scrittura a mano libera")
        self.resize(780, 480)
        self.saved_path = None

        layout = QVBoxLayout(self)
        info = QLabel(
            "Scrivi o disegna a mano libera (mouse o tavoletta grafica). "
            "Tieni premuto il tasto D per disegnare; scegli colore, pennello e forma "
            "dalla barra strumenti."
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        self.drawing = DrawingWidget(width=720, height=320)
        self.canvas = self.drawing.canvas
        self.canvas.setStyleSheet("border: 1px solid #adb5bd; border-radius: 6px;")
        layout.addWidget(self.drawing, 1)

        buttons = QHBoxLayout()
        clear_btn = QPushButton("🧽 Pulisci")
        clear_btn.clicked.connect(self.canvas.clear)
        save_btn = QPushButton("💾 Salva immagine")
        save_btn.clicked.connect(self._save_image)
        close_btn = QPushButton("Chiudi")
        close_btn.clicked.connect(self.accept)
        buttons.addWidget(clear_btn)
        buttons.addWidget(save_btn)
        buttons.addStretch()
        buttons.addWidget(close_btn)
        layout.addLayout(buttons)

    def _save_image(self):
        from PyQt6.QtWidgets import QFileDialog

        path, _ = QFileDialog.getSaveFileName(
            self, "Salva la tua scrittura", "scrittura.png", "Immagine PNG (*.png)"
        )
        if path:
            if not path.lower().endswith(".png"):
                path += ".png"
            self.canvas.image.save(path, "PNG")
            self.saved_path = path


class TreeGraphWidget(QWidget):
    """Disegna un riassunto come albero/grafo di nodi con i punti chiave.

    Riceve una struttura annidata: {"text": str, "children": [ ... ]}.
    """

    NODE_W = 170
    NODE_H = 46
    H_GAP = 26
    V_GAP = 56
    _COLORS = ["#1565c0", "#2e7d32", "#e65100", "#6a1b9a", "#00838f", "#ad1457"]

    def __init__(self, root, parent=None):
        super().__init__(parent)
        self.root = root
        self._leaf = 0
        self._max_depth = 0
        self._assign(self.root, 0)
        cols = max(1, self._leaf)
        self._w = int(cols * (self.NODE_W + self.H_GAP) + self.H_GAP)
        self._h = int((self._max_depth + 1) * (self.NODE_H + self.V_GAP) + self.V_GAP)
        self.setMinimumSize(self._w, self._h)
        self.setStyleSheet("background: #ffffff;")

    def _assign(self, node, depth):
        self._max_depth = max(self._max_depth, depth)
        node["_depth"] = depth
        children = node.get("children", [])
        if not children:
            node["_col"] = self._leaf
            self._leaf += 1
            return node["_col"]
        cols = [self._assign(c, depth + 1) for c in children]
        node["_col"] = sum(cols) / len(cols)
        return node["_col"]

    def _node_rect(self, node):
        x = int(self.H_GAP + node["_col"] * (self.NODE_W + self.H_GAP))
        y = int(self.V_GAP + node["_depth"] * (self.NODE_H + self.V_GAP))
        return QRect(x, y, self.NODE_W, self.NODE_H)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor("#ffffff"))
        self._paint_edges(painter, self.root)
        self._paint_nodes(painter, self.root, 0)

    def _paint_edges(self, painter, node):
        pr = self._node_rect(node)
        painter.setPen(QPen(QColor("#90a4ae"), 2))
        for c in node.get("children", []):
            cr = self._node_rect(c)
            painter.drawLine(pr.center().x(), pr.bottom(), cr.center().x(), cr.top())
            self._paint_edges(painter, c)

    def _paint_nodes(self, painter, node, depth):
        rect = self._node_rect(node)
        fill = QColor(self._COLORS[depth % len(self._COLORS)])
        painter.setBrush(fill)
        painter.setPen(QPen(fill.darker(120), 1))
        painter.drawRoundedRect(rect, 8, 8)
        painter.setPen(QColor("#ffffff"))
        f = painter.font()
        f.setPointSize(10 if depth == 0 else 9)
        f.setBold(depth == 0)
        painter.setFont(f)
        painter.drawText(
            rect.adjusted(6, 2, -6, -2),
            int(Qt.AlignmentFlag.AlignCenter) | int(Qt.TextFlag.TextWordWrap),
            node.get("text", ""),
        )
        for c in node.get("children", []):
            self._paint_nodes(painter, c, depth + 1)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = load_settings()
        self.text_widgets = []

        # Registro dei messaggi/errori dell'applicazione (mostrati da "Messaggi")
        self.app_messages = []

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

        # Timer per aggiornare l'orario nel footer ogni minuto
        from PyQt6.QtCore import QTimer

        self.footer_timer = QTimer()
        self.footer_timer.timeout.connect(self._update_time_labels)
        self.footer_timer.start(60000)  # Aggiorna ogni 60 secondi

        # Aggiorna l'orario immediatamente all'avvio
        self._update_time_labels()

        # Osservazione dei momenti di difficoltà (per genitori/clinici):
        # spenta se non esplicitamente abilitata e acconsentita nelle
        # Impostazioni. Vedi core/difficulty_observer.py.
        self._setup_difficulty_observer()

        logging.info("Applicazione avviata")

        # Log delle metriche iniziali dopo che l'UI è stata configurata
        QTimer.singleShot(1000, lambda: self.log_ui_metrics("INITIAL_SETUP"))

    def update_project_name_input_style(self):
        """Deprecato: il campo nome progetto è stato rimosso."""
        return

    def toggle_input_mode(self):
        """Alterna l'input tra tastiera (testo) e canvas (scrittura/disegno a mano).

        Se erano visibili gli Strumenti, tornando a Testo/Canvas li nasconde.
        """
        if not hasattr(self, "footer_input_stack"):
            return
        if hasattr(self, "toggle_tools_button"):
            self.toggle_tools_button.setChecked(False)
        if hasattr(self, "keyboard_button"):
            self.keyboard_button.setChecked(False)
        # Se non siamo su canvas -> vai a canvas; altrimenti torna al testo
        if self.footer_input_stack.currentIndex() == 1:
            self.footer_input_stack.setCurrentIndex(0)  # testo
            self.toggle_input_mode_button.setText("🖊️ Canvas")
            self.set_status_message("⌨️ Modalità tastiera")
        else:
            self.footer_input_stack.setCurrentIndex(1)  # canvas
            self.toggle_input_mode_button.setText("⌨️ Testo")
            self.set_status_message(
                "🖊️ Modalità scrittura/disegno a mano: invia per convertirla in testo"
            )

    def _send_canvas_pensierino(self):
        """Invia il contenuto del canvas: l'OCR locale lo converte in testo pulito."""
        import os
        import tempfile

        from UI.draggable_text_widget import DraggableTextWidget as _DTW

        canvas = self.footer_canvas
        tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        canvas.image.save(tmp.name, "PNG")

        self.set_status_message("🔎 Conversione della scrittura in testo (OCR)...")
        testo = ""
        try:
            from core.document_tools import ocr_image

            testo = ocr_image(tmp.name)
        except Exception as e:
            self.add_message(f"OCR non disponibile: {e}", "error")

        if testo:
            if _DTW and hasattr(self, "pensierini_layout"):
                self.pensierini_layout.addWidget(_DTW(testo, self.settings))
            self.set_status_message(f"✅ Scrittura convertita in testo: {testo[:40]}")
            self.add_message("Scrittura a mano convertita in testo (OCR)", "info")
        else:
            # Nessun testo (probabilmente un disegno): salva l'immagine e la referenzia
            try:
                scribbles = "Save/scritture_a_mano"
                os.makedirs(scribbles, exist_ok=True)
                from datetime import datetime

                nome = f"scrittura_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                dest = os.path.join(scribbles, nome)
                canvas.image.save(dest, "PNG")
                if _DTW and hasattr(self, "pensierini_layout"):
                    self.pensierini_layout.addWidget(
                        _DTW(f"🖊️ Disegno: {nome}", self.settings)
                    )
                self.set_status_message(f"🖊️ Disegno salvato: {nome}")
            except Exception as e:
                self.add_message(f"Errore salvando il disegno: {e}", "error")
        canvas.clear()

    def send_footer_pensierino(self):
        """Invia un pensierino dalla sezione footer alla colonna A (pensierini)."""
        try:
            # Modalità canvas: converte la scrittura a mano in testo (OCR)
            if (
                hasattr(self, "footer_input_stack")
                and self.footer_input_stack.currentIndex() == 1
            ):
                self._send_canvas_pensierino()
                return

            # Ottieni il testo dal campo footer
            text = self.footer_pensierini_input.toPlainText().strip()

            if not text:
                # Campo vuoto, mostra messaggio informativo
                from PyQt6.QtWidgets import QMessageBox

                QMessageBox.information(
                    self,
                    "Campo Vuoto",
                    "Scrivi qualcosa nel campo prima di inviare! 💭",
                )
                return

            # Calcolatrice: se il pensierino inizia con "=" lo calcoliamo
            # (es. "=2+3*4", "=sqrt(16)+2**3").
            try:
                from core.document_tools import calculate, looks_like_math
                from UI.draggable_text_widget import DraggableTextWidget as _DTW

                if looks_like_math(text):
                    risultato = calculate(text)
                    esito = f"🧮 {text.lstrip('=').strip()} = {risultato}"
                    if _DTW and hasattr(self, "pensierini_layout"):
                        self.pensierini_layout.addWidget(_DTW(esito, self.settings))
                    self.set_status_message(esito)
                    self.footer_pensierini_input.clear()
                    return
            except Exception as e:
                self.add_message(f"Calcolo non riuscito: {e}", "error")
                self.set_status_message(f"🧮 Errore nel calcolo: {e}")
                return

            # Controlla se il testo inizia con il trigger AI
            ai_trigger = get_setting("ai.ai_trigger", "++++")
            if ai_trigger and isinstance(ai_trigger, str) and text.startswith(ai_trigger):
                # Estrai il testo dopo il trigger
                ai_prompt = text[len(ai_trigger):].strip()

                if not ai_prompt:
                    from PyQt6.QtWidgets import QMessageBox
                    QMessageBox.warning(
                        self,
                        "Prompt AI Vuoto",
                        f"Il trigger '{ai_trigger}' è stato rilevato ma non c'è testo da inviare all'AI.\n\nScrivi qualcosa dopo il trigger!",
                    )
                    return

                # Se l'utente chiede un riassunto ad albero/grafo con i punti
                # chiave, istruisce l'AI a restituire un elenco gerarchico che
                # verrà disegnato come mappa nella Lavagna AI (colonna C).
                prompt_da_inviare = ai_prompt
                if self._is_graph_request(ai_prompt):
                    prompt_da_inviare = self._graph_prompt(ai_prompt)
                    self.set_status_message("🗺️ Creo una mappa ad albero dei punti chiave...")

                # Invia la richiesta all'AI
                print(f"🤖 Rilevato trigger AI '{ai_trigger}', invio prompt: {ai_prompt[:50]}...")

                # Mostra feedback visivo nella status bar se disponibile
                if hasattr(self, 'statusBar'):
                    status_bar = self.statusBar()
                    if status_bar:
                        status_bar.showMessage(f"🤖 Invio richiesta AI: {ai_prompt[:30]}...")

                # Usa il bridge Ollama se disponibile
                if hasattr(self, 'ollama_bridge') and self.ollama_bridge:
                    try:
                        # Invia la richiesta all'AI usando il metodo corretto
                        model = get_setting("ai.selected_ai_model", "gemma:2b")
                        self.ollama_bridge.sendPrompt(prompt_da_inviare, model)
                        from PyQt6.QtWidgets import QMessageBox
                        QMessageBox.information(
                            self,
                            "Richiesta AI Inviata",
                            f"✅ Prompt inviato all'AI ({model}):\n\n'{ai_prompt[:100]}{'...' if len(ai_prompt) > 100 else ''}'",
                        )
                    except Exception as e:
                        from PyQt6.QtWidgets import QMessageBox
                        QMessageBox.warning(
                            self,
                            "Errore AI",
                            f"❌ Errore nell'invio della richiesta all'AI:\n\n{str(e)}",
                        )
                else:
                    from PyQt6.QtWidgets import QMessageBox
                    QMessageBox.warning(
                        self,
                        "AI Non Disponibile",
                        "❌ Il servizio AI non è disponibile.\n\nVerifica che Ollama sia installato e configurato.",
                    )

                # Svuota il campo dopo l'invio
                self.footer_pensierini_input.clear()
                return

            # Crea il nuovo widget pensierino (conserva la formattazione del
            # mini WordPad se presente: colori, dimensioni, grassetto...)
            from UI.draggable_text_widget import DraggableTextWidget

            if DraggableTextWidget:
                contenuto = text
                try:
                    html = self.footer_pensierini_input.toHtml()
                    if 'style="' in html or "<span" in html:
                        # Estrae il frammento del corpo per un HTML più pulito
                        import re

                        m = re.search(r"<body[^>]*>(.*)</body>", html, re.DOTALL)
                        contenuto = m.group(1).strip() if m else html
                except Exception:
                    contenuto = text
                widget = DraggableTextWidget(contenuto, self.settings)

                # Aggiungi alla colonna A (pensierini)
                if (
                    hasattr(self, "pensierini_widget")
                    and self.pensierini_widget
                    and hasattr(self.pensierini_widget, "pensierini_layout")
                ):
                    self.pensierini_widget.pensierini_layout.addWidget(widget)

                    # Scroll automatico alla fine della colonna pensierini
                    if hasattr(self, "pensierini_scroll") and self.pensierini_scroll:
                        scroll_bar = self.pensierini_scroll.verticalScrollBar()
                        if scroll_bar:
                            QTimer.singleShot(
                                100, lambda: scroll_bar.setValue(scroll_bar.maximum())
                            )

                # Svuota il campo dopo l'invio
                self.footer_pensierini_input.clear()

                # Feedback visivo
                print(f"💭 Pensierino inviato: {text[:50]}...")

                # Log metriche
                self.log_ui_metrics("FOOTER_PENSIERINO_SENT")

            else:
                from PyQt6.QtWidgets import QMessageBox

                QMessageBox.warning(
                    self, "Errore", "Sistema di pensierini non disponibile."
                )

        except Exception as e:
            print(f"❌ Errore invio pensierino footer: {e}")
            from PyQt6.QtWidgets import QMessageBox

            QMessageBox.critical(
                self, "Errore", f"Errore durante l'invio del pensierino:\n{str(e)}"
            )

    def show_quick_help(self):
        """Mostra la guida rapida dell'applicazione."""
        help_text = """
        <h2>🚀 Guida Rapida CogniFlow</h2>

        <h3>💭 Pensierini</h3>
        <ul>
            <li><b>Campo footer:</b> Scrivi pensierini rapidi e premi Invio o clicca "📤 Invia"</li>
            <li><b>Sezione pensierini:</b> Usa l'area di creazione pensierini per testi più lunghi</li>
            <li><b>Trascina & rilascia:</b> Trascina pensierini tra colonne</li>
        </ul>

        <h3>🎯 Colonne</h3>
        <ul>
            <li><b>Colonna A:</b> Pensierini creativi</li>
            <li><b>Colonna B:</b> Area di lavoro</li>
            <li><b>Colonna C:</b> Lavagna risposte AI</li>
        </ul>

        <h3>🛠️ Cassetta Attrezzi</h3>
        <ul>
            <li><b>Trascrizione:</b> Voce → Testo, Audio → Testo, OCR</li>
            <li><b>AI & Media:</b> Chiedi all'AI, riconoscimento facce/gesti</li>
            <li><b>Materie:</b> Strumenti per tutte le materie scolastiche</li>
            <li><b>Utilità:</b> Carica media, pulizia, log</li>
            <li><b>IoT:</b> Arduino, circuiti, condivisione schermo</li>
        </ul>

        <h3>💾 Salvataggio</h3>
        <ul>
            <li><b>Salva:</b> Salva pensierini e area di lavoro</li>
            <li><b>Carica:</b> Ripristina progetti salvati</li>
            <li><b>Nome progetto:</b> Campo in alto per identificare il progetto</li>
        </ul>

        <h3>🎨 Webcam & Controlli</h3>
        <ul>
            <li><b>Webcam:</b> Attiva/disattiva modalità speculare</li>
            <li><b>Fullscreen:</b> F11 per schermo intero</li>
            <li><b>Impostazioni:</b> Personalizza colori, font e preferenze</li>
        </ul>

        <h3>⌨️ Scorciatoie</h3>
        <ul>
            <li><b>Ctrl+Z:</b> Annulla ultima azione</li>
            <li><b>Invio:</b> Invia pensierino dal campo footer</li>
            <li><b>F11:</b> Schermo intero</li>
        </ul>

        <p><b>💡 Suggerimento:</b> Usa il trascinamento per organizzare i tuoi pensierini!</p>
        """

        from PyQt6.QtWidgets import (
            QMessageBox,
            QDialog,
            QVBoxLayout,
            QTextEdit,
            QPushButton,
            QHBoxLayout,
        )

        # Crea dialog personalizzato per la guida
        dialog = QDialog(self)
        dialog.setWindowTitle("❓ Guida Rapida CogniFlow")
        dialog.resize(600, 500)

        layout = QVBoxLayout(dialog)

        # Area di testo con HTML
        help_display = QTextEdit()
        help_display.setHtml(help_text)
        help_display.setReadOnly(True)
        help_display.setStyleSheet(
            """
            QTextEdit {
                background: rgba(255, 255, 255, 0.95);
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 10px;
                font-size: 12px;
            }
        """
        )
        layout.addWidget(help_display)

        # Pulsanti
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        ok_button = QPushButton("✅ Capito!")
        ok_button.clicked.connect(dialog.accept)
        ok_button.setStyleSheet(
            """
            QPushButton {
                background: #28a745;
                border: 1px solid #1e7e34;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
                color: white;
            }
            QPushButton:hover {
                background: #218838;
            }
        """
        )
        buttons_layout.addWidget(ok_button)

        layout.addLayout(buttons_layout)

        dialog.exec()

    def log_ui_metrics(self, context=""):
        """Registra le metriche dell'interfaccia per il debug."""
        try:
            # Dimensioni finestra principale
            window_size = self.size()
            window_pos = self.pos()

            # Posizioni e dimensioni dei pulsanti nella top bar
            buttons_info = {}
            try:
                if hasattr(self, "options_button") and self.options_button is not None:
                    pos = self.options_button.pos()
                    size = self.options_button.size()
                    buttons_info["options_button"] = {
                        "pos": (pos.x(), pos.y()),
                        "size": (size.width(), size.height()),
                    }
            except Exception as e:
                print(f"Error getting options_button metrics: {e}")

            try:
                if (
                    hasattr(self, "toggle_tools_button")
                    and self.toggle_tools_button is not None
                ):
                    pos = self.toggle_tools_button.pos()
                    size = self.toggle_tools_button.size()
                    buttons_info["toggle_tools_button"] = {
                        "pos": (pos.x(), pos.y()),
                        "size": (size.width(), size.height()),
                    }
            except Exception as e:
                print(f"Error getting toggle_tools_button metrics: {e}")

            try:
                if hasattr(self, "save_button") and self.save_button is not None:
                    pos = self.save_button.pos()
                    size = self.save_button.size()
                    buttons_info["save_button"] = {
                        "pos": (pos.x(), pos.y()),
                        "size": (size.width(), size.height()),
                    }
            except Exception as e:
                print(f"Error getting save_button metrics: {e}")

            try:
                if hasattr(self, "load_button") and self.load_button is not None:
                    pos = self.load_button.pos()
                    size = self.load_button.size()
                    buttons_info["load_button"] = {
                        "pos": (pos.x(), pos.y()),
                        "size": (size.width(), size.height()),
                    }
            except Exception as e:
                print(f"Error getting load_button metrics: {e}")

            # Dimensioni del layout principale
            main_layout_geometry = None
            try:
                if hasattr(self, "centralWidget") and self.centralWidget():
                    cw = self.centralWidget()
                    if cw:
                        geom = cw.geometry()
                        main_layout_geometry = (
                            geom.x(),
                            geom.y(),
                            geom.width(),
                            geom.height(),
                        )
            except Exception as e:
                print(f"Error getting central widget geometry: {e}")

            # Dimensioni dello splitter verticale
            splitter_sizes = None
            if hasattr(self, "vertical_splitter"):
                splitter_sizes = self.vertical_splitter.sizes()

            metrics = {
                "context": context,
                "timestamp": datetime.now().isoformat(),
                "window": {
                    "size": (window_size.width(), window_size.height()),
                    "pos": (window_pos.x(), window_pos.y()),
                },
                "buttons": buttons_info,
                "main_layout": main_layout_geometry,
                "splitter_sizes": splitter_sizes,
            }

            # Salva in un file di log per analisi
            import json
            import os

            log_dir = os.path.join(os.path.dirname(__file__), "debug_logs")
            os.makedirs(log_dir, exist_ok=True)
            log_file = os.path.join(log_dir, "ui_metrics.jsonl")

            with open(log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(metrics, ensure_ascii=False) + "\n")

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
        tools_splitter.setStyleSheet(
            """
            QSplitter::handle {
                background: rgba(108, 117, 125, 0.4);
                border: 1px solid rgba(108, 117, 125, 0.6);
                border-radius: 2px;
            }
            QSplitter::handle:hover {
                background: rgba(74, 144, 226, 0.6);
                border-color: rgba(74, 144, 226, 0.8);
            }
        """
        )

        # === Colonna unica: Strumenti con input pensierini in basso ===
        tools_section = self.create_unified_tools_section_content()
        tools_splitter.addWidget(tools_section)

        # Imposta proporzioni: 100% strumenti (input pensierini ora dentro)
        tools_splitter.setSizes([1])

        unified_layout.addWidget(tools_splitter)
        self.unified_tools_section = unified_section
        self.tools_splitter = tools_splitter
        return unified_section

    def clear_column_a(self):
        """Pulisce la colonna A (pensierini)"""
        try:
            # Per ora, mostriamo solo un messaggio informativo
            # La pulizia effettiva dei pensierini richiede l'implementazione specifica
            print("✅ Colonna A (pensierini) - pulizia pianificata")
            QMessageBox.information(
                self,
                "Info Pulizia",
                "La pulizia della colonna A sarà implementata nella prossima versione.",
            )
        except Exception as e:
            print(f"⚠️ Errore pulizia colonna A: {e}")

    def clear_column_b(self):
        """Pulisce la colonna B (area di lavoro)"""
        try:
            if hasattr(self, "work_area_layout") and self.work_area_layout:
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
            if hasattr(self, "details_layout") and self.details_layout:
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
        """Pulisce i campi di input testo"""
        cleared = False
        # Nota: input_text_area e quick_input sono stati rimossi con la sezione pensierini
        if hasattr(self, "footer_pensierini_input"):
            self.footer_pensierini_input.clear()
            cleared = True
        if cleared:
            print("✅ Campi di input testo puliti")

    def undo_last_action(self):
        """Annulla l'ultima azione nei campi di testo"""
        # Nota: quick_input e input_text_area sono stati rimossi con la sezione pensierini
        print("ℹ️ Undo non disponibile - sezione pensierini rimossa")

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
            QMessageBox.StandardButton.No,
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
                "• Colonna C: VUOTA",
            )
        else:
            print("❌ Pulizia annullata dall'utente")

    def create_unified_tools_section_content(self):
        """Crea il contenuto unificato di tutti gli strumenti con schede e area risultati"""
        # Prima creo tutti i pulsanti necessari
        self._create_subject_buttons()

        tools_group = QGroupBox("🛠️ Cassetta degli attrezzi")
        tools_group.setMinimumHeight(200)
        self.tools_group = tools_group

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

        # Sezione pensierini rimossa da qui - ora è indipendente

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
            (
                "📊 Statistica",
                "probability_stats_button",
                self.handle_probability_stats_button,
            ),
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
        """Crea il widget con griglia 2 colonne a sinistra e contenuto a destra"""
        from PyQt6.QtWidgets import (
            QSplitter,
            QStackedWidget,
            QVBoxLayout,
            QWidget,
            QGridLayout,
            QPushButton,
        )

        # Widget principale con splitter
        main_widget = QWidget()
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Widget contenitore per il menu verticale delle categorie
        grid_container = QWidget()
        grid_container.setMaximumWidth(190)
        grid_layout = QGridLayout(grid_container)
        grid_layout.setContentsMargins(5, 5, 5, 5)
        grid_layout.setHorizontalSpacing(8)
        grid_layout.setVerticalSpacing(8)

        # Stili comuni per i pulsanti
        button_style = """
            QPushButton {
                border: 1px solid #dee2e6;
                border-radius: 6px;
                background: rgba(255, 255, 255, 0.95);
                color: #495057;
                font-weight: bold;
                font-size: 10px;
                padding: 8px 6px;
                text-align: center;
                min-height: 40px;
                min-width: 70px;
                max-width: 70px;
            }

            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f8f9ff, stop:1 #e8f4fd);
                border-color: #64b5f6;
            }

            QPushButton:checked {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #e3f2fd, stop:1 #bbdefb);
                color: #1976d2;
                border-color: #2196f3;
                border-left: 3px solid #2196f3;
            }
        """

        # Menu categorie: colonna verticale di pulsanti larghi (icona + testo)
        menu_button_style = """
            QPushButton {
                border: 1px solid #dee2e6;
                border-radius: 8px;
                background: rgba(255, 255, 255, 0.95);
                color: #495057;
                font-weight: bold;
                font-size: 12px;
                padding: 10px 12px;
                text-align: left;
                min-height: 40px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f8f9ff, stop:1 #e8f4fd);
                border-color: #64b5f6;
            }
            QPushButton:checked {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #e3f2fd, stop:1 #bbdefb);
                color: #1976d2;
                border-color: #2196f3;
                border-left: 4px solid #2196f3;
            }
        """

        # Menu semplificato: solo Materie (Tavoletta rimossa: la scrittura a
        # mano è disponibile dal pulsante "Canvas" nel footer)
        self.subjects_btn = QPushButton("📚  Materie")
        self.subjects_btn.setCheckable(True)
        self.subjects_btn.setStyleSheet(menu_button_style)

        grid_layout.addWidget(self.subjects_btn, 0, 0)
        grid_layout.setRowStretch(1, 1)

        # Stacked widget per il contenuto a destra
        self.tools_stack = QStackedWidget()
        subjects_tab = self.create_subjects_tab()
        self.tools_stack.addWidget(subjects_tab)

        def switch_to_tab(index):
            self.subjects_btn.setChecked(True)
            self.tools_stack.setCurrentIndex(0)

        self.subjects_btn.clicked.connect(lambda: switch_to_tab(0))
        switch_to_tab(0)

        # Aggiungi al layout principale
        main_layout.addWidget(grid_container)
        main_layout.addWidget(self.tools_stack)

        return main_widget

    def create_transcription_tab(self):
        """Crea la scheda Tavoletta: esercizio di scrittura a mano libera.

        Le funzioni Voce/Audio/OCR sono state incorporate nel pulsante "Allega".
        """
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(8)
        layout.setContentsMargins(12, 12, 12, 12)

        descrizione = QLabel(
            "✍️ Esercitati con la scrittura a mano libera usando una tavoletta grafica."
        )
        descrizione.setWordWrap(True)
        descrizione.setStyleSheet("color: #495057; font-size: 12px;")
        layout.addWidget(descrizione)

        layout.addWidget(self.graphics_tablet_button)

        layout.addStretch()
        return widget

    def create_ai_media_tab(self):
        """Crea la scheda AI & Media con stile unificato"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(6)  # Spaziatura unificata
        layout.setContentsMargins(12, 12, 12, 12)  # Margini unificati

        layout.addWidget(self.ai_button)

        # Gruppo riconoscimento con stile unificato
        recognition_group = QGroupBox("👁️ Riconoscimento")
        recognition_group.setStyleSheet(
            """
            QGroupBox {
                font-weight: bold;
                font-size: 11px;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                margin-top: 6px;
                padding-top: 8px;
                background: rgba(255, 255, 255, 0.9);
                color: #495057;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 2px 8px;
                color: #495057;
                font-weight: bold;
            }
        """
        )
        recognition_layout = QVBoxLayout(recognition_group)
        recognition_layout.setSpacing(4)
        recognition_layout.setContentsMargins(8, 8, 8, 8)
        recognition_layout.addWidget(self.face_button)
        recognition_layout.addWidget(self.hand_button)
        layout.addWidget(recognition_group)

        layout.addStretch()  # Spazio flessibile unificato
        return widget

    def create_subjects_tab(self):
        """Crea la scheda Materie con stile unificato"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(6)  # Spaziatura unificata
        layout.setContentsMargins(12, 12, 12, 12)  # Margini unificati

        # Scroll area per le materie con stile unificato
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setStyleSheet(
            """
            QScrollArea {
                border: 1px solid #dee2e6;
                border-radius: 4px;
                background: rgba(255, 255, 255, 0.9);
            }
        """
        )

        subjects_widget = QWidget()
        subjects_layout = QGridLayout(subjects_widget)
        subjects_layout.setSpacing(4)  # Spaziatura unificata per la griglia
        subjects_layout.setContentsMargins(8, 8, 8, 8)  # Margini unificati

        # Aggiungi pulsanti materie in griglia
        subject_buttons = self._create_subject_buttons()
        for i, button in enumerate(subject_buttons):
            row, col = divmod(i, 4)  # 4 colonne per layout uniforme
            subjects_layout.addWidget(button, row, col)

        scroll.setWidget(subjects_widget)
        layout.addWidget(scroll)
        return widget

    def create_utilities_tab(self):
        """Crea la scheda Utilità con stile unificato"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(6)  # Spaziatura unificata
        layout.setContentsMargins(12, 12, 12, 12)  # Margini unificati

        layout.addWidget(self.media_button)
        layout.addWidget(self.clean_button)
        layout.addWidget(self.log_button)

        layout.addStretch()  # Spazio flessibile unificato
        return widget

    def create_iot_tab(self):
        """Crea la scheda IoT con stile unificato"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(6)  # Spaziatura unificata
        layout.setContentsMargins(12, 12, 12, 12)  # Margini unificati

        layout.addWidget(self.arduino_button)
        layout.addWidget(self.circuit_button)
        layout.addWidget(self.screen_share_button)
        layout.addWidget(self.collab_button)

        layout.addStretch()  # Spazio flessibile unificato
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
        self.audio_transcription_button.clicked.connect(
            self.handle_audio_transcription_button
        )

        self.ocr_button = QPushButton("📄 OCR → Testo")
        self.ocr_button.setObjectName("ocr_button")
        self.ocr_button.setMinimumWidth(140)
        self.ocr_button.clicked.connect(self.handle_ocr_button)

        self.graphics_tablet_button = QPushButton("✍️ Apri tavoletta")
        self.graphics_tablet_button.setObjectName("graphics_tablet_button")
        self.graphics_tablet_button.setMinimumWidth(140)
        self.graphics_tablet_button.setToolTip(
            "Esercizio di scrittura a mano libera con tavoletta grafica"
        )
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
        """Mostra gli Strumenti nell'area comune del footer (al posto di
        Testo/Canvas); premuto di nuovo torna al testo."""
        if not hasattr(self, "footer_input_stack") or self._tools_page_index is None:
            return
        stack = self.footer_input_stack
        if stack.currentIndex() == self._tools_page_index:
            stack.setCurrentIndex(0)  # torna al testo
            if hasattr(self, "toggle_tools_button"):
                self.toggle_tools_button.setChecked(False)
            if hasattr(self, "toggle_input_mode_button"):
                self.toggle_input_mode_button.setText("🖊️ Canvas")
            self.set_status_message("⌨️ Area testo")
        else:
            stack.setCurrentIndex(self._tools_page_index)  # mostra Strumenti
            if hasattr(self, "toggle_tools_button"):
                self.toggle_tools_button.setChecked(True)
            if hasattr(self, "keyboard_button"):
                self.keyboard_button.setChecked(False)
            self.set_status_message("🔧 Strumenti nell'area comune")

    def toggle_virtual_keyboard(self):
        """Mostra la tastiera virtuale nell'area comune del footer
        (al posto di Testo/Canvas/Strumenti); premuta di nuovo torna al testo."""
        if (
            not hasattr(self, "footer_input_stack")
            or getattr(self, "_keyboard_page_index", None) is None
        ):
            return
        stack = self.footer_input_stack
        if stack.currentIndex() == self._keyboard_page_index:
            stack.setCurrentIndex(0)  # torna al testo
            self.keyboard_button.setChecked(False)
            if hasattr(self, "toggle_input_mode_button"):
                self.toggle_input_mode_button.setText("🖊️ Canvas")
            self.set_status_message("⌨️ Area testo")
        else:
            stack.setCurrentIndex(self._keyboard_page_index)
            self.keyboard_button.setChecked(True)
            if hasattr(self, "toggle_tools_button"):
                self.toggle_tools_button.setChecked(False)
            self.set_status_message(
                "⌨️ Tastiera a schermo: scrivi col puntatore nel campo pensierini"
            )

    def _hand_pointer_global(self):
        """Posizione globale del cursore del mano-mouse, o None se spento.

        Serve al dwell click della tastiera virtuale: il mano-mouse muove
        un cursore interno (niente puntatore di sistema su Wayland), quindi
        la tastiera non può basarsi solo su QCursor.pos().
        """
        hm = getattr(self, "hand_mouse", None)
        try:
            if hm is not None and hm.cursor.isVisible():
                parent = hm.cursor.parentWidget()
                if parent is not None:
                    return parent.mapToGlobal(hm.cursor.geometry().center())
        except RuntimeError:
            pass  # cursore distrutto durante lo spegnimento della webcam
        return None

    def set_safe_font(self):
        """Imposta un font sicuro e standard per evitare artefatti di rendering, usando le preferenze utente."""
        try:
            # Ottieni le preferenze font dalle impostazioni utente
            user_font_family = self.settings.get("fonts", {}).get(
                "main_font_family", "Arial"
            )
            user_font_size = self.settings.get("fonts", {}).get("main_font_size", 12)

            # Lista di font sicuri e standard, ordinati per priorità
            safe_fonts = [
                user_font_family,  # Prima priorità: font scelto dall'utente
                "Segoe UI",  # Windows moderno
                "SF Pro Display",  # macOS moderno
                "Ubuntu",  # Linux moderno
                "Arial",  # Universale
                "Helvetica",  # Universale
                "DejaVu Sans",  # Linux comune
                "Liberation Sans",  # Linux comune
                "Verdana",  # Windows comune
                "Tahoma",  # Windows comune
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
                logging.info(
                    f"✅ Font sicuro impostato: {selected_font} ({user_font_size}pt)"
                )
            else:
                # Fallback al font di sistema con dimensione utente
                system_font = QApplication.font()
                system_font.setPointSize(user_font_size)
                QApplication.setFont(system_font)
                logging.info(
                    f"✅ Font di sistema impostato come fallback ({user_font_size}pt)"
                )

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
        self.original_width = 0  # Per salvare la larghezza originale
        self.original_height = 0  # Per salvare l'altezza originale
        self.original_x = 0  # Per salvare la posizione X originale
        self.original_y = 0  # Per salvare la posizione Y originale

        # Stato webcam integrata (sfondo video + controllo a gesti)
        self.webcam_active = False
        self.video_thread_main = None
        self.video_bg_label = None
        self.hand_mouse = None

        # Ascolto vocale continuo con parola d'ordine
        self.wake_listener = None

        # Notifiche per i download in background (Impostazioni → 📥 Download)
        try:
            from core.download_manager import download_manager

            download_manager.finished.connect(
                self._on_background_download_finished
            )
        except ImportError:
            logging.warning("Gestore download in background non disponibile")

    def _resolve_vosk_model(self, requested):
        """Restituisce il nome di un modello Vosk installato, oppure None.

        Se nessun modello è presente propone lo scaricamento in background
        (Impostazioni → 📥 Download): l'app resta utilizzabile nel frattempo.
        """
        try:
            from core.download_manager import download_manager, CATALOG
        except ImportError:
            return requested  # gestore assente: lascia il flusso originale

        candidates = [requested] + [m for m in CATALOG if m != requested]
        for model in candidates:
            if download_manager.is_installed(model):
                if model != requested:
                    logging.info(
                        f"Modello '{requested}' assente, uso '{model}' installato"
                    )
                return model

        if download_manager.any_downloading():
            QMessageBox.information(
                self,
                "Download in corso",
                "Il modello vocale si sta già scaricando in background.\n\n"
                "Puoi continuare a usare CogniFlow: il progresso è visibile\n"
                "in ⚙️ Impostazioni → 📥 Download. Riprova quando è completato.",
            )
            return None

        # Proponi il modello leggero al posto del completo da 1,5 GB
        suggestion = (
            "vosk-model-small-it-0.22"
            if requested not in CATALOG or requested == "vosk-model-it-0.22"
            else requested
        )
        reply = QMessageBox.question(
            self,
            "Modello vocale mancante",
            "Per usare la voce serve un modello di riconoscimento.\n\n"
            f"Scaricare ora '{suggestion}' in background?\n"
            "Potrai continuare a usare CogniFlow: il progresso è visibile\n"
            "in ⚙️ Impostazioni → 📥 Download (dove trovi anche il modello completo).",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            download_manager.start(suggestion)
        return None

    def toggle_wake_word_listening(self):
        """Attiva/disattiva l'ascolto continuo con parola d'ordine."""
        if self.wake_listener is not None:
            self._stop_wake_word_listening()
            return

        vosk_model = self.settings.get("vosk_model", "vosk-model-small-it-0.22")
        if not vosk_model or vosk_model == "auto":
            vosk_model = "vosk-model-small-it-0.22"
        vosk_model = self._resolve_vosk_model(vosk_model)
        if vosk_model is None:
            self.wake_word_button.setChecked(False)
            return

        try:
            from Artificial_Intelligence.Riconoscimento_Vocale.managers.speech_recognition_manager import (
                WakeWordListenerThread,
            )
        except ImportError as e:
            QMessageBox.warning(
                self,
                "Ascolto vocale",
                f"Modulo di riconoscimento vocale non disponibile: {e}",
            )
            self.wake_word_button.setChecked(False)
            return

        wake_word = str(self.settings.get("wake_word", "scrivi")).strip() or "scrivi"

        self.wake_listener = WakeWordListenerThread(vosk_model, wake_word)
        self.wake_listener.wake_text.connect(self._on_wake_text)
        self.wake_listener.listener_error.connect(self._on_wake_error)
        self.wake_listener.start()

        self.wake_word_button.setText(f"🎙️ '{wake_word}' ON")
        self.wake_word_button.setChecked(True)
        print(f"🎙️ Ascolto continuo attivo, parola d'ordine: '{wake_word}'")

    def _stop_wake_word_listening(self):
        if self.wake_listener is not None:
            try:
                self.wake_listener.stop()
            except Exception as e:
                logging.warning(f"Errore fermando l'ascolto continuo: {e}")
            self.wake_listener = None
        self.wake_word_button.setText("🎙️ Parola d'ordine")
        self.wake_word_button.setChecked(False)

    def _on_wake_text(self, text):
        """Inserisce nel campo pensierino il testo detto dopo la parola d'ordine.

        Se il testo termina con 'invia', il pensierino viene inviato subito.
        """
        send_now = False
        if text.endswith("invia"):
            text = text[: -len("invia")].strip()
            send_now = True

        if text:
            current = self.footer_pensierini_input.toPlainText().strip()
            self.footer_pensierini_input.setPlainText(
                f"{current} {text}".strip() if current else text
            )
            self.footer_pensierini_input.setFocus()

        if send_now and self.footer_pensierini_input.toPlainText().strip():
            self.send_footer_pensierino()

    def _on_wake_error(self, message):
        self._stop_wake_word_listening()
        QMessageBox.warning(self, "Ascolto vocale", message)

    def _on_background_download_finished(self, item_id, ok):
        """Notifica non bloccante al termine di un download in background."""
        box = QMessageBox(self)
        if ok:
            box.setIcon(QMessageBox.Icon.Information)
            box.setWindowTitle("Download completato")
            box.setText(
                f"✅ '{item_id}' è pronto!\n\n"
                "Ora puoi usare la funzione collegata (es. 🎤 Voce → Testo)."
            )
        else:
            box.setIcon(QMessageBox.Icon.Warning)
            box.setWindowTitle("Download non completato")
            box.setText(
                f"Il download di '{item_id}' è stato annullato o è fallito.\n"
                "Puoi riprovare da ⚙️ Impostazioni → 📥 Download."
            )
        box.setModal(False)
        box.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        box.show()

    def toggle_webcam(self):
        """Attiva/disattiva la webcam integrata: video di sfondo e mano-mouse."""
        try:
            if self.webcam_active:
                self._stop_hand_mouse()
            else:
                self._start_hand_mouse()
        except Exception as e:
            print(f"❌ Errore toggle webcam: {e}")
            try:
                show_user_friendly_error(self, e, "webcam")
            except Exception:
                QMessageBox.critical(self, "Errore", f"Errore webcam: {str(e)}")

    def _start_hand_mouse(self):
        """Avvia la webcam come sfondo con controllo gesti (mano = mouse)."""
        if not VIDEO_THREAD_AVAILABLE or VideoThread is None:
            QMessageBox.warning(
                self,
                "Webcam",
                "VideoThread non disponibile: controlla le dipendenze webcam.",
            )
            return

        central = self.centralWidget()

        # Sfondo video dietro a tutti i pannelli
        if self.video_bg_label is None:
            self.video_bg_label = QLabel(central)
            self.video_bg_label.setScaledContents(True)
            self.video_bg_label.setAttribute(
                Qt.WidgetAttribute.WA_TransparentForMouseEvents
            )
        self.video_bg_label.setGeometry(central.rect())
        self.video_bg_label.lower()
        self.video_bg_label.show()

        # Controller mano-mouse (mano chiusa = click/afferra, aperta = rilascia)
        if self.hand_mouse is None:
            self.hand_mouse = HandMouseController(self)

        # Thread video con rilevamento mani (entrambe), gesti e viso
        vt = VideoThread(main_window=self)
        vt.hand_detection_enabled = True
        vt.gesture_recognition_enabled = True
        vt.left_hand_tracking_enabled = True
        vt.right_hand_tracking_enabled = True
        vt.face_detection_enabled = True
        vt.facial_expression_enabled = False
        vt.human_detection_enabled = False
        vt.use_mediapipe_service = False  # rilevamento locale OpenCV

        vt.change_pixmap_signal.connect(self._on_main_webcam_frame)
        vt.hand_position_signal.connect(self.hand_mouse.on_hand_position)
        vt.gesture_detected_signal.connect(self.hand_mouse.on_gesture)
        # Scrittura sul canvas impugnando una penna vera: l'indice della mano
        # segue la punta; alzare l'indice apre/chiude l'inchiostro digitale
        if hasattr(vt, "pen_tip_signal"):
            vt.pen_tip_signal.connect(self._on_pen_tip)
        vt.status_signal.connect(lambda s: logging.info(f"Webcam: {s}"))

        # Osservazione dei momenti di difficoltà: attiva solo se abilitata
        # e acconsentita nelle Impostazioni (spenta di default)
        obs = getattr(self, "difficulty_observer", None)
        if obs is not None and obs.enabled:
            vt.emit_difficulty = True
            vt.difficulty_signal.connect(self._on_difficulty_score)

        self.video_thread_main = vt
        vt.start()

        self._set_webcam_panels_transparent(True)
        self.webcam_button.setText("📹")
        self.webcam_button.setChecked(True)
        self.webcam_active = True
        # Suggerimento sul canvas: con la webcam attiva si scrive con la penna
        self._canvas_ink_on = False
        drawing = getattr(self, "footer_drawing", None)
        if drawing is not None and hasattr(drawing, "hint_label"):
            drawing.hint_label.setText(
                "✋ Impugna la penna e alza l'indice per aprire/chiudere l'inchiostro"
            )
        # Foglio quasi trasparente in automatico: per scrivere "in aria"
        # bisogna vedere la propria mano attraverso il canvas. Alla chiusura
        # della webcam il valore scelto dall'utente viene ripristinato.
        if drawing is not None and hasattr(drawing, "opacity_slider"):
            if drawing.opacity_slider.value() > 40:
                self._saved_canvas_opacity = drawing.opacity_slider.value()
                drawing.opacity_slider.setValue(30)
        print("📹 Webcam integrata attiva: mano chiusa = click, aperta = rilascia")

    def _stop_hand_mouse(self):
        """Ferma la webcam integrata e ripristina lo sfondo normale."""
        if self.video_thread_main is not None:
            try:
                self.video_thread_main.stop()
            except Exception as e:
                logging.warning(f"Errore fermando il thread video: {e}")
            self.video_thread_main = None

        if self.hand_mouse is not None:
            self.hand_mouse.stop()

        if self.video_bg_label is not None:
            self.video_bg_label.hide()
            self.video_bg_label.clear()

        self._set_webcam_panels_transparent(False)
        self.webcam_button.setText("📹")
        self.webcam_button.setChecked(False)
        self.webcam_active = False
        # Penna in aria: cursore via e rubinetto chiuso
        self._canvas_ink_on = False
        canvas = getattr(self, "footer_canvas", None)
        if canvas is not None:
            canvas.air_pen_point(0.0, 0.0, False)
        drawing = getattr(self, "footer_drawing", None)
        if drawing is not None and hasattr(drawing, "hint_label"):
            drawing.hint_label.setText("Tieni premuto  D  per disegnare")
        # Ripristina la trasparenza del foglio scelta prima della webcam
        saved_opacity = getattr(self, "_saved_canvas_opacity", None)
        if saved_opacity is not None and drawing is not None:
            drawing.opacity_slider.setValue(saved_opacity)
            self._saved_canvas_opacity = None
        print("📹 Webcam integrata disattivata")

    def _on_main_webcam_frame(self, pixmap):
        """Aggiorna lo sfondo con il frame webcam e la scala del mano-mouse."""
        if self.video_bg_label is not None and self.webcam_active:
            self.video_bg_label.setPixmap(pixmap)
        if self.hand_mouse is not None:
            self.hand_mouse.set_frame_size(pixmap.width(), pixmap.height())

    # Frame consecutivi con lo stato dell'indice cambiato prima di accettarlo:
    # filtra i tremolii del rilevamento ed evita aperture/chiusure accidentali
    PEN_TOGGLE_FRAMES = 6

    def _on_pen_tip(self, nx, ny, index_up):
        """Scrittura "in aria" sul canvas del footer impugnando una penna.

        La punta dell'indice della mano primaria fa da punta della penna.
        ALZARE l'indice (mentre si impugna la penna) apre/chiude il
        "rubinetto" dell'inchiostro: aperto = la punta traccia, chiuso = il
        cursore si muove senza scrivere. Vale solo sul canvas del footer.
        """
        canvas = getattr(self, "footer_canvas", None)
        stack = getattr(self, "footer_input_stack", None)
        if canvas is None or stack is None:
            return
        # Solo quando è visibile la pagina canvas (non testo né strumenti)
        if stack.currentIndex() != 1:
            canvas.air_pen_point(0.0, 0.0, False)
            return
        if nx < 0 or ny < 0:  # mano non inquadrata: penna sollevata
            self._pen_index_streak = 0
            canvas.air_pen_point(0.0, 0.0, False)
            return

        # Anti-rimbalzo: l'indice deve restare alzato/abbassato per qualche
        # frame prima che il cambio di stato apra/chiuda il rubinetto
        if not hasattr(self, "_pen_index_state"):
            # Stato di partenza: indice abbassato (impugnatura), così anche
            # un'alzata già in corso al primo frame conta come comando
            self._pen_index_state = False
            self._pen_index_streak = 0
            self._canvas_ink_on = False
        if bool(index_up) != self._pen_index_state:
            self._pen_index_streak += 1
            if self._pen_index_streak >= self.PEN_TOGGLE_FRAMES:
                self._pen_index_state = bool(index_up)
                self._pen_index_streak = 0
                if self._pen_index_state:  # è l'ALZATA che aziona il rubinetto
                    self._canvas_ink_on = not self._canvas_ink_on
                    drawing = getattr(self, "footer_drawing", None)
                    if drawing is not None and hasattr(drawing, "hint_label"):
                        drawing.hint_label.setText(
                            "🖋️ Inchiostro APERTO: la punta scrive"
                            if self._canvas_ink_on
                            else "✋ Inchiostro chiuso: alza l'indice per scrivere"
                        )
        else:
            self._pen_index_streak = 0

        # Mapping spaziale: l'inchiostro appare DOVE si vede la mano.
        # Il video di sfondo copre tutto il centralWidget, quindi la punta
        # nel frame (normalizzata) corrisponde allo stesso punto della
        # finestra; si scrive nella porzione di video coperta dal foglio
        # (reso trasparente in modalità webcam). Fuori dal foglio la penna
        # non c'è: cursore nascosto e tratto chiuso.
        central = self.centralWidget()
        if central is None:
            return
        frame_pt = QPoint(
            int(nx * max(1, central.width() - 1)),
            int(ny * max(1, central.height() - 1)),
        )
        local = canvas.mapFrom(central, frame_pt)
        if not canvas.rect().contains(local):
            canvas.air_pen_point(0.0, 0.0, False)
            return
        canvas.air_pen_point(
            local.x() / max(1, canvas.width() - 1),
            local.y() / max(1, canvas.height() - 1),
            True,
            getattr(self, "_canvas_ink_on", False),
        )

    def _set_webcam_panels_transparent(self, enabled):
        """Rende i pannelli semitrasparenti per vedere il video di sfondo.

        Lo stile globale (_apply_modern_ui_styles) dipinge OGNI QWidget con un
        gradiente opaco: anche gli splitter e i contenitori intermedi coprono
        il video. La trasparenza va quindi impostata widget per widget (lo
        stylesheet proprio vince su quello ereditato dalla finestra), salvando
        gli stili originali per ripristinarli alla disattivazione.
        """
        saved = getattr(self, "_webcam_saved_styles", None)
        if saved is None:
            saved = self._webcam_saved_styles = {}

        if not enabled:
            for widget, style in saved.items():
                try:
                    widget.setStyleSheet(style)
                except RuntimeError:
                    pass  # widget distrutto
            saved.clear()
            for name in ("pensierini_scroll", "work_area_scroll", "details_scroll"):
                scroll = getattr(self, name, None)
                if scroll is not None and scroll.viewport() is not None:
                    scroll.viewport().setAutoFillBackground(True)
            self._set_footer_text_outline(False)
            return

        def apply(widget, style, append=False):
            if widget is None or widget in saved:
                return
            saved[widget] = widget.styleSheet()
            widget.setStyleSheet(
                saved[widget] + "\n" + style if append else style
            )

        # Splitter e contenitori intermedi: trasparenti (mantengono le
        # regole originali dei manici, aggiunte in coda)
        for name in ("vertical_splitter", "main_splitter", "tools_splitter"):
            apply(
                getattr(self, name, None),
                "QSplitter { background: transparent; }",
                append=True,
            )
        apply(
            getattr(self, "unified_tools_section", None), "background: transparent;"
        )

        # Cornici delle tre colonne: velo bianco leggero, titolo leggibile
        group_style = (
            "QGroupBox { background: rgba(255, 255, 255, 0.30); }"
            "QGroupBox::title { background: rgba(255, 255, 255, 0.85);"
            " border-radius: 4px; }"
        )
        for name in ("column_a_group", "column_b_group", "column_c_group"):
            apply(getattr(self, name, None), group_style)

        # Cassetta degli attrezzi: velo più coprente (contiene molti controlli)
        apply(
            getattr(self, "tools_group", None),
            "QGroupBox { background: rgba(255, 255, 255, 0.55); }",
        )

        # Aree di scorrimento: cornice, viewport e contenuto trasparenti
        scroll_style = (
            "QScrollArea { background: transparent; }"
            "QScrollArea > QWidget#qt_scrollarea_viewport { background: transparent; }"
        )
        for name in ("pensierini_scroll", "work_area_scroll", "details_scroll"):
            scroll = getattr(self, name, None)
            if scroll is None:
                continue
            apply(scroll, scroll_style)
            if scroll.viewport() is not None:
                scroll.viewport().setAutoFillBackground(False)
            apply(scroll.widget(), "background: rgba(255, 255, 255, 0.25);")

        # Contenitori del footer (pila di input, canvas e WordPad): lo stile
        # globale li dipinge con un gradiente opaco che coprirebbe il video.
        # Trasparenti, il cursore della trasparenza del foglio mostra davvero
        # la webcam (e la propria mano) ATTRAVERSO il canvas.
        for name in ("footer_input_stack", "footer_drawing", "footer_richtext"):
            apply(getattr(self, name, None), "background: transparent;")
        canvas = getattr(self, "footer_canvas", None)
        if canvas is not None:
            apply(canvas, "background: transparent;")

        # Campo di scrittura del footer: trasparente anche lui, così si vede
        # il video sotto. Il testo resta leggibile grazie al bordino nero
        # attorno ai caratteri (vedi _set_footer_text_outline).
        apply(
            getattr(self, "footer_pensierini_input", None),
            "QTextEdit { background: rgba(255, 255, 255, 0.12);"
            " border: 1px solid rgba(0, 0, 0, 0.35); border-radius: 6px;"
            " padding: 4px 8px; font-size: 12px; }"
            "QTextEdit:focus { border-color: #4a90e2; }",
        )
        self._set_footer_text_outline(True)

    def _set_footer_text_outline(self, enabled):
        """Aggiunge/toglie un bordino nero attorno ai caratteri del footer.

        Con lo sfondo trasparente il testo chiaro (es. bianco) sparirebbe su
        uno sfondo chiaro: il contorno lo rende leggibile su qualsiasi cosa
        ci sia dietro. È solo visivo: l'invio usa toPlainText e i formati
        salvati non cambiano.
        """
        editor = getattr(self, "footer_pensierini_input", None)
        if editor is None:
            return
        pen = (
            QPen(QColor("#000000"), 1.0)
            if enabled
            else QPen(Qt.PenStyle.NoPen)
        )
        fmt = QTextCharFormat()
        fmt.setTextOutline(pen)
        cursor = QTextCursor(editor.document())
        cursor.select(QTextCursor.SelectionType.Document)
        cursor.mergeCharFormat(fmt)
        editor.mergeCurrentCharFormat(fmt)

    def resizeEvent(self, a0):
        """Mantiene lo sfondo video esteso a tutta la finestra."""
        super().resizeEvent(a0)
        if self.video_bg_label is not None and self.centralWidget() is not None:
            self.video_bg_label.setGeometry(self.centralWidget().rect())

    def create_new_pensierino(self):
        """Crea un nuovo pensierino tramite dialogo."""
        try:
            from PyQt6.QtWidgets import QInputDialog

            # Dialogo per inserire il testo del pensierino
            text, ok = QInputDialog.getMultiLineText(
                self,
                "💭 Crea Nuovo Pensierino",
                "Inserisci il testo del pensierino:",
                "",
            )

            if ok and text and text.strip():
                # Crea il nuovo widget pensierino
                from UI.draggable_text_widget import DraggableTextWidget

                widget = DraggableTextWidget(text.strip(), self.settings)

                # Aggiungi alla colonna A (pensierini)
                if (
                    hasattr(self, "pensierini_widget")
                    and self.pensierini_widget
                    and hasattr(self.pensierini_widget, "pensierini_layout")
                ):
                    self.pensierini_widget.pensierini_layout.addWidget(widget)

                print(f"💭 Nuovo pensierino creato: {text.strip()[:50]}...")

        except Exception as e:
            print(f"Errore nella creazione del pensierino: {e}")
            show_user_friendly_error(self, e, "creazione pensierino")

    # Nomi delle ore in italiano per l'orologio "fuzzy" stile KDE
    _ORE_IT = {
        1: "l'una", 2: "le due", 3: "le tre", 4: "le quattro",
        5: "le cinque", 6: "le sei", 7: "le sette", 8: "le otto",
        9: "le nove", 10: "le dieci", 11: "le undici", 12: "le dodici",
    }

    @classmethod
    def _fuzzy_time_it(cls, now):
        """Ora in forma discorsiva, es. 20:44 -> 'Le nove meno un quarto'."""
        h12 = now.hour % 12 or 12
        # Arrotonda al multiplo di 5 minuti più vicino
        m5 = int(round(now.minute / 5.0)) * 5
        nxt = (h12 % 12) + 1
        if m5 >= 60:
            m5 = 0
            h12, nxt = nxt, (nxt % 12) + 1
        base = cls._ORE_IT[h12]
        succ = cls._ORE_IT[nxt]
        frasi = {
            0: base,
            5: f"{base} e cinque",
            10: f"{base} e dieci",
            15: f"{base} e un quarto",
            20: f"{base} e venti",
            25: f"{base} e venticinque",
            30: f"{base} e mezza",
            35: f"{succ} meno venticinque",
            40: f"{succ} meno venti",
            45: f"{succ} meno un quarto",
            50: f"{succ} meno dieci",
            55: f"{succ} meno cinque",
        }
        frase = frasi[m5]
        return frase[:1].upper() + frase[1:]

    _MESI_IT = [
        "Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno",
        "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre",
    ]
    _GIORNI_IT = [
        "Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica",
    ]

    def _speak(self, text):
        """Pronuncia il testo ad alta voce in italiano, senza bloccare la UI.

        Interrompe l'eventuale frase precedente per evitare sovrapposizioni.
        """
        import shutil
        import subprocess

        # Ferma una lettura precedente ancora in corso
        prev = getattr(self, "_tts_process", None)
        if prev is not None and prev.poll() is None:
            try:
                prev.terminate()
            except Exception:
                pass

        try:
            exe = shutil.which("espeak-ng") or shutil.which("espeak")
            if exe:
                self._tts_process = subprocess.Popen(
                    [exe, "-v", "it", "-s", "150", text],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                return
        except Exception as e:
            self.add_message(f"Sintesi vocale non disponibile: {e}", "warning")

    def speak_current_time(self):
        """Dice ad alta voce solo l'ora corrente, es. 'Sono le ore 23:08'."""
        from datetime import datetime

        now = datetime.now()
        frase = f"Sono le ore {now.hour}:{now.minute:02d}"
        self.set_status_message(f"🔊 {frase}")
        self._speak(frase)

    def speak_current_date(self):
        """Dice ad alta voce la data corrente, es. 'Oggi è Domenica 12 Luglio 2026'."""
        from datetime import datetime

        now = datetime.now()
        giorno = self._GIORNI_IT[now.weekday()]
        mese = self._MESI_IT[now.month - 1]
        frase = f"Oggi è {giorno} {now.day} {mese} {now.year}"
        self.set_status_message(f"🔊 {frase}")
        self._speak(frase)

    def _update_time_labels(self):
        """Aggiorna l'orario: ora numerica sotto l'orologio, data breve ed estesa."""
        try:
            from datetime import datetime

            now = datetime.now()
            ora_num = now.strftime("%H:%M")
            data_breve = now.strftime("%d/%m/%Y")
            data_estesa = f"{now.day} {self._MESI_IT[now.month - 1]} {now.year}"
            fuzzy = self._fuzzy_time_it(now)

            # L'etichetta è posizionata SOTTO l'orologio analogico:
            # ora numerica, data breve, data estesa, forma discorsiva.
            if hasattr(self, "left_time_label"):
                self.left_time_label.setText(
                    f"{ora_num}\n{data_breve}\n{data_estesa}\n{fuzzy}"
                )

        except Exception as e:
            print(f"Errore nell'aggiornamento degli orari: {e}")

    def _stop_webcam(self):
        """Ferma la webcam e chiude la finestra."""
        try:
            if hasattr(self, "webcam_window") and self.webcam_window:
                self.webcam_window.close()
                self.webcam_window = None

        except Exception as e:
            print(f"Errore chiusura webcam: {e}")

    def _apply_mirror_effect(self):
        """Applica l'effetto specchio alla webcam (placeholder)."""
        try:
            # Placeholder per l'effetto specchio
            # In futuro: applicare trasformazione di flip orizzontale al video
            if hasattr(self, "webcam_window") and self.webcam_window:
                # Simula un leggero effetto visivo ogni secondo
                current_time = datetime.now().strftime("%S")
                if int(current_time) % 2 == 0:
                    self.webcam_window.setStyleSheet(
                        "QWidget { background: rgba(240, 248, 255, 0.1); }"
                    )
                else:
                    self.webcam_window.setStyleSheet(
                        "QWidget { background: rgba(255, 248, 240, 0.1); }"
                    )
        except Exception as e:
            print(f"Errore effetto specchio: {e}")

    # Marcatore inserito nel prompt per riconoscere le richieste di mappa ad albero
    GRAPH_MARKER = "[[GRAFO_ALBERO]]"

    def _is_graph_request(self, text):
        """True se l'utente chiede un riassunto/mappa ad albero o grafo."""
        t = (text or "").lower()
        forme = (
            "grafo", "albero", "mappa", "mind map", "mindmap",
            "schema", "diagramma", "mappa concett",
        )
        if any(k in t for k in forme):
            return True
        return "riassunt" in t and ("punt" in t or "chiave" in t or "concett" in t)

    def _graph_prompt(self, user_text):
        """Costruisce il prompt che chiede all'AI un elenco gerarchico."""
        return (
            "Crea un riassunto schematico ad ALBERO dei punti chiave.\n"
            "Rispondi ESCLUSIVAMENTE con un elenco puntato annidato: usa il trattino "
            "'-' e 2 spazi di indentazione per ogni livello di profondità, dal "
            "concetto generale ai dettagli. Massimo 4 livelli. Il primo elemento è "
            "l'argomento principale. Niente introduzioni né spiegazioni: solo l'elenco.\n\n"
            f"Argomento/Contenuto:\n{user_text}\n\n{self.GRAPH_MARKER}"
        )

    def _parse_outline_to_tree(self, text):
        """Trasforma un elenco puntato annidato in una struttura ad albero."""
        import re

        root = {"text": "🗺️ Riassunto", "children": []}
        stack = [(-1, root)]
        for raw in text.splitlines():
            if not raw.strip():
                continue
            stripped = raw.lstrip(" \t")
            indent = len(raw) - len(stripped)
            content = re.sub(
                r"^[\-\*•·▪◦●○►▶–—\d\.\)]+\s*", "", stripped
            ).strip()
            if not content:
                continue
            node = {"text": content, "children": []}
            while stack and stack[-1][0] >= indent:
                stack.pop()
            parent = stack[-1][1] if stack else root
            parent["children"].append(node)
            stack.append((indent, node))
        # Se c'è un solo figlio, usalo come radice (l'argomento principale)
        if len(root["children"]) == 1:
            return root["children"][0]
        return root

    def show_tree_in_details(self, root):
        """Mostra la mappa ad albero nella Lavagna AI (colonna C)."""
        from PyQt6.QtWidgets import QLabel, QScrollArea

        self._clear_details()
        titolo = QLabel("🗺️ Mappa ad albero dei punti chiave")
        titolo.setStyleSheet("font-weight: bold; color: #37474f; padding: 4px;")
        self.details_layout.addWidget(titolo)

        tree = TreeGraphWidget(root)
        scroll = QScrollArea()
        scroll.setWidgetResizable(False)
        scroll.setWidget(tree)
        self.details_layout.addWidget(scroll, 1)

    def _on_ai_response_received(self, prompt, response):
        """Gestisce la risposta ricevuta da Ollama."""
        try:
            # Riabilita il pulsante di riformulazione se era disabilitato
            if hasattr(self, "rephrase_button"):
                self.rephrase_button.setEnabled(True)

            # Richiesta di mappa/albero: rendi graficamente i punti chiave
            if self.GRAPH_MARKER in (prompt or ""):
                try:
                    tree = self._parse_outline_to_tree(response)
                    self.show_tree_in_details(tree)
                    return
                except Exception as e:
                    logging.error(f"Errore nel rendering dell'albero: {e}")
                    # In caso di problema mostra comunque il testo
                    self.show_text_in_details(response)
                    return

            # Controlla se è una risposta di riformulazione
            if "Riformula intensamente" in prompt or "Riformulazione intensa" in prompt:
                # Mostra la riformulazione nell'area risultati
                full_content = f"🧠 RIFORMULAZIONE COMPLETATA\n\n✨ Testo riformulato con intelligenza artificiale:\n\n{response}\n\n{'=' * 50}\n\n📊 Statistiche:\n• Testo originale: {len(self.full_text) if hasattr(self, 'full_text') else 0} caratteri\n• Testo riformulato: {len(response)} caratteri"

                # Log della riformulazione
                logging.info(f"Riformulazione AI completata: {len(response)} caratteri")

                # Mostra anche nei dettagli per compatibilità
                self.show_text_in_details(full_content)
            else:
                # Risposta AI normale (non riformulazione)
                full_content = f"📤 Richiesta:\n{prompt}\n\n{'=' * 50}\n\n🤖 Risposta AI (llama2:7b):\n\n{response}"

                # Log della risposta ricevuta
                logging.info(
                    f"Risposta AI ricevuta per prompt: {prompt[:50]}... (lunghezza: {len(response)} caratteri)"
                )

                # Mostra anche nei dettagli per compatibilità
                self.show_text_in_details(full_content)

        except Exception as e:
            logging.error(f"Errore nella gestione della risposta AI: {e}")
            error_msg = f"❌ Errore nella gestione della risposta AI:\n{str(e)}"
            show_user_friendly_error(self, e, "risposta AI")
            # Riabilita il pulsante in caso di errore
            if hasattr(self, "rephrase_button"):
                self.rephrase_button.setEnabled(True)

    def _on_ai_error_occurred(self, error_msg):
        """Gestisce gli errori da Ollama."""
        logging.error(f"Errore AI: {error_msg}")
        # Crea un'eccezione per il sistema user-friendly
        ai_error = Exception(f"Errore dal servizio AI: {error_msg}")
        show_user_friendly_error(self, ai_error, "servizio AI")

    def update_footer_status_old(self):
        """Aggiorna le informazioni di stato nel footer - versione precedente."""
        try:
            from datetime import datetime

            current_time = datetime.now().strftime("%H:%M:%S")
            status_text = (
                f"🕐 {current_time} | 👤 Sessione attiva | 📊 Sistema operativo"
            )
        except Exception as e:
            logging.error(f"Errore nell'aggiornamento del footer: {e}")

    def setup_ui(self):

        # Usa le dimensioni dalla configurazione globale
        window_width = self.settings.get("ui", {}).get("window_width", 1200)
        window_height = self.settings.get("ui", {}).get("window_height", 800)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Applica stile globale con font sicuro
        # Carica colori dalle impostazioni centralizzate
        colors = self.settings.get("colors", {})
        button_text_colors = colors.get("button_text_colors", {})
        button_border_colors = colors.get("button_border_colors", {})
        button_background_colors = colors.get("button_background_colors", {})
        button_hover_colors = colors.get("button_hover_colors", {})
        button_pressed_colors = colors.get("button_pressed_colors", {})

        # Carica preferenze font dalle impostazioni
        main_font_size = self.settings.get("fonts", {}).get("main_font_size", 13)
        pensierini_font_size = self.settings.get("fonts", {}).get(
            "pensierini_font_size", 12
        )

        # CSS dinamico basato sulle impostazioni colori - REMOVED

        main_layout = QVBoxLayout(central_widget)

        # Top bar
        top_layout = QHBoxLayout()
        self.options_button = QPushButton("⚙️ Impostazioni")
        self.options_button.setObjectName("options_button")  # ID per CSS
        self.options_button.clicked.connect(self.open_settings)
        top_layout.addWidget(self.options_button)

        # Pulsante "Messaggi": raccoglie i messaggi di errore dell'applicazione
        self.messages_button = QPushButton("✉️ Messaggi")
        self.messages_button.setObjectName("messages_button")
        self.messages_button.setToolTip("Mostra i messaggi ed errori dell'applicazione")
        self.messages_button.clicked.connect(self.show_messages_dialog)
        top_layout.addWidget(self.messages_button)

        # Il campo "Nome progetto" è stato rimosso: il nome viene dedotto dal
        # contenuto al momento del salvataggio (finestra "Salva con nome").
        top_layout.addStretch()

        self.save_button = QPushButton("💾 Salva")
        self.save_button.setObjectName("save_button")  # ID per CSS
        self.save_button.clicked.connect(self.save_project)
        top_layout.addWidget(self.save_button)

        self.load_button = QPushButton("📂 Carica")
        self.load_button.setObjectName("load_button")  # ID per CSS
        self.load_button.clicked.connect(self.load_project)
        top_layout.addWidget(self.load_button)

        # Pulsante webcam e guida "?" a destra di Carica, con un po' di spazio
        top_layout.addSpacing(24)

        self.webcam_button = QPushButton("📹")
        self.webcam_button.setObjectName("webcam_button")
        self.webcam_button.setCheckable(True)
        self.webcam_button.setMinimumHeight(50)
        self.webcam_button.setFixedWidth(72)
        self.webcam_button.clicked.connect(self.toggle_webcam)
        self.webcam_button.setToolTip("Attiva/disattiva webcam in modalità speculare")
        webcam_font_size = self.settings.get("fonts", {}).get("main_font_size", 13) + 8
        self.webcam_button.setStyleSheet(
            f"""
            QPushButton#webcam_button {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255, 255, 255, 0.95), stop:1 rgba(248, 249, 250, 0.95));
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 6px 8px;
                font-size: {webcam_font_size}px;
                font-weight: bold;
                color: #495057;
                min-height: 20px;
            }}
            QPushButton#webcam_button:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(248, 249, 250, 0.95), stop:1 rgba(241, 243, 244, 0.95));
                border-color: #adb5bd;
            }}
            QPushButton#webcam_button:checked {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(40, 167, 69, 0.1), stop:1 rgba(34, 197, 94, 0.1));
                border-color: #28a745;
                color: #155724;
            }}
        """
        )
        top_layout.addWidget(self.webcam_button)

        self.quick_help_button = QPushButton("?")
        self.quick_help_button.setObjectName("quick_help_button")
        self.quick_help_button.setMinimumHeight(28)
        self.quick_help_button.setFixedWidth(40)
        self.quick_help_button.setStyleSheet(
            """
            QPushButton#quick_help_button {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #17a2b8, stop:1 #138496);
                border: 1px solid #117a8b;
                border-radius: 6px;
                padding: 4px 8px;
                font-size: 16px;
                font-weight: bold;
                color: white;
            }
            QPushButton#quick_help_button:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #138496, stop:1 #117a8b);
            }
            QPushButton#quick_help_button:pressed {
                background: #117a8b;
            }
        """
        )
        self.quick_help_button.setToolTip("Mostra guida rapida dell'applicazione")
        self.quick_help_button.clicked.connect(self.show_quick_help)
        top_layout.addWidget(self.quick_help_button)

        # Pulsante di uscita/logout: chiude la sessione e torna al login.
        self.logout_button = QPushButton("🚪 Esci")
        self.logout_button.setObjectName("logout_button")
        self.logout_button.setMinimumHeight(28)
        self.logout_button.setToolTip("Esci dalla sessione e torna alla schermata di accesso")
        self.logout_button.setStyleSheet(
            """
            QPushButton#logout_button {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #6c757d, stop:1 #5a6268);
                border: 1px solid #545b62;
                border-radius: 6px;
                padding: 4px 12px;
                font-size: 13px;
                font-weight: bold;
                color: white;
            }
            QPushButton#logout_button:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #c82333, stop:1 #bd2130);
                border-color: #b21f2d;
            }
            QPushButton#logout_button:pressed { background: #bd2130; }
        """
        )
        self.logout_button.clicked.connect(self.logout)
        top_layout.addWidget(self.logout_button)

        main_layout.addLayout(top_layout)

        # Main content with SPLITTER for resizable columns
        from PyQt6.QtWidgets import QSplitter

        # Create splitter for resizable columns
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.main_splitter.setHandleWidth(
            8
        )  # Increased divider width for better visibility
        self.main_splitter.setStyleSheet(
            """
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
        """
        )

        # Column A: Pensierini
        self.column_a_group = QGroupBox("📝 Contenuti pensierini creativi (A)")
        self.column_a_group.setObjectName("pensierini")  # ID per CSS
        self.column_a_group.setMinimumWidth(
            250
        )  # Improved minimum width for better usability
        column_a_layout = QVBoxLayout(self.column_a_group)
        self.pensierini_scroll = QScrollArea()
        self.pensierini_scroll.setWidgetResizable(True)
        self.pensierini_widget = PensieriniWidget(
            self.settings, None
        )  # Layout sarà impostato dopo
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
        self.details_scroll.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
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

        # ===========================================
        # === SEZIONE STRUMENTI AVANZATI ===
        # ===========================================
        # Nota: Il QToolBox tradizionale è stato sostituito dal nuovo layout unificato
        # Questo codice è mantenuto per compatibilità ma non viene utilizzato

        # Crea QToolBox (Accordion) per gli strumenti - MANTENUTO PER COMPATIBILITÀ
        self.tools_toolbox = QToolBox()
        self.tools_toolbox.setObjectName("tools_toolbox")
        self.tools_toolbox.setMinimumHeight(320)
        self.tools_toolbox.setStyleSheet(
            """
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
        """
        )

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
        self.audio_transcription_button.clicked.connect(
            self.handle_audio_transcription_button
        )
        transcription_layout.addWidget(self.audio_transcription_button)

        self.ocr_button = QPushButton("📄 OCR → Testo")
        self.ocr_button.setObjectName("ocr_button")
        self.ocr_button.setMinimumWidth(140)
        self.ocr_button.clicked.connect(self.handle_ocr_button)
        transcription_layout.addWidget(self.ocr_button)

        self.graphics_tablet_button = QPushButton("✍️ Apri tavoletta")
        self.graphics_tablet_button.setObjectName("graphics_tablet_button")
        self.graphics_tablet_button.setMinimumWidth(140)
        self.graphics_tablet_button.setToolTip(
            "Esercizio di scrittura a mano libera con tavoletta grafica"
        )
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
        recognition_group.setStyleSheet(
            """
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
        """
        )
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
            (
                "📊 Statistica",
                "probability_stats_button",
                self.handle_probability_stats_button,
            ),
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
        vertical_splitter.setStyleSheet(
            """
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
        """
        )

        # ROW 1: Main content (columns A, B, C) — occupa tutta l'altezza:
        # la cassetta degli attrezzi ora vive nell'area comune del footer.
        vertical_splitter.addWidget(self.main_splitter)
        self.vertical_splitter = vertical_splitter

        # Costruisce il contenuto degli strumenti (verrà mostrato nell'area
        # comune del footer, al posto di Testo/Canvas, cliccando "Strumenti").
        self.tools_content_widget = self.create_unified_tools_section_content()

        # Set minimum window size
        self.setMinimumSize(1000, 850)

        vertical_splitter.setSizes([800])

        if hasattr(self, "toggle_tools_button"):
            self.toggle_tools_button.setChecked(False)
            self.toggle_tools_button.setText("🔧 Strumenti")

        # Add vertical splitter to main layout
        main_layout.addWidget(vertical_splitter, 1)

        # Inizializza lo stile del campo nome progetto
        self.update_project_name_input_style()

        # Footer con informazioni di stato
        footer_layout = QHBoxLayout()

        # Orario sotto l'orologio analogico (ora, data breve, data estesa, fuzzy)
        self.left_time_label = QLabel("⌚️")
        self.left_time_label.setObjectName("left_time_label")
        time_font_size = self.settings.get("fonts", {}).get("main_font_size", 13) + 1
        self.left_time_label.setStyleSheet(
            f"""
            QLabel#left_time_label {{
                color: #495057;
                font-size: {time_font_size}px;
                padding: 4px 10px;
                background: rgba(255, 255, 255, 0.9);
                border-radius: 8px;
                border: 1px solid #dee2e6;
                font-weight: bold;
                qproperty-alignment: AlignCenter;
                min-width: 150px;
                max-width: 220px;
            }}
        """
        )

        # Catturatore eventi mouse (click_status_label) in basso a sinistra
        self.click_status_label = QLabel("Clicca su un elemento...")
        self.click_status_label.setObjectName("click_status_label")
        click_font_size = self.settings.get("fonts", {}).get("main_font_size", 13) - 1
        self.click_status_label.setStyleSheet(
            f"""
            QLabel#click_status_label {{
                color: #666;
                font-size: {click_font_size}px;
                padding: 4px 14px;
                background: rgba(0, 0, 0, 0.04);
                border-radius: 4px;
                border: 1px solid #e0e0e0;
                font-weight: normal;
                text-align: left;
                min-height: 18px;
            }}
        """
        )

        # === CAMPO PENSERINI NEL FOOTER ===
        # Layout orizzontale per campo pensierini + pulsante invio
        pensierini_footer_layout = QHBoxLayout()
        pensierini_footer_layout.setSpacing(8)

        # Campo di testo ampio che riempie lo spazio disponibile del footer
        self.footer_pensierini_input = FooterPensierinoEdit(
            min_lines=6, max_lines=20, expand_to_fill=True
        )
        self.footer_pensierini_input.setPlaceholderText(
            "💭 Scrivi pensierino rapido..."
        )
        self.footer_pensierini_input.setMinimumWidth(200)
        # Si espande in orizzontale per riempire tutto lo spazio del footer
        self.footer_pensierini_input.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            self.footer_pensierini_input.sizePolicy().verticalPolicy(),
        )
        self.footer_pensierini_input.setStyleSheet(
            """
            QTextEdit {
                background: rgba(255, 255, 255, 0.95);
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 4px 8px;
                font-size: 12px;
                color: #495057;
            }
            QTextEdit:focus {
                border-color: #4a90e2;
                background: rgba(255, 255, 255, 1.0);
            }
        """
        )
        # Connetti il tasto Invio per inviare il pensierino
        self.footer_pensierini_input.send_requested.connect(
            self.send_footer_pensierino
        )

        # Canvas alternativo: scrivere/disegnare a mano invece di digitare.
        # Con il pulsante "Testo/Canvas" si passa dall'uno all'altro; inviando
        # il canvas, l'AI (OCR locale) converte la scrittura in testo pulito.
        self.footer_drawing = DrawingWidget(width=200, height=100)
        self.footer_drawing.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        # Riferimento diretto al canvas per OCR/salvataggio
        self.footer_canvas = self.footer_drawing.canvas

        from PyQt6.QtWidgets import QStackedWidget

        # Il campo testo è avvolto in un mini WordPad (barra di formattazione)
        self.footer_richtext = RichTextInputWidget(self.footer_pensierini_input)

        self.footer_input_stack = QStackedWidget()
        self.footer_input_stack.addWidget(self.footer_richtext)  # 0 = testo (WordPad)
        self.footer_input_stack.addWidget(self.footer_drawing)  # 1 = canvas
        # 2 = Strumenti (cassetta degli attrezzi) nell'area comune
        if getattr(self, "tools_content_widget", None) is not None:
            self.footer_input_stack.addWidget(self.tools_content_widget)
            self._tools_page_index = 2
        else:
            self._tools_page_index = None

        # Tastiera virtuale a schermo: per chi scrive solo col puntatore
        # (mouse, mano-mouse, domani BCI). Condivide il documento del campo
        # pensierini, quindi scrive davvero lì anche se lo copre.
        self._keyboard_page_index = None
        try:
            from UI.virtual_keyboard import VirtualKeyboardWidget

            self.virtual_keyboard = VirtualKeyboardWidget(
                target_edit=self.footer_pensierini_input,
                speak=self._speak,
                pointer_provider=self._hand_pointer_global,
                learned_words_path=os.path.join(
                    os.path.dirname(os.path.abspath(__file__)),
                    "Save",
                    "SETUP_TOOLS_&_Data",
                    "tastiera_parole_apprese.json",
                ),
            )
            self.virtual_keyboard.send_requested.connect(
                self.send_footer_pensierino
            )
            self._keyboard_page_index = self.footer_input_stack.addWidget(
                self.virtual_keyboard
            )
        except Exception as e:
            logging.warning(f"Tastiera virtuale non disponibile: {e}")
            self.virtual_keyboard = None
        # Riempie tutto lo spazio libero del footer (orizzontale e verticale)
        self.footer_input_stack.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self.footer_input_stack.setMinimumHeight(150)

        # Pulsante "Strumenti" (ex Cassetta degli attrezzi): collocato nella
        # colonna a destra, sotto "Canvas".
        self.toggle_tools_button = QPushButton("🔧 Strumenti")
        self.toggle_tools_button.setObjectName("toggle_tools_button")
        self.toggle_tools_button.setCheckable(True)
        self.toggle_tools_button.setMinimumHeight(28)
        self.toggle_tools_button.clicked.connect(self.toggle_tools_panel)

        pensierini_footer_layout.addWidget(self.footer_input_stack, 1)

        # Pulsante invio per pensierini
        self.footer_send_pensierino_button = QPushButton("📤 Invia")
        self.footer_send_pensierino_button.setMinimumHeight(28)
        self.footer_send_pensierino_button.setMinimumWidth(60)
        self.footer_send_pensierino_button.setStyleSheet(
            """
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #4a90e2, stop:1 #357abd);
                border: 1px solid #2e5c8a;
                border-radius: 6px;
                padding: 4px 8px;
                font-size: 11px;
                font-weight: bold;
                color: white;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #357abd, stop:1 #2e5c8a);
            }
            QPushButton:pressed {
                background: #2e5c8a;
            }
        """
        )
        self.footer_send_pensierino_button.clicked.connect(self.send_footer_pensierino)

        # Graffetta a destra di "Invia": allega documenti come in una email.
        # Comportamento intelligente per tipo di file:
        # - Se inserisci un qualsiasi audio io te lo trascrivo automaticamente offline
        # - Se inserisci un PDF lo mostro nell'Area di Lavoro per analizzarlo insieme
        self.attach_button = QPushButton("📎 Allega")
        self.attach_button.setToolTip(
            "Allega documenti:\n"
            "• Se inserisci un qualsiasi audio io te lo trascrivo automaticamente offline\n"
            "• Se inserisci un PDF lo mostro nell'Area di Lavoro per analizzarlo insieme"
        )
        self.attach_button.setMinimumWidth(84)
        self.attach_button.setMinimumHeight(28)
        self.attach_button.setStyleSheet(
            """
            QPushButton {
                background: rgba(255, 255, 255, 0.95);
                border: 1px solid #dee2e6;
                border-radius: 6px;
                font-size: 11px;
                font-weight: bold;
                color: #495057;
                padding: 4px 8px;
            }
            QPushButton:hover { border-color: #4a90e2; background: #f1f7ff; }
            QPushButton:pressed { background: #e2ecff; }
        """
        )
        self.attach_button.clicked.connect(self.attach_documents)

        # Pulsante ascolto continuo con parola d'ordine (ora comandato dalle
        # Impostazioni → Voce). Resta come contenitore di stato ma non è
        # mostrato nel footer, quindi lo teniamo nascosto con parent la finestra.
        self.wake_word_button = QPushButton("🎙️ Parola d'ordine", self)
        self.wake_word_button.setCheckable(True)
        self.wake_word_button.setToolTip(
            "Ascolto continuo: pronuncia la parola d'ordine seguita dal testo\n"
            "per inserirlo nel campo pensierino. Termina con 'invia' per\n"
            "inviarlo subito. Parola configurabile in Impostazioni → Voce."
        )
        self.wake_word_button.clicked.connect(self.toggle_wake_word_listening)
        self.wake_word_button.hide()

        # Pulsante cancella pensierini (input + colonne, con conferma)
        self.clear_all_button = QPushButton("🗑️ Cancella pensierini")
        self.clear_all_button.setMinimumHeight(28)
        self.clear_all_button.setMinimumWidth(100)
        self.clear_all_button.setStyleSheet(
            """
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f8f9fa, stop:1 #e9ecef);
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 4px 8px;
                font-size: 10px;
                color: #495057;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #e9ecef, stop:1 #dee2e6);
            }
            QPushButton:pressed {
                background: #dee2e6;
            }
        """
        )
        self.clear_all_button.clicked.connect(
            self.clear_all_pensierini_with_confirmation
        )

        # Pulsante per passare da input testo a canvas (scrittura/disegno a mano)
        self.toggle_input_mode_button = QPushButton("🖊️ Canvas")
        self.toggle_input_mode_button.setMinimumHeight(28)
        self.toggle_input_mode_button.setToolTip(
            "Passa da tastiera a scrittura/disegno a mano.\n"
            "Inviando il canvas, l'AI (OCR locale) converte la tua scrittura in "
            "testo pulito per prendere appunti più facilmente."
        )
        self.toggle_input_mode_button.setStyleSheet(
            """
            QPushButton {
                background: rgba(255, 255, 255, 0.95);
                border: 1px solid #dee2e6;
                border-radius: 6px;
                font-size: 11px;
                font-weight: bold;
                color: #495057;
                padding: 4px 8px;
            }
            QPushButton:hover { border-color: #4a90e2; background: #f1f7ff; }
            QPushButton:pressed { background: #e2ecff; }
        """
        )
        self.toggle_input_mode_button.clicked.connect(self.toggle_input_mode)

        # Riga superiore: Invia + graffetta; sotto: Canvas e Cancella pensierini
        send_top_row = QHBoxLayout()
        send_top_row.setSpacing(4)
        send_top_row.addWidget(self.footer_send_pensierino_button)
        send_top_row.addWidget(self.attach_button)

        # Pulsante per mostrare la tastiera virtuale nell'area comune
        self.keyboard_button = QPushButton("⌨️ Tastiera")
        self.keyboard_button.setCheckable(True)
        self.keyboard_button.setMinimumHeight(28)
        self.keyboard_button.setToolTip(
            "Tastiera a schermo: scrivi con il solo puntatore (mouse o "
            "mano-mouse), con predizione delle parole, dwell click (sosta "
            "sul tasto = pressione) e scansione a singolo segnale."
        )
        self.keyboard_button.setStyleSheet(
            self.toggle_input_mode_button.styleSheet()
        )
        self.keyboard_button.clicked.connect(self.toggle_virtual_keyboard)
        if self._keyboard_page_index is None:
            self.keyboard_button.setEnabled(False)

        send_column_layout = QVBoxLayout()
        send_column_layout.setSpacing(4)
        send_column_layout.addLayout(send_top_row)
        send_column_layout.addWidget(self.toggle_input_mode_button)
        send_column_layout.addWidget(self.toggle_tools_button)  # Strumenti sotto Canvas
        send_column_layout.addWidget(self.keyboard_button)
        send_column_layout.addWidget(self.clear_all_button)
        pensierini_footer_layout.addLayout(send_column_layout)

        # Aggiungi il layout pensierini (espandibile) al footer
        footer_layout.addLayout(pensierini_footer_layout, 1)

        # Orologio analogico in alto, e SOTTO l'orario numerico con data breve
        # ed estesa e la forma discorsiva. "Clicca su un elemento" è nel piè
        # di pagina in fondo.
        self.analog_clock = AnalogClock(size=66)
        # Click sull'orologio: dice l'ora ad alta voce
        self.analog_clock.clicked.connect(self.speak_current_time)
        self.left_time_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        # Click sulla data/orario: dice la data ad alta voce
        self.left_time_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.left_time_label.setToolTip("Clicca per sentire la data")
        self.left_time_label.mousePressEvent = (
            lambda event: self.speak_current_date()
        )
        time_column_layout = QVBoxLayout()
        time_column_layout.setSpacing(2)
        time_column_layout.addWidget(
            self.analog_clock, 0, Qt.AlignmentFlag.AlignHCenter
        )
        time_column_layout.addWidget(self.left_time_label)
        footer_layout.addLayout(time_column_layout)

        main_layout.addLayout(footer_layout)

        # === PIÈ DI PAGINA: barra di stato a tutta larghezza ===
        # Mostra messaggi veloci (caricamenti, cosa si è cliccato o premuto, ecc.)
        footer_status_bar = QHBoxLayout()
        footer_status_bar.setContentsMargins(6, 2, 6, 2)
        footer_status_bar.addWidget(self.click_status_label, 1)
        main_layout.addLayout(footer_status_bar)

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

                /* Pulsanti compatti negli strumenti */
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

                /* Miglioramenti per la lista verticale */
                QListWidget {
                    background: rgba(255, 255, 255, 0.95);
                    border-radius: 6px;
                }

                QListWidget::item {
                    border-bottom: 1px solid #eee;
                }

                QListWidget::item:selected {
                    border-left: 3px solid #2196f3;
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
            if hasattr(self, "toggle_tools_button"):
                self.toggle_animation = QPropertyAnimation(
                    self.toggle_tools_button, b"geometry"
                )
                self.toggle_animation.setDuration(300)
                self.toggle_animation.setEasingCurve(QEasingCurve.Type.OutCubic)

            # Animazione per il click status label
            if hasattr(self, "click_status_label"):
                self.click_label_animation = QPropertyAnimation(
                    self.click_status_label, b"windowOpacity"
                )
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
            if hasattr(self, "options_button"):
                self.options_button.setToolTip(
                    "⚙️ Configura le impostazioni dell'applicazione\n"
                    "Personalizza colori, font e preferenze"
                )

            if hasattr(self, "toggle_tools_button"):
                self.toggle_tools_button.setToolTip(
                    "🔧 Mostra/Nasconde il pannello degli strumenti\n"
                    "Contiene tutte le funzionalità avanzate"
                )

            if hasattr(self, "save_button"):
                self.save_button.setToolTip(
                    "💾 Salva il progetto corrente\n"
                    "Salva tutti i pensierini e le impostazioni"
                )

            if hasattr(self, "load_button"):
                self.load_button.setToolTip(
                    "📂 Carica un progetto salvato\n"
                    "Ripristina pensierini e impostazioni precedenti"
                )

            # Tooltip per i pulsanti di input - rimosso con la sezione pensierini

            # Tooltip per i pulsanti degli strumenti
            if hasattr(self, "voice_button"):
                self.voice_button.setToolTip(
                    "🎤 Riconoscimento vocale\n"
                    "Converte la voce in testo usando Vosk\n"
                    "Premi e parla chiaramente nel microfono"
                )

            if hasattr(self, "audio_transcription_button"):
                self.audio_transcription_button.setToolTip(
                    "🎵 Trascrizione file audio\n"
                    "Converte file audio in testo\n"
                    "Supporta vari formati audio"
                )

            if hasattr(self, "ocr_button"):
                self.ocr_button.setToolTip(
                    "📄 Riconoscimento ottico caratteri\n"
                    "Estrae testo dalle immagini\n"
                    "Supporta screenshot e file immagine"
                )

            if hasattr(self, "ai_button"):
                self.ai_button.setToolTip(
                    "🧠 Chiedi all'Intelligenza Artificiale\n"
                    "AI utilizzata: Llama 2 (7B parametri)\n"
                    "Invia richieste a Ollama AI\n"
                    "Ottieni risposte intelligenti e riformulazioni"
                )

            if hasattr(self, "face_button"):
                self.face_button.setToolTip(
                    "❌ Riconoscimento facciale\n"
                    "Attiva/disattiva il riconoscimento facce\n"
                    "Funzionalità in sviluppo"
                )

            if hasattr(self, "hand_button"):
                self.hand_button.setToolTip(
                    "❌ Riconoscimento gesti\n"
                    "Attiva/disattiva il riconoscimento gesti\n"
                    "Funzionalità in sviluppo"
                )

            # Tooltip per i pulsanti delle materie
            subject_tooltips = {
                "ipa_button": "📝 Fonetica Internazionale\nPronuncia e simboli IPA",
                "math_button": "🔢 Matematica\nCalcoli e formule matematiche",
                "chemistry_button": "⚗️ Chimica\nReazioni e composti chimici",
                "physics_button": "⚛️ Fisica\nLeggi fisiche e meccanica",
                "biology_button": "🧬 Biologia\nScienze della vita e organismi",
                "italian_button": "🇮🇹 Italiano\nGrammatica e letteratura italiana",
                "history_button": "📚 Storia\nEventi storici e civiltà",
                "computer_science_button": "💻 Informatica\nProgrammazione e algoritmi",
                "astronomy_button": "🌌 Astronomia\nStelle, pianeti e universo",
                "advanced_math_button": "📐 Matematica Avanzata\nAnalisi e geometria",
                "law_button": "⚖️ Diritto\nLeggi e giurisprudenza",
                "english_button": "🇺🇸 Inglese\nLingua e letteratura inglese",
                "spanish_button": "🇪🇸 Spagnolo\nLingua e cultura ispanica",
                "german_button": "🇩🇪 Tedesco\nLingua e letteratura tedesca",
                "japanese_button": "🇯🇵 Giapponese\nLingua e cultura giapponese",
                "chinese_button": "🇨🇳 Cinese\nLingua e cultura cinese",
                "russian_button": "🇷🇺 Russo\nLingua e letteratura russa",
            }

            # Applica i tooltip alle materie
            for button_name, tooltip in subject_tooltips.items():
                if hasattr(self, button_name):
                    button = getattr(self, button_name)
                    button.setToolTip(f"{tooltip}\nFunzionalità in sviluppo")

            # Tooltip per gli altri pulsanti
            if hasattr(self, "media_button"):
                self.media_button.setToolTip(
                    "📁 Carica file multimediali\n" "Immagini, audio, video e documenti"
                )

            if hasattr(self, "clean_button"):
                self.clean_button.setToolTip(
                    "🧹 Pulisci tutto\n"
                    "Rimuovi tutti i pensierini e resetta l'area di lavoro"
                )

            if hasattr(self, "log_button"):
                self.log_button.setToolTip(
                    "📋 Mostra/Nasconde il pannello log\n"
                    "Visualizza i messaggi di sistema e debug"
                )

            # Tooltip per i controlli di navigazione
            if hasattr(self, "back_button"):
                self.back_button.setToolTip(
                    "⬅️ Pagina precedente\n" "Torna alla pagina precedente del testo"
                )

            if hasattr(self, "forward_button"):
                self.forward_button.setToolTip(
                    "➡️ Pagina successiva\n" "Vai alla pagina successiva del testo"
                )

            if hasattr(self, "copy_button"):
                self.copy_button.setToolTip(
                    "📋 Copia tutto il testo\n"
                    "Copia il contenuto completo negli appunti"
                )

            if hasattr(self, "rephrase_button"):
                self.rephrase_button.setToolTip(
                    "🧠 Riformula intensamente\n"
                    "Usa AI per migliorare e riformulare il testo"
                )

            # Tooltip per le aree di input - input_text_area rimosso con la sezione pensierini

            if hasattr(self, "project_name_input"):
                self.project_name_input.setToolTip(
                    "Nome del progetto corrente\n"
                    "Viene usato per salvare/caricare progetti"
                )

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
            QShortcut(QKeySequence("Ctrl+T"), self).activated.connect(
                self.toggle_tools_panel
            )
            QShortcut(QKeySequence("Ctrl+L"), self).activated.connect(
                self._toggle_log_panel
            )

            # Scorciatoie per funzioni comuni
            QShortcut(QKeySequence("F2"), self).activated.connect(
                self._focus_input_area
            )
            QShortcut(QKeySequence("F3"), self).activated.connect(self._focus_search)
            QShortcut(QKeySequence("Ctrl+Return"), self).activated.connect(
                self.add_text_from_input_area
            )

            # Scorciatoie per navigazione
            QShortcut(QKeySequence("Ctrl+1"), self).activated.connect(
                lambda: self._focus_column(0)
            )
            QShortcut(QKeySequence("Ctrl+2"), self).activated.connect(
                lambda: self._focus_column(1)
            )
            QShortcut(QKeySequence("Ctrl+3"), self).activated.connect(
                lambda: self._focus_column(2)
            )

            # Scorciatoie per funzioni AI e media
            QShortcut(QKeySequence("Ctrl+A"), self).activated.connect(
                self.handle_ai_button
            )
            QShortcut(QKeySequence("Ctrl+V"), self).activated.connect(
                self.handle_voice_button
            )
            QShortcut(QKeySequence("Ctrl+M"), self).activated.connect(
                self.handle_media_button
            )
            QShortcut(QKeySequence("Ctrl+Z"), self).activated.connect(
                self.undo_last_action
            )

            logging.info("✅ Scorciatoie da tastiera aggiunte con successo")

        except Exception as e:
            logging.error(f"❌ Errore nell'aggiunta delle scorciatoie: {e}")

    def _new_project(self):
        """Crea un nuovo progetto (resetta tutto)."""
        try:
            reply = QMessageBox.question(
                self,
                "Nuovo Progetto",
                "Vuoi creare un nuovo progetto?\n"
                "Tutti i pensierini non salvati andranno persi.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )

            if reply == QMessageBox.StandardButton.Yes:
                # Pulisci tutti i pensierini
                self._clear_all_pensierini()
                # Reset nome progetto
                if hasattr(self, "project_name_input"):
                    self.project_name_input.clear()
                # Reset area di lavoro
                self._clear_work_area()
                # Reset dettagli
                self._clear_details()

                QMessageBox.information(
                    self, "Nuovo Progetto", "✅ Nuovo progetto creato con successo!"
                )

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
        if hasattr(self, "log_button"):
            self.log_button.click()

    def _focus_input_area(self):
        """Imposta il focus sull'area di input - area rimossa con la sezione pensierini."""
        # La sezione pensierini è stata rimossa
        pass

    def _focus_search(self):
        """Imposta il focus sulla barra di ricerca (se presente)."""
        # Placeholder per futura implementazione
        pass

    def _focus_column(self, column_index):
        """Imposta il focus su una colonna specifica."""
        try:
            if column_index == 0 and hasattr(self, "pensierini_scroll"):
                self.pensierini_scroll.setFocus()
            elif column_index == 1 and hasattr(self, "work_area_scroll"):
                self.work_area_scroll.setFocus()
            elif column_index == 2 and hasattr(self, "details_scroll"):
                self.details_scroll.setFocus()
        except Exception as e:
            logging.error(f"Errore nel focus della colonna {column_index}: {e}")

    def _clear_all_pensierini(self):
        """Pulisce tutti i pensierini dalla colonna A."""
        try:
            if (
                hasattr(self, "pensierini_widget")
                and self.pensierini_widget
                and hasattr(self.pensierini_widget, "pensierini_layout")
            ):
                while self.pensierini_widget.pensierini_layout.count():
                    item = self.pensierini_widget.pensierini_layout.takeAt(0)
                    if item:
                        widget = item.widget()
                        if widget and hasattr(widget, "deleteLater"):
                            widget.deleteLater()
        except Exception as e:
            logging.error(f"Errore nella pulizia dei pensierini: {e}")

    def _clear_work_area(self):
        """Pulisce l'area di lavoro."""
        try:
            if hasattr(self, "work_area_layout") and self.work_area_layout:
                while self.work_area_layout.count():
                    item = self.work_area_layout.takeAt(0)
                    if item:
                        widget = item.widget()
                        if widget and hasattr(widget, "deleteLater"):
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
        QMessageBox.information(
            self,
            "📝 IPA",
            "🔤 Funzionalità IPA in Sviluppo\n\n"
            "📚 Questa sezione sarà dedicata a:\n"
            "• Pronuncia fonetica internazionale\n"
            "• Simboli IPA interattivi\n"
            "• Esercizi di pronuncia\n"
            "• Dizionario fonetico\n\n"
            "⚠️ Funzionalità attualmente in fase di implementazione",
        )

    def handle_math_button(self):
        """Gestisce il pulsante Matematica - Funzionalità in sviluppo."""
        QMessageBox.information(
            self,
            "🔢 Matematica",
            "📚 Funzionalità Matematica in Sviluppo\n\n"
            "🧮 Questa sezione sarà dedicata a:\n"
            "• Calcoli matematici interattivi\n"
            "• Risoluzione di equazioni\n"
            "• Geometria e algebra\n"
            "• Statistica e probabilità\n\n"
            "⚠️ Funzionalità attualmente in fase di implementazione",
        )

    def handle_history_button(self):
        """Gestisce il pulsante Storia - Funzionalità in sviluppo."""
        QMessageBox.information(
            self,
            "📚 Storia",
            "🏛️ Funzionalità Storia in Sviluppo\n\n"
            "📜 Questa sezione sarà dedicata a:\n"
            "• Linee temporali interattive\n"
            "• Eventi storici importanti\n"
            "• Biografie di personaggi storici\n"
            "• Mappe storiche\n\n"
            "⚠️ Funzionalità attualmente in fase di implementazione",
        )

    def handle_italian_button(self):
        """Gestisce il pulsante Italiano - Funzionalità in sviluppo."""
        QMessageBox.information(
            self,
            "🇮🇹 Italiano",
            "📖 Funzionalità Italiano in Sviluppo\n\n"
            "✍️ Questa sezione sarà dedicata a:\n"
            "• Grammatica italiana\n"
            "• Analisi del testo\n"
            "• Letteratura italiana\n"
            "• Ortografia e sintassi\n\n"
            "⚠️ Funzionalità attualmente in fase di implementazione",
        )

    def handle_chemistry_button(self):
        """Gestisce il pulsante Chimica - Funzionalità in sviluppo."""
        QMessageBox.information(
            self,
            "⚗️ Chimica",
            "🧪 Funzionalità Chimica in Sviluppo\n\n"
            "🔬 Questa sezione sarà dedicata a:\n"
            "• Tavola periodica interattiva\n"
            "• Reazioni chimiche\n"
            "• Struttura molecolare\n"
            "• Esperimenti virtuali\n\n"
            "⚠️ Funzionalità attualmente in fase di implementazione",
        )

    def handle_physics_button(self):
        """Gestisce il pulsante Fisica - Funzionalità in sviluppo."""
        QMessageBox.information(
            self,
            "⚛️ Fisica",
            "🔭 Funzionalità Fisica in Sviluppo\n\n"
            "⚡ Questa sezione sarà dedicata a:\n"
            "• Leggi della fisica\n"
            "• Meccanica e termodinamica\n"
            "• Elettricità e magnetismo\n"
            "• Fisica quantistica\n\n"
            "⚠️ Funzionalità attualmente in fase di implementazione",
        )

    def handle_biology_button(self):
        """Gestisce il pulsante Scienza dei 5 Regni - Funzionalità in sviluppo."""
        QMessageBox.information(
            self,
            "🧬 Scienza dei 5 Regni",
            "🌿 Funzionalità Biologia in Sviluppo\n\n"
            "🦠 Questa sezione sarà dedicata a:\n"
            "• Classificazione dei 5 regni\n"
            "• Anatomia e fisiologia\n"
            "• Ecologia e ambiente\n"
            "• Genetica e evoluzione\n\n"
            "⚠️ Funzionalità attualmente in fase di implementazione",
        )

    def handle_astronomy_button(self):
        """Gestisce il pulsante Astronomia - Funzionalità in sviluppo."""
        QMessageBox.information(
            self,
            "🌌 Astronomia",
            "🪐 Funzionalità Astronomia in Sviluppo\n\n"
            "🌟 Questa sezione sarà dedicata a:\n"
            "• Sistema solare\n"
            "• Stelle e galassie\n"
            "• Cosmologia\n"
            "• Osservazione astronomica\n\n"
            "⚠️ Funzionalità attualmente in fase di implementazione",
        )

    def handle_computer_science_button(self):
        """Gestisce il pulsante Informatica - Funzionalità in sviluppo."""
        QMessageBox.information(
            self,
            "💻 Informatica",
            "🖥️ Funzionalità Informatica in Sviluppo\n\n"
            "💾 Questa sezione sarà dedicata a:\n"
            "• Programmazione e algoritmi\n"
            "• Strutture dati\n"
            "• Reti e sicurezza informatica\n"
            "• Intelligenza artificiale\n\n"
            "⚠️ Funzionalità attualmente in fase di implementazione",
        )

    def handle_os_scripting_button(self):
        """Gestisce il pulsante Sistemi Operativi e Script - Funzionalità in sviluppo."""
        QMessageBox.information(
            self,
            "🖥️ Sistemi Operativi e Script",
            "🔧 Funzionalità Sistemi Operativi in Sviluppo\n\n"
            "⚙️ Questa sezione sarà dedicata a:\n"
            "• Sistemi operativi (Linux, Windows, macOS)\n"
            "• Scripting (Bash, PowerShell, Python)\n"
            "• Automazione processi\n"
            "• Amministrazione sistemi\n\n"
            "⚠️ Funzionalità attualmente in fase di implementazione",
        )

    def handle_advanced_math_button(self):
        """Gestisce il pulsante Matematica delle Superiori - Funzionalità in sviluppo."""
        QMessageBox.information(
            self,
            "📐 Matematica delle Superiori",
            "🔬 Funzionalità Matematica Avanzata in Sviluppo\n\n"
            "📊 Questa sezione sarà dedicata a:\n"
            "• Analisi matematica\n"
            "• Geometria analitica\n"
            "• Algebra lineare\n"
            "• Calcolo differenziale e integrale\n\n"
            "⚠️ Funzionalità attualmente in fase di implementazione",
        )

    def handle_law_button(self):
        """Gestisce il pulsante Diritto - Funzionalità in sviluppo."""
        QMessageBox.information(
            self,
            "⚖️ Diritto",
            "📋 Funzionalità Diritto in Sviluppo\n\n"
            "🏛️ Questa sezione sarà dedicata a:\n"
            "• Diritto civile e penale\n"
            "• Diritto costituzionale\n"
            "• Diritto internazionale\n"
            "• Casi giuridici e sentenze\n\n"
            "⚠️ Funzionalità attualmente in fase di implementazione",
        )

    def handle_probability_stats_button(self):
        """Gestisce il pulsante Calcolo Probabilità e Statistica - Funzionalità in sviluppo."""
        QMessageBox.information(
            self,
            "📊 Probabilità e Statistica",
            "📈 Funzionalità Statistica in Sviluppo\n\n"
            "🔢 Questa sezione sarà dedicata a:\n"
            "• Teoria delle probabilità\n"
            "• Statistica descrittiva\n"
            "• Inferenza statistica\n"
            "• Analisi dati e modelli\n\n"
            "⚠️ Funzionalità attualmente in fase di implementazione",
        )

    def handle_english_button(self):
        """Gestisce il pulsante Inglese - Funzionalità in sviluppo."""
        QMessageBox.information(
            self,
            "🇺🇸 Inglese",
            "📚 Funzionalità Inglese in Sviluppo\n\n"
            "🇬🇧 Questa sezione sarà dedicata a:\n"
            "• Grammatica inglese\n"
            "• Vocabolario e frasi comuni\n"
            "• Pronuncia e fonetica\n"
            "• Letteratura inglese\n\n"
            "⚠️ Funzionalità attualmente in fase di implementazione",
        )

    def handle_german_button(self):
        """Gestisce il pulsante Tedesco - Funzionalità in sviluppo."""
        QMessageBox.information(
            self,
            "🇩🇪 Tedesco",
            "📚 Funzionalità Tedesco in Sviluppo\n\n"
            "🇩🇪 Questa sezione sarà dedicata a:\n"
            "• Grammatica tedesca\n"
            "• Vocabolario essenziale\n"
            "• Pronuncia corretta\n"
            "• Cultura germanica\n\n"
            "⚠️ Funzionalità attualmente in fase di implementazione",
        )

    def handle_spanish_button(self):
        """Gestisce il pulsante Spagnolo - Funzionalità in sviluppo."""
        QMessageBox.information(
            self,
            "🇪🇸 Spagnolo",
            "📚 Funzionalità Spagnolo in Sviluppo\n\n"
            "🇪🇸 Questa sezione sarà dedicata a:\n"
            "• Grammatica spagnola\n"
            "• Vocabolario e espressioni\n"
            "• Pronuncia e accenti\n"
            "• Letteratura ispanica\n\n"
            "⚠️ Funzionalità attualmente in fase di implementazione",
        )

    def handle_sicilian_button(self):
        """Gestisce il pulsante Siciliano - Funzionalità in sviluppo."""
        QMessageBox.information(
            self,
            "🏛️ Siciliano",
            "📚 Funzionalità Siciliano in Sviluppo\n\n"
            "🇮🇹 Questa sezione sarà dedicata a:\n"
            "• Grammatica siciliana\n"
            "• Vocabolario regionale\n"
            "• Pronuncia tradizionale\n"
            "• Letteratura siciliana\n\n"
            "⚠️ Funzionalità attualmente in fase di implementazione",
        )

    def handle_japanese_button(self):
        """Gestisce il pulsante Giapponese - Funzionalità in sviluppo."""
        QMessageBox.information(
            self,
            "🇯🇵 Giapponese",
            "📚 Funzionalità Giapponese in Sviluppo\n\n"
            "🇯🇵 Questa sezione sarà dedicata a:\n"
            "• Hiragana e Katakana\n"
            "• Kanji essenziali\n"
            "• Grammatica giapponese\n"
            "• Cultura tradizionale\n\n"
            "⚠️ Funzionalità attualmente in fase di implementazione",
        )

    def handle_chinese_button(self):
        """Gestisce il pulsante Cinese - Funzionalità in sviluppo."""
        QMessageBox.information(
            self,
            "🇨🇳 Cinese",
            "📚 Funzionalità Cinese in Sviluppo\n\n"
            "🇨🇳 Questa sezione sarà dedicata a:\n"
            "• Caratteri cinesi semplificati\n"
            "• Pinyin e pronuncia\n"
            "• Grammatica cinese\n"
            "• Cultura cinese\n\n"
            "⚠️ Funzionalità attualmente in fase di implementazione",
        )

    def handle_russian_button(self):
        """Gestisce il pulsante Russo - Funzionalità in sviluppo."""
        QMessageBox.information(
            self,
            "🇷🇺 Russo",
            "📚 Funzionalità Russo in Sviluppo\n\n"
            "🇷🇺 Questa sezione sarà dedicata a:\n"
            "• Alfabeto cirillico\n"
            "• Grammatica russa\n"
            "• Vocabolario essenziale\n"
            "• Letteratura russa\n\n"
            "⚠️ Funzionalità attualmente in fase di implementazione",
        )

    def eventFilter(self, a0, a1):
        """Event filter per intercettare eventi della tastiera e del mouse."""
        from PyQt6.QtCore import Qt, QEvent
        from PyQt6.QtGui import QMouseEvent

        # Handle all mouse events for tracking
        try:
            if a1 and hasattr(a1, "type"):
                event_type = getattr(a1, "type", lambda: None)()

                # Handle mouse button press events
                if event_type == QEvent.Type.MouseButtonPress:
                    event_button = getattr(a1, "button", lambda: None)()
                    self._handle_mouse_event(a0, "PRESS", event_button)

                # Handle mouse button release events
                elif event_type == QEvent.Type.MouseButtonRelease:
                    event_button = getattr(a1, "button", lambda: None)()
                    self._handle_mouse_event(a0, "RELEASE", event_button)

                # Handle mouse double click events
                elif event_type == QEvent.Type.MouseButtonDblClick:
                    event_button = getattr(a1, "button", lambda: None)()
                    self._handle_mouse_event(a0, "DOUBLE_CLICK", event_button)

                # Handle mouse wheel events
                elif event_type == QEvent.Type.Wheel:
                    delta = getattr(a1, "angleDelta", lambda: None)()
                    if delta:
                        if hasattr(delta, "y"):
                            direction = "SU" if delta.y() > 0 else "GIÙ"
                            self._handle_mouse_wheel(a0, direction)

        except Exception:
            logging.error("Errore in eventFilter mouse handling: {e}")

        # Gestisci solo eventi della tastiera - sezione pensierini rimossa

        # Per tutti gli altri casi, lascia che l'evento venga gestito normalmente
        return super().eventFilter(a0, a1)

    def _handle_mouse_event(self, widget, event_type, button):
        """Gestisce tutti gli eventi del mouse per identificare l'elemento e il tipo di evento."""
        try:
            if not hasattr(self, "click_status_label"):
                return

            # Get widget information
            widget_name = ""
            widget_type = ""

            if hasattr(widget, "objectName") and widget.objectName():
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
            if hasattr(self, "click_label_animation"):
                self.click_label_animation.start()

        except Exception as e:
            logging.error(f"Errore in _handle_mouse_event: {e}")
            if hasattr(self, "click_status_label"):
                self.click_status_label.setText("❌ Errore evento mouse")

    def _handle_mouse_wheel(self, widget, direction):
        """Gestisce gli eventi della rotella del mouse."""
        try:
            if not hasattr(self, "click_status_label"):
                return

            # Get widget information
            widget_name = ""
            if hasattr(widget, "objectName") and widget.objectName():
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
            if hasattr(self, "click_status_label"):
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
        if "button" in widget_name.lower() or widget_type == "QPushButton":
            return "🔘"
        elif "checkbox" in widget_name.lower() or widget_type == "QCheckBox":
            return "☑️"
        elif "lineedit" in widget_name.lower() or widget_type == "QLineEdit":
            return "📝"
        elif "textedit" in widget_name.lower() or widget_type == "QTextEdit":
            return "📄"
        elif "combobox" in widget_name.lower() or widget_type == "QComboBox":
            return "📋"
        elif "slider" in widget_name.lower() or widget_type == "QSlider":
            return "🎚️"
        elif "groupbox" in widget_name.lower() or widget_type == "QGroupBox":
            return "📁"
        elif "scrollarea" in widget_name.lower() or widget_type == "QScrollArea":
            return "📜"
        elif "splitter" in widget_name.lower() or widget_type == "QSplitter":
            return "📏"
        else:
            return "📦"

    def _handle_mouse_click(self, widget):
        """Gestisce i click del mouse per identificare l'elemento cliccato (legacy method)."""
        # This method is kept for backward compatibility but now uses the new system
        self._handle_mouse_event(widget, "PRESS", Qt.MouseButton.LeftButton)

    def add_text_from_input_area(self):
        """Aggiunge testo dall'area di input come pensierino - sezione pensierini rimossa."""
        # La sezione pensierini è stata completamente rimossa
        logging.info(
            "Funzione add_text_from_input_area non disponibile - sezione pensierini rimossa"
        )

    def _collect_work_area_text(self):
        """Raccoglie il testo dei pensierini presenti nell'Area di Lavoro (B)."""
        testi = []
        layout = getattr(self, "work_area_layout", None)
        if layout is None:
            return ""
        for i in range(layout.count()):
            item = layout.itemAt(i)
            w = item.widget() if item is not None else None
            if w is None:
                continue
            label = getattr(w, "text_label", None)
            if label is not None and hasattr(label, "text"):
                t = label.text().strip()
                if t:
                    testi.append(t)
            elif hasattr(w, "toPlainText"):
                t = w.toPlainText().strip()
                if t:
                    testi.append(t)
        return "\n".join(testi)

    def request_information_gesture(self):
        """Richiesta di informazione attivata dal gesto 'O' sull'Area di Lavoro.

        Raccoglie il contenuto dell'Area di Lavoro (B) e chiede all'AI di
        fornire informazioni; la risposta compare nella Lavagna AI (C).
        """
        contenuto = self._collect_work_area_text()
        if hasattr(self, "status_label") and self.status_label is not None:
            self.status_label.setText("Status: ℹ️ Richiesta informazione (gesto 'O')")

        if not contenuto:
            QMessageBox.information(
                self,
                "Richiesta informazione",
                "Metti dei pensierini nell'Area di Lavoro (B) e ripeti il gesto 'O'\n"
                "(indice e pollice a cerchio) per ricevere informazioni.",
            )
            return

        prompt = (
            "Fornisci informazioni utili e una spiegazione sintetica su quanto "
            "segue:\n" + contenuto
        )

        if getattr(self, "ollama_bridge", None) and self.ollama_bridge.checkConnection():
            try:
                model = get_setting("ai.selected_ai_model", "gemma:2b")
                self.ollama_bridge.sendPrompt(prompt, model)
                print("🤖 Richiesta informazione inviata all'AI dal gesto 'O'")
            except Exception as e:
                logging.warning(f"Errore invio richiesta informazione: {e}")
        else:
            QMessageBox.information(
                self,
                "Richiesta informazione",
                "Contenuto dell'Area di Lavoro:\n\n"
                + contenuto
                + "\n\n(AI non disponibile: avvia Ollama per ricevere una risposta.)",
            )

    def handle_ai_button(self):
        """Gestisce la funzione AI: invia richiesta a Ollama e mostra risposta."""
        # La sezione pensierini è stata rimossa, usa un dialogo per l'input
        text, ok = QInputDialog.getText(
            self, "Richiesta AI", "Inserisci la tua richiesta per l'AI:"
        )
        if not ok or not text.strip():
            return
        text = text.strip()

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
                ai_pensierino_text = f"🤖 {truncated_text}"
                pensierino_widget = DraggableTextWidget(
                    ai_pensierino_text, self.settings
                )
                self.pensierini_layout.addWidget(pensierino_widget)

            # Mostra richiesta nell'area risultati

            # Invia richiesta a Ollama con modello di default; se è una
            # richiesta di mappa/albero, la trasforma in elenco gerarchico.
            default_model = "gemma:2b"  # Modello raccomandato
            prompt_da_inviare = (
                self._graph_prompt(text) if self._is_graph_request(text) else text
            )
            self.ollama_bridge.sendPrompt(prompt_da_inviare, default_model)

            # Log dell'invio richiesta
            logging.info(
                f"Richiesta AI inviata: {text[:50]}... (modello: {default_model})"
            )

        except Exception as e:
            logging.error(f"Errore nell'invio richiesta AI: {e}")
            return

        # La sezione pensierini è stata rimossa - niente da pulire

    def show_text_in_details(self, full_text):
        """Mostra il testo completo nei dettagli con paginazione di 250 caratteri."""
        # Pulisci dettagli esistenti
        self._clear_details()

        # Crea widget per mostrare testo con paginazione
        self.create_paginated_text_widget(full_text)

    def create_paginated_text_widget(self, full_text):
        """Crea un widget con testo paginato per i dettagli."""
        from PyQt6.QtWidgets import (
            QVBoxLayout,
            QLabel,
            QPushButton,
            QHBoxLayout,
            QWidget,
        )

        # Carica preferenze font dalle impostazioni
        main_font_size = self.settings.get("fonts", {}).get("main_font_size", 13)
        page_button_font_size = (
            main_font_size - 1
        )  # Un po' più piccolo per il pulsante pagina

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
        self.details_text_label.setMinimumHeight(
            300
        )  # Circa 10 righe con font personalizzato
        # Imposta size policy per espansione massima
        from PyQt6.QtWidgets import QSizePolicy

        self.details_text_label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        # Rimuovi entrambe le scrollbar per massimizzare lo spazio
        self.details_text_label.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.details_text_label.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )

        # Usa dimensione font dalle preferenze per i dettagli
        details_font_size = main_font_size + 3  # Un po' più grande per i dettagli
        self.details_text_label.setStyleSheet(
            f"""
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


        """
        )

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
        rephrase_button_font_size = self.settings.get("fonts", {}).get(
            "main_font_size", 13
        )
        self.rephrase_button.setStyleSheet(
            f"""
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
        """
        )
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
        self.copy_button.setStyleSheet(
            f"""
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
        """
        )
        rephrase_layout.addWidget(self.copy_button)

        rephrase_layout.addWidget(self.rephrase_button)

        # Pulsante pagina non cliccabile (più compatto)
        self.page_info_label = QPushButton("Pag. 1")
        self.page_info_label.setObjectName("page_info_label")
        self.page_info_label.setEnabled(False)  # Non cliccabile

        # Usa dimensione font dalle preferenze per il pulsante pagina
        page_button_font_size = (
            self.settings.get("fonts", {}).get("main_font_size", 13) - 1
        )  # Un po' più piccolo per il pulsante pagina
        self.page_info_label.setStyleSheet(
            f"""
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
        """
        )
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
        details_splitter.setStyleSheet(
            """
            QSplitter::handle {
                background: rgba(108, 117, 125, 0.3);
                border-radius: 2px;
            }
            QSplitter::handle:hover {
                background: rgba(108, 117, 125, 0.6);
            }
        """
        )

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
        self.forward_button.setEnabled(
            True
        )  # Sempre abilitato (per tornare all'inizio)

    def _clear_details(self):
        """Pulisce la colonna dettagli."""
        try:
            while self.details_layout.count():
                item = self.details_layout.takeAt(0)
                if item:
                    widget = item.widget()
                    if widget and hasattr(widget, "deleteLater"):
                        widget.deleteLater()
        except Exception:
            logging.error("Errore pulizia dettagli: {e}")

    def handle_voice_button(self):
        """Avvia il riconoscimento vocale utilizzando il modulo Riconoscimento_Vocale."""
        if not SpeechRecognitionThread:
            QMessageBox.critical(
                self,
                "Errore",
                "Modulo di riconoscimento vocale non disponibile.\n\n"
                "Assicurati che le librerie 'vosk' e 'pyaudio' siano installate.",
            )
            return

        # Disabilita il pulsante durante il riconoscimento
        self.voice_button.setEnabled(False)
        self.voice_button.setText("🎤 In ascolto...")

        # Ottieni il modello Vosk dalle impostazioni
        vosk_model = self.settings.get("vosk_model", "vosk-model-it-0.22")

        # Se il modello non è configurato, usa quello italiano di default
        if not vosk_model or vosk_model == "auto":
            vosk_model = "vosk-model-it-0.22"

        # Verifica il modello: se manca, proponi il download in background
        # (nessun dialogo bloccante: l'app resta utilizzabile)
        vosk_model = self._resolve_vosk_model(vosk_model)
        if vosk_model is None:
            self.voice_button.setEnabled(True)
            self.voice_button.setText("🎤 Trascrivi la mia voce")
            return

        try:
            # Crea il thread di riconoscimento vocale con callback
            self.speech_thread = SpeechRecognitionThread(
                vosk_model, text_callback=self._on_voice_recognized
            )

            # Connetti i segnali come fallback
            self.speech_thread.recognized_text.connect(self._on_voice_recognized)
            self.speech_thread.recognition_error.connect(self._on_voice_error)
            self.speech_thread.stopped_by_silence.connect(
                self._on_voice_stopped_by_silence
            )
            self.speech_thread.finished.connect(self._on_voice_finished)

            # Avvia il riconoscimento
            self.speech_thread.start()

            QMessageBox.information(
                self,
                "Riconoscimento Vocale",
                "🎤 Riconoscimento vocale avviato!\n\n"
                "Parla chiaramente nel microfono.\n"
                "Il testo riconosciuto verrà aggiunto direttamente ai pensierini.\n"
                "Il riconoscimento si fermerà automaticamente dopo 3 secondi di silenzio.",
            )

        except Exception as e:
            show_user_friendly_error(self, e, "riconoscimento vocale")
            self.voice_button.setEnabled(True)
            self.voice_button.setText("🎤 Trascrivi la mia voce")

    def _on_voice_recognized(self, text):
        """Callback quando viene riconosciuto del testo vocale."""
        logging.info("🎤 _on_voice_recognized chiamata con testo: '{text}'")

        if text and text.strip():
            logging.info("📝 Testo valido ricevuto: '{text.strip()}'")

            # Verifica che l'UI sia completamente inizializzata
            if not hasattr(self, "pensierini_layout"):
                logging.warning(
                    "⚠️ pensierini_layout non ancora inizializzato - ritento più tardi"
                )
                # Ritarda l'operazione di 100ms per permettere l'inizializzazione dell'UI
                from PyQt6.QtCore import QTimer

                QTimer.singleShot(
                    100, lambda: self._add_recognized_text_to_pensierini(text.strip())
                )
                return

            # Inserisci il testo direttamente nella colonna dei pensierini
            if self.pensierini_layout:
                logging.info("✅ pensierini_layout disponibile")
                self._add_recognized_text_to_pensierini(text.strip())
            else:
                logging.error("❌ pensierini_layout è None")
                # Fallback: mostra in un messaggio
                QMessageBox.information(
                    self, "Testo Riconosciuto", f"Testo: {text.strip()}"
                )

    def _add_recognized_text_to_pensierini(self, text):
        """Aggiunge il testo riconosciuto ai pensierini in modo thread-safe."""
        try:
            # Crea un nuovo pensierino con il testo riconosciuto
            if DraggableTextWidget:
                widget = DraggableTextWidget(f"🎤 {text}", self.settings)
                self.pensierini_layout.addWidget(widget)
                logging.info(
                    f"✅ Widget creato e aggiunto ai pensierini: {text[:50]}..."
                )

                # Scroll automatico alla fine della colonna pensierini
                if hasattr(self, "pensierini_scroll") and self.pensierini_scroll:
                    scroll_bar = self.pensierini_scroll.verticalScrollBar()
                    if scroll_bar:
                        scroll_bar.setValue(scroll_bar.maximum())
            else:
                logging.error("❌ DraggableTextWidget non disponibile")
                QMessageBox.information(self, "Testo Riconosciuto", f"Testo: {text}")
        except Exception as e:
            logging.error(f"❌ Errore aggiunta testo ai pensierini: {e}")
            # Fallback: mostra in un messaggio
            QMessageBox.information(
                self, "Testo Riconosciuto", f"Testo: {text.strip()}"
            )
        else:
            logging.warning("⚠️ Testo vuoto o None ricevuto: '{text}'")

    def _on_voice_error(self, error_msg):
        """Callback per gestire errori del riconoscimento vocale."""
        QMessageBox.warning(
            self,
            "Errore Riconoscimento",
            "Errore durante il riconoscimento vocale:\n\n{error_msg}",
        )
        self._reset_voice_button()

    def _on_voice_stopped_by_silence(self):
        """Callback quando il riconoscimento si ferma per silenzio."""
        QMessageBox.information(
            self,
            "Riconoscimento Completato",
            "🎤 Riconoscimento vocale completato!\n\n"
            "Il sistema si è fermato automaticamente dopo 3 secondi di silenzio.",
        )
        self._reset_voice_button()

    def _on_voice_finished(self):
        """Callback quando il thread di riconoscimento finisce."""
        self._reset_voice_button()

    def _reset_voice_button(self):
        """Riporta il pulsante voce allo stato normale."""
        if hasattr(self, "voice_button"):
            self.voice_button.setEnabled(True)
            self.voice_button.setText("🎤 Trascrivi la mia voce")

    def handle_copy_button(self):
        """Copia tutto il testo dei dettagli negli appunti."""
        if not hasattr(self, "full_text") or not self.full_text:
            QMessageBox.warning(
                self, "Nessun Contenuto", "Non c'è contenuto da copiare nei dettagli."
            )
            return

        try:
            # Ottieni gli appunti dell'applicazione
            clipboard = QApplication.clipboard()
            if clipboard:
                clipboard.setText(self.full_text)
            else:
                QMessageBox.critical(
                    self,
                    "Errore Appunti",
                    "Impossibile accedere agli appunti del sistema.",
                )
                return

            # Mostra notifica di successo
            QMessageBox.information(
                self,
                "Copia Completata",
                "✅ Testo copiato negli appunti!\n\n"
                "📝 {len(self.full_text)} caratteri copiati",
            )

            logging.info("Testo copiato negli appunti: {len(self.full_text)} caratteri")

        except Exception:
            logging.error("Errore durante la copia: {e}")
            QMessageBox.critical(
                self, "Errore Copia", "Errore durante la copia del testo:\n{str(e)}"
            )

    def handle_rephrase_button(self):
        """Gestisce la riformulazione intensa del contenuto nei dettagli usando LLM."""
        if not hasattr(self, "full_text") or not self.full_text:
            QMessageBox.warning(
                self,
                "Nessun Contenuto",
                "Non c'è contenuto da riformulare nei dettagli.",
            )
            return

        # Controlla se il bridge Ollama è disponibile
        if not self.ollama_bridge:
            QMessageBox.critical(
                self,
                "AI Non Disponibile",
                "Il servizio AI non è disponibile. Verifica che Ollama sia installato e funzionante.",
            )
            return

        # Verifica connessione con Ollama
        if not self.ollama_bridge.checkConnection():
            QMessageBox.critical(
                self,
                "Connessione AI Fallita",
                "Impossibile connettersi al servizio AI Ollama.\n"
                "Assicurati che Ollama sia in esecuzione con: ollama serve",
            )
            return

        # Disabilita il pulsante durante l'elaborazione
        if hasattr(self, "rephrase_button"):
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
            default_model = "gemma:2b"  # Modello raccomandato
            self.ollama_bridge.sendPrompt(prompt, default_model)

            logging.info(
                f"Richiesta riformulazione inviata: {len(self.full_text)} caratteri (modello: {default_model})"
            )

        except Exception as e:
            logging.error(f"Errore nell'invio richiesta riformulazione: {e}")
            QMessageBox.critical(
                self, "Errore AI", f"Errore nell'invio della richiesta AI:\n{str(e)}"
            )
            # Riabilita il pulsante in caso di errore
            if hasattr(self, "rephrase_button"):
                self.rephrase_button.setEnabled(True)
                self.rephrase_button.setText("🧠 Riformula intensamente")

    def handle_media_button(self):
        """Gestisce il caricamento di file multimediali (audio/video)."""
        try:
            # Apri dialog per selezionare file
            file_dialog = QFileDialog(self)
            file_dialog.setWindowTitle("Seleziona file multimediale")
            file_dialog.setNameFilter(
                "File multimediali (*.mp3 *.wav *.mp4 *.avi *.mkv *.mov);;Audio (*.mp3 *.wav);;Video (*.mp4 *.avi *.mkv *.mov);;Tutti i file (*)"
            )

            if file_dialog.exec() == QFileDialog.DialogCode.Accepted:
                selected_files = file_dialog.selectedFiles()
                if selected_files:
                    file_path = selected_files[0]
                    self.process_media_file(file_path)

        except Exception:
            logging.error("Errore caricamento file multimediale: {e}")
            QMessageBox.critical(
                self, "Errore", "Errore durante il caricamento del file:\n{str(e)}"
            )

    def process_media_file(self, file_path):
        """Elabora il file multimediale selezionato."""
        import os
        from pathlib import Path

        file_name = os.path.basename(file_path)
        file_ext = Path(file_path).suffix.lower()

        # Determina il tipo di file
        audio_extensions = [".mp3", ".wav", ".flac", ".aac", ".ogg"]
        video_extensions = [".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv"]

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
            self.play_button.clicked.connect(
                lambda: self.toggle_audio_playback(file_path)
            )
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
            spectrum_label.setStyleSheet(
                "color: #666; font-style: italic; padding: 10px;"
            )
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
                wrapper_widget = DraggableTextWidget(
                    "🎵 Audio: {file_name}", self.settings
                )
                # Sostituisci il contenuto con il widget audio
                wrapper_layout = QVBoxLayout(wrapper_widget)
                wrapper_layout.addWidget(audio_widget)
                self.pensierini_layout.addWidget(wrapper_widget)

            QMessageBox.information(
                self,
                "File Audio Caricato",
                "✅ File audio '{file_name}' caricato con successo!\n\n"
                "🎵 Controlli multimediali disponibili\n"
                "📊 Analizzatore spettro in sviluppo",
            )

        except ImportError as e:
            QMessageBox.warning(
                self,
                "Funzionalità Limitata",
                "Alcune funzionalità audio potrebbero non essere disponibili:\n{str(e)}\n\n"
                "Il file è stato comunque aggiunto come elemento generico.",
            )
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
                wrapper_widget = DraggableTextWidget(
                    "🎥 Video: {file_name}", self.settings
                )
                wrapper_layout = QVBoxLayout(wrapper_widget)
                wrapper_layout.addWidget(video_widget)
                self.pensierini_layout.addWidget(wrapper_widget)

            QMessageBox.information(
                self,
                "File Video Caricato",
                "✅ File video '{file_name}' caricato con successo!",
            )

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
                wrapper_widget = DraggableTextWidget(
                    "📄 File: {file_name}", self.settings
                )
                wrapper_layout = QVBoxLayout(wrapper_widget)
                wrapper_layout.addWidget(generic_widget)
                self.pensierini_layout.addWidget(wrapper_widget)

            QMessageBox.information(
                self, "File Caricato", "✅ File '{file_name}' caricato con successo!"
            )

        except Exception:
            logging.error("Errore creazione widget generico: {e}")
            QMessageBox.critical(
                self, "Errore", "Errore durante la creazione del widget:\n{str(e)}"
            )

    def handle_ocr_button(self):
        """Gestisce la trascrizione OCR da documenti."""
        try:
            if not OCR_AVAILABLE:
                QMessageBox.warning(
                    self,
                    "OCR Non Disponibile",
                    "La funzionalità OCR richiede pytesseract e PIL.\n\n"
                    "Installa con: pip install pytesseract pillow\n\n"
                    "Inoltre assicurati che Tesseract-OCR sia installato sul sistema.",
                )
                return

            # Apri dialog per selezionare immagine/documento
            file_dialog = QFileDialog(self)
            file_dialog.setWindowTitle("Seleziona documento per OCR")
            file_dialog.setNameFilter(
                "Immagini e documenti (*.png *.jpg *.jpeg *.bmp *.tiff *.pdf);;Immagini (*.png *.jpg *.jpeg *.bmp *.tiff);;PDF (*.pdf);;Tutti i file (*)"
            )

            if file_dialog.exec() == QFileDialog.DialogCode.Accepted:
                selected_files = file_dialog.selectedFiles()
                if selected_files:
                    file_path = selected_files[0]
                    self.process_ocr_file(file_path)

        except Exception:
            logging.error("Errore caricamento file OCR: {e}")
            QMessageBox.critical(
                self, "Errore", "Errore durante il caricamento del file:\n{str(e)}"
            )

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
            if file_ext.lower() == ".pdf":
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
                    ocr_pensierino_text = (
                        "📄 OCR: {file_name[:30]}... ({len(text)} caratteri)"
                    )
                    pensierino_widget = DraggableTextWidget(
                        ocr_pensierino_text, self.settings
                    )
                    self.pensierini_layout.addWidget(pensierino_widget)

                QMessageBox.information(
                    self,
                    "OCR Completato",
                    "✅ Testo estratto con successo!\n\n"
                    "📄 File: {file_name}\n"
                    "📝 Caratteri: {len(text)}\n"
                    "📊 Parole: {len(text.split())}",
                )
            else:
                QMessageBox.warning(
                    self,
                    "OCR Fallito",
                    "Nessun testo rilevato nel documento.\n\n"
                    "Possibili cause:\n"
                    "• Immagine di bassa qualità\n"
                    "• Testo non chiaramente leggibile\n"
                    "• Orientamento del documento\n"
                    "• Carattere non supportato",
                )

        except Exception:
            if progress_msg is not None:
                progress_msg.close()
            logging.error("Errore OCR: {e}")
            QMessageBox.critical(
                self, "Errore OCR", "Errore durante l'elaborazione OCR:\n{str(e)}"
            )

    def extract_text_from_image(self, image_path):
        """Estrae testo da un'immagine usando VLM OCR o pytesseract come fallback."""
        try:
            # Prima prova con VLM OCR se disponibile
            if VLM_OCR_AVAILABLE and get_vlm_ocr:
                try:
                    vlm_ocr = get_vlm_ocr()
                    if vlm_ocr.is_available():
                        logging.info("Usando VLM OCR per estrazione testo")
                        result = vlm_ocr.extract_text(
                            image_path=image_path, language="ita+eng"
                        )

                        if result and result.get("text"):
                            text = result["text"]
                            logging.info(
                                f"VLM OCR completato: {len(text)} caratteri estratti"
                            )
                            return text
                        else:
                            logging.warning(
                                "VLM OCR non ha restituito testo, uso fallback"
                            )
                except Exception as e:
                    logging.warning(f"VLM OCR fallito, uso fallback: {e}")

            # Fallback a pytesseract tradizionale
            if not Image or not pytesseract:
                raise ImportError("PIL o pytesseract non disponibili")

            # Apri l'immagine
            image = Image.open(image_path)

            # Configurazione OCR ottimale
            custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyzàèéìòùÀÈÉÌÒÙ .,!?-()[]{}:;"\'\n'

            # Esegui OCR tradizionale
            text = pytesseract.image_to_string(
                image, lang="ita+eng", config=custom_config
            )

            logging.info(
                f"OCR tradizionale completato: {len(text.strip())} caratteri estratti"
            )
            return text.strip()

        except Exception as e:
            logging.error(f"Errore estrazione testo da immagine: {e}")
            raise

    def extract_text_from_pdf(self, pdf_path):
        """Estrae testo da un PDF (placeholder per implementazione futura)."""
        # Per ora restituiamo un messaggio che OCR su PDF non è ancora implementato
        return (
            "📄 OCR per PDF non ancora implementato.\n\n"
            "Converti prima il PDF in immagini per utilizzare l'OCR.\n\n"
            "Funzionalità futura: estrazione automatica immagini da PDF."
        )

    def handle_ocr_button(self):
        """Gestisce l'OCR avanzato usando VLM o fallback tradizionale."""
        try:
            # Verifica disponibilità OCR
            ocr_available = (
                VLM_OCR_AVAILABLE and get_vlm_ocr and get_vlm_ocr().is_available()
            ) or OCR_AVAILABLE

            if not ocr_available:
                QMessageBox.warning(
                    self,
                    "OCR Non Disponibile",
                    "La funzionalità OCR richiede:\n\n"
                    "• VLM OCR (raccomandato): Ollama con modello LLaVA\n"
                    "• OCR tradizionale: pytesseract e PIL\n\n"
                    "Installa con:\n"
                    "pip install pytesseract pillow\n\n"
                    "Per VLM OCR:\n"
                    "ollama pull llava-phi3",
                )
                return

            # Apri dialog per selezionare immagine/documento
            file_dialog = QFileDialog(self)
            file_dialog.setWindowTitle("Seleziona documento per OCR Avanzato")
            file_dialog.setNameFilter(
                "Immagini e documenti (*.png *.jpg *.jpeg *.bmp *.tiff *.pdf);;Immagini (*.png *.jpg *.jpeg *.bmp *.tiff);;PDF (*.pdf);;Tutti i file (*)"
            )

            if file_dialog.exec() == QFileDialog.DialogCode.Accepted:
                selected_files = file_dialog.selectedFiles()
                if selected_files:
                    file_path = selected_files[0]
                    self.process_ocr_file(file_path)

        except Exception as e:
            logging.error(f"Errore caricamento file OCR: {e}")
            QMessageBox.critical(
                self, "Errore", f"Errore durante il caricamento del file:\n{str(e)}"
            )

    def handle_audio_transcription_button(self):
        """Gestisce la trascrizione di file audio in testo."""
        try:
            if not AudioFileTranscriptionThread:
                QMessageBox.critical(
                    self,
                    "Errore",
                    "Modulo di trascrizione audio non disponibile.\n\n"
                    "Assicurati che le librerie 'vosk' e 'wave' siano installate.",
                )
                return

            # Apri dialog per selezionare file audio
            file_dialog = QFileDialog(self)
            file_dialog.setWindowTitle("Seleziona file audio per trascrizione")
            file_dialog.setNameFilter(
                "File audio (*.wav *.mp3 *.flac *.aac *.ogg);;WAV (*.wav);;MP3 (*.mp3);;FLAC (*.flac);;AAC (*.aac);;OGG (*.ogg);;Tutti i file (*)"
            )
            file_dialog.setFileMode(QFileDialog.FileMode.ExistingFile)

            if file_dialog.exec() == QFileDialog.DialogCode.Accepted:
                selected_files = file_dialog.selectedFiles()
                if selected_files:
                    audio_file_path = selected_files[0]
                    self.transcribe_audio_file(audio_file_path)

        except Exception:
            logging.error("Errore caricamento file audio: {e}")
            QMessageBox.critical(
                self, "Errore", "Errore durante il caricamento del file:\n{str(e)}"
            )

    def transcribe_audio_file(self, audio_file_path):
        """Trascrive un file audio in testo."""
        import os
        from pathlib import Path

        file_name = os.path.basename(audio_file_path)
        file_ext = Path(audio_file_path).suffix.lower()

        # Verifica formato supportato
        supported_formats = [".wav", ".mp3", ".flac", ".aac", ".ogg"]
        if file_ext not in supported_formats:
            QMessageBox.warning(
                self,
                "Formato Non Supportato",
                "Il formato '{file_ext}' non è attualmente supportato.\n\n"
                "Formati supportati: {', '.join(supported_formats)}\n\n"
                "Converti il file in uno dei formati supportati.",
            )
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
            vosk_model = self.settings.get("vosk_model", "vosk-model-it-0.22")

            # Se il modello non è configurato, usa quello italiano di default
            if not vosk_model or vosk_model == "auto":
                vosk_model = "vosk-model-it-0.22"

            # Verifica il modello: se manca, proponi il download in background
            # (nessun dialogo bloccante: l'app resta utilizzabile)
            vosk_model = self._resolve_vosk_model(vosk_model)
            if vosk_model is None:
                progress_msg.close()
                return

            progress_msg.close()

            # Mostra messaggio di inizio trascrizione
            QMessageBox.information(
                self,
                "Trascrizione Avviata",
                "🎵 Avvio trascrizione del file:\n{file_name}\n\n"
                "📝 Il testo trascritto verrà aggiunto ai pensierini.\n"
                "⏳ L'operazione potrebbe richiedere alcuni minuti...",
            )

            # Crea il thread di trascrizione
            if AudioFileTranscriptionThread:
                self.audio_transcription_thread = AudioFileTranscriptionThread(
                    audio_file_path,
                    vosk_model,
                    text_callback=self._on_audio_transcription_completed,
                )
            else:
                raise ImportError("AudioFileTranscriptionThread non disponibile")

            # Connetti i segnali
            self.audio_transcription_thread.transcription_progress.connect(
                self._on_transcription_progress
            )
            self.audio_transcription_thread.transcription_completed.connect(
                self._on_audio_transcription_completed
            )
            self.audio_transcription_thread.transcription_error.connect(
                self._on_transcription_error
            )

            # Avvia la trascrizione
            self.audio_transcription_thread.start()

        except Exception:
            if progress_msg is not None:
                progress_msg.close()
            logging.error("Errore avvio trascrizione: {e}")
            QMessageBox.critical(
                self, "Errore Avvio", "Errore nell'avvio della trascrizione:\n{str(e)}"
            )

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
                transcription_pensierino_text = (
                    "🎵 Trascrizione: {text[:50]}... ({len(text)} caratteri)"
                )
                pensierino_widget = DraggableTextWidget(
                    transcription_pensierino_text, self.settings
                )
                self.pensierini_layout.addWidget(pensierino_widget)

            QMessageBox.information(
                self,
                "Trascrizione Completata",
                "✅ Trascrizione completata con successo!\n\n"
                "🎵 File audio elaborato\n"
                "📝 Caratteri: {len(text)}\n"
                "📊 Parole: {len(text.split())}",
            )
        else:
            QMessageBox.warning(
                self,
                "Trascrizione Vuota",
                "La trascrizione non ha prodotto testo.\n\n"
                "Possibili cause:\n"
                "• File audio di bassa qualità\n"
                "• Audio senza parlato\n"
                "• Problemi di riconoscimento",
            )

    def _on_transcription_error(self, error_msg):
        """Gestisce gli errori della trascrizione."""
        logging.error("Errore trascrizione: {error_msg}")
        QMessageBox.critical(
            self,
            "Errore Trascrizione",
            "Errore durante la trascrizione:\n\n{error_msg}",
        )

    def handle_face_recognition(self):
        """Gestisce il toggle per il riconoscimento facciale."""
        try:
            if self.face_button.isChecked():
                # Abilita riconoscimento facciale
                self.face_button.setText("✅ Riconoscimento Faciale")
                QMessageBox.information(
                    self,
                    "Funzione in Sviluppo",
                    "🔧 Riconoscimento Faciale\n\n"
                    "📋 Stato: ABILITATO\n\n"
                    "⚠️ In Manutenzione - WIP Work in progress\n\n"
                    "Questa funzione sarà disponibile nelle prossime versioni.",
                )
            else:
                # Disabilita riconoscimento facciale
                self.face_button.setText("❌ Riconoscimento Faciale")
                QMessageBox.information(
                    self,
                    "Funzione Disabilitata",
                    "🔧 Riconoscimento Faciale\n\n"
                    "📋 Stato: DISABILITATO\n\n"
                    "La funzione è stata disabilitata.",
                )

        except Exception:
            logging.error("Errore toggle riconoscimento facciale: {e}")
            QMessageBox.critical(
                self,
                "Errore",
                "Errore durante la gestione del riconoscimento facciale:\n{str(e)}",
            )

    def handle_hand_gestures(self):
        """Gestisce il toggle per il riconoscimento gesti mani."""
        try:
            if self.hand_button.isChecked():
                # Abilita riconoscimento gesti mani
                self.hand_button.setText("✅ Abilita Gesti Mani")
                QMessageBox.information(
                    self,
                    "Funzione in Sviluppo",
                    "🔧 Riconoscimento Gesti Mani\n\n"
                    "📋 Stato: ABILITATO\n\n"
                    "⚠️ In Manutenzione - WIP Work in progress\n\n"
                    "Questa funzione sarà disponibile nelle prossime versioni.",
                )
            else:
                # Disabilita riconoscimento gesti mani
                self.hand_button.setText("❌ Abilita Gesti Mani")
                QMessageBox.information(
                    self,
                    "Funzione Disabilitata",
                    "🔧 Riconoscimento Gesti Mani\n\n"
                    "📋 Stato: DISABILITATO\n\n"
                    "La funzione è stata disabilitata.",
                )

        except Exception:
            logging.error("Errore toggle riconoscimento gesti mani: {e}")
            QMessageBox.critical(
                self,
                "Errore",
                "Errore durante la gestione del riconoscimento gesti mani:\n{str(e)}",
            )

    def _ipa_to_pronunciation_text(self, symbol):
        """Converte un simbolo IPA in testo pronunciabile per il TTS."""
        # Mappa dei simboli IPA a testi pronunciabili in italiano
        ipa_mapping = {
            # Vocali
            "[i]": "i come in mìle",
            "[e]": "e come in mèta",
            "[ɛ]": "e aperta come in mèta",
            "[a]": "a come in casa",
            "[ɔ]": "o aperta come in còrso",
            "[o]": "o come in còrso",
            "[u]": "u come in cùpa",
            # Consonanti
            "[p]": "p come in pane",
            "[b]": "b come in buono",
            "[t]": "t come in tavolo",
            "[d]": "d come in dono",
            "[k]": "c come in cane",
            "[g]": "g come in gatto",
            "[f]": "f come in fare",
            "[v]": "v come in vino",
            "[s]": "s come in sole",
            "[z]": "s sonora come in rosa",
            "[ʃ]": "sc come in scena",
            "[ʒ]": "j francese come in jour",
            "[m]": "m come in mamma",
            "[n]": "n come in nonna",
            "[ɲ]": "gn come in gnomo",
            "[l]": "l come in luna",
            "[ʎ]": "gl come in gli",
            "[r]": "r come in rosa",
            "[ʁ]": "r francese come in rouge",
            # Simboli speciali
            "[ˈ]": "accento principale",
            "[ˌ]": "accento secondario",
            "[.]": "sillaba",
            "[:]": "lunga",
            "[̯]": "semi vocale",
            "[̃]": "nasale",
            # Altri simboli comuni
            "[t͡s]": "z come in grazie",
            "[d͡z]": "z sonora come in zero",
            "[t͡ʃ]": "c come in cena",
            "[d͡ʒ]": "g come in giro",
        }

        # Rimuovi le parentesi quadre se presenti
        clean_symbol = symbol.strip("[]")

        # Cerca corrispondenza esatta
        if symbol in ipa_mapping:
            return ipa_mapping[symbol]

        # Cerca corrispondenza senza parentesi
        bracketed_symbol = f"[{clean_symbol}]"
        if bracketed_symbol in ipa_mapping:
            return ipa_mapping[bracketed_symbol]

        # Se non trovato, restituisci il simbolo pulito
        return clean_symbol

    def keyPressEvent(self, a0):
        """Gestisce gli eventi della tastiera per scorciatoie."""
        from PyQt6.QtCore import Qt

        try:
            # Controlla la combinazione Ctrl+F per toggle fullscreen
            if (
                a0
                and hasattr(a0, "key")
                and hasattr(a0, "modifiers")
                and a0.key() == Qt.Key.Key_F
                and a0.modifiers() & Qt.KeyboardModifier.ControlModifier
            ):
                self.toggle_fullscreen()
                if hasattr(a0, "accept"):
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
                    logging.info(
                        "Salvata dimensione originale: {self.original_width}x{self.original_height} at ({self.original_x}, {self.original_y})"
                    )

                # Entra in modalità fullscreen
                self.showFullScreen()
                self.is_fullscreen = True
                logging.info("Entrato in modalità fullscreen")

        except Exception:
            logging.error("Errore toggle fullscreen: {e}")
            QMessageBox.critical(
                self,
                "Errore Fullscreen",
                "Errore durante il cambio modalità schermo:\n{str(e)}",
            )

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

                logging.info(
                    "Ripristinate dimensioni originali: {self.original_width}x{self.original_height} at ({self.original_x}, {self.original_y})"
                )
            else:
                logging.warning("Nessuna dimensione originale da ripristinare")

        except Exception:
            logging.error("Errore ripristino dimensioni: {e}")

    def handle_log_toggle(self):
        """Gestisce il toggle del pulsante log per mostrare/nascondere il contenuto del log nei dettagli."""
        try:
            if self.log_button.isChecked():
                # Salva il contenuto attuale dei dettagli prima di sovrascriverlo
                if hasattr(self, "full_text"):
                    self.previous_details_content = self.full_text

                # Mostra il contenuto del log nei dettagli
                self.show_log_content()
                self.log_button.setText("📋 Log ✓")
            else:
                # Nasconde il contenuto del log (torna alla visualizzazione precedente o pulisce)
                if hasattr(self, "previous_details_content"):
                    self.show_text_in_details(self.previous_details_content)
                    delattr(self, "previous_details_content")
                else:
                    self._clear_details()
                self.log_button.setText("📋 Log")

        except Exception:
            logging.error("Errore toggle log: {e}")
            QMessageBox.critical(
                self, "Errore Log", "Errore durante il toggle del log:\n{str(e)}"
            )

    def show_log_content(self):
        """Mostra il contenuto del log nei dettagli."""
        try:
            from .main_03_configurazione_e_opzioni import get_config
            import os
            from datetime import datetime

            # Ottieni il percorso del file di log
            log_config = get_config()
            log_file = log_config.get_setting("files.log_file", "Save/LOG/app.log")

            if not os.path.exists(log_file):
                log_content = "📁 File log non trovato:\n{log_file}"
            else:
                # Leggi il file di log
                with open(log_file, "r", encoding="utf-8") as f:
                    log_content = f.read()

                # Filtra solo errori e warning
                lines = log_content.split("\n")
                filtered_lines = []

                for line in lines:
                    line_lower = line.lower()
                    if (
                        "error" in line_lower
                        or "warning" in line_lower
                        or "critical" in line_lower
                        or "exception" in line_lower
                    ):
                        filtered_lines.append(line)

                if not filtered_lines:
                    log_content = (
                        "📋 LOG ERRORI E WARNING\n\n"
                        "✅ Nessun errore o warning trovato nel log!\n\n"
                        "📁 File log: {log_file}\n"
                        "📊 Righe totali nel log: {len(lines)}\n"
                        "🔄 Ultimo aggiornamento: {datetime.now().strftime('%H:%M:%S')}"
                    )
                else:
                    log_content = (
                        "📋 LOG ERRORI E WARNING\n\n"
                        "🔍 Trovati {len(filtered_lines)} errori/warning:\n\n"
                        "{'=' * 60}\n\n"
                        "{chr(10).join(filtered_lines[-50:])}\n\n"
                        "{'=' * 60}\n\n"
                        "📁 File log: {log_file}\n"
                        "📊 Righe totali nel log: {len(lines)}\n"
                        "🔄 Ultimo aggiornamento: {datetime.now().strftime('%H:%M:%S')}"
                    )

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
            reply = QMessageBox.question(
                self,
                "Conferma Pulizia Log",
                "Sei sicuro di voler pulire il file di log?\n\n"
                "Questa azione rimuoverà tutti gli errori e warning registrati.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )

            if reply == QMessageBox.StandardButton.Yes:
                from .main_03_configurazione_e_opzioni import get_config

                log_config = get_config()
                log_file = log_config.get_setting("files.log_file", "Save/LOG/app.log")

                # Svuota il file di log
                with open(log_file, "w", encoding="utf-8") as f:
                    f.write(
                        "[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] INFO Log pulito dall'utente\n"
                    )

                # Log pulito, non è necessario aggiornare la visualizzazione
                QMessageBox.information(
                    self, "Log Pulito", "✅ File di log pulito con successo!"
                )

        except Exception:
            logging.error("Errore pulizia log: {e}")
            QMessageBox.critical(
                self,
                "Errore Pulizia Log",
                "Errore durante la pulizia del log:\n{str(e)}",
            )

    def hide_log_window(self):
        """Nasconde la visualizzazione del log nei dettagli."""
        try:
            # Nasconde il contenuto del log nei dettagli
            if hasattr(self, "log_button"):
                self.log_button.setChecked(False)
                # Torna alla visualizzazione precedente o pulisce
                if hasattr(self, "previous_details_content"):
                    self.show_text_in_details(self.previous_details_content)
                else:
                    self._clear_details()

        except Exception:
            logging.error("Errore nascondendo log: {e}")

    def toggle_audio_playback(self, file_path):
        """Alterna play/pausa per l'audio."""
        if hasattr(self, "media_player") and self.media_player and QMediaPlayer:
            try:
                if (
                    self.media_player.playbackState()
                    == QMediaPlayer.PlaybackState.PlayingState
                ):
                    self.media_player.pause()
                    if hasattr(self, "play_button"):
                        self.play_button.setText("▶️ Play")
                else:
                    self.media_player.play()
                    if hasattr(self, "play_button"):
                        self.play_button.setText("⏸️ Pausa")
            except Exception:
                logging.error("Errore toggle audio playback: {e}")

    def pause_audio(self):
        """Mette in pausa l'audio."""
        if hasattr(self, "media_player"):
            self.media_player.pause()
            if hasattr(self, "play_button"):
                self.play_button.setText("▶️ Play")

    def stop_audio(self):
        """Ferma l'audio."""
        if hasattr(self, "media_player"):
            self.media_player.stop()
            if hasattr(self, "play_button"):
                self.play_button.setText("▶️ Play")

    def update_position(self, position):
        """Aggiorna la posizione del slider."""
        if hasattr(self, "position_slider"):
            self.position_slider.setValue(position)

    def update_duration(self, duration):
        """Aggiorna la durata totale."""
        if hasattr(self, "position_slider"):
            self.position_slider.setRange(0, duration)
        if hasattr(self, "duration_label"):
            # Converti millisecondi in formato MM:SS
            total_seconds = duration // 1000
            minutes = total_seconds // 60
            seconds = total_seconds % 60
            self.duration_label.setText("00:00 / {minutes:02d}:{seconds:02d}")

    def set_position(self, position):
        """Imposta la posizione dell'audio."""
        if hasattr(self, "media_player"):
            self.media_player.setPosition(position)

    def handle_ipa_button(self):
        """Mostra un dialog con pulsanti interattivi per i simboli IPA e area clipboard."""
        try:
            # Crea il dialog IPA
            ipa_dialog = QDialog(self)
            ipa_dialog.setWindowTitle(
                "📝 Simboli IPA - Alfabeto Fonetico Internazionale"
            )
            ipa_dialog.setFixedSize(
                1200, 1000
            )  # Aumentato l'altezza per vedere nasalizzazione e suggerimento
            ipa_dialog.setStyleSheet(
                """
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
            """
            )

            # Layout principale con splitter
            main_layout = QVBoxLayout(ipa_dialog)

            # Titolo
            title = QLabel("📝 Simboli IPA Interattivi con Clipboard")
            title.setObjectName("title")
            main_layout.addWidget(title)

            # Descrizione
            desc = QLabel(
                "Clicca sui simboli IPA per copiarli negli appunti. Tutto quello che copi appare anche nell'area clipboard qui sotto per un riscontro immediato."
            )
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
                ("[u]", "cùpa"),
            ]

            for symbol, example in vocali_data:
                # Pulsante principale del simbolo (copia negli appunti)
                btn = QPushButton("{symbol}\n{example}")
                btn.setObjectName("ipa_symbol")
                btn.setToolTip(
                    "Esempio: '{example}' → trascrizione fonetica con {symbol}"
                )
                btn.clicked.connect(
                    lambda checked, s=symbol: self.copy_single_ipa_symbol_with_clipboard(
                        s, ipa_dialog
                    )
                )
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
                ("[v]", "vino"),
            ]

            for symbol, example in cons1_data:
                # Pulsante principale del simbolo (copia negli appunti)
                btn = QPushButton("{symbol}\n{example}")
                btn.setObjectName("ipa_symbol")
                btn.setToolTip(
                    "Esempio: '{example}' → trascrizione fonetica con {symbol}"
                )
                btn.clicked.connect(
                    lambda checked, s=symbol: self.copy_single_ipa_symbol_with_clipboard(
                        s, ipa_dialog
                    )
                )
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
                ("[l]", "luna"),
            ]

            for symbol, example in cons2_data:
                # Pulsante principale del simbolo (copia negli appunti)
                btn = QPushButton("{symbol}\n{example}")
                btn.setObjectName("ipa_symbol")
                btn.setToolTip(
                    "Esempio: '{example}' → trascrizione fonetica con {symbol}"
                )
                btn.clicked.connect(
                    lambda checked, s=symbol: self.copy_single_ipa_symbol_with_clipboard(
                        s, ipa_dialog
                    )
                )
                cons2_layout.addWidget(btn)

            cons2_layout.addStretch()
            scroll_layout.addLayout(cons2_layout)

            # Terza riga consonanti
            cons3_layout = QHBoxLayout()
            cons3_data = [("[ʎ]", "gli"), ("[r]", "raro"), ("[ʁ]", "r francese")]

            for symbol, example in cons3_data:
                # Pulsante principale del simbolo (copia negli appunti)
                btn = QPushButton("{symbol}\n{example}")
                btn.setObjectName("ipa_symbol")
                btn.setToolTip(
                    "Esempio: '{example}' → trascrizione fonetica con {symbol}"
                )
                btn.clicked.connect(
                    lambda checked, s=symbol: self.copy_single_ipa_symbol_with_clipboard(
                        s, ipa_dialog
                    )
                )
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
                ("[̃]", "nasalizzazione"),
            ]

            for symbol, example in speciali_data:
                # Pulsante principale del simbolo (copia negli appunti)
                btn = QPushButton("{symbol}\n{example}")
                btn.setObjectName("ipa_symbol")
                if symbol == "[ˈ]":
                    btn.setToolTip(
                        "Esempio: 'grazie' → [ˈɡrat.t͡sje] (accento primario sulla prima sillaba)"
                    )
                else:
                    btn.setToolTip("Esempio pratico con {symbol}: {example}")
                btn.clicked.connect(
                    lambda checked, s=symbol: self.copy_single_ipa_symbol_with_clipboard(
                        s, ipa_dialog
                    )
                )
                speciali_layout.addWidget(btn)

            speciali_layout.addStretch()
            scroll_layout.addLayout(speciali_layout)

            # SPIEGAZIONE
            info_label = QLabel(
                "💡 Guida all'utilizzo:\n\n"
                "• Utilizza questi simboli per trascrivere correttamente la pronuncia delle parole italiane\n"
                "• Passa il mouse sui pulsanti per vedere esempi pratici di utilizzo\n"
                "• Clicca sui simboli per copiarli negli appunti\n"
                "• Tutto quello che copi appare automaticamente nel clipboard sottostante\n\n"
                "🔍 Suggerimento: Inizia con le vocali e consonanti più comuni!"
            )
            info_label.setObjectName("section")
            info_label.setWordWrap(True)
            info_label.setStyleSheet(
                "font-size: 14px; color: #28a745; margin-top: 25px; margin-bottom: 15px; "
                "background-color: rgba(40, 167, 69, 0.1); padding: 15px; border-radius: 8px; "
                "border: 1px solid rgba(40, 167, 69, 0.3);"
            )
            scroll_layout.addWidget(info_label)

            # Imposta lo scroll
            scroll_area.setWidget(scroll_widget)
            scroll_area.setWidgetResizable(True)
            scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            scroll_area.setHorizontalScrollBarPolicy(
                Qt.ScrollBarPolicy.ScrollBarAsNeeded
            )
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
            self.clipboard_text.setPlaceholderText(
                "Qui appariranno tutti i simboli IPA che copi...\n\nInizia cliccando sui pulsanti sopra! 🎵"
            )
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
            QMessageBox.critical(
                self, "Errore", "Errore nell'apertura della guida IPA:\n{str(e)}"
            )

    def copy_single_ipa_symbol_with_clipboard(self, symbol, dialog):
        """Copia un singolo simbolo IPA negli appunti e aggiungilo al clipboard del dialog. Se TTS è abilitato, pronuncia anche il simbolo."""
        try:
            # Copia negli appunti di sistema
            clipboard = QApplication.clipboard()
            if clipboard:
                clipboard.setText(symbol)

            # Aggiungi al clipboard del dialog
            current_text = self.clipboard_text.toPlainText()
            if current_text and not current_text.endswith(" "):
                self.clipboard_text.setPlainText(current_text + symbol)
            else:
                self.clipboard_text.setPlainText(current_text + symbol)

            # Scorri automaticamente alla fine
            cursor = self.clipboard_text.textCursor()
            cursor.movePosition(cursor.MoveOperation.End)
            self.clipboard_text.setTextCursor(cursor)

            # Se TTS è abilitato, pronuncia il simbolo
            if hasattr(self, "tts_enabled") and self.tts_enabled:
                try:
                    # Converti il simbolo IPA in testo pronunciabile
                    pronunciation_text = self._ipa_to_pronunciation_text(symbol)

                    if pronunciation_text and TTS_AVAILABLE and TTSThread:
                        # Crea e avvia il thread TTS
                        tts_thread = TTSThread(
                            text=pronunciation_text,
                            engine_name="pyttsx3",  # Usa pyttsx3 per velocità
                            voice_or_lang="it",  # Voce italiana
                            speed=0.8,  # Più lento per chiarezza
                            pitch=1.0,
                        )

                        # Connetti segnali
                        tts_thread.started_reading.connect(
                            lambda: logging.info(
                                "🔊 Pronunciando simbolo IPA: {symbol}"
                            )
                        )
                        tts_thread.finished_reading.connect(
                            lambda: logging.info(
                                "✅ Pronuncia simbolo IPA completata: {symbol}"
                            )
                        )
                        tts_thread.error_occurred.connect(
                            lambda err: logging.error(
                                "❌ Errore pronuncia simbolo IPA {symbol}: {err}"
                            )
                        )

                        # Avvia la pronuncia
                        tts_thread.start()

                        # Salva riferimento per evitare garbage collection
                        if not hasattr(self, "_tts_threads"):
                            self._tts_threads = []
                        self._tts_threads.append(tts_thread)

                except Exception as tts_error:
                    logging.warning("Errore TTS per simbolo IPA {symbol}: {tts_error}")
                    # Non mostrare errori TTS per non interrompere l'esperienza utente

            # Rimossa la notifica popup per un'esperienza più fluida

        except Exception:
            logging.error("Errore copia simbolo IPA: {e}")
            QMessageBox.critical(
                dialog, "Errore Copia", "Errore durante la copia:\n{str(e)}"
            )

    def clear_clipboard(self):
        """Pulisce l'area clipboard."""
        try:
            self.clipboard_text.clear()
            self.clipboard_text.setPlaceholderText(
                "Clipboard pulito! 🎵\n\nInizia cliccando sui pulsanti sopra!"
            )
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
                    QMessageBox.information(
                        self,
                        "Clipboard Copiato",
                        "✅ Tutto il contenuto del clipboard copiato negli appunti!\n\n"
                        "📝 {len(content)} caratteri copiati",
                    )
            else:
                QMessageBox.warning(
                    self,
                    "Clipboard Vuoto",
                    "Il clipboard è vuoto. Clicca prima sui simboli IPA per riempirlo!",
                )
        except Exception:
            logging.error("Errore copia clipboard: {e}")
            QMessageBox.critical(
                self, "Errore Copia", "Errore durante la copia:\n{str(e)}"
            )

    def pronounce_ipa_symbol(self, symbol, dialog=None):
        """Pronuncia un simbolo IPA e lo aggiunge al clipboard del dialog."""
        try:
            # Prima copia il simbolo nel clipboard (se dialog è fornito)
            if dialog and hasattr(self, "clipboard_text"):
                # Copia negli appunti di sistema
                clipboard = QApplication.clipboard()
                if clipboard:
                    clipboard.setText(symbol)

                # Aggiungi al clipboard del dialog
                current_text = self.clipboard_text.toPlainText()
                if current_text and not current_text.endswith(" "):
                    self.clipboard_text.setPlainText(current_text + symbol)
                else:
                    self.clipboard_text.setPlainText(current_text + symbol)

                # Scorri automaticamente alla fine
                cursor = self.clipboard_text.textCursor()
                cursor.movePosition(cursor.MoveOperation.End)
                self.clipboard_text.setTextCursor(cursor)

            # Controlla se TTS è abilitato
            if not hasattr(self, "tts_enabled") or not self.tts_enabled:
                QMessageBox.information(
                    self,
                    "TTS Disabilitato",
                    "🔇 La sintesi vocale è attualmente disabilitata.\n\n"
                    "Clicca sul pulsante '🔇 TTS OFF' per riabilitarla.",
                )
                return

            if not TTS_AVAILABLE or not TTSThread:
                QMessageBox.warning(
                    self,
                    "TTS Non Disponibile",
                    "Il sistema di sintesi vocale non è disponibile.\n\n"
                    "Assicurati che le librerie 'pyttsx3' e 'gtts' siano installate.",
                )
                return

            # Converti il simbolo IPA in testo pronunciabile
            pronunciation_text = self._ipa_to_pronunciation_text(symbol)

            if not pronunciation_text:
                QMessageBox.warning(
                    self,
                    "Simbolo Non Supportato",
                    "Il simbolo '{symbol}' non ha una pronuncia definita.",
                )
                return

            # Crea e avvia il thread TTS
            # Converti il simbolo IPA in testo pronunciabile
            pronunciation_text = self._ipa_to_pronunciation_text(symbol)

            if not pronunciation_text:
                QMessageBox.warning(
                    self,
                    "Simbolo Non Supportato",
                    "Il simbolo '{symbol}' non ha una pronuncia definita.",
                )
                return

            # Crea e avvia il thread TTS
            tts_thread = TTSThread(
                text=pronunciation_text,
                engine_name="pyttsx3",  # Usa pyttsx3 per velocità
                voice_or_lang="it",  # Voce italiana
                speed=0.8,  # Più lento per chiarezza
                pitch=1.0,
            )

            # Connetti segnali
            tts_thread.started_reading.connect(
                lambda: logging.info("🔊 Pronunciando: {symbol}")
            )
            tts_thread.finished_reading.connect(
                lambda: logging.info("✅ Pronuncia completata: {symbol}")
            )
            tts_thread.error_occurred.connect(
                lambda err: logging.error("❌ Errore pronuncia {symbol}: {err}")
            )

            # Avvia la pronuncia
            tts_thread.start()

            # Salva riferimento per evitare garbage collection
            if not hasattr(self, "_tts_threads"):
                self._tts_threads = []
            self._tts_threads.append(tts_thread)

        except Exception:
            logging.error("Errore integrato pronuncia+copia IPA {symbol}: {e}")
            QMessageBox.critical(
                self, "Errore Integrato", "Errore durante copia e pronuncia:\n{str(e)}"
            )
            logging.error("Errore copia simbolo IPA: {e}")
            QMessageBox.critical(
                self, "Errore Copia", "Errore durante la copia:\n{str(e)}"
            )

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
                QMessageBox.information(
                    self,
                    "Guida Completa Copiata",
                    "✅ Tutti i simboli IPA copiati negli appunti!\n\n"
                    "Ora hai a disposizione la guida completa per le trascrizioni fonetiche.",
                )
        except Exception:
            logging.error("Errore copia tutti i simboli IPA: {e}")
            QMessageBox.critical(
                self, "Errore Copia", "Errore durante la copia:\n{str(e)}"
            )

    def copy_ipa_symbols(self, content):
        """Copia il contenuto IPA negli appunti."""
        try:
            clipboard = QApplication.clipboard()
            if clipboard:
                clipboard.setText(content)
                QMessageBox.information(
                    self,
                    "Copia Completata",
                    "✅ Contenuto IPA copiato negli appunti!\n\n"
                    "Ora puoi incollarlo dove necessario.",
                )
            else:
                QMessageBox.warning(
                    self,
                    "Errore Appunti",
                    "Impossibile accedere agli appunti del sistema.",
                )
        except Exception:
            logging.error("Errore copia IPA: {e}")
            QMessageBox.critical(
                self, "Errore Copia", "Errore durante la copia:\n{str(e)}"
            )

    def toggle_tts(self, button):
        """Abilita/disabilita la sintesi vocale per i simboli IPA."""
        try:
            self.tts_enabled = not self.tts_enabled

            if self.tts_enabled:
                button.setText("🔊 TTS ON")
                button.setStyleSheet(
                    """
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
                """
                )
                QMessageBox.information(
                    self,
                    "TTS Abilitato",
                    "🔊 Sintesi vocale abilitata!\n\n"
                    "Ora puoi cliccare sui pulsanti 🔊 accanto ai simboli IPA per sentirne la pronuncia.",
                )
            else:
                button.setText("🔇 TTS OFF")
                button.setStyleSheet(
                    """
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
                """
                )
                QMessageBox.information(
                    self,
                    "TTS Disabilitato",
                    "🔇 Sintesi vocale disabilitata!\n\n"
                    "I pulsanti 🔊 sono ora disattivati per risparmiare risorse.",
                )

        except Exception:
            logging.error("Errore toggle TTS: {e}")
            QMessageBox.critical(
                self, "Errore TTS", "Errore durante il cambio stato TTS:\n{str(e)}"
            )

    def handle_clean_button(self):
        """Gestisce la pulizia di tutti i widget con conferma utente."""
        # Mostra finestra di conferma
        reply = QMessageBox.question(
            self,
            "Conferma Pulizia",
            "Sei sicuro di voler cancellare tutto?\n\n"
            "Questa azione rimuoverà tutti i pensierini e il contenuto dell'area di lavoro.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,  # Default: No
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
                        if (
                            widget
                            and hasattr(widget, "deleteLater")
                            and callable(getattr(widget, "deleteLater", None))
                        ):
                            widget.deleteLater()
                    except (AttributeError, TypeError):
                        pass
            while self.work_area_layout.count():
                item = self.work_area_layout.takeAt(0)
                if item:
                    try:
                        widget = item.widget()
                        if (
                            widget
                            and hasattr(widget, "deleteLater")
                            and callable(getattr(widget, "deleteLater", None))
                        ):
                            widget.deleteLater()
                    except (AttributeError, TypeError):
                        pass
            logging.info("Area pulita")
        except Exception:
            logging.error("Errore pulizia area: {e}")

    def _suggest_project_name(self, project_data):
        """Deduce un nome per il progetto dal contenuto (primo testo utile)."""
        import re

        testo = ""
        for chiave in ("workspace", "pensierini"):
            for elem in project_data.get(chiave, []):
                t = (elem.get("text") or "").strip()
                if t:
                    testo = t
                    break
            if testo:
                break
        if not testo:
            return f"progetto_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        # Prime parole, ripulite per un nome file valido
        parole = re.sub(r"[^\w\s-]", "", testo).split()
        nome = "_".join(parole[:5]) or "progetto"
        return nome[:50]

    def save_project(self):
        """Salva il progetto: chiede dove salvarlo e deduce il nome dal contenuto."""
        from PyQt6.QtWidgets import QFileDialog

        self.save_button.setEnabled(False)
        self.save_button.setText("💾 Salvataggio...")

        try:
            # Prepara i dati da salvare (colonne A e B)
            project_data = {
                "metadata": {
                    "name": "",
                    "created": datetime.now().isoformat(),
                    "version": "1.0",
                },
                "pensierini": [],
                "workspace": [],
            }

            for i in range(self.pensierini_layout.count()):
                item = self.pensierini_layout.itemAt(i)
                widget = item.widget() if item else None
                text_label = getattr(widget, "text_label", None) if widget else None
                if text_label is not None and text_label.text().strip():
                    project_data["pensierini"].append(
                        {"text": text_label.text(), "order": i}
                    )

            for i in range(self.work_area_layout.count()):
                item = self.work_area_layout.itemAt(i)
                widget = item.widget() if item else None
                text_label = getattr(widget, "text_label", None) if widget else None
                if text_label is not None and text_label.text().strip():
                    project_data["workspace"].append(
                        {"text": text_label.text(), "order": i}
                    )

            # Nome dedotto dal contenuto (proposto come nome file predefinito)
            nome_suggerito = self._suggest_project_name(project_data)

            projects_dir = "Save/mia_dispenda_progetti"
            os.makedirs(projects_dir, exist_ok=True)
            default_path = os.path.join(projects_dir, f"{nome_suggerito}.json")

            # Chiede all'utente come/dove salvare
            filepath, _ = QFileDialog.getSaveFileName(
                self,
                "Salva progetto",
                default_path,
                "Progetto CogniFlow (*.json)",
            )
            if not filepath:
                return  # annullato
            if not filepath.lower().endswith(".json"):
                filepath += ".json"

            # Il nome del progetto è dedotto dal file scelto
            project_name = os.path.splitext(os.path.basename(filepath))[0]
            project_data["metadata"]["name"] = project_name

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(project_data, f, indent=2, ensure_ascii=False)

            QMessageBox.information(
                self,
                "Salvataggio Completato",
                f"Progetto '{project_name}' salvato con successo!\n\n"
                f"File: {os.path.basename(filepath)}\n"
                f"Pensierini: {len(project_data['pensierini'])}\n"
                f"Workspace: {len(project_data['workspace'])}",
            )
            self.set_status_message(f"💾 Progetto salvato: {project_name}")
            logging.info(f"Progetto salvato: {filepath}")

        except Exception as e:
            self.add_message(f"Errore durante il salvataggio: {e}", "error")
            QMessageBox.critical(
                self, "Errore Salvataggio", f"Errore durante il salvataggio:\n{e}"
            )
            logging.error(f"Errore salvataggio progetto: {e}")
        finally:
            self.save_button.setEnabled(True)
            self.save_button.setText("💾 Salva")

    def load_project(self):
        """Carica un progetto salvato (colonne 1 e 2)."""
        try:
            # Crea directory progetti se non esiste
            projects_dir = "Save/mia_dispenda_progetti"
            if not os.path.exists(projects_dir):
                os.makedirs(projects_dir, exist_ok=True)
                QMessageBox.information(
                    self, "Nessun Progetto", "Non ci sono progetti salvati."
                )
                return

            # Ottieni lista file progetti
            project_files = [f for f in os.listdir(projects_dir) if f.endswith(".json")]

            if not project_files:
                QMessageBox.information(
                    self, "Nessun Progetto", "Non ci sono progetti salvati."
                )
                return

            # Crea dialog per selezione progetto
            from PyQt6.QtWidgets import (
                QListWidget,
                QVBoxLayout,
                QDialog,
                QPushButton,
                QHBoxLayout,
            )

            dialog = QDialog(self)
            dialog.setWindowTitle("Seleziona Progetto da Caricare")
            dialog.resize(400, 300)

            layout = QVBoxLayout(dialog)

            # Lista progetti
            list_widget = QListWidget()
            for filename in sorted(project_files, reverse=True):
                try:
                    filepath = os.path.join(projects_dir, filename)
                    with open(filepath, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    if data:
                        name = data.get("metadata", {}).get("name", filename)
                        created = data.get("metadata", {}).get("created", "")
                        pens_count = len(data.get("pensierini", []))
                        work_count = len(data.get("workspace", []))

                        display_text = (
                            "{name} - {pens_count} pensierini, {work_count} workspace"
                        )
                        if created:
                            display_text += " ({created[:19]})"

                        list_widget.addItem(display_text)
                        item = list_widget.item(list_widget.count() - 1)
                        if item and hasattr(item, "setData"):
                            item.setData(Qt.ItemDataRole.UserRole, filepath)
                    else:
                        list_widget.addItem(filename)
                        item = list_widget.item(list_widget.count() - 1)
                        if item and hasattr(item, "setData"):
                            item.setData(
                                Qt.ItemDataRole.UserRole,
                                os.path.join(projects_dir, filename),
                            )

                except Exception:
                    list_widget.addItem(filename)
                    item = list_widget.item(list_widget.count() - 1)
                    if item and hasattr(item, "setData"):
                        item.setData(
                            Qt.ItemDataRole.UserRole,
                            os.path.join(projects_dir, filename),
                        )

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

            if (
                dialog.exec() == QDialog.DialogCode.Accepted
                and list_widget.currentItem()
            ):
                current_item = list_widget.currentItem()
                if current_item and hasattr(current_item, "data"):
                    selected_file = current_item.data(Qt.ItemDataRole.UserRole)
                else:
                    selected_file = None

                if selected_file:
                    # Conferma caricamento
                    reply = QMessageBox.question(
                        self,
                        "Conferma Caricamento",
                        "Caricare questo progetto? I dati attuali verranno sostituiti.",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    )

                    if reply == QMessageBox.StandardButton.Yes:
                        self._load_project_from_file(selected_file)
                else:
                    QMessageBox.warning(
                        self,
                        "Selezione Non Valida",
                        "Seleziona un progetto valido da caricare.",
                    )

        except Exception:
            QMessageBox.critical(
                self, "Errore Caricamento", "Errore durante il caricamento:\n{str(e)}"
            )
            logging.error("Errore caricamento progetto: {e}")

    def _load_project_from_file(self, filepath):
        """Carica progetto da file specifico."""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                project_data = json.load(f)

            if not project_data:
                raise ValueError("File progetto vuoto o corrotto")

            # Nome progetto (mostrato nello stato, il campo dedicato è stato rimosso)
            project_name = project_data.get("metadata", {}).get(
                "name", "Progetto Caricato"
            )
            self.set_status_message(f"📂 Progetto caricato: {project_name}")

            # Pulisci colonne esistenti
            self._clear_columns()

            # Carica pensierini (colonna 1)
            pensierini_data = project_data.get("pensierini", [])
            for pensierino in pensierini_data:
                if isinstance(pensierino, dict):
                    text = pensierino.get("text", "")
                    if text.strip() and DraggableTextWidget:
                        widget = DraggableTextWidget(text, self.settings)
                        self.pensierini_layout.addWidget(widget)

            # Carica workspace (colonna 2)
            workspace_data = project_data.get("workspace", [])
            for work_item in workspace_data:
                if isinstance(work_item, dict):
                    text = work_item.get("text", "")
                    if text.strip() and DraggableTextWidget:
                        widget = DraggableTextWidget(text, self.settings)
                        self.work_area_layout.addWidget(widget)

            QMessageBox.information(
                self,
                "Caricamento Completato",
                "Progetto '{project_name}' caricato con successo!\n\n"
                "Pensierini: {len(pensierini_data)}\n"
                "Workspace: {len(workspace_data)}",
            )

            logging.info("Progetto caricato: {filepath}")

        except Exception:
            QMessageBox.critical(
                self,
                "Errore Caricamento",
                "Errore durante il caricamento del file:\n{str(e)}",
            )
            logging.error("Errore caricamento file progetto: {e}")

    def _clear_columns(self):
        """Pulisce entrambe le colonne prima del caricamento."""
        try:
            # Pulisci colonna 1 (pensierini)
            while self.pensierini_layout.count():
                item = self.pensierini_layout.takeAt(0)
                if item:
                    widget = item.widget()
                    if (
                        widget
                        and hasattr(widget, "deleteLater")
                        and callable(getattr(widget, "deleteLater", None))
                    ):
                        widget.deleteLater()

            # Pulisci colonna 2 (workspace)
            while self.work_area_layout.count():
                item = self.work_area_layout.takeAt(0)
                if item:
                    widget = item.widget()
                    if (
                        widget
                        and hasattr(widget, "deleteLater")
                        and callable(getattr(widget, "deleteLater", None))
                    ):
                        widget.deleteLater()

            logging.info("Colonne pulite per caricamento progetto")

        except Exception:
            logging.error("Errore pulizia colonne: {e}")

    def logout(self):
        """Chiude la sessione e torna alla schermata di accesso."""
        reply = QMessageBox.question(
            self,
            "Esci dalla sessione",
            "Vuoi uscire e tornare alla schermata di accesso?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        # Segnala l'intenzione di riavviare dal login: l'avvio successivo
        # mostrerà l'accesso a prescindere dal bypass di comodo.
        self._logout_requested = True
        logging.info("Logout richiesto dall'utente")
        self.close()

    # === Osservazione dei momenti di difficoltà (genitori/clinici) ===

    def _difficulty_output_dir(self):
        return os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "Save",
            "Osservazioni_Riservate",
        )

    def _grab_interface(self):
        """Screenshot dell'interfaccia (non della webcam) come QPixmap."""
        try:
            return self.grab()
        except Exception:
            return None

    def _difficulty_context(self):
        """Breve descrizione di cosa sta facendo l'utente, per il registro."""
        try:
            stack = getattr(self, "footer_input_stack", None)
            if stack is not None:
                idx = stack.currentIndex()
                nomi = {
                    0: "scrittura testo",
                    1: "canvas (scrittura/disegno a mano)",
                    self._tools_page_index: "strumenti",
                    getattr(self, "_keyboard_page_index", None): "tastiera a schermo",
                }
                return nomi.get(idx, "area di lavoro")
        except Exception:
            pass
        return "area di lavoro"

    def _setup_difficulty_observer(self):
        """Crea l'osservatore leggendo le impostazioni (spento di default)."""
        self.difficulty_observer = None
        try:
            from core.difficulty_observer import DifficultyObserver
        except Exception as e:
            logging.warning(f"Osservazione difficoltà non disponibile: {e}")
            return
        enabled = bool(get_setting("observation.difficulty_capture_enabled", False))
        consent = bool(get_setting("observation.consent_given", False))
        self.difficulty_observer = DifficultyObserver(
            output_dir=self._difficulty_output_dir(),
            screenshot_provider=self._grab_interface,
            enabled=enabled and consent,
            threshold=float(get_setting("observation.threshold", 0.5)),
            cooldown_s=float(get_setting("observation.cooldown_s", 20.0)),
            retention_days=int(get_setting("observation.retention_days", 30)),
            context_provider=self._difficulty_context,
        )
        if enabled and consent:
            logging.info("Osservazione dei momenti di difficoltà: attiva")

    def refresh_difficulty_observer(self):
        """Rilegge le impostazioni (chiamata dopo il salvataggio del dialog)."""
        self._setup_difficulty_observer()
        # Se la webcam è già attiva, aggiorna al volo l'emissione del segnale
        vt = getattr(self, "video_thread_main", None)
        if vt is not None:
            obs = self.difficulty_observer
            active = obs is not None and obs.enabled
            vt.emit_difficulty = active
            try:
                vt.difficulty_signal.disconnect(self._on_difficulty_score)
            except (TypeError, RuntimeError):
                pass
            if active:
                vt.difficulty_signal.connect(self._on_difficulty_score)

    def _on_difficulty_score(self, score):
        obs = getattr(self, "difficulty_observer", None)
        if obs is not None:
            obs.on_difficulty(score)

    def open_settings(self):
        """Apre il dialog delle impostazioni."""
        if SettingsDialog is None:
            QMessageBox.critical(self, "Errore", "Modulo impostazioni non disponibile")
            return

        try:
            dialog = SettingsDialog(self)
            dialog.exec()
        except Exception as e:
            self.add_message(f"Errore nell'apertura delle impostazioni: {e}", "error")
            QMessageBox.critical(
                self, "Errore", f"Errore nell'apertura delle impostazioni: {e}"
            )

    # === Messaggi rapidi nel footer e registro messaggi/errori ===
    def set_status_message(self, text):
        """Mostra un messaggio veloce nel footer (es. caricamento, click)."""
        if hasattr(self, "click_status_label") and self.click_status_label is not None:
            self.click_status_label.setText(text)

    def add_message(self, text, level="info"):
        """Registra un messaggio/errore mostrabile dal pulsante 'Messaggi'."""
        from datetime import datetime

        entry = {
            "time": datetime.now().strftime("%H:%M:%S"),
            "level": level,
            "text": str(text),
        }
        if not hasattr(self, "app_messages"):
            self.app_messages = []
        self.app_messages.append(entry)
        # Riflette anche nello stato rapido del footer
        icona = {"error": "❌", "warning": "⚠️", "info": "ℹ️"}.get(level, "ℹ️")
        self.set_status_message(f"{icona} {text}")
        # Evidenzia il pulsante Messaggi se ci sono errori
        if level == "error" and hasattr(self, "messages_button"):
            self.messages_button.setText(f"✉️ Messaggi ({sum(1 for m in self.app_messages if m['level'] == 'error')})")

    def show_messages_dialog(self):
        """Mostra il registro dei messaggi/errori dell'applicazione."""
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QPushButton

        dialog = QDialog(self)
        dialog.setWindowTitle("✉️ Messaggi")
        dialog.resize(560, 400)
        layout = QVBoxLayout(dialog)

        view = QTextEdit()
        view.setReadOnly(True)
        if self.app_messages:
            righe = [
                f"[{m['time']}] {m['level'].upper()}: {m['text']}"
                for m in self.app_messages
            ]
            view.setPlainText("\n".join(righe))
        else:
            view.setPlainText("Nessun messaggio.")
        layout.addWidget(view)

        clear_btn = QPushButton("🗑️ Svuota")
        def _clear():
            self.app_messages.clear()
            view.setPlainText("Nessun messaggio.")
            if hasattr(self, "messages_button"):
                self.messages_button.setText("✉️ Messaggi")
        clear_btn.clicked.connect(_clear)
        layout.addWidget(clear_btn)

        close_btn = QPushButton("Chiudi")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        dialog.exec()

    def attach_documents(self):
        """Allega documenti come in un'email, con comportamento per tipo di file.

        - Se inserisci un qualsiasi audio io te lo trascrivo automaticamente offline
          (trascrizione locale con Vosk, nessun invio a server esterni).
        - Se inserisci un PDF lo mostro nell'Area di Lavoro (B) così possiamo
          analizzarlo insieme.
        - Gli altri file vengono aggiunti come pensierini nella colonna A.
        """
        from PyQt6.QtWidgets import QFileDialog
        import os

        files, _ = QFileDialog.getOpenFileNames(
            self, "Allega documenti", "", "Tutti i file (*.*)"
        )
        if not files:
            return

        audio_ext = {".wav", ".mp3", ".ogg", ".flac", ".m4a", ".aac", ".opus", ".wma"}
        image_ext = {".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif", ".gif", ".webp"}
        for path in files:
            ext = os.path.splitext(path)[1].lower()
            nome = os.path.basename(path)
            try:
                if ext in audio_ext:
                    # Se inserisci un qualsiasi audio io te lo trascrivo
                    # automaticamente offline
                    self._transcribe_audio_offline(path)
                elif ext == ".pdf":
                    # Se inserisci un PDF lo mostro nell'Area di Lavoro per
                    # analizzarlo insieme
                    self._show_pdf_in_work_area(path)
                elif ext in image_ext:
                    # Immagine: OCR locale (modelli Tesseract ita+eng)
                    self._ocr_image_offline(path)
                elif DraggableTextWidget and hasattr(self, "pensierini_layout"):
                    widget = DraggableTextWidget(f"📎 {nome}", self.settings)
                    self.pensierini_layout.addWidget(widget)
                    self.set_status_message(f"📎 Allegato: {nome}")
            except Exception as e:
                self.add_message(f"Errore allegando {nome}: {e}", "error")

    def _ocr_image_offline(self, path):
        """Estrae il testo da un'immagine con OCR locale e lo aggiunge come pensierino."""
        import os

        nome = os.path.basename(path)
        self.set_status_message(f"🔎 OCR offline di '{nome}'...")
        try:
            from core.document_tools import ocr_image

            testo = ocr_image(path)
        except Exception as e:
            self.add_message(f"OCR non disponibile per '{nome}': {e}", "error")
            return
        if not testo:
            self.set_status_message(f"🔎 '{nome}': nessun testo riconosciuto")
            return
        try:
            if DraggableTextWidget and hasattr(self, "pensierini_layout"):
                widget = DraggableTextWidget(f"🔎 {nome}:\n{testo}", self.settings)
                self.pensierini_layout.addWidget(widget)
        except Exception as e:
            self.add_message(f"Errore inserendo l'OCR: {e}", "error")
        self.set_status_message(f"✅ OCR di '{nome}' completato")
        self.add_message(f"OCR di '{nome}' completato", "info")

    def _transcribe_audio_offline(self, path):
        """Avvia la trascrizione offline (Vosk) di un file audio allegato."""
        import os

        nome = os.path.basename(path)
        self.set_status_message(f"🎙️ Trascrizione offline di '{nome}'...")
        self.add_message(f"Avvio trascrizione offline di '{nome}'", "info")

        try:
            from Artificial_Intelligence.Riconoscimento_Vocale.managers.speech_recognition_manager import (
                AudioFileTranscriptionThread,
            )
        except ImportError as e:
            self.add_message(f"Modulo di trascrizione non disponibile: {e}", "error")
            return

        # Converte in WAV 16kHz mono se necessario (mp3, ogg, ...)
        wav_path = self._ensure_wav_16k_mono(path)
        if wav_path is None:
            return

        vosk_model = self.settings.get("vosk_model", "vosk-model-small-it-0.22")
        if not vosk_model or vosk_model == "auto":
            vosk_model = "vosk-model-small-it-0.22"
        vosk_model = self._resolve_vosk_model(vosk_model)
        if vosk_model is None:
            self.add_message(
                "Nessun modello Vosk installato: scaricalo da Impostazioni → Download.",
                "error",
            )
            return

        thread = AudioFileTranscriptionThread(wav_path, vosk_model)
        thread.transcription_progress.connect(self.set_status_message)
        thread.transcription_completed.connect(
            lambda text, n=nome: self._on_audio_transcribed(n, text)
        )
        thread.transcription_error.connect(
            lambda err: self.add_message(f"Trascrizione: {err}", "error")
        )
        # Mantiene un riferimento per evitare la garbage collection
        if not hasattr(self, "_transcription_threads"):
            self._transcription_threads = []
        self._transcription_threads.append(thread)
        thread.start()

    def _on_audio_transcribed(self, nome, text):
        """Inserisce il testo trascritto come pensierino nella colonna A."""
        text = (text or "").strip()
        if not text:
            self.set_status_message(f"🎙️ '{nome}': nessun parlato riconosciuto")
            return
        try:
            if DraggableTextWidget and hasattr(self, "pensierini_layout"):
                widget = DraggableTextWidget(f"🎙️ {nome}: {text}", self.settings)
                self.pensierini_layout.addWidget(widget)
        except Exception as e:
            self.add_message(f"Errore inserendo la trascrizione: {e}", "error")
        self.set_status_message(f"✅ Trascrizione di '{nome}' completata")
        self.add_message(f"Trascrizione di '{nome}' completata", "info")

    def _ensure_wav_16k_mono(self, path):
        """Restituisce un WAV mono 16kHz; converte con pydub se necessario."""
        import os

        if path.lower().endswith(".wav"):
            return path  # la trascrizione gestisce mono/sample-rate
        try:
            import tempfile
            from pydub import AudioSegment

            seg = AudioSegment.from_file(path)
            seg = seg.set_channels(1).set_frame_rate(16000)
            tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
            seg.export(tmp.name, format="wav")
            return tmp.name
        except Exception as e:
            self.add_message(
                f"Impossibile convertire l'audio '{os.path.basename(path)}': {e}. "
                "Serve ffmpeg per i formati non-WAV.",
                "error",
            )
            return None

    def _show_pdf_in_work_area(self, path):
        """Mostra un PDF allegato nell'Area di Lavoro (B) per analizzarlo insieme.

        Estrae il testo con PyMuPDF; se il PDF è scansionato usa l'OCR locale.
        """
        import os

        nome = os.path.basename(path)
        self.set_status_message(f"📄 Lettura PDF '{nome}'...")
        testo = ""
        try:
            from core.document_tools import extract_pdf_text

            testo = extract_pdf_text(path)
        except Exception as e:
            self.add_message(f"Impossibile leggere il PDF '{nome}': {e}", "error")

        contenuto = f"📄 {nome}"
        if testo:
            anteprima = testo if len(testo) <= 4000 else testo[:4000] + "\n[...]"
            contenuto = f"📄 {nome}\n\n{anteprima}"
        try:
            if DraggableTextWidget and hasattr(self, "work_area_layout"):
                widget = DraggableTextWidget(contenuto, self.settings)
                setattr(widget, "attached_file_path", path)
                self.work_area_layout.addWidget(widget)
                self.set_status_message(f"📄 PDF '{nome}' aperto in Area di Lavoro")
                self.add_message(f"PDF '{nome}' mostrato in Area di Lavoro", "info")
            else:
                self.add_message(
                    "Area di Lavoro non disponibile per mostrare il PDF.", "error"
                )
        except Exception as e:
            self.add_message(f"Errore mostrando il PDF '{nome}': {e}", "error")

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
            if hasattr(self, "pensierini_layout") and self.pensierini_layout:
                pensierini_count = self.pensierini_layout.count()

            work_items_count = 0
            if hasattr(self, "work_area_layout") and self.work_area_layout:
                work_items_count = self.work_area_layout.count()

            # Stato del sistema
            ai_status = (
                "🟢"
                if (hasattr(self, "ollama_bridge") and self.ollama_bridge)
                else "🔴"
            )
            voice_status = "🟢" if SpeechRecognitionThread else "🔴"
            ocr_status = "🟢" if OCR_AVAILABLE else "🔴"

            # Messaggio dinamico basato sul contesto
            if pensierini_count > 0:
                status_text = f"🕐 {current_time} | 📝 {pensierini_count} pensierini | 🎯 {work_items_count} elementi | {ai_status} AI | {voice_status} Voce | {ocr_status} OCR"
            else:
                status_text = f"🕐 {current_time} | 🎨 CogniFlow pronto | Premi F1 per aiuto | {ai_status} AI | {voice_status} Voce | {ocr_status} OCR"

        except Exception as e:
            logging.error(f"Errore nell'aggiornamento del footer: {e}")

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
        if hasattr(self, "footer_timer"):
            self.footer_timer.stop()

        # Ferma l'ascolto vocale continuo se attivo
        if getattr(self, "wake_listener", None) is not None:
            try:
                self.wake_listener.stop()
            except Exception as e:
                logging.warning(f"Errore fermando l'ascolto continuo: {e}")
            self.wake_listener = None

        # Ferma la webcam integrata se attiva
        if getattr(self, "video_thread_main", None) is not None:
            try:
                self.video_thread_main.stop()
            except Exception as e:
                logging.warning(f"Errore fermando il thread video: {e}")
            self.video_thread_main = None

        # Chiama il metodo originale
        super().closeEvent(a0)

    def handle_arduino_button(self):
        """Gestisce il pulsante Risposta Arduino - Funzionalità in sviluppo."""
        QMessageBox.information(
            self,
            "🔌 Risposta Arduino",
            "🤖 Funzionalità Arduino in Sviluppo\n\n"
            "⚙️ Questa sezione sarà dedicata a:\n"
            "• Programmazione Arduino interattiva\n"
            "• Simulazione circuiti elettronici\n"
            "• Controllo dispositivi IoT\n"
            "• Progetti maker e robotica\n\n"
            "⚠️ Funzionalità attualmente in fase di implementazione",
        )

    def handle_circuit_button(self):
        """Gestisce il pulsante Circuito elettrico - Funzionalità in sviluppo."""
        QMessageBox.information(
            self,
            "⚡ Circuito elettrico",
            "🔌 Funzionalità Circuiti Elettrici in Sviluppo\n\n"
            "⚡ Questa sezione sarà dedicata a:\n"
            "• Simulazione circuiti elettrici\n"
            "• Analisi componenti elettronici\n"
            "• Progettazione schemi elettrici\n"
            "• Calcoli elettrici interattivi\n\n"
            "⚠️ Funzionalità attualmente in fase di implementazione",
        )

    def handle_graphics_tablet_button(self):
        """Apre la tavoletta per la scrittura a mano libera."""
        dialog = HandwritingTabletDialog(self)
        dialog.exec()
        if getattr(dialog, "saved_path", None):
            self.set_status_message(f"✍️ Scrittura salvata: {dialog.saved_path}")

    def handle_screen_share_button(self):
        """Gestisce il pulsante Condividi schermo - Funzionalità in sviluppo."""
        QMessageBox.information(
            self,
            "📺 Condividi schermo",
            "🎬 Funzionalità Condivisione Schermo in Sviluppo\n\n"
            "📺 Questa sezione sarà dedicata a:\n"
            "• Condivisione schermo con VLC\n"
            "• Streaming video in tempo reale\n"
            "• Registrazione sessioni di lavoro\n"
            "• Condivisione contenuti multimediali\n\n"
            "⚠️ Funzionalità attualmente in fase di implementazione",
        )

    def handle_collab_button(self):
        """Gestisce il pulsante Collabora Online - Funzionalità in sviluppo."""
        QMessageBox.information(
            self,
            "🤝 Collabora Online",
            "🌐 Funzionalità Collaborazione Online in Sviluppo\n\n"
            "🤝 Questa sezione sarà dedicata a:\n"
            "• Collaborazione in tempo reale\n"
            "• Condivisione progetti online\n"
            "• Lavoro di squadra remoto\n"
            "• Sincronizzazione contenuti\n\n"
            "⚠️ Funzionalità attualmente in fase di implementazione",
        )


def setup_logging():
    """Configura il sistema di logging."""
    log_config = get_config()
    if log_config and hasattr(log_config, 'get_setting'):
        log_file = log_config.get_setting("files.log_file", "Save/LOG/app.log")
    else:
        log_file = "Save/LOG/app.log"

    # Assicura che la directory dei log esista
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.FileHandler(log_file), logging.StreamHandler(sys.stdout)],
    )


def test_imports():
    """Test degli import critici."""
    print("🔍 Test degli import per Aircraft...")

    try:
        # Test import configurazione
        config = get_config()
        settings = load_settings()
        print(
            f"✓ Sistema configurazione caricato - Tema: {settings['application']['theme']}"
        )

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


def _run_event_loop(app):
    """Avvia l'event loop Qt, con profiling opzionale.

    Impostando la variabile d'ambiente COGNIFLOW_PROFILE=1 l'esecuzione viene
    profilata con cProfile: alla chiusura dell'app viene salvato un file .prof
    e stampato un riepilogo. Il nome del file si può scegliere con
    COGNIFLOW_PROFILE_OUT.

    Esempio:
        COGNIFLOW_PROFILE=1 ./avvia_cogniflow.sh
    Poi apri il report con:  snakeviz profilo_*.prof
    """
    if not os.environ.get("COGNIFLOW_PROFILE"):
        return app.exec()

    import cProfile
    import pstats
    from datetime import datetime

    out = os.environ.get("COGNIFLOW_PROFILE_OUT") or (
        f"profilo_{datetime.now():%Y%m%d_%H%M%S}.prof"
    )
    print(f"🔎 Profiling attivo (COGNIFLOW_PROFILE): report in '{out}' alla chiusura.")
    profiler = cProfile.Profile()
    profiler.enable()
    try:
        return app.exec()
    finally:
        profiler.disable()
        try:
            profiler.dump_stats(out)
            print(f"\n🔎 Profilo salvato in: {out}")
            print("   Primi 25 per tempo cumulativo:")
            pstats.Stats(profiler).sort_stats("cumulative").print_stats(25)
            print(f"   Apri con:  snakeviz {out}")
            print(
                f"   Oppure:    python3 -c \"import pstats; "
                f"pstats.Stats('{out}').sort_stats('tottime').print_stats(25)\""
            )
        except Exception as e:
            print(f"⚠️ Impossibile salvare il profilo: {e}")


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
        app.setApplicationName(settings.get("application", {}).get("app_name", "CogniFlow"))
        app.setOrganizationName("DSA Aircraft")
        print("QApplication created successfully")

        # Imposta icona se disponibile
        icon_path = "ICO-fonts-wallpaper/ICONA.ico"
        if os.path.exists(icon_path):
            from PyQt6.QtGui import QIcon

            app.setWindowIcon(QIcon(icon_path))
            logger.info("Icona caricata: {icon_path}")

        # Login all'avvio (disattivabile con Impostazioni → Bypass login).
        # Ciclo: dopo un logout si torna qui e si mostra di nuovo l'accesso.
        bypass_login = settings.get("startup", {}).get("bypass_login", False)
        while True:
            if not bypass_login:
                try:
                    from Autenticazione_e_Accesso.login_dialog import LoginDialog
                except ImportError:
                    from assistente_dsa.Autenticazione_e_Accesso.login_dialog import (
                        LoginDialog,
                    )
                login_dialog = LoginDialog()
                result = login_dialog.exec()
                if (
                    result != LoginDialog.DialogCode.Accepted.value
                    or login_dialog.authenticated_user is None
                ):
                    print("🔐 Login annullato: chiusura applicazione")
                    sys.exit(0)
                print(
                    f"🔐 Accesso effettuato: {login_dialog.authenticated_user['username']}"
                )

            print("About to create MainWindow...")
            # Crea e mostra finestra principale (Aircraft) a schermo intero
            window = MainWindow()
            print("MainWindow created successfully")
            window.showMaximized()

            logger.info("✓ Aircraft avviata con successo")
            print("✅ Aircraft - Schermata principale avviata!")

            # Avvia event loop (con profiling opzionale: COGNIFLOW_PROFILE=1)
            rc = _run_event_loop(app)

            if getattr(window, "_logout_requested", False):
                # L'utente ha scelto "Esci": torna alla schermata di accesso
                # (anche se il bypass era attivo, ora si chiede di nuovo).
                bypass_login = False
                window = None
                print("🚪 Logout: ritorno alla schermata di accesso")
                continue
            sys.exit(rc)

    except Exception as e:
        logger.error(f"Errore avvio Aircraft: {e}")
        print(f"❌ Errore avvio Aircraft: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
