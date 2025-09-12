# tts_manager.py

import pyttsx3
import threading
import logging
import os
import simpleaudio as sa
import gtts
import subprocess
from io import BytesIO

from PyQt6.QtCore import QThread, pyqtSignal

# ==============================================================================
# Configurazione Voci e Motori TTS
# ==============================================================================


def _get_pyttsx3_voices():
    """Restituisce un dizionario di voci pyttsx3 disponibili con nome e sesso."""
    voices_info = []
    try:
        engine = pyttsx3.init()
        voices = engine.getProperty("voices")

        # Handle different types of voices objects
        if voices:
            # Try different approaches to access voices
            if isinstance(voices, (list, tuple)):
                for voice in voices:  # type: ignore
                    try:
                        voice_gender = "Sconosciuto"
                        if hasattr(voice, "name") and hasattr(voice, "id"):
                            if "male" in voice.name.lower():
                                voice_gender = "Maschile"
                            elif "female" in voice.name.lower():
                                voice_gender = "Femminile"
                            voices_info.append(
                                {
                                    "name": voice.name,
                                    "gender": voice_gender,
                                    "id": voice.id,
                                }
                            )
                    except AttributeError:
                        continue
            elif hasattr(voices, "__iter__"):
                # Fallback for other iterable objects
                try:
                    for voice in voices:  # type: ignore
                        try:
                            voice_gender = "Sconosciuto"
                            if hasattr(voice, "name") and hasattr(voice, "id"):
                                if "male" in voice.name.lower():
                                    voice_gender = "Maschile"
                                elif "female" in voice.name.lower():
                                    voice_gender = "Femminile"
                                voices_info.append(
                                    {
                                        "name": voice.name,
                                        "gender": voice_gender,
                                        "id": voice.id,
                                    }
                                )
                        except AttributeError:
                            continue
                except (TypeError, AttributeError):
                    pass

        # If no voices found, add a default one
        if not voices_info:
            voices_info.append(
                {
                    "name": "Voce Sistema (Default)",
                    "gender": "Sconosciuto",
                    "id": "default",
                }
            )

    except Exception:
        logging.error("Errore nel caricamento delle voci pyttsx3: {e}")
        voices_info.append(
            {"name": "Zephyr (Fallback)", "gender": "Sconosciuto", "id": "fallback"}
        )
    return voices_info


VOCI_DI_SISTEMA = _get_pyttsx3_voices()

# Lista delle lingue supportate da gTTS (solo le più comuni)
# Formato: {'codice_lingua': 'Nome Lingua'}
GTTS_LANGUAGES = {
    "it": "Italiano",
    "en": "Inglese",
    "es": "Spagnolo",
    "fr": "Francese",
    "de": "Tedesco",
    "ja": "Giapponese",
    "ko": "Coreano",
    "zh-cn": "Cinese Semplificato",
}

# ==============================================================================
# Thread per la Sintesi Vocale
# ==============================================================================


class TTSThread(QThread):
    """
    Thread per la sintesi vocale asincrona, supporta diversi motori TTS.
    """

    finished_reading = pyqtSignal()
    started_reading = pyqtSignal()
    error_occurred = pyqtSignal(str)

    def __init__(
        self, text, engine_name="pyttsx3", voice_or_lang="it", speed=1.0, pitch=1.0
    ):
        super().__init__()
        self.text_to_speak = text
        self.engine_name = engine_name
        self.voice_or_lang = voice_or_lang
        self.speed = speed
        self.pitch = pitch
        self._is_running = True

    def run(self):
        """Esegue il processo di sintesi vocale in base al motore scelto."""
        self.started_reading.emit()
        try:
            if self.engine_name == "pyttsx3":
                self._speak_pyttsx3()
            elif self.engine_name == "gTTS":
                self._speak_gtts()
            elif self.engine_name == "Piper (WIP)":
                self.error_occurred.emit(
                    "Il sintetizzatore Piper non è ancora stato integrato."
                )
            else:
                self.error_occurred.emit(
                    "Motore TTS non supportato: {self.engine_name}"
                )
        except Exception:
            logging.error("Errore nella sintesi vocale: {e}")
            self.error_occurred.emit("Errore: {str(e)}")
        finally:
            if self._is_running:
                self.finished_reading.emit()

    def stop(self):
        """Segnala al thread di fermarsi in modo sicuro."""
        self._is_running = False

    def _speak_pyttsx3(self):
        """Gestisce la sintesi vocale con pyttsx3."""
        engine = None
        try:
            engine = pyttsx3.init()
            # Mantieni un riferimento forte all'engine per evitare il garbage collection
            self._tts_engine = engine

            # Imposta la velocità
            rate = engine.getProperty("rate")
            if rate is not None and isinstance(rate, (int, float)):
                engine.setProperty("rate", int(rate * self.speed))

            # Imposta l'intonazione (pitch) - pyttsx3 non ha un metodo diretto, ma alcune voci lo supportano
            # In questo caso, il parametro pitch è solo un placeholder

            # Imposta la voce usando l'ID
            try:
                engine.setProperty("voice", self.voice_or_lang)
            except Exception:
                logging.warning(
                    "Impossibile impostare la voce '{self.voice_or_lang}': {e}. Verrà usata la voce di default."
                )

            engine.say(self.text_to_speak)
            engine.runAndWait()

        except Exception:
            self.error_occurred.emit("Errore con pyttsx3: {str(e)}")
            logging.error("Errore pyttsx3: {e}")
        finally:
            # Pulisci il riferimento dopo l'uso
            if hasattr(self, "_tts_engine"):
                self._tts_engine = None

    def _speak_gtts(self):
        """Gestisce la sintesi vocale con gTTS e riproduzione audio."""
        try:
            # Estrai il codice lingua dal testo del combobox (es. 'Italiano (it)' -> 'it')
            lang_code = self.voice_or_lang.split("(")[-1].replace(")", "")

            tts = gtts.gTTS(self.text_to_speak, lang=lang_code)

            # gTTS salva in un file temporaneo in memoria (BytesIO)
            mp3_fp = BytesIO()
            tts.write_to_fp(mp3_fp)
            mp3_fp.seek(0)

            # Usa un processo esterno per riprodurre il file mp3.
            os.makedirs("Audio", exist_ok=True)
            file_name = "Audio/temp_gtts.mp3"
            tts.save(file_name)

            # Usa un processo esterno per riprodurre il file mp3.
            subprocess.run(["mpg123", file_name])
            if os.path.exists(file_name):
                os.remove(file_name)

        except Exception:
            self.error_occurred.emit("Errore con gTTS: {str(e)}")
            logging.error("Errore gTTS: {e}")
