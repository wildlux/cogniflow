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
    logging.error("Errore: Assicurati che le librerie 'vosk' e 'pyaudio' siano installate. {e}")
    VOSK_AVAILABLE = False
    PYAUDIO_AVAILABLE = False
    vosk = None
    pyaudio = None

try:
    import wave
    import audioop
    WAVE_AVAILABLE = True
except ImportError:
    logging.warning("Modulo 'wave' non disponibile - funzionalità di conversione audio limitata")
    WAVE_AVAILABLE = False
    wave = None
    audioop = None


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
            self.model_status.emit("Errore: {error_msg}")
            self.recognition_error.emit(error_msg)
            return

        vosk_model_path = os.path.join("Artificial_Intelligence", "Riconoscimento_Vocale", "models", "vosk_models", self.vosk_model_name)

        if not os.path.exists(vosk_model_path):
            error_msg = "Modello Vosk non trovato in {vosk_model_path}"
            logging.error(error_msg)
            self.model_status.emit("Errore: {error_msg}")
            self.recognition_error.emit(error_msg)
            return

        try:
            if vosk is None or pyaudio is None:
                raise ImportError("Librerie vosk o pyaudio non disponibili")

            self.model_status.emit("Caricamento modello Vosk: {self.vosk_model_name}")
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
                        logging.info("🎤 Testo riconosciuto nel thread: '{text}'")

                        # Usa la callback se disponibile (più affidabile)
                        if self.text_callback:
                            try:
                                self.text_callback(text)
                                logging.info("📞 Callback chiamata per: '{text}'")
                            except Exception:
                                logging.error("❌ Errore callback: {e}")

                        # Emetti anche il segnale come fallback
                        self.recognized_text.emit(text)
                        logging.info("📤 Segnale recognized_text emesso per: '{text}'")
                        silent_chunks_count = 0  # Reimposta il contatore del silenzio

                else:  # Il risultato non è un testo completo (probabilmente silenzio)
                    partial_result = json.loads(recognizer.PartialResult())
                    if not partial_result.get('partial', '').strip():
                        silent_chunks_count += 1
                        if silent_chunks_count > silent_chunks_threshold:
                            self.running = False  # Ferma il ciclo
                            self.stopped_by_silence.emit()  # Emette un segnale che il thread si è fermato per silenzio
                            break
                    else:
                        silent_chunks_count = 0  # Reimposta il contatore se c'è attività vocale

        except Exception:
            error_msg = "Errore fatale nel thread di riconoscimento vocale: {e}"
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
        self.wait()  # Attende la chiusura del thread


