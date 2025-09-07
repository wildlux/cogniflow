# settings_manager.py - Gestore centralizzato delle impostazioni
"""
Modulo per la gestione centralizzata delle impostazioni dell'applicazione.
Tutte le costanti e configurazioni vengono caricate dal file settings.json.
"""

import json
from typing import Dict, Any, Optional


class SettingsManager:
    """Gestore centralizzato delle impostazioni dell'applicazione."""

    # Impostazioni di default
    DEFAULT_SETTINGS: Dict[str, Any] = {
        "app_name": "CogniFlow",
        "theme": "Chiaro",
        "main_font_family": "OpenDyslexic",
        "main_font_size": 14,
        "main_font_weight": "Normale",
        "pensierini_font_family": "OpenDyslexic",
        "pensierini_font_size": 12,
        "pensierini_font_weight": "Normale",
        "hand_detection_system": "Auto (Migliore)",
        "face_detection_system": "Auto (Migliore)",
        "gesture_system": "Auto (Migliore)",
        "hand_confidence": 50,
        "face_confidence": 50,
        "show_hand_landmarks": True,
        "show_expressions": True,
        "detect_glasses": True,
        "gesture_timeout": 3,
        "gesture_sensitivity": 5,
        "gpu_system": "Auto (Migliore)",
        "gpu_memory_limit": 80,
        "gpu_filters": True,
        "interface_language": "Italiano",
        "tts_language": "it-IT",
        "tts_engine": "pyttsx3",
        "tts_speed": 1.0,
        "tts_pitch": 1.0,
        "ai_trigger": "++++",
        "hand_detection": True,
        "face_detection": True,
        "selected_ai_model": "gemma:2b",
        "cpu_monitoring_enabled": True,
        "cpu_threshold_percent": 95.0,
        "cpu_high_duration_seconds": 30,
        "cpu_check_interval_seconds": 5,
        "cpu_signal_type": "SIGTERM",
        "temperature_monitoring_enabled": True,
        "temperature_threshold_celsius": 80.0,
        "temperature_high_duration_seconds": 60,
        "temperature_critical_threshold": 90.0,
        "button_icon_position": "top-left",
        "button_text_position": "right",
        "button_min_width": 120,
        "button_min_height": 40,
        "window_width": 1200,
        "window_height": 800,
        "config_dialog_width": 1000,
        "config_dialog_height": 700,
        "widget_min_height": 60,
        "default_font_size": 12,
        "default_pensierini_font_size": 10,
        "settings_file": os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "Save", "SETUP_TOOLS_&_Data", "settings.json"),
        "log_file": "Save/LOG/app.log"
    }

    def __init__(self):
        self._settings = {}
        self._settings_file = None
        self._load_settings()

    def _load_settings(self) -> None:
        """Carica le impostazioni dal file JSON."""
        # Usa il percorso assoluto del file settings principale
        self._settings_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "Save", "SETUP_TOOLS_&_Data", "settings.json")

        try:
            if os.path.exists(self._settings_file):
                with open(self._settings_file, 'r', encoding='utf-8') as f:
                    loaded_settings = json.load(f)
                # Unisci le impostazioni caricate con quelle di default
                self._settings = {**self.DEFAULT_SETTINGS, **loaded_settings}
                print("✓ Impostazioni caricate da: {self._settings_file}")
            else:
                print("⚠️ File impostazioni non trovato: {self._settings_file}")
                print("   Creazione impostazioni di default...")
                self._settings = self.DEFAULT_SETTINGS.copy()
                self._save_settings()
        except json.JSONDecodeError as e:
            print("✗ Errore parsing settings.json: {e}")
            print("   Utilizzo impostazioni di default...")
            self._settings = self.DEFAULT_SETTINGS.copy()
        except Exception:
            print("✗ Errore caricamento impostazioni: {e}")
            print("   Utilizzo impostazioni di default...")
            self._settings = self.DEFAULT_SETTINGS.copy()

    def _save_settings(self) -> None:
        """Salva le impostazioni nel file JSON."""
        if not self._settings_file:
            return

        try:
            os.makedirs(os.path.dirname(self._settings_file), exist_ok=True)
            with open(self._settings_file, 'w', encoding='utf-8') as f:
                json.dump(self._settings, f, indent=4, ensure_ascii=False)
            print("✓ Impostazioni salvate in: {self._settings_file}")
        except Exception:
            print("✗ Errore salvataggio impostazioni: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """Ottiene il valore di una impostazione."""
        return self._settings.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Imposta il valore di una impostazione."""
        self._settings[key] = value
        self._save_settings()

    def get_all(self) -> Dict[str, Any]:
        """Restituisce tutte le impostazioni."""
        return self._settings.copy()

    def update(self, settings: Dict[str, Any]) -> None:
        """Aggiorna multiple impostazioni."""
        self._settings.update(settings)
        self._save_settings()

    def reset_to_defaults(self) -> None:
        """Ripristina le impostazioni di default."""
        self._settings = self.DEFAULT_SETTINGS.copy()
        self._save_settings()

    # Proprietà specifiche per accesso diretto
    @property
    def window_width(self) -> int:
        return self.get('window_width', 1200)

    @property
    def window_height(self) -> int:
        return self.get('window_height', 800)

    @property
    def config_dialog_width(self) -> int:
        return self.get('config_dialog_width', 1000)

    @property
    def config_dialog_height(self) -> int:
        return self.get('config_dialog_height', 700)

    @property
    def widget_min_height(self) -> int:
        return self.get('widget_min_height', 60)

    @property
    def default_font_size(self) -> int:
        return self.get('default_font_size', 12)

    @property
    def default_pensierini_font_size(self) -> int:
        return self.get('default_pensierini_font_size', 10)

    @property
    def main_font_weight(self) -> str:
        return self.get('main_font_weight', 'Normale')

    @property
    def pensierini_font_weight(self) -> str:
        return self.get('pensierini_font_weight', 'Normale')

    @property
    def app_name(self) -> str:
        return self.get('app_name', 'CogniFlow')

    @property
    def settings_file(self) -> str:
        return self._settings_file or os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "Save", "SETUP_TOOLS_&_Data", "settings.json")

    @property
    def log_file(self) -> str:
        return self.get('log_file', "Save/LOG/app.log")


# Istanza globale del gestore impostazioni
settings_manager = SettingsManager()

# Per compatibilità con il codice esistente
DEFAULT_SETTINGS = settings_manager.get_all()
WINDOW_WIDTH = settings_manager.window_width
WINDOW_HEIGHT = settings_manager.window_height
CONFIG_DIALOG_WIDTH = settings_manager.config_dialog_width
CONFIG_DIALOG_HEIGHT = settings_manager.config_dialog_height
WIDGET_MIN_HEIGHT = settings_manager.widget_min_height
DEFAULT_FONT_SIZE = settings_manager.default_font_size
DEFAULT_PENSIERINI_FONT_SIZE = settings_manager.default_pensierini_font_size
SETTINGS_FILE = settings_manager.settings_file
LOG_FILE = settings_manager.log_file
