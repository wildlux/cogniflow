# constants.py - Costanti e impostazioni di default per l'applicazione

from typing import Dict, Any

# Impostazioni di default dell'applicazione
DEFAULT_SETTINGS: Dict[str, Any] = {
    'app_name': 'CogniFlow',
    'theme': 'Chiaro',
    'main_font_family': 'OpenDyslexic',
    'main_font_size': 14,
    'pensierini_font_family': 'OpenDyslexic',
    'pensierini_font_size': 12,
    'hand_detection_system': 'Auto (Migliore)',
    'face_detection_system': 'Auto (Migliore)',
    'gesture_system': 'Auto (Migliore)',
    'hand_confidence': 50,
    'face_confidence': 50,
    'show_hand_landmarks': True,
    'show_expressions': True,
    'detect_glasses': True,
    'gesture_timeout': 3,
    'gesture_sensitivity': 5,
    'gpu_system': 'Auto (Migliore)',
    'gpu_memory_limit': 80,
    'gpu_filters': True,
    'interface_language': 'Italiano',
    'tts_language': 'it-IT',
    'tts_engine': 'pyttsx3',
    'tts_speed': 1.0,
    'tts_pitch': 1.0,
    'ai_trigger': '++++',
    'cpu_monitoring_enabled': True,
    'cpu_threshold_percent': 95.0,
    'cpu_high_duration_seconds': 30,
    'cpu_check_interval_seconds': 5,
    'cpu_signal_type': 'SIGTERM',
    'temperature_monitoring_enabled': True,
    'temperature_threshold_celsius': 80.0,
    'temperature_high_duration_seconds': 60,
    'temperature_critical_threshold': 90.0,
    'hand_detection': True,
    'face_detection': True,
    'selected_ai_model': 'gemma:2b',
    'button_icon_position': 'top-left',
    'button_text_position': 'right',
    'button_min_width': 120,
    'button_min_height': 40
}

# Costanti dell'applicazione
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800
CONFIG_DIALOG_WIDTH = 1000
CONFIG_DIALOG_HEIGHT = 700
WIDGET_MIN_HEIGHT = 60
DEFAULT_FONT_SIZE = 14
DEFAULT_PENSIERINI_FONT_SIZE = 12

# File di configurazione
SETTINGS_FILE = "Save/SETUP_TOOLS_&_Data/settings.json"
LOG_FILE = "Save/LOG/app.log"