class AudioFileTranscriptionThread(QThread):
    """
    Thread per la trascrizione di file audio utilizzando Vosk.
    Supporta formati WAV, MP3 e altri formati audio comuni.
    """
    # Segnali per comunicare con l'interfaccia utente
    transcription_progress = pyqtSignal(str)
    transcription_completed = pyqtSignal(str)
    transcription_error = pyqtSignal(str)

    def __init__(self, audio_file_path, vosk_model_name, text_callback=None):
        super().__init__()
        self.audio_file_path = audio_file_path
        self.vosk_model_name = vosk_model_name
        self.text_callback = text_callback
        self.running = True

    def run(self):
        """Esegue la trascrizione del file audio."""
        # Verifica disponibilità librerie
        if not VOSK_AVAILABLE:
            error_msg = "Libreria vosk non disponibile per la trascrizione"
            logging.error(error_msg)
            self.transcription_error.emit(error_msg)
            return

        if not WAVE_AVAILABLE:
            error_msg = "Modulo wave non disponibile per la trascrizione"
            logging.error(error_msg)
            self.transcription_error.emit(error_msg)
            return

        # Verifica esistenza file audio
        if not os.path.exists(self.audio_file_path):
            error_msg = "File audio non trovato: {self.audio_file_path}"
            logging.error(error_msg)
            self.transcription_error.emit(error_msg)
            return

        vosk_model_path = os.path.join("Artificial_Intelligence", "Riconoscimento_Vocale", "models", "vosk_models", self.vosk_model_name)

        if not os.path.exists(vosk_model_path):
            error_msg = "Modello Vosk non trovato in {vosk_model_path}"
            logging.error(error_msg)
            self.transcription_error.emit(error_msg)
            return

        try:
            self.transcription_progress.emit("Caricamento modello Vosk...")
            model = vosk.Model(vosk_model_path)

            self.transcription_progress.emit("Elaborazione file audio...")

            # Leggi il file audio
            with wave.open(self.audio_file_path, 'rb') as wf:
                # Verifica formato audio
                if wf.getnchannels() != 1:
                    # Converti a mono se necessario
                    self.transcription_progress.emit("Conversione audio a mono...")
                    frames = wf.readframes(wf.getnframes())
                    # Converti stereo a mono
                    frames = audioop.tomono(frames, wf.getsampwidth(), 0.5, 0.5)
                    # Ricrea il wave file in memoria
                    import io
                    mono_wf = io.BytesIO()
                    with wave.open(mono_wf, 'wb') as mono_file:
                        mono_file.setnchannels(1)
                        mono_file.setsampwidth(wf.getsampwidth())
                        mono_file.setframerate(wf.getframerate())
                        mono_file.writeframes(frames)
                    mono_wf.seek(0)
                    wf = wave.open(mono_wf, 'rb')

                # Verifica sample rate
                sample_rate = wf.getframerate()
                if sample_rate != 16000:
                    self.transcription_progress.emit("Conversione sample rate da {sample_rate}Hz a 16000Hz...")
                    # Per ora assumiamo che il file sia già a 16kHz
                    # Una implementazione completa richiederebbe resampling
                    pass

                # Inizializza recognizer
                recognizer = vosk.KaldiRecognizer(model, sample_rate)

                # Leggi e trascrivi l'audio
                full_text = []
                chunk_size = 4000

                self.transcription_progress.emit("Trascrizione in corso...")

                while self.running:
                    data = wf.readframes(chunk_size)
                    if len(data) == 0:
                        break

                    if recognizer.AcceptWaveform(data):
                        result = json.loads(recognizer.Result())
                        text = result.get('text', '').strip()
                        if text:
                            full_text.append(text)
                            self.transcription_progress.emit("Testo riconosciuto: {text[:50]}...")

                # Ottieni il risultato finale
                final_result = json.loads(recognizer.FinalResult())
                final_text = final_result.get('text', '').strip()
                if final_text:
                    full_text.append(final_text)

                # Combina tutto il testo
                complete_text = ' '.join(full_text).strip()

                if complete_text:
                    self.transcription_progress.emit("Trascrizione completata!")
                    self.transcription_completed.emit(complete_text)

                    # Usa callback se disponibile
                    if self.text_callback:
                        try:
                            self.text_callback(complete_text)
                        except Exception:
                            logging.error("Errore callback trascrizione: {e}")
                else:
                    self.transcription_error.emit("Nessun testo riconosciuto nel file audio")

        except Exception:
            error_msg = "Errore durante la trascrizione: {str(e)}"
            logging.error(error_msg)
            self.transcription_error.emit(error_msg)

    def stop(self):
        """Ferma la trascrizione."""
        self.running = False
        self.wait()


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
        model_url = "{base_url}/{model_name}.zip"

        # Directory di destinazione
        models_dir = os.path.join("Artificial_Intelligence", "Riconoscimento_Vocale", "models", "vosk_models")
        if not os.path.exists(models_dir):
            os.makedirs(models_dir, exist_ok=True)

        model_path = os.path.join(models_dir, model_name)

        # Verifica se il modello è già presente
        if os.path.exists(model_path):
            logging.info("Modello {model_name} già presente in {model_path}")
            return True

        logging.info("Scaricamento modello {model_name} da {model_url}")

        if progress_callback:
            progress_callback("🔄 Scaricamento modello {model_name}...")

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
                        progress_callback("🔄 Scaricamento: {progress}%")

        if progress_callback:
            progress_callback("📦 Estrazione modello {model_name}...")

        # Estrai il file zip
        with zipfile.ZipFile(temp_zip_path, 'r') as zip_ref:
            zip_ref.extractall(models_dir)

        # Rimuovi il file temporaneo
        os.unlink(temp_zip_path)

        # Verifica che l'estrazione sia riuscita
        if os.path.exists(model_path):
            logging.info("Modello {model_name} scaricato e estratto con successo")
            if progress_callback:
                progress_callback("✅ Modello {model_name} pronto!")
            return True
        else:
            logging.error("Estrazione fallita: directory {model_path} non trovata")
            if progress_callback:
                progress_callback("❌ Errore nell'estrazione del modello")
            return False

    except requests.exceptions.RequestException as e:
        error_msg = "Errore nel download del modello {model_name}: {e}"
        logging.error(error_msg)
        if progress_callback:
            progress_callback("❌ Errore download: {str(e)}")
        return False
    except zipfile.BadZipFile as e:
        error_msg = "File zip corrotto per il modello {model_name}: {e}"
        logging.error(error_msg)
        if progress_callback:
            progress_callback("❌ File zip corrotto")
        return False
    except Exception:
        error_msg = "Errore imprevisto durante il download del modello {model_name}: {e}"
        logging.error(error_msg)
        if progress_callback:
            progress_callback("❌ Errore imprevisto: {str(e)}")
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
        logging.info("Modello {model_name} già disponibile")
        return True

    logging.info("Modello {model_name} mancante, tentativo di download...")
    return download_vosk_model(model_name, progress_callback)
