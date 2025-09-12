"""
MediaPipe service module.

⚠️  ATTENZIONE: MediaPipe richiede installazione manuale
=======================================================

Questo modulo fornisce servizi MediaPipe per visione computer avanzata.

DEPENDENZE RICHIESTE:
--------------------
1. Flask (installato): pip install flask ✅
2. MediaPipe: Richiede installazione manuale ❌

INSTALLAZIONE MEDIAPIPE:
-----------------------
MediaPipe non può essere installato via pip semplice a causa di:
- Dipendenze specifiche del sistema operativo
- Requisiti di compilazione complessi
- Versioni specifiche di altre librerie

Per installare MediaPipe:
1. Verifica requisiti: https://developers.google.com/mediapipe/framework/getting_started/install
2. Installa dipendenze OS (OpenCV, protobuf, etc.)
3. Usa wheel precompilato se disponibile per la tua piattaforma
4. Oppure compila da sorgente: https://github.com/google-ai-edge/mediapipe

GESTIONE ERRORI:
---------------
Il codice gestisce automaticamente l'assenza di MediaPipe:
- Servizi disabilitati gracefully
- Logging informativo
- Fallback ad altri backend (OpenCV)
"""

import logging

logger = logging.getLogger(__name__)

# Verifica Flask (dovrebbe essere disponibile)
try:
    import flask
    logger.info("✅ Flask disponibile per MediaPipe services")
except ImportError:
    logger.error("❌ Flask non disponibile - installare: pip install flask")

# Tentativo import MediaPipe con gestione dettagliata
try:
    import mediapipe as mp
    from .mediapipe_service import MediaPipeService
    from .mediapipe_processor import MediaPipeProcessor
    logger.info("✅ MediaPipe caricato correttamente - tutti i servizi disponibili")
except ImportError as e:
    logger.warning("⚠️  MediaPipe non disponibile - servizi disabilitati")
    logger.warning(f"   Errore: {e}")
    logger.warning("   Per abilitare: seguire istruzioni sopra")
    MediaPipeService = None
    MediaPipeProcessor = None

__all__ = ["MediaPipeService", "MediaPipeProcessor"]
