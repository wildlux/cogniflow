#!/usr/bin/env python3
"""
Configurazioni e Opzioni - DSA Assistant
Modulo centralizzato per la gestione delle impostazioni dell'applicazione
"""

import json
import logging
import os
from typing import Any

# Import del cache manager per ottimizzazioni
try:
    from core.cache_manager import get_cache_manager
    cache_manager = get_cache_manager()
    CACHE_AVAILABLE = True
except ImportError:
    cache_manager = None
    CACHE_AVAILABLE = False

# Configurazione logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConfigManager:
    """Gestore centralizzato delle configurazioni dell'applicazione DSA."""

    def __init__(self, config_dir: str | None = None):
        if config_dir is None:
            # Usa il percorso assoluto della cartella Save principale
            self.config_dir: str = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Save", "SETUP_TOOLS_&_Data")
        else:
            self.config_dir = config_dir
        self.settings_file: str = os.path.join(self.config_dir, "settings.json")
        self.ensure_config_dir()
        self._cached_settings: dict[str, Any] | None = None
        self._settings_loaded = False

    def ensure_config_dir(self):
        """Assicura che la directory di configurazione esista."""
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir, exist_ok=True)
            logger.info(f"Directory configurazione creata: {self.config_dir}")

    def get_default_settings(self) -> dict[str, Any]:
        """Restituisce le impostazioni di default."""
        return {
            "application": {
                "app_name": "CogniFlow",
                "theme": "Chiaro",
                "interface_language": "Italiano",
                "version": "1.0.0"
            },
            "themes": {
                "available": [
                    {"name": "Professionale", "icon": "💼", "description": "Per professionisti e studenti universitari"},
                    {"name": "Studente", "icon": "🎒", "description": "Per ragazzi che vanno a scuola"},
                    {"name": "Chimico", "icon": "🥽", "description": "Per chimici o subacquei"},
                    {"name": "Donna", "icon": "👝", "description": "Per donne che hanno tutto in borsa"},
                    {"name": "Artigiano", "icon": "🧰", "description": "Per artigiani, cassetta degli attrezzi"},
                    {"name": "Specchio", "icon": "🪞", "description": "Tema specchio"},
                    {"name": "Magico", "icon": "🪄", "description": "Tema magico"},
                    {"name": "Pensieri", "icon": "💭", "description": "Tema pensieri"},
                    {"name": "Nuvola", "icon": "🗯", "description": "Tema nuvola"},
                    {"name": "Audio", "icon": "🔊", "description": "Tema audio"},
                    {"name": "Chat", "icon": "💬", "description": "Tema chat"}
                ],
                "selected": "Professionale"
            },
            "ui": {
                "window_width": 1200,
                "window_height": 800,
                "config_dialog_width": 1000,
                "config_dialog_height": 700,
                "widget_min_height": 60,
                "button_min_width": 120,
                "button_min_height": 40,
                "button_icon_position": "top-left",
                "button_text_position": "right",
                "tools_panel_visible": True
            },
            "fonts": {
                "main_font_family": "Arial",
                "main_font_size": 12,
                "pensierini_font_family": "Arial",
                "pensierini_font_size": 10,
                "default_font_size": 12,
                "default_pensierini_font_size": 10
            },
            "colors": {
                "button_text_colors": {
                    "options_button": "#ffffff",
                    "toggle_tools_button": "#ffffff",
                    "save_button": "#ffffff",
                    "load_button": "#ffffff",
                    "add_pensierino_button": "#ffffff",
                    "voice_button": "#ffffff",
                    "audio_transcription_button": "#ffffff",
                    "ocr_button": "#ffffff",
                    "graphics_tablet_button": "#ffffff",
                    "ai_button": "#ffffff",
                    "face_button": "#ffffff",
                    "hand_button": "#ffffff",
                    "ipa_button": "#ffffff",
                    "math_button": "#ffffff",
                    "chemistry_button": "#ffffff",
                    "physics_button": "#ffffff",
                    "biology_button": "#ffffff",
                    "italian_button": "#ffffff",
                    "history_button": "#ffffff",
                    "computer_science_button": "#ffffff",
                    "os_scripting_button": "#ffffff",
                    "astronomy_button": "#ffffff",
                    "advanced_math_button": "#ffffff",
                    "law_button": "#ffffff",
                    "probability_stats_button": "#ffffff",
                    "english_button": "#ffffff",
                    "german_button": "#ffffff",
                    "spanish_button": "#ffffff",
                    "sicilian_button": "#ffffff",
                    "japanese_button": "#ffffff",
                    "chinese_button": "#ffffff",
                    "russian_button": "#ffffff",
                    "media_button": "#ffffff",
                    "clean_button": "#ffffff",
                    "log_button": "#ffffff",
                    "arduino_button": "#ffffff",
                    "circuit_button": "#ffffff",
                    "screen_share_button": "#ffffff",
                    "collab_button": "#ffffff"
                },
                "button_border_colors": {
                    "general_border": "#495057",
                    "toggle_tools_border": "#495057",
                    "save_border": "#495057",
                    "load_border": "#495057",
                    "add_pensierino_border": "#495057"
                },
                "button_background_colors": {
                    "general_background": "transparent",
                    "toggle_tools_background": "transparent",
                    "save_background": "transparent",
                    "load_background": "transparent",
                    "add_pensierino_background": "transparent",
                    "tools_background": "transparent"
                },
                "button_hover_colors": {
                    "general_hover": "#e9ecef",
                    "toggle_tools_hover": "#e9ecef",
                    "save_hover": "#e9ecef",
                    "load_hover": "#e9ecef",
                    "add_pensierino_hover": "#e9ecef"
                },
                "button_pressed_colors": {
                    "general_pressed": "#dee2e6",
                    "toggle_tools_pressed": "#dee2e6",
                    "save_pressed": "#dee2e6",
                    "load_pressed": "#dee2e6",
                    "add_pensierino_pressed": "#dee2e6"
                }
            },
            "detection_systems": {
                "hand_detection_system": "Auto (Migliore)",
                "face_detection_system": "Auto (Migliore)",
                "gesture_system": "Auto (Migliore)",
                "hand_detection": True,
                "face_detection": True
            },
            "detection_parameters": {
                "hand_confidence": 50,
                "face_confidence": 50,
                "show_hand_landmarks": True,
                "show_expressions": True,
                "detect_glasses": True,
                "gesture_timeout": 3,
                "gesture_sensitivity": 5
            },
            "ai": {
                "ai_trigger": "++++",
                "selected_ai_model": "gemma:2b",
                "ollama_url": "http://localhost:11434",
                "ollama_timeout": 30,
                "ollama_temperature": 0.7,
                "ollama_max_tokens": 2000
            },
            "tts": {
                "tts_language": "it-IT",
                "tts_engine": "pyttsx3",
                "tts_speed": 1.0,
                "tts_pitch": 1.0,
                "tts_voice_or_lang": "it-IT"
            },
            "gpu": {
                "gpu_system": "Auto (Migliore)",
                "gpu_memory_limit": 80,
                "gpu_filters": True
            },
            "cpu_monitoring": {
                "cpu_monitoring_enabled": True,
                "cpu_threshold_percent": 95.0,
                "cpu_high_duration_seconds": 30,
                "cpu_check_interval_seconds": 5,
                "cpu_signal_type": "SIGTERM"
            },
            "temperature_monitoring": {
                "temperature_monitoring_enabled": True,
                "temperature_threshold_celsius": 80.0,
                "temperature_high_duration_seconds": 60,
                "temperature_critical_threshold": 90.0
            },
            "files": {
                "settings_file": os.path.join(os.path.dirname(os.path.dirname(__file__)), "Save", "SETUP_TOOLS_&_Data", "settings.json"),
                "log_file": os.path.join(os.path.dirname(os.path.dirname(__file__)), "Save", "LOG", "app.log"),
                "projects_dir": os.path.join(os.path.dirname(os.path.dirname(__file__)), "Save", "mia_dispenda_progetti")
            },
            "paths": {
                "save_dir": os.path.join(os.path.dirname(os.path.dirname(__file__)), "Save"),
                "log_dir": os.path.join(os.path.dirname(os.path.dirname(__file__)), "Save", "LOG"),
                "config_dir": os.path.join(os.path.dirname(os.path.dirname(__file__)), "Save", "SETUP_TOOLS_&_Data"),
                "projects_dir": os.path.join(os.path.dirname(os.path.dirname(__file__)), "Save", "mia_dispenda_progetti")
            },
            "startup": {
                "bypass_login": False,
                "auto_start_main_app": False
            },
            "mediapipe": {
                "service_enabled": True,
                "service_url": "http://localhost:8001",
                "detection_type": "Pose",
                "pose_detection_enabled": True,
                "hand_detection_enabled": True,
                "face_detection_enabled": False,
                "gesture_recognition_enabled": True,
                "facial_expression_enabled": False,
                "left_hand_tracking_enabled": False,
                "right_hand_tracking_enabled": True,
                "hand_confidence": 50,
                "face_confidence": 50,
                "gesture_timeout": 3,
                "gesture_sensitivity": 5,
                "show_hand_landmarks": True,
                "show_pose_landmarks": True,
                "show_expressions": True,
                "show_bounding_boxes": True,
                "detect_glasses": True,
                "human_min_area": 10000,
                "human_max_area": 300000,
                "skin_min_hue": 0,
                "skin_min_sat": 20,
                "skin_min_val": 70,
                "skin_max_hue": 20,
                "skin_max_sat": 255,
                "skin_max_val": 255
            },

        }

    def load_settings(self) -> dict[str, Any]:
        """Carica le impostazioni dal file JSON."""
        if self._settings_loaded and self._cached_settings is not None:
            return self._cached_settings

        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                logger.info(f"✓ Impostazioni caricate da: {self.settings_file}")
                self._cached_settings = settings
                self._settings_loaded = True
                return settings
            else:
                logger.warning(f"File impostazioni non trovato: {self.settings_file}")
                default_settings = self.create_default_settings()
                self._cached_settings = default_settings
                self._settings_loaded = True
                return default_settings
        except json.JSONDecodeError as e:
            logger.error(f"Errore parsing JSON: {e}")
            default_settings = self.create_default_settings()
            self._cached_settings = default_settings
            self._settings_loaded = True
            return default_settings
        except Exception as e:
            logger.error(f"Errore caricamento impostazioni: {e}")
            default_settings = self.create_default_settings()
            self._cached_settings = default_settings
            self._settings_loaded = True
            return default_settings

    def create_default_settings(self) -> dict[str, Any]:
        """Crea e salva le impostazioni di default."""
        default_settings = self.get_default_settings()
        self.save_settings(default_settings)
        logger.info(f"✓ Impostazioni di default create: {self.settings_file}")
        return default_settings

    def save_settings(self, settings: dict[str, Any]) -> bool:
        """Salva le impostazioni su file."""
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=4, ensure_ascii=False)
            logger.info("✓ Impostazioni salvate con successo")
            # Clear cache so next load_settings() will reload from disk
            self._cached_settings = None
            self._settings_loaded = False
            return True
        except Exception as e:
            logger.error(f"Errore salvataggio impostazioni: {e}")
            return False

    def get_setting(self, key_path: str, default: Any = None) -> Any:
        """Ottiene un'impostazione specifica usando la notazione con punti."""
        # Input validation
        if not key_path or not isinstance(key_path, str):
            logger.warning(f"Invalid key_path: {key_path}")
            return default

        # Prevent path traversal attacks
        if '..' in key_path or key_path.startswith('/') or '\\' in key_path:
            logger.error(f"Security violation: Suspicious key_path: {key_path}")
            return default

        settings = self.load_settings()
        keys = key_path.split('.')
        value: Any = settings

        try:
            for key in keys:
                if not isinstance(value, dict):
                    logger.warning(f"Invalid path structure at key '{key}' in path '{key_path}'")
                    return default
                value = value[key]
            return value
        except (KeyError, TypeError) as e:
            logger.debug(f"Setting not found: {key_path}, returning default: {default}")
            return default

    def set_setting(self, key_path: str, value: Any) -> bool:
        """Imposta un'impostazione specifica usando la notazione con punti."""
        # Input validation
        if not key_path or not isinstance(key_path, str):
            logger.error(f"Invalid key_path for set_setting: {key_path}")
            return False

        # Prevent path traversal attacks
        if '..' in key_path or key_path.startswith('/') or '\\' in key_path:
            logger.error(f"Security violation: Suspicious key_path for set_setting: {key_path}")
            return False

        settings = self.load_settings()
        keys = key_path.split('.')
        target: Any = settings

        try:
            # Naviga fino all'ultimo livello
            for key in keys[:-1]:
                if not isinstance(target, dict):
                    logger.error(f"Invalid path structure at key '{key}' in path '{key_path}'")
                    return False
                if key not in target:
                    target[key] = {}
                target = target[key]

            # Imposta il valore
            target[keys[-1]] = value
            return self.save_settings(settings)
        except Exception as e:
            logger.error(f"Errore impostazione {key_path}: {e}")
            return False

    def validate_settings(self, settings: dict[str, Any]) -> dict[str, Any]:
        """Valida e corregge le impostazioni caricate."""
        validated = settings.copy()
        defaults = self.get_default_settings()

        # Validazione dimensioni finestra
        if 'ui' not in validated:
            validated['ui'] = defaults['ui']

        ui_settings: Any = validated['ui']
        if 'window_width' in ui_settings:
            ui_settings['window_width'] = max(800, min(3000, ui_settings['window_width']))
        if 'window_height' in ui_settings:
            ui_settings['window_height'] = max(600, min(2000, ui_settings['window_height']))

        # Validazione confidenza rilevamento
        if 'detection_parameters' in validated:
            params: Any = validated['detection_parameters']
            if 'hand_confidence' in params:
                params['hand_confidence'] = max(1, min(100, params['hand_confidence']))
            if 'face_confidence' in params:
                params['face_confidence'] = max(1, min(100, params['face_confidence']))

        return validated

    def reset_to_defaults(self) -> bool:
        """Resetta tutte le impostazioni ai valori di default."""
        return True

    def export_settings(self, export_path: str) -> bool:
        """Esporta le impostazioni in un file specifico."""
        try:
            settings = self.load_settings()
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=4, ensure_ascii=False)
            logger.info(f"✓ Impostazioni esportate in: {export_path}")
            return True
        except Exception as e:
            logger.error(f"Errore esportazione impostazioni: {e}")
            return False

    def import_settings(self, import_path: str) -> bool:
        """Importa le impostazioni da un file specifico."""
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                settings = json.load(f)
            validated_settings = self.validate_settings(settings)
            return self.save_settings(validated_settings)
        except Exception as e:
            logger.error(f"Errore importazione impostazioni: {e}")
            return False


# Istanza globale del gestore configurazione
config_manager = ConfigManager()


def get_config() -> ConfigManager:
    """Restituisce l'istanza globale del gestore configurazione."""
    return config_manager


def load_settings() -> dict[str, Any]:
    """Funzione di comodo per caricare le impostazioni."""
    return config_manager.load_settings()


def save_settings(settings: dict[str, Any]) -> bool:
    """Funzione di comodo per salvare le impostazioni."""
    return config_manager.save_settings(settings)


def get_setting(key_path: str, default: Any = None) -> Any:
    """Funzione di comodo per ottenere un'impostazione specifica."""
    return config_manager.get_setting(key_path, default)


def set_setting(key_path: str, value: Any) -> bool:
    """Funzione di comodo per impostare un'impostazione specifica."""
    return config_manager.set_setting(key_path, value)


# Costanti derivate dalle impostazioni (per retrocompatibilità)
# Nota: Queste costanti sono mantenute per compatibilità ma si raccomanda
# di usare get_setting() per ottenere i valori aggiornati
window_width = 1200
window_height = 800
config_dialog_width = 1000
config_dialog_height = 700
widget_min_height = 60
default_font_size = 12
default_pensierini_font_size = 10
