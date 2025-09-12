#!/usr/bin/env python3
"""
Bridge per integrare Ollama con QML
"""

import logging
import os
import sys
from PyQt6.QtCore import QObject, pyqtSignal, QThread, pyqtSlot
from PyQt6.QtQml import QQmlApplicationEngine

# Aggiungi il percorso per importare i moduli
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from Artificial_Intelligence.Ollama.ollama_manager import OllamaManager, OllamaThread, OllamaModelsThread


class OllamaBridge(QObject):
    """Bridge per collegare Ollama al QML"""

    # Segnali per comunicare con QML
    responseReceived = pyqtSignal(str, str)  # prompt, response
    errorOccurred = pyqtSignal(str)
    modelsLoaded = pyqtSignal(list)
    statusChanged = pyqtSignal(str)
    logMessage = pyqtSignal(str, str)  # level, message

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ollama_manager = OllamaManager()
        self.current_thread = None

    @pyqtSlot(bool)
    def checkConnection(self):
        """Verifica la connessione con Ollama"""
        if self.ollama_manager.check_ollama_running():
            self.statusChanged.emit("Connesso")
            return True
        else:
            self.statusChanged.emit("Non connesso")
            return False

    @pyqtSlot()
    def loadModels(self):
        """Carica la lista dei modelli disponibili"""
        self.statusChanged.emit("Caricamento modelli...")

        thread = OllamaModelsThread()
        thread.models_list.connect(self._onModelsLoaded)
        thread.error_occurred.connect(self._onError)
        thread.start()

        self.current_thread = thread

    def _onModelsLoaded(self, models):
        """Callback quando i modelli sono stati caricati"""
        self.modelsLoaded.emit(models)
        self.statusChanged.emit("Modelli caricati")

    def _onError(self, error_msg):
        """Callback per errori"""
        self.errorOccurred.emit(error_msg)
        self.statusChanged.emit("Errore")

    @pyqtSlot(str, str)
    def sendPrompt(self, prompt, model="gemma:2b"):
        """Invia un prompt a Ollama"""
        print("🔍 Bridge: sendPrompt chiamato con prompt '{prompt[:50]}...' e modello '{model}'")

        if not self.checkConnection():
            print("🔍 Bridge: Ollama non connesso")
            self.errorOccurred.emit("Ollama non è in esecuzione. Avvia il servizio prima.")
            return

        print("🔍 Bridge: Invio richiesta a Ollama...")
        self.statusChanged.emit("Invio richiesta...")

        thread = OllamaThread(prompt, model)
        thread.ollama_response.connect(lambda response: self._onResponseReceived(prompt, response))
        thread.ollama_error.connect(self._onError)
        thread.finished.connect(lambda: print("🔍 Bridge: Thread Ollama completato"))
        thread.start()

        self.current_thread = thread
        print("🔍 Bridge: Thread avviato")

    def _onResponseReceived(self, prompt, response):
        """Callback quando arriva una risposta"""
        print("🔍 Bridge: Risposta ricevuta per prompt '{prompt[:50]}...'")
        print("🔍 Bridge: Lunghezza risposta: {len(response)} caratteri")
        self.responseReceived.emit(prompt, response)
        self.statusChanged.emit("Risposta ricevuta")

    def sendLogMessage(self, level, message):
        """Invia un messaggio di log al QML"""
        self.logMessage.emit(level, message)

    def setup_logging_bridge(self):
        """Configura il bridge per catturare i messaggi di log dal sistema Python"""
        # Crea un handler personalizzato che invia i log al QML
        class QMLLogHandler(logging.Handler):
            def __init__(self, bridge):
                super().__init__()
                self.bridge = bridge

            def emit(self, record):
                # Invia solo WARNING, ERROR e CRITICAL al QML
                if record.levelno >= logging.WARNING:
                    level_name = record.levelname
                    message = self.format(record)
                    self.bridge.sendLogMessage(level_name, message)

        # Aggiungi l'handler al logger root
        qml_handler = QMLLogHandler(self)
        qml_handler.setLevel(logging.WARNING)

        # Configura il formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        qml_handler.setFormatter(formatter)

        # Aggiungi l'handler al logger root
        root_logger = logging.getLogger()
        root_logger.addHandler(qml_handler)

        print("🔍 Bridge: Sistema di logging collegato al QML")


# Istanza globale del bridge
ollama_bridge = OllamaBridge()


def register_bridge(engine):
    """Registra il bridge nel contesto QML"""
    engine.rootContext().setContextProperty("ollamaBridge", ollama_bridge)
    return ollama_bridge


if __name__ == "__main__":
    print("🔧 Ollama Bridge per QML")
    print("Questo file fornisce l'integrazione tra QML e Ollama")
