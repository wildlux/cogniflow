#!/usr/bin/env python3
"""
CogniFlow Controller - Logica di business principale
Separazione della logica dall'interfaccia utente
"""

import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable

from PyQt6.QtCore import QObject, pyqtSignal, QTimer

# Import dei servizi
from ..services.ai_service import AIService
from ..services.tts_service import TTSService
from ..services.speech_recognition_service import SpeechRecognitionService
from ..services.ocr_service import OCRService
from ..services.media_service import MediaService
from ..services.project_service import ProjectService

# Import dei modelli
from ..models.project_model import ProjectModel
from ..models.settings_model import SettingsModel


class CogniFlowController(QObject):
    """
    Controller principale che gestisce tutta la logica di business
    separata dall'interfaccia utente
    """

    # Segnali per comunicazione con l'UI
    ai_response_received = pyqtSignal(str, str)  # prompt, response
    ai_error_occurred = pyqtSignal(str)  # error_msg
    speech_recognized = pyqtSignal(str)  # text
    ocr_completed = pyqtSignal(str)  # text
    tts_started = pyqtSignal()
    tts_finished = pyqtSignal()
    project_saved = pyqtSignal(str)  # project_name
    project_loaded = pyqtSignal(str)  # project_name
    error_occurred = pyqtSignal(str, str)  # error_type, message

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)

        # Inizializza i modelli
        self.settings = SettingsModel()
        self.current_project = ProjectModel()

        # Inizializza i servizi
        self._init_services()

        # Stato dell'applicazione
        self.ai_active = False
        self.speech_recognition_active = False
        self.tts_active = False

        self.logger.info("CogniFlow Controller inizializzato")

    def _init_services(self):
        """Inizializza tutti i servizi"""
        try:
            self.ai_service = AIService()
            self.tts_service = TTSService()
            self.speech_service = SpeechRecognitionService()
            self.ocr_service = OCRService()
            self.media_service = MediaService()
            self.project_service = ProjectService()

            # Connetti i segnali dei servizi
            self._connect_service_signals()

            self.logger.info("Tutti i servizi inizializzati con successo")
        except Exception as e:
            self.logger.error(f"Errore nell'inizializzazione dei servizi: {e}")
            self.error_occurred.emit("init_error", str(e))

    def _connect_service_signals(self):
        """Connette i segnali dei servizi ai segnali del controller"""
        # AI Service
        self.ai_service.response_received.connect(self.ai_response_received)
        self.ai_service.error_occurred.connect(self.ai_error_occurred)

        # Speech Recognition Service
        self.speech_service.text_recognized.connect(self.speech_recognized)

        # OCR Service
        self.ocr_service.text_extracted.connect(self.ocr_completed)

        # TTS Service
        self.tts_service.speech_started.connect(self.tts_started)
        self.tts_service.speech_finished.connect(self.tts_finished)

        # Project Service
        self.project_service.project_saved.connect(self.project_saved)
        self.project_service.project_loaded.connect(self.project_loaded)

    # ==================== AI METHODS ====================

    def send_ai_request(self, prompt: str, model: Optional[str] = None) -> bool:
        """Invia una richiesta all'AI"""
        try:
            if model is None:
                model = self.settings.get("ai.selected_ai_model", "gemma:2b")

            # Ensure model is not None
            if model is None:
                model = "gemma:2b"

            self.ai_active = True
            return self.ai_service.send_request(prompt, model)
        except Exception as e:
            self.logger.error(f"Errore nell'invio richiesta AI: {e}")
            self.error_occurred.emit("ai_error", str(e))
            return False

    def rephrase_text(self, text: str) -> bool:
        """Riformula il testo con AI"""
        prompt = f"Riformula intensamente il seguente testo mantenendo il significato ma migliorando lo stile e la chiarezza:\n\n{text}"
        return self.send_ai_request(prompt)

    # ==================== SPEECH METHODS ====================

    def start_speech_recognition(self) -> bool:
        """Avvia il riconoscimento vocale"""
        try:
            self.speech_recognition_active = True
            return self.speech_service.start_recognition()
        except Exception as e:
            self.logger.error(f"Errore nell'avvio riconoscimento vocale: {e}")
            self.error_occurred.emit("speech_error", str(e))
            return False

    def stop_speech_recognition(self) -> bool:
        """Ferma il riconoscimento vocale"""
        try:
            self.speech_recognition_active = False
            return self.speech_service.stop_recognition()
        except Exception as e:
            self.logger.error(f"Errore nell'arresto riconoscimento vocale: {e}")
            return False

    # ==================== TTS METHODS ====================

    def speak_text(self, text: str) -> bool:
        """Pronuncia il testo"""
        try:
            self.tts_active = True
            return self.tts_service.speak(text)
        except Exception as e:
            self.logger.error(f"Errore nella sintesi vocale: {e}")
            self.error_occurred.emit("tts_error", str(e))
            return False

    # ==================== OCR METHODS ====================

    def process_image_ocr(self, image_path: str) -> bool:
        """Elabora un'immagine con OCR"""
        try:
            return self.ocr_service.process_image(image_path)
        except Exception as e:
            self.logger.error(f"Errore nell'elaborazione OCR: {e}")
            self.error_occurred.emit("ocr_error", str(e))
            return False

    # ==================== MEDIA METHODS ====================

    def load_media_file(self, file_path: str) -> bool:
        """Carica un file multimediale"""
        try:
            return self.media_service.load_file(file_path)
        except Exception as e:
            self.logger.error(f"Errore nel caricamento file multimediale: {e}")
            self.error_occurred.emit("media_error", str(e))
            return False

    # ==================== PROJECT METHODS ====================

    def save_project(self, project_name: str, data: Dict[str, Any]) -> bool:
        """Salva un progetto"""
        try:
            self.current_project.name = project_name
            self.current_project.data = data
            self.current_project.last_modified = datetime.now()

            return self.project_service.save_project(self.current_project)
        except Exception as e:
            self.logger.error(f"Errore nel salvataggio progetto: {e}")
            self.error_occurred.emit("save_error", str(e))
            return False

    def load_project(self, project_name: str) -> Optional[Dict[str, Any]]:
        """Carica un progetto"""
        try:
            project = self.project_service.load_project(project_name)
            if project:
                self.current_project = project
                return project.data
            return None
        except Exception as e:
            self.logger.error(f"Errore nel caricamento progetto: {e}")
            self.error_occurred.emit("load_error", str(e))
            return None

    def get_available_projects(self) -> List[str]:
        """Restituisce la lista dei progetti disponibili"""
        try:
            return self.project_service.get_project_list()
        except Exception as e:
            self.logger.error(f"Errore nel recupero lista progetti: {e}")
            return []

    # ==================== SETTINGS METHODS ====================

    def get_setting(self, key: str, default: Any = None) -> Any:
        """Ottiene un'impostazione"""
        return self.settings.get(key, default)

    def set_setting(self, key: str, value: Any) -> bool:
        """Imposta un'impostazione"""
        try:
            self.settings.set(key, value)
            return True
        except Exception as e:
            self.logger.error(f"Errore nell'impostazione: {e}")
            return False

    # ==================== UTILITY METHODS ====================

    def cleanup(self):
        """Pulisce le risorse"""
        try:
            # Ferma tutti i servizi attivi
            if self.speech_recognition_active:
                self.stop_speech_recognition()

            if self.tts_active:
                self.tts_service.stop()

            # Salva le impostazioni
            self.settings.save()

            self.logger.info("Cleanup completato")
        except Exception as e:
            self.logger.error(f"Errore durante il cleanup: {e}")

    def get_status_info(self) -> Dict[str, Any]:
        """Restituisce informazioni di stato del sistema"""
        return {
            "ai_active": self.ai_active,
            "speech_active": self.speech_recognition_active,
            "tts_active": self.tts_active,
            "current_project": (
                self.current_project.name if self.current_project.name else None
            ),
            "services_status": {
                "ai": self.ai_service.is_available(),
                "speech": self.speech_service.is_available(),
                "tts": self.tts_service.is_available(),
                "ocr": self.ocr_service.is_available(),
            },
        }
