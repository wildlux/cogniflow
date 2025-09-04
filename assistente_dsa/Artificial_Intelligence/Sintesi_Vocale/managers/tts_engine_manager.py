# TTS/tts_engine_manager.py
# Gestore unificato per tutti i motori TTS

import os
import logging
import json
from typing import List, Dict, Optional, Any, Union
from enum import Enum

class TTSEngine(Enum):
    """Enumerazione dei motori TTS disponibili."""
    PYTTSX3 = "pyttsx3"
    GTTS = "gtts"
    EDGE_TTS = "edge_tts"
    PIPER = "piper"
    COQUI = "coqui"

class TTSManager:
    """Gestore unificato per tutti i motori TTS."""

    def __init__(self):
        self.logger = logging.getLogger("TTSManager")
        self.config_dir = os.path.join(os.path.dirname(__file__), "configs")
        self.cache_dir = os.path.join(os.path.dirname(__file__), "cache")

        # Crea le directory
        for directory in [self.config_dir, self.cache_dir]:
            os.makedirs(directory, exist_ok=True)

        # Inizializza i motori
        self.engines = {}
        self._initialize_engines()

        # Carica la configurazione
        self.config = self._load_config()

        # Motore corrente
        self.current_engine = self.config.get("default_engine", TTSEngine.PYTTSX3.value)

    def _initialize_engines(self):
        """Inizializza tutti i motori TTS disponibili."""
        try:
            # pyttsx3 - Sempre disponibile
            self.engines[TTSEngine.PYTTSX3.value] = {
                "available": True,
                "instance": None,
                "quality": "Medium",
                "speed": "Fast",
                "languages": ["it", "en", "es", "fr", "de"]
            }

            # gTTS
            try:
                import gtts
                self.engines[TTSEngine.GTTS.value] = {
                    "available": True,
                    "instance": None,
                    "quality": "Medium",
                    "speed": "Medium",
                    "languages": ["it", "en", "es", "fr", "de", "ja", "ko", "zh-cn"]
                }
            except ImportError:
                self.engines[TTSEngine.GTTS.value] = {
                    "available": False,
                    "instance": None,
                    "quality": "Medium",
                    "speed": "Medium",
                    "languages": ["it", "en", "es", "fr", "de", "ja", "ko", "zh-cn"]
                }

            # Edge TTS
            try:
                import edge_tts
                from .engines.edge_tts_engine import EdgeTTSEngine
                self.engines[TTSEngine.EDGE_TTS.value] = {
                    "available": True,
                    "instance": EdgeTTSEngine(),
                    "quality": "High",
                    "speed": "Medium",
                    "languages": ["it", "en", "es", "fr", "de"]
                }
            except ImportError:
                self.engines[TTSEngine.EDGE_TTS.value] = {
                    "available": False,
                    "instance": None,
                    "quality": "High",
                    "speed": "Medium",
                    "languages": ["it", "en", "es", "fr", "de"]
                }

            # Piper TTS
            try:
                import piper
                from .engines.piper_tts_engine import PiperTTSEngine
                self.engines[TTSEngine.PIPER.value] = {
                    "available": True,
                    "instance": PiperTTSEngine(),
                    "quality": "High",
                    "speed": "Medium",
                    "languages": ["it", "en", "es", "fr", "de"]
                }
            except ImportError:
                self.engines[TTSEngine.PIPER.value] = {
                    "available": False,
                    "instance": None,
                    "quality": "High",
                    "speed": "Medium",
                    "languages": ["it", "en", "es", "fr", "de"]
                }

            # Coqui TTS
            try:
                from TTS.api import TTS
                from .engines.coqui_tts_engine import CoquiTTSEngine
                self.engines[TTSEngine.COQUI.value] = {
                    "available": True,
                    "instance": CoquiTTSEngine(),
                    "quality": "Very High",
                    "speed": "Slow",
                    "languages": ["it", "en", "es", "fr", "de", "multi"]
                }
            except ImportError:
                self.engines[TTSEngine.COQUI.value] = {
                    "available": False,
                    "instance": None,
                    "quality": "Very High",
                    "speed": "Slow",
                    "languages": ["it", "en", "es", "fr", "de", "multi"]
                }

        except Exception as e:
            self.logger.error(f"Errore nell'inizializzazione dei motori: {e}")

    def _load_config(self) -> Dict[str, Any]:
        """Carica la configurazione TTS."""
        config_file = os.path.join(self.config_dir, "tts_config.json")

        default_config = {
            "default_engine": TTSEngine.PYTTSX3.value,
            "auto_fallback": True,
            "cache_enabled": True,
            "max_cache_age_days": 7,
            "default_voice": "it-IT",
            "default_speed": 1.0,
            "default_pitch": 1.0,
            "default_volume": 1.0
        }

        try:
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    default_config.update(loaded_config)
        except Exception as e:
            self.logger.error(f"Errore nel caricamento della configurazione: {e}")

        return default_config

    def save_config(self):
        """Salva la configurazione corrente."""
        config_file = os.path.join(self.config_dir, "tts_config.json")

        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            self.logger.info("Configurazione TTS salvata")
        except Exception as e:
            self.logger.error(f"Errore nel salvataggio della configurazione: {e}")

    def get_available_engines(self) -> List[Dict[str, Any]]:
        """Restituisce la lista dei motori disponibili."""
        engines_info = []

        for engine_name, engine_info in self.engines.items():
            engines_info.append({
                "name": engine_name,
                "available": engine_info["available"],
                "quality": engine_info["quality"],
                "speed": engine_info["speed"],
                "languages": engine_info["languages"]
            })

        return engines_info

    def get_available_voices(self, engine: Optional[str] = None) -> List[Dict[str, Any]]:
        """Restituisce la lista delle voci disponibili per un motore specifico."""
        if engine is None:
            engine = self.current_engine

        if engine not in self.engines or not self.engines[engine]["available"]:
            return []

        try:
            engine_instance = self.engines[engine]["instance"]
            if engine_instance and hasattr(engine_instance, 'get_available_voices'):
                return engine_instance.get_available_voices()
        except Exception as e:
            self.logger.error(f"Errore nel recupero delle voci per {engine}: {e}")

        return []

    def set_engine(self, engine_name: str) -> bool:
        """Imposta il motore TTS corrente."""
        if engine_name in self.engines and self.engines[engine_name]["available"]:
            self.current_engine = engine_name
            self.config["default_engine"] = engine_name
            self.save_config()
            self.logger.info(f"Motore TTS cambiato a: {engine_name}")
            return True
        else:
            self.logger.error(f"Motore TTS non disponibile: {engine_name}")
            return False

    def synthesize(self, text: str, engine: Optional[str] = None,
                  voice: Optional[str] = None, speed: float = 1.0,
                  pitch: float = 1.0, volume: float = 1.0) -> Optional[str]:
        """
        Sintetizza il testo in audio usando il motore specificato.

        Args:
            text: Testo da sintetizzare
            engine: Motore TTS da utilizzare (None = motore corrente)
            voice: Voce da utilizzare
            speed: Velocità (0.5-2.0)
            pitch: Intonazione (0.5-2.0)
            volume: Volume (0.0-1.0)

        Returns:
            Path del file audio generato o None se errore
        """
        if engine is None:
            engine = self.current_engine

        if engine not in self.engines or not self.engines[engine]["available"]:
            self.logger.error(f"Motore TTS non disponibile: {engine}")
            if self.config.get("auto_fallback", True):
                return self._fallback_synthesis(text, voice, speed, pitch, volume)
            return None

        try:
            engine_instance = self.engines[engine]["instance"]

            # Per pyttsx3 e gTTS usa il sistema esistente
            if engine in [TTSEngine.PYTTSX3.value, TTSEngine.GTTS.value]:
                return self._synthesize_with_builtin_engine(text, engine, voice, speed, pitch, volume)
            elif engine_instance:
                return engine_instance.synthesize(text, voice or self.config["default_voice"],
                                               speed, pitch, volume)

        except Exception as e:
            self.logger.error(f"Errore nella sintesi con {engine}: {e}")
            if self.config.get("auto_fallback", True):
                return self._fallback_synthesis(text, voice, speed, pitch, volume)

        return None

    def _synthesize_with_builtin_engine(self, text: str, engine: str, voice: str,
                                      speed: float, pitch: float, volume: float) -> Optional[str]:
        """Sintetizza usando i motori built-in (pyttsx3, gTTS)."""
        try:
            if engine == TTSEngine.PYTTSX3.value:
                return self._synthesize_pyttsx3(text, voice, speed, pitch, volume)
            elif engine == TTSEngine.GTTS.value:
                return self._synthesize_gtts(text, voice, speed, pitch, volume)
        except Exception as e:
            self.logger.error(f"Errore nella sintesi built-in: {e}")
        return None

    def _synthesize_pyttsx3(self, text: str, voice: str, speed: float,
                           pitch: float, volume: float) -> Optional[str]:
        """Sintetizza usando pyttsx3."""
        try:
            import pyttsx3

            engine = pyttsx3.init()

            # Imposta velocità
            rate = engine.getProperty('rate')
            if rate:
                engine.setProperty('rate', int(rate * speed))

            # Imposta voce
            if voice:
                try:
                    engine.setProperty('voice', voice)
                except:
                    pass

            # Crea file temporaneo
            import tempfile
            import time

            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_path = temp_file.name

            # Questo è un workaround - pyttsx3 non salva facilmente su file
            # In una implementazione reale, si potrebbe usare un sistema di registrazione audio
            engine.say(text)
            engine.runAndWait()

            # Per ora restituiamo None, ma in produzione si salverebbe il file
            return None

        except Exception as e:
            self.logger.error(f"Errore pyttsx3: {e}")
            return None

    def _synthesize_gtts(self, text: str, voice: str, speed: float,
                        pitch: float, volume: float) -> Optional[str]:
        """Sintetizza usando gTTS."""
        try:
            import gtts
            import os

            # Estrai lingua dal voice (es. 'it-IT' -> 'it')
            lang_code = voice.split('-')[0] if voice else 'it'

            tts = gtts.gTTS(text, lang=lang_code)

            # Crea file nella cache
            import hashlib
            import time

            hash_input = f"{text}_{voice}_{speed}_{time.time()}"
            file_hash = hashlib.md5(hash_input.encode()).hexdigest()[:8]
            output_file = os.path.join(self.cache_dir, f"gtts_{file_hash}.mp3")

            tts.save(output_file)
            return output_file

        except Exception as e:
            self.logger.error(f"Errore gTTS: {e}")
            return None

    def _fallback_synthesis(self, text: str, voice: str, speed: float,
                           pitch: float, volume: float) -> Optional[str]:
        """Sintesi di fallback usando il motore più affidabile disponibile."""
        fallback_order = [
            TTSEngine.PYTTSX3.value,
            TTSEngine.GTTS.value,
            TTSEngine.EDGE_TTS.value,
            TTSEngine.PIPER.value,
            TTSEngine.COQUI.value
        ]

        for engine_name in fallback_order:
            if (engine_name in self.engines and
                self.engines[engine_name]["available"] and
                engine_name != self.current_engine):
                self.logger.info(f"Tentativo fallback con: {engine_name}")
                result = self.synthesize(text, engine_name, voice, speed, pitch, volume)
                if result:
                    return result

        self.logger.error("Tutti i motori TTS hanno fallito")
        return None

    def play_audio(self, audio_file: str, engine: Optional[str] = None) -> bool:
        """Riproduce un file audio."""
        if engine is None:
            engine = self.current_engine

        try:
            if engine in self.engines and self.engines[engine]["instance"]:
                instance = self.engines[engine]["instance"]
                if hasattr(instance, 'play_audio'):
                    return instance.play_audio(audio_file)

            # Fallback generico
            import subprocess
            result = subprocess.run(
                ["mpg123", audio_file],
                capture_output=True,
                timeout=60
            )
            return result.returncode == 0

        except Exception as e:
            self.logger.error(f"Errore nella riproduzione: {e}")
            return False

    def cleanup_cache(self, max_age_days: Optional[int] = None):
        """Pulisce la cache di tutti i motori."""
        if max_age_days is None:
            max_age_days = self.config.get("max_cache_age_days", 7)

        try:
            import time

            cutoff_time = time.time() - (max_age_days * 24 * 60 * 60)
            cleaned_count = 0

            for filename in os.listdir(self.cache_dir):
                filepath = os.path.join(self.cache_dir, filename)
                if os.path.getmtime(filepath) < cutoff_time:
                    os.remove(filepath)
                    cleaned_count += 1

            # Pulizia specifica per ogni motore
            for engine_info in self.engines.values():
                if engine_info["instance"] and hasattr(engine_info["instance"], 'cleanup_cache'):
                    engine_info["instance"].cleanup_cache(max_age_days)

            if cleaned_count > 0:
                self.logger.info(f"Cache pulita: {cleaned_count} file rimossi")

        except Exception as e:
            self.logger.error(f"Errore nella pulizia cache: {e}")

    def get_engine_info(self, engine_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Ottiene informazioni su un motore specifico."""
        if engine_name is None:
            engine_name = self.current_engine

        if engine_name in self.engines:
            return self.engines[engine_name]
        return None

# Istanza globale
tts_manager = TTSManager()

# Funzioni di utilità per retrocompatibilità
def get_available_engines():
    """Funzione di compatibilità."""
    return tts_manager.get_available_engines()

def synthesize_text(text, engine=None, voice=None, speed=1.0, pitch=1.0, volume=1.0):
    """Funzione di compatibilità."""
    return tts_manager.synthesize(text, engine, voice, speed, pitch, volume)

if __name__ == "__main__":
    print("🔊 Test TTS Manager...")

    # Mostra motori disponibili
    engines = tts_manager.get_available_engines()
    print(f"📦 Motori TTS disponibili: {len(engines)}")

    for engine in engines:
        status = "✅" if engine["available"] else "❌"
        print(f"  {status} {engine['name']} - {engine['quality']} quality")

    # Test sintesi
    print("\n🎤 Test sintesi vocale...")
    audio_file = tts_manager.synthesize(
        "Ciao! Sono il sistema TTS avanzato dell'assistente DSA.",
        engine="pyttsx3",
        voice="it-IT",
        speed=1.0
    )

    if audio_file:
        print(f"✅ Audio generato: {audio_file}")
    else:
        print("❌ Errore nella generazione audio")