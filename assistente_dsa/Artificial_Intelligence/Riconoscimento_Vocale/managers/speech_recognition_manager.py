import os
import logging
import requests
import zipfile
import tempfile
from PyQt6.QtCore import QThread, pyqtSignal
import json

try:
    import vosk
    import pyaudio
    VOSK_AVAILABLE = True
    PYAUDIO_AVAILABLE = True
except ImportError as e:
    logging.error(f"Errore: Assicurati che le librerie 'vosk' e 'pyaudio' siano installate. {e}")
    VOSK_AVAILABLE = False
    PYAUDIO_AVAILABLE = False
    vosk = None
    pyaudio = None

class SpeechRecognitionThread(QThread):
    """
    Thread per il riconoscimento vocale con timeout sul silenzio.
    """
    # Segnali per comunicare con l'interfaccia utente
    model_status = pyqtSignal(str)
    recognized_text = pyqtSignal(str)
    recognition_error = pyqtSignal(str)
    stopped_by_silence = pyqtSignal()

    def __init__(self, vosk_model_name, text_callback=None):
        super().__init__()
        self.vosk_model_name = vosk_model_name
        self.running = True
        self.SILENCE_TIMEOUT_SECONDS = 3  # Timeout in secondi per il silenzio
        self.text_callback = text_callback  # Callback function per il testo riconosciuto

    def run(self):
        # Initialize variables to avoid unbound errors
        stream = None
        p = None

        # Check if required libraries are available
        if not VOSK_AVAILABLE or not PYAUDIO_AVAILABLE:
            error_msg = "Librerie vosk o pyaudio non disponibili"
            logging.error(error_msg)
            self.model_status.emit(f"Errore: {error_msg}")
            self.recognition_error.emit(error_msg)
            return

        vosk_model_path = os.path.join("Artificial_Intelligence", "Riconoscimento_Vocale", "models", "vosk_models", self.vosk_model_name)

        if not os.path.exists(vosk_model_path):
            error_msg = f"Modello Vosk non trovato in {vosk_model_path}"
            logging.error(error_msg)
            self.model_status.emit(f"Errore: {error_msg}")
            self.recognition_error.emit(error_msg)
            return

        try:
            if vosk is None or pyaudio is None:
                raise ImportError("Librerie vosk o pyaudio non disponibili")

            self.model_status.emit(f"Caricamento modello Vosk: {self.vosk_model_name}")
            model = vosk.Model(vosk_model_path)

            # Parametri per il flusso audio
            SAMPLE_RATE = 16000
            CHUNK_SIZE = 4000

            p = pyaudio.PyAudio()
            stream = p.open(format=pyaudio.paInt16,
                              channels=1,
                              rate=SAMPLE_RATE,
                              input=True,
                              frames_per_buffer=CHUNK_SIZE)

            recognizer = vosk.KaldiRecognizer(model, SAMPLE_RATE)

            self.model_status.emit("In ascolto...")
            logging.info("Riconoscimento vocale avviato...")

            silent_chunks_count = 0
            silent_chunks_threshold = (SAMPLE_RATE / CHUNK_SIZE) * self.SILENCE_TIMEOUT_SECONDS

            while self.running:
                data = stream.read(CHUNK_SIZE, exception_on_overflow=False)

                if not data:
                    continue

                if recognizer.AcceptWaveform(data):
                    result = json.loads(recognizer.Result())
                    text = result.get('text')
                    if text:
                        logging.info(f"🎤 Testo riconosciuto nel thread: '{text}'")

                        # Usa la callback se disponibile (più affidabile)
                        if self.text_callback:
                            try:
                                self.text_callback(text)
                                logging.info(f"📞 Callback chiamata per: '{text}'")
                            except Exception as e:
                                logging.error(f"❌ Errore callback: {e}")

                        # Emetti anche il segnale come fallback
                        self.recognized_text.emit(text)
                        logging.info(f"📤 Segnale recognized_text emesso per: '{text}'")
                        silent_chunks_count = 0 # Reimposta il contatore del silenzio

                else: # Il risultato non è un testo completo (probabilmente silenzio)
                    partial_result = json.loads(recognizer.PartialResult())
                    if not partial_result.get('partial', '').strip():
                        silent_chunks_count += 1
                        if silent_chunks_count > silent_chunks_threshold:
                            self.running = False # Ferma il ciclo
                            self.stopped_by_silence.emit() # Emette un segnale che il thread si è fermato per silenzio
                            break
                    else:
                        silent_chunks_count = 0 # Reimposta il contatore se c'è attività vocale

        except Exception as e:
            error_msg = f"Errore fatale nel thread di riconoscimento vocale: {e}"
            logging.error(error_msg)
            self.recognition_error.emit(error_msg)
        finally:
            # Assicura che il flusso audio venga sempre chiuso correttamente
            if stream and stream.is_active():
                stream.stop_stream()
                stream.close()
            if p:
                p.terminate()

        self.model_status.emit("Riconoscimento vocale terminato")
        logging.info("Riconoscimento vocale terminato.")

    def stop(self):
        self.running = False
        self.wait() # Attende la chiusura del thread


