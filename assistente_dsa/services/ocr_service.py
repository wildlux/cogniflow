#!/usr/bin/env python3
"""
OCR Service - Gestione dell'OCR (Optical Character Recognition)
"""

import logging
from typing import Optional
from PyQt6.QtCore import QObject, pyqtSignal

# Import delle librerie OCR esistenti
try:
    import pytesseract
    from PIL import Image

    OCR_AVAILABLE = True
except ImportError:
    pytesseract = None
    Image = None
    OCR_AVAILABLE = False


class OCRService(QObject):
    """
    Servizio per gestire l'OCR
    """

    # Segnali
    text_extracted = pyqtSignal(str)  # extracted_text
    processing_started = pyqtSignal(str)  # image_path
    processing_finished = pyqtSignal(str)  # image_path
    error_occurred = pyqtSignal(str)  # error_msg

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)

        if OCR_AVAILABLE:
            self.logger.info("OCR Service inizializzato")
        else:
            self.logger.warning("OCR non disponibile - servizio limitato")

    def process_image(self, image_path: str) -> bool:
        """Elabora un'immagine con OCR"""
        if not OCR_AVAILABLE:
            error_msg = "Servizio OCR non disponibile"
            self.logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            return False

        if not image_path or not self._is_valid_image(image_path):
            error_msg = "Percorso immagine non valido o immagine non supportata"
            self.logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            return False

        try:
            self.processing_started.emit(image_path)

            # Apri l'immagine
            image = Image.open(image_path)

            # Estrai il testo
            text = pytesseract.image_to_string(image, lang="ita+eng")

            if text and text.strip():
                self.logger.info(f"Testo estratto dall'immagine: {text[:50]}...")
                self.text_extracted.emit(text.strip())
                self.processing_finished.emit(image_path)
                return True
            else:
                error_msg = "Nessun testo rilevato nell'immagine"
                self.logger.warning(error_msg)
                self.error_occurred.emit(error_msg)
                return False

        except Exception as e:
            error_msg = f"Errore nell'elaborazione OCR: {str(e)}"
            self.logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            return False

    def _is_valid_image(self, image_path: str) -> bool:
        """Verifica se il file è un'immagine valida"""
        if not image_path:
            return False

        valid_extensions = [".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif"]
        import os

        _, ext = os.path.splitext(image_path.lower())

        return ext in valid_extensions and os.path.exists(image_path)

    def is_available(self) -> bool:
        """Verifica se il servizio OCR è disponibile"""
        return OCR_AVAILABLE

    def get_supported_languages(self) -> list:
        """Restituisce la lista delle lingue supportate"""
        if not OCR_AVAILABLE:
            return []

        try:
            return ["ita", "eng", "spa", "fra", "deu"]
        except Exception as e:
            self.logger.error(f"Errore recupero lingue OCR: {e}")
            return []

    def cleanup(self):
        """Pulisce le risorse del servizio OCR"""
        try:
            self.logger.info("OCR Service cleanup completato")
        except Exception as e:
            self.logger.error(f"Errore durante cleanup OCR Service: {e}")
