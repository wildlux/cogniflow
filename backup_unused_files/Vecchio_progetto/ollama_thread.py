# ollama_thread.py - Thread per la gestione delle chiamate API a Ollama

import logging
import requests
from PyQt6.QtCore import QThread, pyqtSignal


class OllamaThread(QThread):
    """Thread per la gestione delle chiamate API a Ollama."""

    ollama_response = pyqtSignal(str)
    ollama_error = pyqtSignal(str)

    def __init__(self, prompt, model):
        super().__init__()
        self.prompt = prompt
        self.model = model

    def run(self):
        try:
            logging.info(
                f"Invio prompt a Ollama. Modello: {self.model}, Prompt: {self.prompt}"
            )
            url = "http://localhost:11434/api/generate"
            payload = {"model": self.model, "prompt": self.prompt, "stream": False}

            response = requests.post(url, json=payload, timeout=60)
            response.raise_for_status()

            data = response.json()
            full_response = data.get("response", "Nessuna risposta ricevuta.")

            self.ollama_response.emit(full_response.strip())
            logging.info("Risposta Ollama ricevuta.")

        except requests.exceptions.ConnectionError:
            logging.error(
                "Errore di connessione: Il server Ollama non è raggiungibile."
            )
            self.ollama_error.emit(
                "Errore di connessione: Il server Ollama non è raggiungibile. Assicurati che sia in esecuzione."
            )
        except requests.exceptions.RequestException as e:
            logging.error(f"Errore nella richiesta Ollama: {e}")
            self.ollama_error.emit(f"Errore nella richiesta Ollama: {e}")
        except Exception as e:
            logging.error(f"Si è verificato un errore inaspettato: {e}")
            self.ollama_error.emit(f"Si è verificato un errore inaspettato: {e}")