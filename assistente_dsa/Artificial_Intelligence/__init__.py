"""
Modulo AI unificato per l'Assistente DSA
Contiene tutti i moduli di intelligenza artificiale organizzati
"""

# Esporta i moduli unificati
from . import Sintesi_Vocale
from . import Riconoscimento_Vocale
from . import Ollama

# Esporta le classi principali per accesso diretto
from .Sintesi_Vocale.managers.tts_manager import TTSThread
from .Sintesi_Vocale.managers.tts_engine_manager import tts_manager
from .Riconoscimento_Vocale.managers.speech_recognition_manager import (
    SpeechRecognitionThread,
)
from .Ollama.ollama_manager import OllamaManager, OllamaThread, OllamaModelsThread

__all__ = [
    "Sintesi_Vocale",
    "Riconoscimento_Vocale",
    "Ollama",
    "TTSThread",
    "tts_manager",
    "SpeechRecognitionThread",
    "OllamaManager",
    "OllamaThread",
    "OllamaModelsThread",
]
