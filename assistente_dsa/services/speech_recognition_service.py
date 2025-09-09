#!/usr/bin/env python3
"""
Speech Recognition Service - Gestione del riconoscimento vocale
"""

import logging
from typing import Optional
from PyQt6.QtCore import QObject, pyqtSignal

# Import del speech recognition manager esistente
try:
    from Artificial_Intelligence.Riconoscimento_Vocale.managers.speech_recognition_manager import (
        SpeechRecognitionThread
    )
    SPEECH_AVAILABLE = True
except ImportError:
    SpeechRecognitionThread = None
    SPEECH_AVAILABLE = False


class SpeechRecognitionService(QObject):
    """
    Servizio per gestire il riconoscimento vocale
    """

    # Segnali
    text_recognized = pyqtSignal(str)  # recognized_text
    recognition_started = pyqtSignal()
    recognition_stopped = pyqtSignal()
    error_occurred = pyqtSignal(str)  # error_msg

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)

        self.recognition_thread = None
        self._is_recognizing = False

        if SPEECH_AVAILABLE:
            self.logger.info("Speech Recognition Service inizializzato")
        else:
            self.logger.warning("Speech Recognition non disponibile - servizio limitato")

    def start_recognition(self) -> bool:
        """Avvia il riconoscimento vocale"""
        if not SPEECH_AVAILABLE:
            error_msg = "Servizio di riconoscimento vocale non disponibile"
            self.logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            return False

        try:
            # Ferma eventuali riconoscimenti in corso
            self.stop_recognition()

            # Crea un nuovo thread di riconoscimento
            self.recognition_thread = SpeechRecognitionThread()

            # Connetti i segnali (da implementare nel thread esistente)
            # self.recognition_thread.text_recognized.connect(self._on_text_recognized)
            # self.recognition_thread.started.connect(self._on_recognition_started)
            # self.recognition_thread.finished.connect(self._on_recognition_stopped)

            # Avvia il riconoscimento
            self.recognition_thread.start()
            self._is_recognizing = True
            self.recognition_started.emit()
            self.logger.info("Riconoscimento vocale avviato")
            return True

        except Exception as e:
            error_msg = f"Errore nell'avvio riconoscimento vocale: {str(e)}"
            self.logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            return False

    def stop_recognition(self) -> bool:
        """Ferma il riconoscimento vocale"""
        try:
            if self.recognition_thread and hasattr(self.recognition_thread, 'isRunning') and self.recognition_thread.isRunning():
                self.recognition_thread.stop()
                self.recognition_thread.wait()
                self.logger.info("Riconoscimento vocale fermato")

            self._is_recognizing = False
            self.recognition_stopped.emit()
            return True
        except Exception as e:
            self.logger.error(f"Errore nell'arresto riconoscimento vocale: {e}")
            return False

    def _on_text_recognized(self, text: str):
        """Gestisce il testo riconosciuto"""
        self.logger.info(f"Testo riconosciuto: {text[:50]}...")
        self.text_recognized.emit(text)

    def _on_recognition_started(self):
        """Gestisce l'inizio del riconoscimento"""
        self._is_recognizing = True
        self.recognition_started.emit()

    def _on_recognition_stopped(self):
        """Gestisce la fine del riconoscimento"""
        self._is_recognizing = False
        self.recognition_stopped.emit()

    def is_recognizing(self) -> bool:
        """Verifica se è in corso un riconoscimento vocale"""
        return self._is_recognizing

    def is_available(self) -> bool:
        """Verifica se il servizio di riconoscimento vocale è disponibile"""
        return SPEECH_AVAILABLE

    def get_available_languages(self) -> list:
        """Restituisce la lista delle lingue disponibili"""
        if not SPEECH_AVAILABLE:
            return []

        try:
            # Lista delle lingue supportate
            return ["it-IT", "en-US", "es-ES", "fr-FR", "de-DE"]
        except Exception as e:
            self.logger.error(f"Errore recupero lingue: {e}")
            return []

    def cleanup(self):
        """Pulisce le risorse del servizio di riconoscimento vocale"""
        try:
            self.stop_recognition()
            self.logger.info("Speech Recognition Service cleanup completato")
        except Exception as e:
            self.logger.error(f"Errore durante cleanup Speech Recognition Service: {e}")