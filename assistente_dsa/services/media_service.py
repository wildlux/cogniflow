#!/usr/bin/env python3
"""
Media Service - Gestione dei file multimediali
"""

import logging
import os
from typing import Optional
from PyQt6.QtCore import QObject, pyqtSignal


class MediaService(QObject):
    """
    Servizio per gestire i file multimediali
    """

    # Segnali
    file_loaded = pyqtSignal(str, str)  # file_path, file_type
    file_error = pyqtSignal(str, str)  # file_path, error_msg
    processing_started = pyqtSignal(str)  # file_path
    processing_finished = pyqtSignal(str)  # file_path

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)

        # Tipi di file supportati
        self.supported_audio = [".mp3", ".wav", ".flac", ".aac", ".ogg"]
        self.supported_video = [".mp4", ".avi", ".mkv", ".mov", ".wmv"]
        self.supported_images = [".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".gif"]

        self.logger.info("Media Service inizializzato")

    def load_file(self, file_path: str) -> bool:
        """Carica un file multimediale"""
        if not file_path or not os.path.exists(file_path):
            error_msg = "File non trovato o percorso non valido"
            self.logger.error(error_msg)
            self.file_error.emit(file_path, error_msg)
            return False

        try:
            self.processing_started.emit(file_path)

            # Determina il tipo di file
            file_type = self._get_file_type(file_path)

            if not file_type:
                error_msg = "Tipo di file non supportato"
                self.logger.error(error_msg)
                self.file_error.emit(file_path, error_msg)
                return False

            # Qui dovremmo implementare la logica specifica per ciascun tipo
            # Per ora ci limitiamo a segnalare il caricamento
            self.logger.info(f"File caricato: {file_path} (tipo: {file_type})")
            self.file_loaded.emit(file_path, file_type)
            self.processing_finished.emit(file_path)

            return True

        except Exception as e:
            error_msg = f"Errore nel caricamento del file: {str(e)}"
            self.logger.error(error_msg)
            self.file_error.emit(file_path, error_msg)
            return False

    def _get_file_type(self, file_path: str) -> Optional[str]:
        """Determina il tipo di file"""
        _, ext = os.path.splitext(file_path.lower())

        if ext in self.supported_audio:
            return "audio"
        elif ext in self.supported_video:
            return "video"
        elif ext in self.supported_images:
            return "image"
        else:
            return None

    def get_supported_formats(self) -> dict:
        """Restituisce i formati supportati"""
        return {
            "audio": self.supported_audio,
            "video": self.supported_video,
            "images": self.supported_images,
        }

    def is_supported_file(self, file_path: str) -> bool:
        """Verifica se il file è supportato"""
        return self._get_file_type(file_path) is not None

    def cleanup(self):
        """Pulisce le risorse del servizio media"""
        try:
            self.logger.info("Media Service cleanup completato")
        except Exception as e:
            self.logger.error(f"Errore durante cleanup Media Service: {e}")
