#!/usr/bin/env python3
"""
AI Service - Gestione delle funzionalità AI (Ollama)
"""

import logging
from typing import Optional
from PyQt6.QtCore import QObject, pyqtSignal

# Import del bridge Ollama esistente
try:
    from Artificial_Intelligence.Ollama.ollama_bridge import OllamaBridge
    OLLAMA_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Impossibile importare OllamaBridge: {e}")
    OllamaBridge = None
    OLLAMA_AVAILABLE = False


class AIService(QObject):
    """
    Servizio per gestire le funzionalità AI tramite Ollama
    """

    # Segnali
    response_received = pyqtSignal(str, str)  # prompt, response
    error_occurred = pyqtSignal(str)  # error_msg
    connection_status_changed = pyqtSignal(bool)  # connected

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)

        # Inizializza il bridge Ollama
        if OLLAMA_AVAILABLE and OllamaBridge is not None:
            self.ollama_bridge = OllamaBridge()
        else:
            self.ollama_bridge = None
        self._connected = False

        if self.ollama_bridge:
            # Connetti i segnali del bridge
            self.ollama_bridge.responseReceived.connect(self._on_response_received)
            self.ollama_bridge.errorOccurred.connect(self._on_error_occurred)
            self.logger.info("AI Service inizializzato con Ollama")
        else:
            self.logger.warning("Ollama non disponibile - servizio AI limitato")

    def _on_response_received(self, prompt: str, response: str):
        """Gestisce la risposta ricevuta da Ollama"""
        self.logger.info(f"Risposta AI ricevuta per prompt: {prompt[:50]}...")
        self.response_received.emit(prompt, response)

    def _on_error_occurred(self, error_msg: str):
        """Gestisce gli errori da Ollama"""
        self.logger.error(f"Errore AI: {error_msg}")
        self.error_occurred.emit(error_msg)

    def send_request(self, prompt: str, model: str = "gemma:2b") -> bool:
        """Invia una richiesta all'AI"""
        if not self.ollama_bridge:
            error_msg = "Servizio AI non disponibile - Ollama non inizializzato"
            self.logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            return False

        try:
            # Verifica connessione
            if not self.check_connection():
                error_msg = "Impossibile connettersi al servizio AI Ollama"
                self.error_occurred.emit(error_msg)
                return False

            # Invia la richiesta
            self.ollama_bridge.sendPrompt(prompt, model)
            self.logger.info(f"Richiesta AI inviata: {prompt[:50]}... (modello: {model})")
            return True

        except Exception as e:
            error_msg = f"Errore nell'invio richiesta AI: {str(e)}"
            self.logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            return False

    def check_connection(self) -> bool:
        """Verifica la connessione con Ollama"""
        if not self.ollama_bridge:
            return False

        try:
            connected = self.ollama_bridge.checkConnection()
            if connected != self._connected:
                self._connected = connected
                self.connection_status_changed.emit(connected)
            return connected
        except Exception as e:
            self.logger.error(f"Errore verifica connessione AI: {e}")
            return False

    def get_available_models(self) -> list:
        """Restituisce la lista dei modelli disponibili"""
        if not self.ollama_bridge:
            return []

        try:
            # Qui dovremmo implementare la logica per ottenere i modelli disponibili
            # Per ora restituiamo una lista di default
            return ["gemma:2b", "llama2:7b", "llama2:13b", "codellama:7b", "mistral:7b"]
        except Exception as e:
            self.logger.error(f"Errore recupero modelli: {e}")
            return []

    def is_available(self) -> bool:
        """Verifica se il servizio AI è disponibile"""
        return self.ollama_bridge is not None and self.check_connection()

    def cleanup(self):
        """Pulisce le risorse del servizio AI"""
        try:
            if self.ollama_bridge:
                # Qui dovremmo implementare la logica di cleanup se necessaria
                pass
            self.logger.info("AI Service cleanup completato")
        except Exception as e:
            self.logger.error(f"Errore durante cleanup AI Service: {e}")