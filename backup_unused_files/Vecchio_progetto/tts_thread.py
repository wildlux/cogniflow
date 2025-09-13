# tts_thread.py - Thread per la sintesi vocale

import logging
from PyQt6.QtCore import QThread, pyqtSignal

# Importa la libreria pyttsx3 per una sintesi vocale più robusta
try:
    import pyttsx3
except ImportError:
    logging.error(
        "La libreria 'pyttsx3' non è installata. "
        "Installala con 'pip install pyttsx3'"
    )
    pyttsx3 = None


class TTSThread(QThread):
    """
    Un thread dedicato per la lettura vocale del testo utilizzando pyttsx3,
    evitando di bloccare l'interfaccia utente.

    Emette segnali per comunicare lo stato al widget DraggableTextWidget.
    """

    finished_reading = pyqtSignal()
    started_reading = pyqtSignal()
    error_occurred = pyqtSignal(str)

    def __init__(self, text_to_read):
        super().__init__()
        self.text_to_read = text_to_read
        self._is_running = True
        self.engine = None

    def run(self):
        if not pyttsx3:
            self.error_occurred.emit("Libreria 'pyttsx3' non disponibile.")
            return

        try:
            self.engine = pyttsx3.init()
            self.engine.say(self.text_to_read)

            self.started_reading.emit()
            logging.info(f"Lettura in corso: {self.text_to_read}")

            # Il metodo runAndWait blocca l'esecuzione finché l'audio non è terminato.
            # Questo avviene in modo sicuro all'interno del thread.
            self.engine.runAndWait()

            # Se la lettura è stata interrotta, l'engine potrebbe essere fermato.
            # Controlliamo il flag _is_running prima di emettere il segnale.
            if self._is_running:
                self.finished_reading.emit()

        except Exception as e:
            logging.error(f"Errore nel thread di lettura vocale: {e}")
            self.error_occurred.emit(str(e))
        finally:
            # Assicurati di fermare il motore pyttsx3
            if self.engine:
                self.engine.stop()
                self.engine = None

    def stop(self):
        """Interrompe la lettura vocale in modo sicuro."""
        self._is_running = False
        if self.engine:
            self.engine.stop()
        self.wait()