def download_vosk_model(model_name, progress_callback=None):
    """
    Scarica un modello Vosk dal repository ufficiale.

    Args:
        model_name (str): Nome del modello da scaricare (es. 'vosk-model-it-0.22')
        progress_callback (callable): Funzione di callback per il progresso (opzionale)

    Returns:
        bool: True se il download è riuscito, False altrimenti
    """
    try:
        # URL base per i modelli Vosk
        base_url = "https://alphacephei.com/vosk/models"
        model_url = f"{base_url}/{model_name}.zip"

        # Directory di destinazione
        models_dir = os.path.join("Artificial_Intelligence", "Riconoscimento_Vocale", "models", "vosk_models")
        if not os.path.exists(models_dir):
            os.makedirs(models_dir, exist_ok=True)

        model_path = os.path.join(models_dir, model_name)

        # Verifica se il modello è già presente
        if os.path.exists(model_path):
            logging.info(f"Modello {model_name} già presente in {model_path}")
            return True

        logging.info(f"Scaricamento modello {model_name} da {model_url}")

        if progress_callback:
            progress_callback(f"🔄 Scaricamento modello {model_name}...")

        # Scarica il file zip
        response = requests.get(model_url, stream=True)
        response.raise_for_status()

        # Ottieni la dimensione totale per il progresso
        total_size = int(response.headers.get('content-length', 0))

        # Crea un file temporaneo per il download
        with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as temp_file:
            temp_zip_path = temp_file.name

            downloaded_size = 0
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    temp_file.write(chunk)
                    downloaded_size += len(chunk)

                    # Aggiorna progresso se disponibile
                    if progress_callback and total_size > 0:
                        progress = int((downloaded_size / total_size) * 100)
                        progress_callback(f"🔄 Scaricamento: {progress}%")

        if progress_callback:
            progress_callback(f"📦 Estrazione modello {model_name}...")

        # Estrai il file zip
        with zipfile.ZipFile(temp_zip_path, 'r') as zip_ref:
            zip_ref.extractall(models_dir)

        # Rimuovi il file temporaneo
        os.unlink(temp_zip_path)

        # Verifica che l'estrazione sia riuscita
        if os.path.exists(model_path):
            logging.info(f"Modello {model_name} scaricato e estratto con successo")
            if progress_callback:
                progress_callback(f"✅ Modello {model_name} pronto!")
            return True
        else:
            logging.error(f"Estrazione fallita: directory {model_path} non trovata")
            if progress_callback:
                progress_callback(f"❌ Errore nell'estrazione del modello")
            return False

    except requests.exceptions.RequestException as e:
        error_msg = f"Errore nel download del modello {model_name}: {e}"
        logging.error(error_msg)
        if progress_callback:
            progress_callback(f"❌ Errore download: {str(e)}")
        return False
    except zipfile.BadZipFile as e:
        error_msg = f"File zip corrotto per il modello {model_name}: {e}"
        logging.error(error_msg)
        if progress_callback:
            progress_callback(f"❌ File zip corrotto")
        return False
    except Exception as e:
        error_msg = f"Errore imprevisto durante il download del modello {model_name}: {e}"
        logging.error(error_msg)
        if progress_callback:
            progress_callback(f"❌ Errore imprevisto: {str(e)}")
        return False


def ensure_vosk_model_available(model_name, progress_callback=None):
    """
    Assicura che un modello Vosk sia disponibile, scaricandolo se necessario.

    Args:
        model_name (str): Nome del modello da verificare/scaricare
        progress_callback (callable): Funzione di callback per il progresso (opzionale)

    Returns:
        bool: True se il modello è disponibile, False altrimenti
    """
    model_path = os.path.join("Artificial_Intelligence", "Riconoscimento_Vocale", "models", "vosk_models", model_name)

    if os.path.exists(model_path):
        logging.info(f"Modello {model_name} già disponibile")
        return True

    logging.info(f"Modello {model_name} mancante, tentativo di download...")
    return download_vosk_model(model_name, progress_callback)
