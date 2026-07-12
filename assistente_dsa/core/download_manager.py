#!/usr/bin/env python3
"""Gestore download in background per modelli e componenti opzionali.

Singleton condiviso da tutta l'applicazione: i download proseguono anche se
la finestra Impostazioni viene chiusa e l'app resta utilizzabile nel frattempo.
La scheda Impostazioni → 📥 Download è solo una vista su questo gestore.
"""

import logging
import os
import tempfile
import zipfile

import requests
from PyQt6.QtCore import QObject, QThread, pyqtSignal

# Directory del pacchetto assistente_dsa (indipendente dalla cwd di lancio)
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

VOSK_MODELS_DIR = os.path.join(
    _BASE_DIR,
    "Artificial_Intelligence",
    "Riconoscimento_Vocale",
    "models",
    "vosk_models",
)

# Catalogo dei componenti scaricabili (estendibile: aggiungere una voce qui
# la fa comparire automaticamente in Impostazioni → 📥 Download)
CATALOG = {
    "vosk-model-small-it-0.22": {
        "label": "🎤 Voce italiano leggero (~50 MB)",
        "description": "Riconoscimento vocale rapido, ideale per comandi e note brevi",
        "url": "https://alphacephei.com/vosk/models/vosk-model-small-it-0.22.zip",
        "dest_dir": VOSK_MODELS_DIR,
    },
    "vosk-model-it-0.22": {
        "label": "🎤 Voce italiano completo (~1,5 GB)",
        "description": "Riconoscimento vocale di alta qualità per dettatura lunga",
        "url": "https://alphacephei.com/vosk/models/vosk-model-it-0.22.zip",
        "dest_dir": VOSK_MODELS_DIR,
    },
}


class _DownloadThread(QThread):
    progress = pyqtSignal(str, int)  # item_id, percentuale (-1 se sconosciuta)
    status = pyqtSignal(str, str)  # item_id, messaggio
    done = pyqtSignal(str, bool)  # item_id, successo

    def __init__(self, item_id, url, dest_dir):
        super().__init__()
        self.item_id = item_id
        self.url = url
        self.dest_dir = dest_dir
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    def run(self):
        temp_zip_path = None
        try:
            os.makedirs(self.dest_dir, exist_ok=True)
            self.status.emit(self.item_id, "Connessione…")
            response = requests.get(self.url, stream=True, timeout=30)
            response.raise_for_status()
            total = int(response.headers.get("content-length", 0))

            with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp:
                temp_zip_path = tmp.name
                received = 0
                for chunk in response.iter_content(chunk_size=65536):
                    if self._cancelled:
                        self.status.emit(self.item_id, "Annullato")
                        self.done.emit(self.item_id, False)
                        return
                    if chunk:
                        tmp.write(chunk)
                        received += len(chunk)
                        if total > 0:
                            self.progress.emit(
                                self.item_id, int(received / total * 100)
                            )
                        else:
                            self.progress.emit(self.item_id, -1)

            self.status.emit(self.item_id, "Estrazione…")
            with zipfile.ZipFile(temp_zip_path, "r") as zf:
                zf.extractall(self.dest_dir)

            self.status.emit(self.item_id, "✅ Completato")
            self.done.emit(self.item_id, True)

        except Exception as e:
            logging.error(f"Download {self.item_id} fallito: {e}")
            self.status.emit(self.item_id, f"❌ Errore: {e}")
            self.done.emit(self.item_id, False)
        finally:
            if temp_zip_path and os.path.exists(temp_zip_path):
                try:
                    os.unlink(temp_zip_path)
                except OSError:
                    pass


class DownloadManager(QObject):
    """Coordina i download in background; vive quanto l'applicazione."""

    progress = pyqtSignal(str, int)  # item_id, percentuale
    status = pyqtSignal(str, str)  # item_id, messaggio
    finished = pyqtSignal(str, bool)  # item_id, successo

    def __init__(self):
        super().__init__()
        self._threads = {}

    def is_installed(self, item_id):
        item = CATALOG.get(item_id)
        if item is None:
            return False
        return os.path.exists(os.path.join(item["dest_dir"], item_id))

    def is_downloading(self, item_id):
        thread = self._threads.get(item_id)
        return thread is not None and thread.isRunning()

    def any_downloading(self):
        return any(t.isRunning() for t in self._threads.values())

    def start(self, item_id):
        """Avvia il download in background di un elemento del catalogo."""
        if item_id not in CATALOG or self.is_downloading(item_id):
            return False
        if self.is_installed(item_id):
            self.status.emit(item_id, "✅ Già installato")
            return False

        item = CATALOG[item_id]
        thread = _DownloadThread(item_id, item["url"], item["dest_dir"])
        thread.progress.connect(self.progress)
        thread.status.connect(self.status)
        thread.done.connect(self._on_done)
        self._threads[item_id] = thread
        thread.start()
        logging.info(f"Download in background avviato: {item_id}")
        self.status.emit(item_id, "Download avviato…")
        return True

    def cancel(self, item_id):
        thread = self._threads.get(item_id)
        if thread is not None and thread.isRunning():
            thread.cancel()

    def _on_done(self, item_id, ok):
        thread = self._threads.pop(item_id, None)
        if thread is not None:
            thread.deleteLater()
        self.finished.emit(item_id, ok)


# Istanza globale condivisa
download_manager = DownloadManager()
