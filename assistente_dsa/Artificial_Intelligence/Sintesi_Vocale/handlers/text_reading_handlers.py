# text_reading_handlers.py - Gestori per la lettura vocale del testo

import logging
from PyQt6.QtWidgets import QMessageBox

from ..managers.tts_manager import TTSThread


class TextReadingHandlers:
    """Classe che gestisce la lettura vocale del testo."""

    def __init__(self, main_window):
        self.main_window = main_window
        self.logger = logging.getLogger(__name__)

    def toggle_read_text(self):
        """Avvia o ferma la lettura del testo usando il thread."""
        if not self.main_window.is_reading:
            self.start_reading()
        else:
            self.stop_reading()

    def start_reading(self):
        """Avvia il thread di lettura vocale."""
        if self.main_window.tts_thread and self.main_window.tts_thread.isRunning():
            return

        self.main_window.is_reading = True

        selected_voice = self.main_window.settings.get("tts_voice", "it-IT")
        # Gestisci la voce in modo sicuro
        if selected_voice == "Zephyr":
            selected_voice = "it-IT"  # Fallback a una voce valida

        # Usa direttamente la voce selezionata senza mapping complesso
        # Il sistema TTS dovrebbe gestire direttamente i codici lingua
        # Se non funziona, usa una voce di fallback
        if selected_voice not in ["it-IT", "en-US", "en-GB", "es-ES", "fr-FR", "de-DE"]:
            selected_voice = "it-IT"  # Fallback sicuro
        self.main_window.tts_thread = TTSThread(
            self.main_window.text_label.text(), selected_voice
        )
        self.main_window.tts_thread.started_reading.connect(self.on_reading_started)
        self.main_window.tts_thread.finished_reading.connect(self.on_reading_finished)
        self.main_window.tts_thread.error_occurred.connect(self.on_reading_error)
        self.main_window.tts_thread.start()

    def stop_reading(self):
        """Ferma il thread di lettura vocale."""
        if self.main_window.tts_thread:
            if self.main_window.tts_thread.isRunning():
                self.main_window.tts_thread.stop()
                # Attendi che il thread termini completamente
                if not self.main_window.tts_thread.wait(5000):  # Timeout di 5 secondi
                    logging.warning("Thread TTS non terminato entro il timeout")
            self.main_window.tts_thread = None
        self.main_window.is_reading = False
        logging.info("Lettura testo interrotta.")

    def on_reading_started(self):
        """Gestisce l'inizio della lettura."""
        logging.info("Lettura del testo iniziata.")

    def on_reading_finished(self):
        """Gestisce la fine della lettura."""
        self.main_window.is_reading = False
        logging.info("Lettura testo completata.")

    def on_reading_error(self, message):
        """Gestisce gli errori durante la lettura."""
        self.main_window.is_reading = False
        self.main_window.read_button.setStyleSheet("")
        logging.error("Errore durante la lettura vocale: {message}")
        self.main_window.tts_thread = None
