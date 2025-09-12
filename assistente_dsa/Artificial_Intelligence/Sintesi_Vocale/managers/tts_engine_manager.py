# Gestore semplificato per TTS usando pyttsx3

import logging
from typing import Optional, List


class TTSManager:
    """Gestore semplificato per TTS usando pyttsx3."""

    def __init__(self):
        self.logger = logging.getLogger("TTSManager")
        self.engine = None
        self._init_engine()

    def _init_engine(self):
        """Inizializza il motore TTS."""
        try:
            import pyttsx3

            self.engine = pyttsx3.init()
            self.logger.info("TTS engine initialized successfully")
        except ImportError:
            self.logger.error("pyttsx3 not available")
            self.engine = None

    def speak(self, text: str, voice: Optional[str] = None):
        """Pronuncia il testo specificato."""
        if not self.engine:
            self.logger.error("TTS engine not available")
            return

        try:
            if voice:
                voices = self.engine.getProperty("voices")
                for v in voices:
                    if voice.lower() in v.name.lower():
                        self.engine.setProperty("voice", v.id)
                        break

            self.engine.say(text)
            self.engine.runAndWait()
            self.logger.info(f"Text spoken: {text[:50]}...")
        except Exception as e:
            self.logger.error(f"Error speaking text: {e}")

    def get_available_voices(self) -> List[str]:
        """Restituisce la lista delle voci disponibili."""
        if not self.engine:
            return []

        try:
            voices = self.engine.getProperty("voices")
            return [voice.name for voice in voices] if voices else []
        except Exception as e:
            self.logger.error(f"Error getting voices: {e}")
            return []

    def set_voice(self, voice_name: str):
        """Imposta la voce da utilizzare."""
        if not self.engine:
            return

        try:
            voices = self.engine.getProperty("voices")
            for voice in voices:
                if voice_name.lower() in voice.name.lower():
                    self.engine.setProperty("voice", voice.id)
                    self.logger.info(f"Voice set to: {voice_name}")
                    break
        except Exception as e:
            self.logger.error(f"Error setting voice: {e}")

    def set_rate(self, rate: int):
        """Imposta la velocità di pronuncia."""
        if self.engine:
            self.engine.setProperty("rate", rate)

    def set_volume(self, volume: float):
        """Imposta il volume (0.0 - 1.0)."""
        if self.engine:
            self.engine.setProperty("volume", volume)
