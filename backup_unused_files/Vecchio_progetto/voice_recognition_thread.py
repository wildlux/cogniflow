# voice_recognition_thread.py - Thread per il riconoscimento vocale asincrono

import logging
from PyQt6.QtCore import QThread, pyqtSignal

# Importa la libreria per il riconoscimento vocale
try:
    import speech_recognition as sr
except ImportError:
    logging.error(
        "La libreria 'speech_recognition' non è installata. "
        "Per abilitare il riconoscimento vocale, installala con 'pip install SpeechRecognition PyAudio'"
    )
    sr = None


class VoiceRecognitionThread(QThread):
    """Thread per il riconoscimento vocale asincrono."""

    recognized_text = pyqtSignal(str)
    recognition_error = pyqtSignal(str)

    def __init__(self, lang_setting):
        super().__init__()
        self._running = True
        if sr is None:
            self.recognizer = None
        else:
            self.recognizer = sr.Recognizer()

        lang_map = {
            "Italiano": "it-IT",
            "English": "en-US",
            "Français": "fr-FR",
            "Deutsch": "de-DE",
        }
        self.lang_code = lang_map.get(lang_setting, "it-IT")

    def run(self):
        if sr is None or self.recognizer is None:
            self.recognition_error.emit(
                "Libreria di riconoscimento vocale non disponibile."
            )
            return

        try:
            with sr.Microphone() as source:
                self.recognizer.adjust_for_ambient_noise(source)
                logging.info("In ascolto per il riconoscimento vocale...")
                try:
                    audio = self.recognizer.listen(
                        source, timeout=5, phrase_time_limit=10
                    )
                    if not self._running:
                        return

                    logging.info("Riconoscimento in corso...")
                    text = self.recognizer.recognize_google(
                        audio, language=self.lang_code
                    )
                    self.recognized_text.emit(text)

                except sr.WaitTimeoutError:
                    logging.warning(
                        "Tempo di attesa scaduto per il riconoscimento vocale."
                    )
                    self.recognition_error.emit(
                        "Tempo di attesa scaduto. Nessun input vocale ricevuto."
                    )
                except sr.UnknownValueError:
                    logging.warning(
                        "Impossibile riconoscere il testo dal segnale audio."
                    )
                    self.recognition_error.emit(
                        "Impossibile riconoscere il testo. Riprova."
                    )
                except sr.RequestError as e:
                    logging.error(f"Errore dal servizio di riconoscimento vocale: {e}")
                    self.recognition_error.emit(
                        f"Errore dal servizio di riconoscimento vocale; {e}"
                    )
                except Exception as e:
                    logging.error(
                        f"Si è verificato un errore inaspettato nel riconoscimento vocale: {e}"
                    )
                    self.recognition_error.emit(
                        f"Si è verificato un errore inaspettato: {e}"
                    )
        except Exception as e:
            logging.error(f"Errore nell'inizializzazione del microfono: {e}")
            self.recognition_error.emit(
                f"Errore nell'inizializzazione del microfono: {e}"
            )

    def stop(self):
        self._running = False
        self.wait()