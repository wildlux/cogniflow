#!/usr/bin/env python3
"""
TTS Service - Gestione della sintesi vocale
"""

import logging
from typing import Optional
from PyQt6.QtCore import QObject, pyqtSignal, QThread

# Import del TTS manager esistente
try:
    from Artificial_Intelligence.Sintesi_Vocale.managers.tts_manager import TTSThread
    TTS_AVAILABLE = True
except ImportError:
    TTSThread = None
    TTS_AVAILABLE = False


class TTSService(QObject):
    """
    Servizio per gestire la sintesi vocale
    """

    # Segnali
    speech_started = pyqtSignal()
    speech_finished = pyqtSignal()
    error_occurred = pyqtSignal(str)  # error_msg

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)

        self.tts_thread = None
        self._is_speaking = False

        if TTS_AVAILABLE:
            self.logger.info("TTS Service inizializzato")
        else:
            self.logger.warning("TTS non disponibile - servizio limitato")

    def speak(self, text: str) -> bool:
        """Pronuncia il testo specificato"""
        if not TTS_AVAILABLE:
            error_msg = "Servizio TTS non disponibile"
            self.logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            return False

        if not text or not text.strip():
            error_msg = "Testo vuoto o non valido"
            self.logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            return False

        try:
            # Ferma eventuali sintesi in corso
            self.stop()

            # Crea un nuovo thread TTS
            self.tts_thread = TTSThread(text.strip())

            # Connetti i segnali
            self.tts_thread.speech_started.connect(self._on_speech_started)
            self.tts_thread.speech_finished.connect(self._on_speech_finished)
            self.tts_thread.error_occurred.connect(self._on_error_occurred)

            # Avvia la sintesi
            self.tts_thread.start()
            self.logger.info(f"Sintesi vocale avviata per testo: {text[:50]}...")
            return True

        except Exception as e:
            error_msg = f"Errore nell'avvio sintesi vocale: {str(e)}"
            self.logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            return False

    def stop(self) -> bool:
        """Ferma la sintesi vocale in corso"""
        try:
            if self.tts_thread and self.tts_thread.isRunning():
                self.tts_thread.stop()
                self.tts_thread.wait()  # Aspetta che il thread finisca
                self.logger.info("Sintesi vocale fermata")
            self._is_speaking = False
            return True
        except Exception as e:
            self.logger.error(f"Errore nell'arresto sintesi vocale: {e}")
            return False

    def _on_speech_started(self):
        """Gestisce l'inizio della sintesi vocale"""
        self._is_speaking = True
        self.speech_started.emit()
        self.logger.debug("Sintesi vocale iniziata")

    def _on_speech_finished(self):
        """Gestisce la fine della sintesi vocale"""
        self._is_speaking = False
        self.speech_finished.emit()
        self.logger.debug("Sintesi vocale completata")

    def _on_error_occurred(self, error_msg: str):
        """Gestisce gli errori della sintesi vocale"""
        self._is_speaking = False
        self.logger.error(f"Errore TTS: {error_msg}")
        self.error_occurred.emit(error_msg)

    def is_speaking(self) -> bool:
        """Verifica se è in corso una sintesi vocale"""
        return self._is_speaking

    def is_available(self) -> bool:
        """Verifica se il servizio TTS è disponibile"""
        return TTS_AVAILABLE

    def get_available_voices(self) -> list:
        """Restituisce la lista delle voci disponibili"""
        if not TTS_AVAILABLE:
            return []

        try:
            # Qui dovremmo implementare la logica per ottenere le voci disponibili
            # Per ora restituiamo una lista di default
            return ["it-IT", "en-US", "es-ES", "fr-FR", "de-DE"]
        except Exception as e:
            self.logger.error(f"Errore recupero voci TTS: {e}")
            return []

    def cleanup(self):
        """Pulisce le risorse del servizio TTS"""
        try:
            self.stop()
            self.logger.info("TTS Service cleanup completato")
        except Exception as e:
            self.logger.error(f"Errore durante cleanup TTS Service: {e}")