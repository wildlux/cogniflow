# detection_handlers.py - Gestori per le funzioni di rilevamento video

import logging
from PyQt6.QtWidgets import QMessageBox


class DetectionHandlers:
    """Classe che gestisce tutte le funzioni di rilevamento video."""

    def __init__(self, main_window):
        self.main_window = main_window
        self.logger = logging.getLogger(__name__)

    def initialize_detection_system(self):
        """Inizializza il sistema di rilevamento basato sulle impostazioni."""
        try:
            detection_system = self.main_window.settings.get('detection_system', 'opencv')

            if detection_system == 'opencv':
                # Inizializza OpenCV per il rilevamento
                try:
                    # Use the VideoThread class which has OpenCV functionality
                    from .visual_background import VideoThread
                    self.main_window.hand_detector = VideoThread()
                    self.main_window.face_detector = VideoThread()  # Usa la stessa classe per entrambi
                    logging.info("Sistema di rilevamento OpenCV inizializzato")
                except ImportError:
                    logging.warning("OpenCV detector non disponibile, rilevamento disabilitato")
                    self.main_window.hand_detector = None
                    self.main_window.face_detector = None

            elif detection_system == 'mediapipe':
                # Inizializza MediaPipe per il rilevamento
                try:
                    # TODO: Create MediaPipeHandDetector class
                    # from .mediapipe.detector.mediapipe_detector import MediaPipeHandDetector
                    raise ImportError("MediaPipe detector not yet implemented")
                except ImportError:
                    logging.warning("MediaPipe detector non disponibile, uso OpenCV come fallback")
                    try:
                        from .visual_background import VideoThread
                        self.main_window.hand_detector = VideoThread()
                        self.main_window.face_detector = VideoThread()
                        logging.info("Sistema di rilevamento OpenCV inizializzato (fallback)")
                    except ImportError:
                        logging.warning("Nessun sistema di rilevamento disponibile")
                        self.main_window.hand_detector = None
                        self.main_window.face_detector = None
            else:
                logging.warning("Sistema di rilevamento '{detection_system}' non riconosciuto, uso OpenCV")
                try:
                    from .visual_background import VideoThread
                    self.main_window.hand_detector = VideoThread()
                    self.main_window.face_detector = VideoThread()
                    logging.info("Sistema di rilevamento OpenCV inizializzato")
                except ImportError:
                    logging.warning("OpenCV detector non disponibile, rilevamento disabilitato")
                    self.main_window.hand_detector = None
                    self.main_window.face_detector = None

        except Exception:
            logging.error("Errore nell'inizializzazione del sistema di rilevamento: {e}")
            # Fallback a rilevamento disabilitato
            self.main_window.hand_detector = None
            self.main_window.face_detector = None
