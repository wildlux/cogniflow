#!/usr/bin/env python3
"""
Settings Model - Modello per gestire le impostazioni dell'applicazione
"""

import json
import os
from typing import Dict, Any, Optional
from main_03_configurazione_e_opzioni import load_settings, save_settings


class SettingsModel:
    """Modello per gestire le impostazioni dell'applicazione"""

    def __init__(self):
        self._settings = {}
        self._load_settings()

    def _load_settings(self):
        """Carica le impostazioni"""
        try:
            self._settings = load_settings()
        except Exception:
            # Fallback alle impostazioni di default
            self._settings = self._get_default_settings()

    def _get_default_settings(self) -> Dict[str, Any]:
        """Restituisce le impostazioni di default"""
        return {
            "application": {
                "app_name": "CogniFlow",
                "theme": "Chiaro",
                "interface_language": "Italiano",
                "version": "1.0.0",
            },
            "ui": {
                "window_width": 1200,
                "window_height": 800,
                "tools_panel_visible": True,
            },
            "fonts": {
                "main_font_family": "Arial",
                "main_font_size": 12,
                "pensierini_font_size": 10,
            },
            "colors": {
                "button_text_colors": {"general": "#000000"},
                "button_border_colors": {"general": "#000000"},
                "button_background_colors": {"general": "#FFFFFF"},
            },
            "ai": {
                "selected_ai_model": "gemma:2b",
                "ollama_url": "http://localhost:11434",
            },
            "tts": {"tts_language": "it-IT", "tts_engine": "pyttsx3"},
        }

    def get(self, key: str, default: Any = None) -> Any:
        """Ottiene un'impostazione usando la notazione con punti"""
        keys = key.split(".")
        value = self._settings

        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

    def set(self, key: str, value: Any):
        """Imposta un'impostazione usando la notazione con punti"""
        keys = key.split(".")
        settings = self._settings

        # Naviga fino all'ultimo livello
        for k in keys[:-1]:
            if k not in settings:
                settings[k] = {}
            settings = settings[k]

        # Imposta il valore
        settings[keys[-1]] = value

    def save(self) -> bool:
        """Salva le impostazioni"""
        try:
            return save_settings(self._settings)
        except Exception:
            return False

    def reload(self):
        """Ricarica le impostazioni"""
        self._load_settings()

    def get_all(self) -> Dict[str, Any]:
        """Restituisce tutte le impostazioni"""
        return self._settings.copy()

    def reset_to_defaults(self):
        """Resetta alle impostazioni di default"""
        self._settings = self._get_default_settings()
        self.save()
