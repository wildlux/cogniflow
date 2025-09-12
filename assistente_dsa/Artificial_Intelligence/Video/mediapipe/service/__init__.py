"""
MediaPipe service module.

NOTA: Questo modulo richiede dipendenze aggiuntive:
- pip install mediapipe flask

Se le dipendenze non sono installate, i servizi saranno disabilitati.
"""

import logging

logger = logging.getLogger(__name__)

# Tentativo import con gestione errori dettagliata
try:
    from .mediapipe_service import MediaPipeService

    logger.info("MediaPipe service caricato correttamente")
except ImportError as e:
    logger.warning(f"MediaPipe service disabilitato: {e}")
    logger.warning("Installare dipendenze: pip install mediapipe flask")
    MediaPipeService = None

try:
    from .mediapipe_processor import MediaPipeProcessor

    logger.info("MediaPipe processor caricato correttamente")
except ImportError as e:
    logger.warning(f"MediaPipe processor disabilitato: {e}")
    MediaPipeProcessor = None

__all__ = ["MediaPipeService", "MediaPipeProcessor"]
