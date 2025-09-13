# visual_background.py

import cv2
import logging
import numpy as np
import math
import os
import asyncio
import logging
from PyQt6.QtCore import QThread, pyqtSignal, QSize, Qt
from PyQt6.QtGui import QImage, QPixmap

# Import Vision Language Detector - NUOVA IMPLEMENTAZIONE VLM
try:
    from .vision_language_detector import VisionLanguageDetector

    VLM_AVAILABLE = True
    logging.info("VisionLanguageDetector importato con successo")
except ImportError as e:
    VLM_AVAILABLE = False
    VisionLanguageDetector = None
    logging.warning(f"VisionLanguageDetector non disponibile: {e}")

# Import VLM Manager - NUOVA IMPLEMENTAZIONE
try:
    # Prova import relativo
    from ...Artificial_Intelligence.Ollama.vlm_manager import (
        VLMManager,
        get_vlm_manager,
    )

    VLM_MANAGER_AVAILABLE = True
    logging.info("VLM Manager importato con successo")
except ImportError:
    try:
        # Fallback: import assoluto
        import sys
        import os

        current_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(os.path.dirname(current_dir))
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)

        from assistente_dsa.Artificial_Intelligence.Ollama.vlm_manager import (
            VLMManager,
            get_vlm_manager,
        )

        VLM_MANAGER_AVAILABLE = True
        logging.info("VLM Manager importato con successo (fallback)")
    except ImportError as e:
        VLM_MANAGER_AVAILABLE = False
        VLMManager = None
        get_vlm_manager = None
        logging.warning(f"VLM Manager non disponibile: {e}")

# Import MediaPipe client - MANTIENI COME FALLBACK
try:
    from .mediapipe.client.mediapipe_client import MediaPipeClient

    MEDIAPIPE_CLIENT_AVAILABLE = True
    logging.info("MediaPipe client disponibile come fallback")
except ImportError:
    MEDIAPIPE_CLIENT_AVAILABLE = False
    MediaPipeClient = None
    logging.info("MediaPipe client non disponibile - solo VLM")

# MediaPipe imports
try:
    import mediapipe as mp  # type: ignore

    MEDIAPIPE_AVAILABLE = True
    mp_pose = mp.solutions.pose
    mp_drawing = mp.solutions.drawing_utils
    mp_drawing_styles = mp.solutions.drawing_styles
except ImportError:
    MEDIAPIPE_AVAILABLE = False
    mp_pose = None
    mp_drawing = None
    mp_drawing_styles = None
    logging.warning("MediaPipe non disponibile - rilevamento pose limitato")


class VideoThread(QThread):
    """
    Thread per la cattura e l'elaborazione del flusso video dalla webcam.
    """

    change_pixmap_signal = pyqtSignal(
        QPixmap
    )  # Invia QPixmap invece di dati raw per efficienza
    status_signal = pyqtSignal(str)
    hand_position_signal = pyqtSignal(int, int)  # x, y coordinates
    gesture_detected_signal = pyqtSignal(str)  # gesture type
    human_detected_signal = pyqtSignal(
        list
    )  # list of human bounding boxes [(x,y,w,h), ...]
    human_position_signal = pyqtSignal(int, int)  # center position of primary human

    def __init__(self, main_window=None):
        super().__init__()
        self._run_flag = True
        self.face_detection_enabled = False
        self.hand_detection_enabled = False
        self.gesture_recognition_enabled = False
        self.facial_expression_enabled = False
        self.left_hand_tracking_enabled = False
        self.right_hand_tracking_enabled = True  # Abilitato di default
        self.human_detection_enabled = (
            True  # LIDAR-like human detection enabled by default
        )
        self.main_window = main_window

<<<<<<< HEAD
        # Initialize Vision Language Detector
        self.vlm_detector = None
        if VLM_AVAILABLE and VisionLanguageDetector:
            try:
                self.vlm_detector = VisionLanguageDetector()
                logging.info("VisionLanguageDetector inizializzato nella VideoThread")
            except Exception as e:
                logging.warning(f"Errore inizializzazione VLM: {e}")
                self.vlm_detector = None

        # Initialize VLM Manager
        self.vlm_manager = None
        if VLM_MANAGER_AVAILABLE and get_vlm_manager:
            try:
                self.vlm_manager = get_vlm_manager()
                logging.info("VLM Manager inizializzato nella VideoThread")
            except Exception as e:
                logging.warning(f"Errore inizializzazione VLM Manager: {e}")
                self.vlm_manager = None

        # Initialize MediaPipe client (fallback)
        self.mediapipe_client = None
        self.use_mediapipe_service = True  # Flag to enable/disable MediaPipe service

        if MEDIAPIPE_CLIENT_AVAILABLE and MediaPipeClient:
            try:
                mediapipe_url = os.getenv(
                    "MEDIAPIPE_SERVICE_URL", "http://localhost:8001"
                )
                self.mediapipe_client = MediaPipeClient(mediapipe_url)
                logging.info(f"MediaPipe client initialized with URL: {mediapipe_url}")
            except Exception as e:
                logging.warning(f"Failed to initialize MediaPipe client: {e}")
                self.mediapipe_client = None
        else:
            logging.info("MediaPipe client not available, using local detection")

        # Carica i classificatori Haar per il rilevamento
        try:
            import cv2.data

            cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
            logging.info(f"Caricamento cascade da: {cascade_path}")

            self.face_cascade = cv2.CascadeClassifier(cascade_path)
            if self.face_cascade is None or self.face_cascade.empty():
                logging.warning(
                    "File Haar cascade per il rilevamento facciale non trovato o vuoto. Rilevamento facciale disabilitato."
                )
                self.face_cascade = None
            else:
                logging.info(
                    "Cascade Haar per rilevamento facciale caricato correttamente"
                )
        except Exception as e:
            logging.error(f"Errore nel caricamento del cascade Haar: {e}")
            self.face_cascade = None

        # Parametri per il rilevamento umano basato su contorni (LIDAR-like)
        self.human_min_area = 10000  # Area minima per considerare un umano
        self.human_max_area = 300000  # Area massima
        self.human_min_aspect = 0.3  # Rapporto aspetto minimo (larghezza/altezza)
        self.human_max_aspect = 1.2  # Rapporto aspetto massimo

        # Per le mani, usiamo un approccio alternativo basato sulla pelle
        # TODO: Calibration - Adjust skin color thresholds based on lighting conditions
        self.lower_skin = np.array([0, 20, 70], dtype=np.uint8)
        self.upper_skin = np.array([20, 255, 255], dtype=np.uint8)

        # Parametri per il riconoscimento dei gesti
        self.prev_hand_positions = []
        self.gesture_history = []
        self.selected_widget = None
        self.drag_start_time: float = 0.0
        self.is_dragging = False
        self.drag_timer = 0
        # TODO: Calibration - Adjust drag threshold based on user preference (seconds)
        self.DRAG_THRESHOLD = 6.0  # 6 secondi per iniziare il trascinamento

        # Parametri per il riconoscimento delle espressioni facciali
        self.prev_face_positions = []
        self.expression_history = []

        # Parametri per il riconoscimento avanzato delle mani
        self.hand_tracking = {
            "left": {
                "position": None,
                "fingers": 0,
                "gesture": "unknown",
                "confidence": 0,
            },
            "right": {
                "position": None,
                "fingers": 0,
                "gesture": "unknown",
                "confidence": 0,
            },
        }
        self.active_inputs = set()  # Traccia dispositivi attivi (mani + mouse)

        # Backend selection - OpenCV only
        self.current_backend = "opencv"

    def set_backend(self, backend):
        """Imposta il backend per il rilevamento (solo OpenCV supportato)."""
        if backend != "opencv":
            logging.warning(f"Backend '{backend}' non supportato. Usando OpenCV.")
            backend = "opencv"

        self.current_backend = backend
        logging.info(f"Backend impostato a: {backend}")

    def set_vm_mode(self, enabled):
        """Imposta la modalità macchina virtuale per MediaPipe."""
        self.vm_mode = enabled
        logging.info(f"Modalità VM {'attivata' if enabled else 'disattivata'}")

        if enabled and self.current_backend == "mediapipe":
            # Inizializza il client per la comunicazione con la VM
            try:
                from ..mediapipe.client.mediapipe_client import MediaPipeClient

                mediapipe_url = os.getenv(
                    "MEDIAPIPE_SERVICE_URL", "http://localhost:8001"
                )
                self.mediapipe_client = MediaPipeClient(mediapipe_url)
                logging.info(f"Client MediaPipe VM inizializzato: {mediapipe_url}")
            except Exception as e:
                logging.error(f"Errore inizializzazione client VM: {e}")
                self.mediapipe_client = None
        elif not enabled:
            # Ritorna alla modalità locale
            if hasattr(self, "mediapipe_client"):
                self.mediapipe_client = None

    def run(self):
        """Metodo principale del thread."""
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            self.status_signal.emit("Errore: Impossibile aprire la webcam.")
            self._run_flag = False
            return

        self.status_signal.emit("Webcam avviata. Caricamento...")

        while self._run_flag:
            ret, frame = self.cap.read()
            if ret:
                # ==========================================================
                # Modifica qui per invertire orizzontalmente l'immagine
                # Il valore 1 indica l'inversione orizzontale.
                # ==========================================================
                frame = cv2.flip(frame, 1)

                # ==========================================================
                # Logica di rilevamento faccia, mani, gesti ed espressioni
                # ==========================================================

                # Mostra sempre lo stato dei rilevamenti
                status_text = ""
                if self.face_detection_enabled:
                    status_text += "Faccia: ON  "
                else:
                    status_text += "Faccia: OFF  "

                if self.hand_detection_enabled:
                    if (
                        self.left_hand_tracking_enabled
                        and self.right_hand_tracking_enabled
                    ):
                        status_text += "Mani: SX+DX  "
                    elif self.left_hand_tracking_enabled:
                        status_text += "Mani: SX  "
                    elif self.right_hand_tracking_enabled:
                        status_text += "Mani: DX  "
                    else:
                        status_text += "Mani: OFF  "
                else:
                    status_text += "Mani: OFF  "

                if self.gesture_recognition_enabled:
                    status_text += "Gesti: ON  "
                else:
                    status_text += "Gesti: OFF  "

                if self.facial_expression_enabled:
                    status_text += "Espressioni: ON  "
                else:
                    status_text += "Espressioni: OFF  "

                if self.human_detection_enabled:
                    status_text += "Umani: ON"
                else:
                    status_text += "Umani: OFF"

                cv2.putText(
                    frame,
                    status_text,
                    (10, frame.shape[0] - 20),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (255, 255, 255),
                    2,
                )

                # Applica i rilevamenti nell'ordine corretto
                if self.face_detection_enabled:
                    frame = self.detect_faces(frame)

                if self.hand_detection_enabled:
                    frame = self.detect_hands(frame)

                if self.gesture_recognition_enabled:
                    frame = self.detect_hand_gestures(frame)

                if self.facial_expression_enabled:
                    frame = self.detect_facial_expressions(frame)

                if self.human_detection_enabled:
                    frame = self.detect_humans(frame)

                # ===========================================
                # Integrazione VLM Manager per analisi avanzata
                # ===========================================
                if self.vlm_manager and self.vlm_manager.is_initialized:
                    try:
                        # Analizza il frame con VLM per gesture, OCR, etc.
                        vlm_results = self.vlm_manager.analyze_frame(frame)

                        # Elabora risultati gesture
                        if "gestures" in vlm_results and vlm_results["gestures"]:
                            gesture = vlm_results["gestures"][0]
                            gesture_type = gesture.get("gesture", "unknown")

                            # Invia segnale gesture rilevata
                            self.gesture_detected_signal.emit(gesture_type)

                            # Aggiungi testo informativo al frame
                            cv2.putText(
                                frame,
                                f"VLM Gesture: {gesture_type}",
                                (10, frame.shape[0] - 60),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                0.7,
                                (0, 255, 0),
                                2,
                            )

                        # Elabora risultati umani
                        if "humans" in vlm_results and vlm_results["humans"]:
                            humans_count = len(vlm_results["humans"])
                            self.human_detected_signal.emit(vlm_results["humans"])

                            # Aggiungi testo informativo al frame
                            cv2.putText(
                                frame,
                                f"VLM Humans: {humans_count}",
                                (10, frame.shape[0] - 100),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                0.7,
                                (255, 0, 255),
                                2,
                            )

                        # Aggiungi indicatore VLM attivo
                        cv2.putText(
                            frame,
                            "VLM: ACTIVE",
                            (frame.shape[1] - 120, 30),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.6,
                            (0, 255, 255),
                            2,
                        )

                    except Exception as e:
                        logging.warning(f"Errore analisi VLM: {e}")
                        # Aggiungi indicatore errore VLM
                        cv2.putText(
                            frame,
                            "VLM: ERROR",
                            (frame.shape[1] - 120, 30),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.6,
                            (0, 0, 255),
                            2,
                        )

                # Converti il frame in QPixmap per efficienza
                rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w = rgb_image.shape[:2]
                # Converti in bytes per QImage
                bytes_per_line = 3 * w
                # Converti esplicitamente in bytes
                image_bytes = bytes(rgb_image.tobytes())
                q_image = QImage(
                    image_bytes, w, h, bytes_per_line, QImage.Format.Format_RGB888
                )
                pixmap = QPixmap.fromImage(q_image)
                # Invia QPixmap invece di dati raw per ridurre uso memoria
                self.change_pixmap_signal.emit(pixmap)
            else:
                self.status_signal.emit("Errore di lettura del frame dalla webcam.")
                break

        # Rilascia la webcam quando il thread si ferma
        self.cap.release()
        logging.info("VideoThread terminato e webcam rilasciata.")

    def detect_faces(self, frame):
        """Rileva le facce nel frame e disegna rettangoli."""
        # Prima prova con approccio MediaPipe-style se possibile
        try:
            # Usa approccio ibrido MediaPipe-OpenCV
            # Face detection using OpenCV only
            return frame
        except Exception as e:
            logging.warning(
                f"MediaPipe-style face detection failed: {e}, falling back to OpenCV"
            )

        # Fallback a OpenCV
        if self.face_cascade is None:
            # Se il cascade non è disponibile, mostra un messaggio
            cv2.putText(
                frame,
                "Rilevamento faccia non disponibile",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 0, 255),
                2,
            )
            return frame

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Migliora il contrasto per migliore rilevamento
        gray = cv2.equalizeHist(gray)

        # Parametri ottimizzati per il rilevamento facciale
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,  # Leggermente più permissivo
            minNeighbors=2,  # Ridotto per più rilevamenti
            minSize=(20, 20),  # Dimensione minima ancora più piccola
            maxSize=(400, 400),  # Dimensione massima più grande
            flags=cv2.CASCADE_SCALE_IMAGE,
        )

        # Se non trova facce con parametri normali, prova con parametri più permissivi
        if len(faces) == 0:
            faces = self.face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.2,  # Più permissivo
                minNeighbors=1,  # Molto permissivo
                minSize=(15, 15),  # Molto piccolo
                maxSize=(500, 500),  # Molto grande
                flags=cv2.CASCADE_SCALE_IMAGE,
            )

        # Logging dettagliato per debug
        logging.debug(f"Rilevamento facciale OpenCV: {len(faces)} facce trovate")

        # Mostra sempre lo stato del rilevamento con più dettagli
        if len(faces) > 0:
            cv2.putText(
                frame,
                f"Faccia rilevata: {len(faces)}",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 255, 0),
                2,
            )
            logging.info(f"Rilevamento facciale riuscito: {len(faces)} facce")
        else:
            cv2.putText(
                frame,
                "Nessuna faccia rilevata",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 255, 255),
                2,
            )
            logging.debug(
                "Nessuna faccia rilevata - possibili cause: illuminazione, angolazione, occlusioni"
            )

        for x, y, w, h in faces:
            cv2.rectangle(
                frame, (x, y), (x + w, y + h), (255, 0, 0), 3
            )  # Rettangolo più spesso
            cv2.putText(
                frame,
                "Faccia",
                (x, y - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 0, 0),
                1,
            )

            # Aggiungi informazioni di debug sul rettangolo
            cv2.putText(
                frame,
                f"({x},{y}) {w}x{h}",
                (x, y + h + 20),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.4,
                (255, 0, 0),
                1,
            )

        return frame

    def detect_hand_gestures(self, frame):
        """Rileva i gesti delle mani avanzati con riconoscimento destra/sinistra e dita."""
        if not self.gesture_recognition_enabled:
            return frame

        # Using OpenCV detection only

        # Fallback a OpenCV tradizionale
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, self.lower_skin, self.upper_skin)

        # Operazioni morfologiche avanzate
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

        # Trova i contorni con approssimazione migliore
        contours, _ = cv2.findContours(
            mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_TC89_L1
        )

        detected_hands = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > 5000:  # Area minima per considerare un oggetto
                x, y, w, h = cv2.boundingRect(contour)
                aspect_ratio = w / h if h > 0 else 0

                if 0.4 < aspect_ratio < 2.5:  # Range più ampio per diverse orientamenti
                    # Filtro intelligente per evitare confusione con volti
                    # Se il riconoscimento facciale è abilitato, permetti aree più grandi
                    # per non escludere facce che potrebbero sembrare mani
                    max_area = 100000 if self.face_detection_enabled else 50000

                    if area > max_area:
                        continue  # Troppo grande per essere una mano/faccia

                    # Controllo dimensione per mani realistiche
                    if area < 80000:  # Solo processa oggetti di dimensione ragionevole
                        # Analisi avanzata della mano
                        hand_info = self.analyze_hand_advanced(
                            contour, x, y, w, h, frame.shape[1]
                        )

                        if hand_info is None:
                            continue

                        if (
                            hand_info["confidence"] > 0.3
                        ):  # Solo mani con buona confidenza
                            # Controlla se il tracciamento per questa mano è abilitato
                            hand_type = hand_info["hand_type"]
                            if (
                                hand_type == "left"
                                and not self.left_hand_tracking_enabled
                            ) or (
                                hand_type == "right"
                                and not self.right_hand_tracking_enabled
                            ):
                                continue  # Salta questa mano se il tracciamento è disabilitato

                        detected_hands.append((x, y, w, h, hand_info))

                        # Colore diverso per mano destra e sinistra
                        if hand_info["hand_type"] == "right":
                            color = (0, 255, 0)  # Verde per destra
                        else:
                            color = (255, 0, 255)  # Magenta per sinistra

                        # Disegna rettangolo e informazioni
                        cv2.rectangle(frame, (x, y), (x + w, y + h), color, 3)

                        # Info sulla mano
                        info_text = f"{hand_info['hand_type'].upper()}: {hand_info['fingers']} dita, {hand_info['gesture']}"
                        cv2.putText(
                            frame,
                            info_text,
                            (x, y - 15),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.5,
                            color,
                            1,
                        )

                        # Info sulle dita individuali
                        finger_text = "Pollice:{'ON' if hand_info['thumb'] else 'OFF'} Indice:{'ON' if hand_info['index'] else 'OFF'}"
                        cv2.putText(
                            frame,
                            finger_text,
                            (x, y + h + 15),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.4,
                            color,
                            1,
                        )

                        # Emit signals for hand position and gesture
                        hand_center_x = x + w // 2
                        hand_center_y = y + h // 2
                        self.hand_position_signal.emit(hand_center_x, hand_center_y)
                        self.gesture_detected_signal.emit(hand_info["gesture"])

                        # Add visual cursor indicator
                        cursor_color = (
                            (0, 255, 0)
                            if hand_info["gesture"] == "Open Hand"
                            else (0, 0, 255)
                        )
                        cv2.circle(
                            frame, (hand_center_x, hand_center_y), 10, cursor_color, 2
                        )
                        cv2.circle(
                            frame, (hand_center_x, hand_center_y), 2, cursor_color, -1
                        )

                        # Gestisci l'interazione con l'interfaccia
                        frame = self.handle_advanced_hand_interaction(
                            frame, x, y, w, h, hand_info
                        )

        # Aggiorna il tracking delle mani
        self.update_hand_tracking(detected_hands)

        # Mostra statistiche
        self.display_hand_statistics(frame, detected_hands)

        return frame

    def detect_hands(self, frame):
        """Rileva le mani nel frame usando il colore della pelle."""
        if not self.hand_detection_enabled:
            return frame

        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, self.lower_skin, self.upper_skin)

        # Operazioni morfologiche per migliorare la maschera
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

        # Trova i contorni nell'immagine binaria
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        hand_count = 0
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > 3000:  # Soglia ridotta per più rilevamenti
                x, y, w, h = cv2.boundingRect(contour)
                # Filtra per proporzioni ragionevoli (mani non troppo strette o larghe)
                aspect_ratio = w / h if h > 0 else 0
                if 0.5 < aspect_ratio < 2.0:
                    cv2.rectangle(
                        frame, (x, y), (x + w, y + h), (0, 255, 0), 2
                    )  # Verde per mani base
                    cv2.putText(
                        frame,
                        "Mano",
                        (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        (0, 255, 0),
                        1,
                    )
                    hand_count += 1

        # Mostra lo stato del riconoscimento mani
        if hand_count > 0:
            cv2.putText(
                frame,
                f"Mani rilevate: {hand_count}",
                (10, 60),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 255, 0),
                2,
            )
        else:
            cv2.putText(
                frame,
                "Nessuna mano rilevata",
                (10, 60),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 255, 0),
                2,
            )

        return frame

    def detect_humans(self, frame):
        """Rileva figure umane usando MediaPipe service o fallback OpenCV."""
        if not self.human_detection_enabled:
            return frame

        # Using OpenCV detection only

        # Fallback sempre attivo a OpenCV migliorato
        logging.info("Utilizzo rilevamento pose OpenCV")
        return self.detect_humans_opencv(frame)

        # Fallback to original OpenCV method
        return self.detect_humans_opencv(frame)



            if pose_result and pose_result.get("detected"):
                # Draw pose landmarks
                frame = self.draw_pose_landmarks(frame, pose_result)

                # Extract bounding boxes for compatibility
                detected_humans = []
                if pose_result.get("bbox"):
                    bbox = pose_result["bbox"]
                    detected_humans.append(
                        (bbox["x"], bbox["y"], bbox["width"], bbox["height"])
                    )

                # Emit signals
                if detected_humans:
                    self.human_detected_signal.emit(detected_humans)

                    # Calculate center position
                    if pose_result.get("bbox"):
                        bbox = pose_result["bbox"]
                        center_x = bbox["x"] + bbox["width"] // 2
                        center_y = bbox["y"] + bbox["height"] // 2
                        self.human_position_signal.emit(center_x, center_y)

                # Show detection status
                confidence = pose_result.get("confidence", 0.0)
                cv2.putText(
                    frame,
                    f"MediaPipe: Pose rilevata ({confidence:.2f})",
                    (10, 150),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (0, 255, 0),
                    2,
                )

                return frame

            else:
                # No pose detected
                cv2.putText(
                    frame,
                    "MediaPipe: Nessuna posa rilevata",
                    (10, 150),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (0, 255, 255),
                    2,
                )
                return frame

        except Exception as e:
            logging.error(f"MediaPipe pose detection error: {e}")
            return None

    def detect_humans_opencv(self, frame):
        """Rilevamento umani con OpenCV (metodo originale - fallback)."""
        # Verifica che abbiamo i parametri necessari
        if not hasattr(self, "human_min_area"):
            return frame

        # Usa rilevamento basato su movimento e forma per umani
        # Approccio semplificato che analizza i contorni più grandi
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Applica filtro gaussiano per ridurre rumore
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)

        # Rilevamento edges con Canny
        edges = cv2.Canny(blurred, 50, 150)

        # Operazioni morfologiche per chiudere i contorni
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (7, 7))
        closed = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)

        # Trova contorni
        contours, _ = cv2.findContours(
            closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        detected_humans = []
        primary_human_center = None

        for contour in contours:
            area = cv2.contourArea(contour)

            # Filtra per area (umani dovrebbero avere una certa dimensione)
            if self.human_min_area < area < self.human_max_area:
                # Ottieni bounding box
                x, y, w, h = cv2.boundingRect(contour)

                # Filtra per rapporto aspetto (umani sono generalmente verticali)
                aspect_ratio = w / h if h > 0 else 0
                if self.human_min_aspect < aspect_ratio < self.human_max_aspect:
                    # Calcola circolarità e solidità per filtrare forme umane
                    perimeter = cv2.arcLength(contour, True)
                    if perimeter > 0:
                        circularity = 4 * math.pi * area / (perimeter * perimeter)
                        hull = cv2.convexHull(contour)
                        hull_area = cv2.contourArea(hull)
                        solidity = area / hull_area if hull_area > 0 else 0

                        # Umani hanno generalmente bassa circolarità e alta solidità
                        if circularity < 0.8 and solidity > 0.7:
                            # Calcola confidenza basata su area e forma
                            confidence = min(
                                1.0, (area / self.human_max_area) * 0.8 + solidity * 0.2
                            )

                            if confidence > 0.4:  # Soglia di confidenza
                                detected_humans.append((x, y, w, h))

                                # Disegna rettangolo per l'umano rilevato
                                color = (
                                    (0, 255, 0) if confidence > 0.7 else (0, 165, 255)
                                )
                                cv2.rectangle(frame, (x, y), (x + w, y + h), color, 3)

                                # Calcola centro dell'umano
                                center_x = x + w // 2
                                center_y = y + h // 2

                                # Info sull'umano rilevato
                                info_text = f"Umano: {confidence:.2f}"
                                cv2.putText(
                                    frame,
                                    info_text,
                                    (x, y - 10),
                                    cv2.FONT_HERSHEY_SIMPLEX,
                                    0.6,
                                    color,
                                    2,
                                )

                                # Disegna centro come punto di riferimento (LIDAR-like)
                                cv2.circle(frame, (center_x, center_y), 8, color, -1)
                                cv2.circle(frame, (center_x, center_y), 12, color, 2)

                                # Il primo umano rilevato è considerato primario
                                if primary_human_center is None:
                                    primary_human_center = (center_x, center_y)

        # Mostra statistiche rilevamento umani
        if detected_humans:
            cv2.putText(
                frame,
                f"OpenCV: Umani rilevati: {len(detected_humans)}",
                (10, 150),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 255, 0),
                2,
            )

            # Emit signals per umani rilevati
            self.human_detected_signal.emit(detected_humans)
            if primary_human_center:
                self.human_position_signal.emit(
                    primary_human_center[0], primary_human_center[1]
                )
        else:
            cv2.putText(
                frame,
                "OpenCV: Nessun umano rilevato",
                (10, 150),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 255, 255),
                2,
            )

        return frame

    def draw_pose_landmarks(self, frame, pose_data):
        """Disegna i landmark della posa sul frame."""
        if not pose_data.get("landmarks"):
            return frame

        height, width = frame.shape[:2]

        # Draw pose connections (simplified)
        pose_connections = [
            (11, 12),
            (11, 13),
            (13, 15),
            (15, 17),
            (15, 19),
            (15, 21),  # Left arm
            (12, 14),
            (14, 16),
            (16, 18),
            (16, 20),
            (16, 22),  # Right arm
            (11, 23),
            (12, 24),
            (23, 24),  # Shoulders to hips
            (23, 25),
            (25, 27),
            (27, 29),
            (29, 31),  # Left leg
            (24, 26),
            (26, 28),
            (28, 30),
            (30, 32),  # Right leg
        ]

        landmarks = pose_data["landmarks"]

        # Draw connections
        for connection in pose_connections:
            start_idx, end_idx = connection
            if start_idx < len(landmarks) and end_idx < len(landmarks):
                start_lm = landmarks[start_idx]
                end_lm = landmarks[end_idx]

                start_x = int(start_lm["x"] * width)
                start_y = int(start_lm["y"] * height)
                end_x = int(end_lm["x"] * width)
                end_y = int(end_lm["y"] * height)

                cv2.line(frame, (start_x, start_y), (end_x, end_y), (255, 0, 0), 2)

        # Draw landmarks
        for landmark in landmarks:
            x = int(landmark["x"] * width)
            y = int(landmark["y"] * height)
            cv2.circle(frame, (x, y), 5, (0, 255, 0), -1)

        return frame

    def analyze_hand_shape(self, contour, x, y, w, h):
        """Analizza la forma del contorno per determinare il gesto della mano."""
        # Calcola la convessità
        hull = cv2.convexHull(contour)
        hull_area = cv2.contourArea(hull)
        contour_area = cv2.contourArea(contour)

        if hull_area > 0:
            solidity = contour_area / hull_area
        else:
            solidity = 0

        # Calcola il perimetro e la compattezza
        perimeter = cv2.arcLength(contour, True)
        if perimeter > 0:
            compactness = (4 * math.pi * contour_area) / (perimeter * perimeter)
        else:
            compactness = 0

        # Calcola l'aspetto ratio
        aspect_ratio = w / h if h > 0 else 0

        # Calcola i difetti di convessità per contare le dita
        hull_indices = cv2.convexHull(contour, returnPoints=False)

        # Verifica che gli indici siano validi e in ordine monotono
        defects = None
        if hull_indices is not None and len(hull_indices) > 0:
            try:
                # Verifica che gli indici siano in ordine crescente
                if np.all(hull_indices[:-1] <= hull_indices[1:]):
                    defects = cv2.convexityDefects(contour, hull_indices)
                else:
                    # Se non sono in ordine, riordina
                    sorted_indices = np.sort(hull_indices.flatten())
                    defects = cv2.convexityDefects(
                        contour, sorted_indices.reshape(-1, 1)
                    )
            except cv2.error as e:
                # Se si verifica un errore, logga e continua senza difetti
                print(f"Errore in convexityDefects (analyze_hand_shape): {e}")
                defects = None

        finger_count = 0
        if defects is not None:
            for i in range(defects.shape[0]):
                s, e, f, d = defects[i, 0]
                start = tuple(contour[s][0])
                end = tuple(contour[e][0])
                far = tuple(contour[f][0])

                # Calcola la distanza dal punto lontano al contorno
                a = math.sqrt((end[0] - start[0]) ** 2 + (end[1] - start[1]) ** 2)
                b = math.sqrt((far[0] - start[0]) ** 2 + (far[1] - start[1]) ** 2)
                c = math.sqrt((end[0] - far[0]) ** 2 + (end[1] - far[1]) ** 2)

                # Usa la formula di Erone per calcolare l'area
                s = (a + b + c) / 2
                area = math.sqrt(max(0, s * (s - a) * (s - b) * (s - c)))

                # Calcola la distanza dal punto lontano
                distance = (2 * area) / a if a > 0 else 0

                # Conta le dita basandosi sulla profondità dei difetti
                if distance > 15:  # Soglia ridotta per più sensibilità
                    finger_count += 1

        # Algoritmo migliorato per distinguere mano aperta/chiusa
        # Mano chiusa: alta compattezza, bassa solidità, poche dita
        # Mano aperta: bassa compattezza, alta solidità, molte dita

        # Criteri per mano chiusa:
        # - Alta compattezza (forma più circolare)
        # - Bassa solidità (molti spazi vuoti)
        # - Poche dita rilevate
        # - Aspect ratio vicino a 1 (quasi quadrata)

        is_closed_by_compactness = compactness > 0.6
        is_closed_by_solidity = solidity < 0.7
        is_closed_by_fingers = finger_count <= 2
        is_closed_by_aspect = 0.7 < aspect_ratio < 1.4

        # Criteri per mano aperta:
        # - Bassa compattezza (forma allungata)
        # - Alta solidità (poca concavità)
        # - Molte dita rilevate
        is_open_by_compactness = compactness < 0.4
        is_open_by_solidity = solidity > 0.8
        is_open_by_fingers = finger_count >= 3

        # Decisione finale
        if (
            is_closed_by_compactness and is_closed_by_solidity and is_closed_by_fingers
        ) or (is_closed_by_aspect and is_closed_by_fingers):
            return "Closed Hand"
        elif is_open_by_compactness and is_open_by_solidity and is_open_by_fingers:
            return "Open Hand"
        else:
            return "Partial Gesture"

    def is_face_like_region(self, frame, x, y, w, h):
        """Verifica se una regione sembra un volto per evitare confusione con le mani."""
        if self.face_cascade is None:
            return False

        # Estrai la regione di interesse
        roi = frame[y : y + h, x : x + w]
        if roi.size == 0:
            return False

        # Converti in scala di grigi
        gray_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

        # Rileva volti nella regione
        faces = self.face_cascade.detectMultiScale(
            gray_roi, scaleFactor=1.1, minNeighbors=3, minSize=(20, 20)
        )

        # Se viene rilevato un volto nella regione, è probabile che sia un volto
        return len(faces) > 0

    def determine_hand_orientation_advanced(
        self, contour, x, y, w, h, center_x, center_y, frame_width
    ):
        """
        Algoritmo avanzato per determinare se una mano è destra o sinistra.
        Ottimizzato per riconoscere correttamente entrambe le mani.
        """
        try:
            # Logging per debug della mano sinistra
            is_left_side = center_x < frame_width // 2
            logging.debug(
                f"Analisi mano - Posizione: {center_x}/{frame_width} ({'SINISTRA' if is_left_side else 'DESTRA'})"
            )

            # Metodo 1: Analisi migliorata della posizione del pollice
            thumb_based_result = self.analyze_thumb_position(contour, x, y, w, h)
            if thumb_based_result != "unknown":
                # Correzione specifica per mano sinistra
                if is_left_side and thumb_based_result == "right":
                    # Se siamo a sinistra ma il pollice indica destra, potrebbe essere un falso positivo
                    logging.debug(
                        "Correzione: pollice destra rilevata a sinistra, potrebbe essere mano sinistra"
                    )
                    return "left"
                elif not is_left_side and thumb_based_result == "left":
                    # Se siamo a destra ma il pollice indica sinistra, potrebbe essere un falso positivo
                    logging.debug(
                        "Correzione: pollice sinistra rilevata a destra, potrebbe essere mano destra"
                    )
                    return "right"
                else:
                    logging.debug(
                        f"Mano classificata tramite pollice: {thumb_based_result}"
                    )
                    return thumb_based_result

            # Metodo 2: Analisi dell'orientamento con correzioni per mano sinistra
            orientation_result = self.analyze_hand_orientation(contour, x, y, w, h)
            if orientation_result != "unknown":
                logging.debug(
                    f"Mano classificata tramite orientamento: {orientation_result}"
                )
                return orientation_result

            # Metodo 3: Analisi basata sulla posizione con correzioni
            position_result = self.analyze_position_based(center_x, frame_width)
            if position_result != "unknown":
                logging.debug(f"Mano classificata tramite posizione: {position_result}")
                return position_result

            # Metodo 4: Analisi dell'angolo con considerazioni per mano sinistra
            angle_result = self.analyze_contour_angle(contour)
            if angle_result != "unknown":
                logging.debug(f"Mano classificata tramite angolo: {angle_result}")
                return angle_result

            # Fallback finale con logging
            fallback_result = "left" if center_x < frame_width // 2 else "right"
            logging.debug(f"Fallback finale: {fallback_result}")
            return fallback_result

        except Exception as e:
            logging.warning(f"Errore analisi orientamento mano: {e}")
            return "left" if center_x < frame_width // 2 else "right"

    def analyze_thumb_position_improved(self, contour, x, y, w, h, is_left_side):
        """
        Analizza migliorata della posizione del pollice con considerazioni specifiche per mano sinistra.
        """
        try:
            hull = cv2.convexHull(contour)
            hull_indices = cv2.convexHull(contour, returnPoints=False)

            if hull_indices is None or len(hull_indices) < 3:
                return "unknown"

            defects = cv2.convexityDefects(contour, hull_indices)
            if defects is None:
                return "unknown"

            # Trova punti estremi
            leftmost = tuple(contour[contour[:, :, 0].argmin()][0])
            rightmost = tuple(contour[contour[:, :, 0].argmax()][0])
            topmost = tuple(contour[contour[:, :, 1].argmin()][0])
            bottommost = tuple(contour[contour[:, :, 1].argmax()][0])

            width_diff = rightmost[0] - leftmost[0]
            height_diff = bottommost[1] - topmost[1]

            # Logica migliorata per riconoscere il pollice
            if width_diff > w * 0.25:  # Soglia ridotta per essere più sensibili
                left_protrusion = leftmost[0] - x
                right_protrusion = (x + w) - rightmost[0]

                # Considerazioni specifiche per la posizione della mano
                if is_left_side:
                    # Per mano sinistra, il pollice tende ad essere più prominente a sinistra
                    if left_protrusion > right_protrusion * 1.2:
                        return "left"
                    elif right_protrusion > left_protrusion * 1.8:
                        return "right"
                else:
                    # Per mano destra, il pollice tende ad essere più prominente a destra
                    if right_protrusion > left_protrusion * 1.2:
                        return "right"
                    elif left_protrusion > right_protrusion * 1.8:
                        return "left"

            return "unknown"

        except Exception as e:
            logging.debug(f"Errore analisi pollice migliorata: {e}")
            return "unknown"

    def analyze_hand_orientation(self, contour, x, y, w, h):
        """
        Analizza l'orientamento generale della mano basato sulla distribuzione dei punti.
        """
        try:
            # Calcola il momento del contorno per determinare l'orientamento
            moments = cv2.moments(contour)
            if moments["m00"] == 0:
                return "unknown"

            # Centroide
            cx = int(moments["m10"] / moments["m00"])
            cy = int(moments["m01"] / moments["m00"])

            # Calcola l'orientamento basato sulla distribuzione dei punti rispetto al centroide
            left_points = 0
            right_points = 0

            for point in contour:
                px, py = point[0]
                if px < cx:
                    left_points += 1
                else:
                    right_points += 1

            # Se c'è una distribuzione asimmetrica, può indicare l'orientamento
            total_points = len(contour)
            left_ratio = left_points / total_points
            right_ratio = right_points / total_points

            # Soglia per determinare l'asimmetria
            asymmetry_threshold = 0.6

            if left_ratio > asymmetry_threshold:
                return "left"  # Più punti a sinistra = probabilmente mano sinistra
            elif right_ratio > asymmetry_threshold:
                return "right"  # Più punti a destra = probabilmente mano destra

            return "unknown"

        except Exception as e:
            logging.debug(f"Errore nell'analisi dell'orientamento: {e}")
            return "unknown"

    def analyze_position_based(self, center_x, frame_width):
        """
        Analizza basata sulla posizione nel frame con margini più intelligenti.
        """
        # Margine centrale dove l'analisi è ambigua
        margin = frame_width * 0.15  # 15% del frame è zona neutra

        if center_x < frame_width // 2 - margin:
            return "left"
        elif center_x > frame_width // 2 + margin:
            return "right"
        else:
            return "unknown"  # Zona centrale ambigua

    def analyze_contour_angle(self, contour):
        """
        Analizza l'angolo di rotazione del contorno per determinare l'orientamento.
        """
        try:
            # Calcola il rettangolo di rotazione minima
            rect = cv2.minAreaRect(contour)
            angle = rect[2]

            # Normalizza l'angolo tra -90 e 90
            if angle > 90:
                angle -= 180
            elif angle < -90:
                angle += 180

            # Gli angoli possono indicare l'orientamento della mano
            # Mani tipicamente hanno angoli tra -45 e 45 gradi quando sono orientate naturalmente
            if -30 < angle < 30:
                # Angolo neutro, usa altre euristiche
                return "unknown"
            elif angle < -30:
                # Rotazione antioraria, potrebbe indicare mano destra
                return "right"
            else:
                # Rotazione oraria, potrebbe indicare mano sinistra
                return "left"

        except Exception as e:
            logging.debug(f"Errore nell'analisi dell'angolo del contorno: {e}")
            return "unknown"

    def extract_hand_landmarks(self, contour, x, y, w, h):
        """
        Estrae i landmark della mano dal contorno (simulazione MediaPipe-style).
        MediaPipe usa 21 landmark per mano.
        """
        try:
            # Trova i punti chiave del contorno
            hull = cv2.convexHull(contour)
            hull_indices = cv2.convexHull(contour, returnPoints=False)

            if hull_indices is None or len(hull_indices) < 5:
                return None

            # Calcola i difetti di convessità per identificare le dita
            defects = cv2.convexityDefects(contour, hull_indices)
            if defects is None:
                return None

            # Simula i 21 landmark di MediaPipe
            landmarks = []

            # Landmark 0: Polso (centro della base della mano)
            wrist_x = x + w // 2
            wrist_y = y + h - h // 6  # Posizione approssimativa del polso
            landmarks.append((wrist_x, wrist_y))

            # Landmark 1-4: Pollice (4 punti)
            thumb_points = self.extract_thumb_landmarks(contour, defects, x, y, w, h)
            landmarks.extend(thumb_points)

            # Landmark 5-8: Indice (4 punti)
            index_points = self.extract_finger_landmarks(
                contour, defects, x, y, w, h, finger_idx=0
            )
            landmarks.extend(index_points)

            # Landmark 9-12: Medio (4 punti)
            middle_points = self.extract_finger_landmarks(
                contour, defects, x, y, w, h, finger_idx=1
            )
            landmarks.extend(middle_points)

            # Landmark 13-16: Anulare (4 punti)
            ring_points = self.extract_finger_landmarks(
                contour, defects, x, y, w, h, finger_idx=2
            )
            landmarks.extend(ring_points)

            # Landmark 17-20: Mignolo (4 punti)
            pinky_points = self.extract_finger_landmarks(
                contour, defects, x, y, w, h, finger_idx=3
            )
            landmarks.extend(pinky_points)

            return landmarks

        except Exception as e:
            logging.debug(f"Errore estrazione landmark: {e}")
            return None

    def extract_thumb_landmarks(self, contour, defects, x, y, w, h):
        """Estrae i landmark del pollice."""
        try:
            # Trova il punto più distante (probabilmente la punta del pollice)
            max_dist = 0
            thumb_tip = None

            for i in range(defects.shape[0]):
                s, e, f, d = defects[i, 0]
                start = tuple(contour[s][0])
                end = tuple(contour[e][0])
                far = tuple(contour[f][0])

                distance = d / 256.0  # Converti da fixed point
                if distance > max_dist:
                    max_dist = distance
                    thumb_tip = far

            if thumb_tip is None:
                # Fallback: usa il punto più a sinistra/destra
                leftmost = tuple(contour[contour[:, :, 0].argmin()][0])
                rightmost = tuple(contour[contour[:, :, 0].argmax()][0])
                thumb_tip = leftmost if leftmost[0] < rightmost[0] else rightmost

            # Crea punti intermedi per il pollice
            base_x = x + w // 2
            base_y = y + h - h // 4

            mid1_x = int(thumb_tip[0] * 0.75 + base_x * 0.25)
            mid1_y = int(thumb_tip[1] * 0.75 + base_y * 0.25)

            mid2_x = int(thumb_tip[0] * 0.5 + base_x * 0.5)
            mid2_y = int(thumb_tip[1] * 0.5 + base_y * 0.5)

            return [
                (base_x, base_y),  # MCP (base)
                (mid1_x, mid1_y),  # PIP
                (mid2_x, mid2_y),  # DIP
                thumb_tip,  # TIP
            ]

        except Exception as e:
            logging.debug(f"Errore estrazione landmark pollice: {e}")
            return [(x + w // 2, y + h // 2)] * 4  # Fallback

    def extract_finger_landmarks(self, contour, defects, x, y, w, h, finger_idx):
        """Estrae i landmark per un dito specifico (indice, medio, anulare, mignolo)."""
        try:
            # Dividi la mano in regioni per ogni dito
            finger_width = w // 5
            finger_start_x = x + finger_width * (finger_idx + 1)  # Salta il pollice

            # Trova i difetti in questa regione
            finger_defects = []
            for i in range(defects.shape[0]):
                s, e, f, d = defects[i, 0]
                far = tuple(contour[f][0])

                if finger_start_x <= far[0] < finger_start_x + finger_width:
                    finger_defects.append((far, d / 256.0))

            # Ordina per profondità (i più profondi sono le articolazioni)
            finger_defects.sort(key=lambda x: x[1], reverse=True)

            # Crea landmark per il dito
            base_y = y + h - h // 3
            tip_y = y + h // 4

            if len(finger_defects) >= 2:
                # Usa i difetti trovati come articolazioni
                pip_point = finger_defects[0][0]  # PIP
                dip_point = finger_defects[1][0]  # DIP
                tip_point = (dip_point[0], tip_y)  # TIP
            else:
                # Fallback: crea punti equidistanti
                mid_x = finger_start_x + finger_width // 2
                pip_point = (mid_x, base_y - h // 4)
                dip_point = (mid_x, base_y - h // 2)
                tip_point = (mid_x, tip_y)

            mcp_point = (finger_start_x + finger_width // 2, base_y)

            return [
                mcp_point,  # MCP (base)
                pip_point,  # PIP
                dip_point,  # DIP
                tip_point,  # TIP
            ]

        except Exception as e:
            logging.debug(f"Errore estrazione landmark dito {finger_idx}: {e}")
            # Fallback
            mid_x = x + w // 2
            return [
                (mid_x, y + h - h // 3),  # MCP
                (mid_x, y + h // 2),  # PIP
                (mid_x, y + h // 3),  # DIP
                (mid_x, y + h // 6),  # TIP
            ]

    def classify_hand_with_landmarks(self, landmarks, center_x, frame_width):
        """
        Classifica la mano come destra o sinistra usando i landmark (MediaPipe-style).
        """
        try:
            if len(landmarks) < 21:
                return "unknown"

            # Metodo 1: Analizza la posizione relativa del pollice
            wrist = landmarks[0]  # Polso
            thumb_base = landmarks[1]  # Base pollice
            thumb_tip = landmarks[4]  # Punta pollice

            # Se il pollice è a sinistra del polso = mano sinistra
            # Se il pollice è a destra del polso = mano destra
            if thumb_base[0] < wrist[0] - 10:  # Pollice significativamente a sinistra
                return "left"
            elif thumb_base[0] > wrist[0] + 10:  # Pollice significativamente a destra
                return "right"

            # Metodo 2: Analizza l'orientamento generale dei landmark
            # Conta quanti landmark sono a sinistra/destra del centro
            left_count = sum(1 for lm in landmarks if lm[0] < wrist[0])
            right_count = sum(1 for lm in landmarks if lm[0] > wrist[0])

            if left_count > right_count + 2:
                return "left"
            elif right_count > left_count + 2:
                return "right"

            # Metodo 3: Fallback alla posizione del frame
            margin = frame_width * 0.15
            if center_x < frame_width // 2 - margin:
                return "left"
            elif center_x > frame_width // 2 + margin:
                return "right"
            else:
                return "unknown"

        except Exception as e:
            logging.debug(f"Errore classificazione mano con landmark: {e}")
            return "unknown"

    def count_fingers_with_landmarks(self, landmarks):
        """
        Conta le dita usando i landmark (MediaPipe-style).
        """
        try:
            if len(landmarks) < 21:
                return 0

            finger_count = 0

            # Definisci le coppie MCP-TIP per ogni dito
            finger_pairs = [
                (1, 4),  # Pollice: MCP(1) - TIP(4)
                (5, 8),  # Indice: MCP(5) - TIP(8)
                (9, 12),  # Medio: MCP(9) - TIP(12)
                (13, 16),  # Anulare: MCP(13) - TIP(16)
                (17, 20),  # Mignolo: MCP(17) - TIP(20)
            ]

            for mcp_idx, tip_idx in finger_pairs:
                if mcp_idx < len(landmarks) and tip_idx < len(landmarks):
                    mcp_y = landmarks[mcp_idx][1]
                    tip_y = landmarks[tip_idx][1]

                    # Se la punta è sopra la base = dito esteso
                    if tip_y < mcp_y - 15:  # Soglia minima
                        finger_count += 1

            return finger_count

        except Exception as e:
            logging.debug(f"Errore conteggio dita con landmark: {e}")
            return 0

    def classify_gesture_with_landmarks(self, landmarks, finger_count):
        """
        Classifica il gesto della mano basato sui landmark e numero di dita.
        """
        try:
            if len(landmarks) < 21:
                return "Unknown"

            # Analizza la posizione delle punte delle dita
            finger_tips = [
                landmarks[4],
                landmarks[8],
                landmarks[12],
                landmarks[16],
                landmarks[20],
            ]

            # Calcola la posizione media delle punte
            avg_tip_y = sum(tip[1] for tip in finger_tips) / len(finger_tips)

            # Confronta con la posizione del polso
            wrist_y = landmarks[0][1]

            # Se le punte sono molto sopra il polso = mano aperta
            if avg_tip_y < wrist_y - 30:
                if finger_count >= 4:
                    return "Open Hand"
                elif finger_count <= 1:
                    return "Closed Hand"
                else:
                    return "Partial Gesture"
            else:
                # Mano più chiusa o in posizione neutra
                if finger_count <= 1:
                    return "Closed Hand"
                elif finger_count >= 3:
                    return "Open Hand"
                else:
                    return "Partial Gesture"

        except Exception as e:
            logging.debug(f"Errore classificazione gesto: {e}")
            return "Unknown"

    def count_fingers_basic(self, contour):
        """
        Conteggio base delle dita usando il metodo tradizionale dei difetti di convessità.
        """
        try:
            hull = cv2.convexHull(contour)
            hull_indices = cv2.convexHull(contour, returnPoints=False)

            if hull_indices is None:
                return 0

            defects = cv2.convexityDefects(contour, hull_indices)
            if defects is None:
                return 0

            finger_count = 0
            for i in range(defects.shape[0]):
                s, e, f, d = defects[i, 0]
                start = tuple(contour[s][0])
                end = tuple(contour[e][0])
                far = tuple(contour[f][0])

                # Calcola la profondità
                a = math.sqrt((end[0] - start[0]) ** 2 + (end[1] - start[1]) ** 2)
                b = math.sqrt((far[0] - start[0]) ** 2 + (far[1] - start[1]) ** 2)
                c = math.sqrt((end[0] - far[0]) ** 2 + (end[1] - far[1]) ** 2)

                if a > 0:
                    area = math.sqrt(max(0, (s * (s - a) * (s - b) * (s - c))))
                    distance = (2 * area) / a
                else:
                    distance = 0

                # Conta come dito se la profondità è sufficiente
                if distance > 15:
                    finger_count += 1

            return min(finger_count, 5)  # Max 5 dita

        except Exception as e:
            logging.debug(f"Errore conteggio dita base: {e}")
            return 0

    def detect_hands_mediapipe(self, frame):
        """Rilevamento mani usando approccio MediaPipe-style."""
        try:
            logging.info("Rilevamento mani con approccio MediaPipe-style")

            # Usa OpenCV con logica MediaPipe-like per ora
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            mask = cv2.inRange(hsv, self.lower_skin, self.upper_skin)

            # Operazioni morfologiche migliorate
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

            # Trova contorni con parametri ottimizzati
            contours, _ = cv2.findContours(
                mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_TC89_L1
            )

            detected_hands = []
            for contour in contours:
                area = cv2.contourArea(contour)
                if area > 8000:  # Soglia più alta per MediaPipe-style
                    x, y, w, h = cv2.boundingRect(contour)
                    aspect_ratio = w / h if h > 0 else 0

                    if 0.3 < aspect_ratio < 3.0:  # Range più ampio
                        # Usa la logica avanzata per determinare destra/sinistra
                        hand_info = self.analyze_hand_advanced(
                            contour, x, y, w, h, frame.shape[1]
                        )

                        if (
                            hand_info and hand_info["confidence"] > 0.4
                        ):  # Confidenza più alta
                            detected_hands.append((x, y, w, h, hand_info))

            # Visualizza risultati
            for x, y, w, h, hand_info in detected_hands:
                hand_type = hand_info["hand_type"]
                fingers = hand_info.get("fingers", 0)

                # Colori diversi per destra/sinistra
                color = (0, 255, 0) if hand_type == "right" else (255, 0, 0)

                cv2.rectangle(frame, (x, y), (x + w, y + h), color, 3)
                cv2.putText(
                    frame,
                    f"{hand_type.upper()} Hand ({fingers} dita)",
                    (x, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    color,
                    2,
                )

            # Mostra statistiche
            if detected_hands:
                cv2.putText(
                    frame,
                    f"Mani rilevate (MP-style): {len(detected_hands)}",
                    (10, 60),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (0, 255, 0),
                    2,
                )
            else:
                cv2.putText(
                    frame,
                    "Nessuna mano rilevata (MP-style)",
                    (10, 60),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (0, 255, 255),
                    2,
                )

            return frame

        except Exception as e:
            logging.error(f"Errore in detect_hands_mediapipe: {e}")
            return frame

    def analyze_hand_orientation_improved(self, contour, x, y, w, h, is_left_side):
        """
        Analizza migliorata dell'orientamento con correzioni specifiche per mano sinistra.
        """
        try:
            moments = cv2.moments(contour)
            if moments["m00"] == 0:
                return "unknown"

            cx = int(moments["m10"] / moments["m00"])
            cy = int(moments["m01"] / moments["m00"])

            left_points = sum(1 for point in contour if point[0][0] < cx)
            right_points = sum(1 for point in contour if point[0][0] > cx)
            total_points = len(contour)

            left_ratio = left_points / total_points
            right_ratio = right_points / total_points

            # Soglie adattive basate sulla posizione
            if is_left_side:
                # Per mano sinistra, soglia più permissiva per destra
                if left_ratio > 0.55:
                    return "left"
                elif right_ratio > 0.65:
                    return "right"
            else:
                # Per mano destra, soglia più permissiva per sinistra
                if right_ratio > 0.55:
                    return "right"
                elif left_ratio > 0.65:
                    return "left"

            return "unknown"

        except Exception as e:
            logging.debug(f"Errore analisi orientamento migliorata: {e}")
            return "unknown"

    def analyze_position_based_improved(self, center_x, frame_width, is_left_side):
        """
        Analisi posizione migliorata con considerazioni specifiche per mano sinistra.
        """
        # Margini più ampi per ridurre errori
        margin = frame_width * 0.2  # 20% invece di 15%

        if center_x < frame_width // 2 - margin:
            return "left"
        elif center_x > frame_width // 2 + margin:
            return "right"
        else:
            # Zona ambigua - usa euristica basata su posizione relativa
            if is_left_side:
                # Se siamo nel lato sinistro ma vicini al centro, probabilmente è sinistra
                return "left" if center_x < frame_width // 2 else "unknown"
            else:
                # Se siamo nel lato destro ma vicini al centro, probabilmente è destra
                return "right" if center_x > frame_width // 2 else "unknown"

    def analyze_contour_angle_improved(self, contour, is_left_side):
        """
        Analizza angolo migliorata con considerazioni per mano sinistra.
        """
        try:
            rect = cv2.minAreaRect(contour)
            angle = rect[2]

            if angle > 90:
                angle -= 180
            elif angle < -90:
                angle += 180

            # Considerazioni specifiche per lato
            if is_left_side:
                # Per mano sinistra, angoli diversi possono indicare orientamenti diversi
                if -45 < angle < 15:
                    return "left"
                elif angle < -45 or angle > 15:
                    return "right"
            else:
                # Per mano destra
                if -15 < angle < 45:
                    return "right"
                elif angle < -15 or angle > 45:
                    return "left"

            return "unknown"

        except Exception as e:
            logging.debug(f"Errore analisi angolo migliorata: {e}")
            return "unknown"

    def detect_hands_mediapipe(self, frame):
        """Rilevamento mani usando approccio MediaPipe-style."""
        try:
            logging.info("Rilevamento mani con approccio MediaPipe-style")

            # Usa OpenCV con logica MediaPipe-like per ora
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            mask = cv2.inRange(hsv, self.lower_skin, self.upper_skin)

            # Operazioni morfologiche migliorate
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

            # Trova contorni con parametri ottimizzati
            contours, _ = cv2.findContours(
                mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_TC89_L1
            )

            detected_hands = []
            for contour in contours:
                area = cv2.contourArea(contour)
                if area > 8000:  # Soglia più alta per MediaPipe-style
                    x, y, w, h = cv2.boundingRect(contour)
                    aspect_ratio = w / h if h > 0 else 0

                    if 0.3 < aspect_ratio < 3.0:  # Range più ampio
                        # Usa la logica avanzata per determinare destra/sinistra
                        hand_info = self.analyze_hand_advanced(
                            contour, x, y, w, h, frame.shape[1]
                        )

                        if (
                            hand_info and hand_info["confidence"] > 0.4
                        ):  # Confidenza più alta
                            detected_hands.append((x, y, w, h, hand_info))

            # Visualizza risultati
            for x, y, w, h, hand_info in detected_hands:
                hand_type = hand_info["hand_type"]
                fingers = hand_info.get("fingers", 0)

                # Colori diversi per destra/sinistra
                color = (0, 255, 0) if hand_type == "right" else (255, 0, 0)

                cv2.rectangle(frame, (x, y), (x + w, y + h), color, 3)
                cv2.putText(
                    frame,
                    f"{hand_type.upper()} Hand ({fingers} dita)",
                    (x, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    color,
                    2,
                )

            # Mostra statistiche
            if detected_hands:
                cv2.putText(
                    frame,
                    f"Mani rilevate (MP-style): {len(detected_hands)}",
                    (10, 60),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (0, 255, 0),
                    2,
                )
            else:
                cv2.putText(
                    frame,
                    "Nessuna mano rilevata (MP-style)",
                    (10, 60),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (0, 255, 255),
                    2,
                )

            return frame

        except Exception as e:
            logging.error(f"Errore in detect_hands_mediapipe: {e}")
            return frame

    def detect_humans_opencv_enhanced(self, frame):
        """Rilevamento pose umane avanzato usando OpenCV con tecniche migliorate."""
        try:
            logging.info("Rilevamento pose umane con OpenCV avanzato")

            # Converti in scala di grigi
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            # Migliora il contrasto per migliore rilevamento
            gray = cv2.equalizeHist(gray)

            # Usa una combinazione di tecniche per rilevare pose umane

            # Metodo 1: Rilevamento basato su contorni (corpo completo)
            pose_contours = self.detect_pose_by_contours(frame, gray)

            # Metodo 2: Rilevamento basato su movimento (se disponibile)
            pose_movement = self.detect_pose_by_movement(frame)

            # Metodo 3: Rilevamento basato su forme geometriche
            pose_shapes = self.detect_pose_by_shapes(frame, gray)

            # Combina i risultati
            all_poses = pose_contours + pose_movement + pose_shapes

            # Rimuovi duplicati e filtra
            filtered_poses = self.filter_duplicate_poses(all_poses)

            # Disegna i risultati
            for i, (x, y, w, h) in enumerate(filtered_poses):
                cv2.rectangle(
                    frame, (x, y), (x + w, y + h), (255, 0, 255), 3
                )  # Magenta per pose
                cv2.putText(
                    frame,
                    f"Pose {i+1}",
                    (x, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (255, 0, 255),
                    2,
                )

            # Mostra statistiche
            if filtered_poses:
                cv2.putText(
                    frame,
                    f"Pose rilevate (OpenCV): {len(filtered_poses)}",
                    (10, 90),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (255, 0, 255),
                    2,
                )
                logging.info(
                    f"Rilevamento pose OpenCV riuscito: {len(filtered_poses)} pose"
                )

                # Emit signals
                self.human_detected_signal.emit(filtered_poses)

                # Calculate center position for primary pose
                if filtered_poses:
                    primary_pose = filtered_poses[0]
                    center_x = primary_pose[0] + primary_pose[2] // 2
                    center_y = primary_pose[1] + primary_pose[3] // 2
                    self.human_position_signal.emit(center_x, center_y)
            else:
                cv2.putText(
                    frame,
                    "Nessuna posa rilevata (OpenCV)",
                    (10, 90),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (255, 165, 0),
                    2,
                )
                logging.debug("Nessuna posa rilevata con OpenCV avanzato")

            return frame

        except Exception as e:
            logging.error(f"Errore rilevamento pose OpenCV avanzato: {e}")
            return frame

    def detect_pose_by_contours(self, frame, gray):
        """Rileva pose basandosi sui contorni del corpo."""
        try:
            # Soglia adattiva per segmentare il corpo
            thresh = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2
            )

            # Operazioni morfologiche per pulire l'immagine
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
            thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
            thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)

            # Trova contorni
            contours, _ = cv2.findContours(
                thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )

            poses = []
            for contour in contours:
                area = cv2.contourArea(contour)
                if 10000 < area < 300000:  # Range per corpi umani
                    x, y, w, h = cv2.boundingRect(contour)
                    aspect_ratio = w / h if h > 0 else 0

                    # Filtra per proporzioni umane tipiche
                    if 0.2 < aspect_ratio < 1.0:
                        poses.append((x, y, w, h))

            return poses

        except Exception as e:
            logging.debug(f"Errore rilevamento pose per contorni: {e}")
            return []

    def detect_pose_by_movement(self, frame):
        """Rileva pose basandosi sul movimento (placeholder per futura implementazione)."""
        # Per ora restituisce lista vuota
        # In futuro potrebbe usare optical flow o background subtraction
        return []

    def detect_pose_by_shapes(self, frame, gray):
        """Rileva pose basandosi su forme geometriche caratteristiche."""
        try:
            # Usa HOG (Histogram of Oriented Gradients) per rilevare persone
            # Questa è una implementazione semplificata
            poses = []

            # Calcola gradienti
            sobelx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
            sobely = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)

            # Calcola magnitudo del gradiente
            magnitude = np.sqrt(sobelx**2 + sobely**2)
            magnitude = np.uint8(magnitude / np.max(magnitude) * 255)

            # Soglia per trovare aree con alto gradiente (probabilmente contorni)
            _, thresh = cv2.threshold(magnitude, 50, 255, cv2.THRESH_BINARY)

            # Trova contorni nelle aree di alto gradiente
            contours, _ = cv2.findContours(
                thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )

            for contour in contours:
                area = cv2.contourArea(contour)
                if 5000 < area < 100000:  # Range più piccolo per parti del corpo
                    x, y, w, h = cv2.boundingRect(contour)
                    aspect_ratio = w / h if h > 0 else 0

                    # Filtra per proporzioni ragionevoli
                    if 0.3 < aspect_ratio < 2.0:
                        poses.append((x, y, w, h))

            return poses

        except Exception as e:
            logging.debug(f"Errore rilevamento pose per forme: {e}")
            return []

    def filter_duplicate_poses(self, poses):
        """Rimuove pose duplicate o sovrapposte."""
        try:
            if not poses:
                return []

            filtered = []
            for pose in poses:
                x, y, w, h = pose

                # Controlla se questa posa si sovrappone significativamente con quelle già filtrate
                overlap = False
                for fx, fy, fw, fh in filtered:
                    # Calcola intersezione
                    x_overlap = max(0, min(x + w, fx + fw) - max(x, fx))
                    y_overlap = max(0, min(y + h, fy + fh) - max(y, fy))

                    if x_overlap > 0 and y_overlap > 0:
                        # Calcola area di intersezione
                        intersection = x_overlap * y_overlap
                        # Calcola area dell'unione
                        union = (w * h) + (fw * fh) - intersection

                        if union > 0:
                            iou = intersection / union
                            if iou > 0.3:  # Se si sovrappongono per più del 30%
                                overlap = True
                                break

                if not overlap:
                    filtered.append(pose)

            return filtered

        except Exception as e:
            logging.debug(f"Errore filtro pose duplicate: {e}")
            return poses

    def detect_facial_expressions(self, frame):
        """Rileva le espressioni facciali usando landmark e geometria."""
        if not self.facial_expression_enabled or self.face_cascade is None:
            return frame

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(
            gray, scaleFactor=1.05, minNeighbors=3, minSize=(30, 30), maxSize=(300, 300)
        )

        expression_count = 0
        for x, y, w, h in faces:
            # Estrai la regione del volto
            face_roi = gray[y : y + h, x : x + w]

            # Analizza l'espressione usando caratteristiche geometriche
            expression = self.analyze_facial_expression(face_roi, x, y, w, h)

            # Disegna il rettangolo e l'espressione rilevata
            cv2.rectangle(
                frame, (x, y), (x + w, y + h), (255, 0, 255), 3
            )  # Magenta per espressioni
            cv2.putText(
                frame,
                f"Espressione: {expression}",
                (x, y + h + 20),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 0, 255),
                1,
            )
            expression_count += 1

        # Mostra lo stato del riconoscimento espressioni
        if expression_count > 0:
            cv2.putText(
                frame,
                f"Espressioni rilevate: {expression_count}",
                (10, 120),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (255, 0, 255),
                2,
            )
        else:
            cv2.putText(
                frame,
                "Nessuna espressione rilevata",
                (10, 120),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (255, 0, 255),
                2,
            )

        return frame



    def detect_faces_opencv(self, frame):
        """Rilevamento facciale tradizionale con OpenCV."""
        if self.face_cascade is None:
            cv2.putText(
                frame,
                "Cascade non disponibile",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 0, 255),
                2,
            )
            return frame

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.equalizeHist(gray)

        # Parametri ottimizzati
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=2,
            minSize=(20, 20),
            maxSize=(400, 400),
            flags=cv2.CASCADE_SCALE_IMAGE,
        )

        logging.debug(f"OpenCV detection found {len(faces)} faces")

        if len(faces) > 0:
            cv2.putText(
                frame,
                f"Faccia rilevata (OpenCV): {len(faces)}",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (255, 0, 0),
                2,
            )
        else:
            cv2.putText(
                frame,
                "Nessuna faccia rilevata (OpenCV)",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (255, 165, 0),
                2,
            )

        for x, y, w, h in faces:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
            cv2.putText(
                frame,
                "Face (CV)",
                (x, y - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 0, 0),
                1,
            )

        return frame

    def is_face_like_region(self, frame, x, y, w, h):
        """Verifica se una regione sembra un volto per evitare confusione con le mani."""
        if self.face_cascade is None:
            return False

        # Estrai la regione di interesse
        roi = frame[y : y + h, x : x + w]
        if roi.size == 0:
            return False

        # Converti in scala di grigi
        gray_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

        # Rileva volti nella regione
        faces = self.face_cascade.detectMultiScale(
            gray_roi, scaleFactor=1.1, minNeighbors=3, minSize=(20, 20)
        )

        # Se viene rilevato un volto nella regione, è probabile che sia un volto
        return len(faces) > 0

    def analyze_facial_expression(self, face_roi, x, y, w, h):
        """Analizza l'espressione facciale usando caratteristiche geometriche e texture."""
        if face_roi.size == 0:
            return "Non rilevabile"

        # Converti in scala di grigi se necessario
        if len(face_roi.shape) > 2:
            face_roi = cv2.cvtColor(face_roi, cv2.COLOR_BGR2GRAY)

        height, width = face_roi.shape

        # Migliora il contrasto per una migliore analisi
        face_roi = cv2.equalizeHist(face_roi)

        # Dividi il volto in regioni più precise
        eye_region = face_roi[height // 5 : 2 * height // 5, :]  # Regione occhi
        nose_region = face_roi[2 * height // 5 : 3 * height // 5, :]  # Regione naso
        mouth_region = face_roi[3 * height // 5 : 4 * height // 5, :]  # Regione bocca

        # Calcola statistiche per ogni regione
        eye_mean = np.mean(eye_region)
        eye_std = np.std(eye_region)
        mouth_mean = np.mean(mouth_region)
        mouth_std = np.std(mouth_region)

        # Calcola i gradienti per rilevare i contorni
        sobelx = cv2.Sobel(face_roi, cv2.CV_64F, 1, 0, ksize=3)
        sobely = cv2.Sobel(face_roi, cv2.CV_64F, 0, 1, ksize=3)
        gradient_magnitude = np.sqrt(sobelx**2 + sobely**2)

        # Analizza la regione della bocca (dove si concentrano le espressioni)
        mouth_gradient = np.mean(
            gradient_magnitude[3 * height // 5 : 4 * height // 5, :]
        )

        # Calcola l'entropia per misurare la complessità della texture
        def calculate_entropy(region):
            hist = cv2.calcHist([region], [0], None, [256], [0, 256])
            hist = hist / hist.sum()  # Normalizza
            entropy = -np.sum(hist * np.log2(hist + 1e-10))  # Evita log(0)
            return entropy

        eye_entropy = calculate_entropy(eye_region)
        mouth_entropy = calculate_entropy(mouth_region)

        # Algoritmo di classificazione migliorato
        # Sorriso: alta variazione nella regione bocca, luminosità aumentata
        is_smile = (
            mouth_gradient > 30
            and mouth_std > 25
            and mouth_entropy > 6.5
            and mouth_mean > eye_mean
        )

        # Triste: bassa variazione, luminosità diminuita nella regione inferiore
        is_sad = (
            mouth_gradient < 15
            and mouth_std < 20
            and mouth_mean < eye_mean
            and mouth_entropy < 6.0
        )

        # Sorpreso: alta entropia in regione occhi, variazione elevata
        is_surprised = (
            eye_entropy > 7.0
            and eye_std > 30
            and mouth_gradient > 25
            and mouth_std > 25
        )

        # Neutro: valori intermedi, bassa variazione
        is_neutral = (
            15 <= mouth_gradient <= 30
            and 20 <= mouth_std <= 30
            and 6.0 <= mouth_entropy <= 7.0
        )

        # Decisione finale basata sui punteggi
        if is_smile:
            return "Sorriso"
        elif is_sad:
            return "Triste"
        elif is_surprised:
            return "Sorpreso"
        elif is_neutral:
            return "Neutro"
        else:
            return "Neutro"

    def check_hand_interaction(self, frame, hand_x, hand_y, hand_w, hand_h, gesture):
        """Verifica se la mano sta interagendo con elementi dell'interfaccia."""
        if not hasattr(self, "main_window") or self.main_window is None:
            return frame

        # Coordinate approssimative della colonna A (pensierini)
        # Queste sono stime basate sul layout tipico dell'interfaccia
        column_a_left = 50
        column_a_right = frame.shape[1] // 3
        column_a_top = 100
        column_a_bottom = frame.shape[0] - 100

        # Verifica se la mano è nella colonna A
        hand_center_x = hand_x + hand_w // 2
        hand_center_y = hand_y + hand_h // 2

        is_in_column_a = (
            column_a_left < hand_center_x < column_a_right
            and column_a_top < hand_center_y < column_a_bottom
        )

        if is_in_column_a:
            # Disegna un'indicazione visiva che la mano è nella zona di interazione
            cv2.rectangle(
                frame,
                (column_a_left, column_a_top),
                (column_a_right, column_a_bottom),
                (0, 255, 255),
                2,
            )
            cv2.putText(
                frame,
                "ZONA INTERAZIONE",
                (column_a_left + 10, column_a_top + 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 255),
                2,
            )

            # Se la mano è chiusa, inizia il trascinamento
            if gesture == "Closed Hand" and not self.is_dragging:
                self.start_dragging()
                cv2.putText(
                    frame,
                    "TRASCINAMENTO INIZIATO!",
                    (hand_center_x - 100, hand_center_y - 20),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 255, 0),
                    2,
                )
            elif gesture == "Open Hand" and self.is_dragging:
                self.stop_dragging()
                cv2.putText(
                    frame,
                    "TRASCINAMENTO COMPLETATO!",
                    (hand_center_x - 120, hand_center_y - 20),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 255, 0),
                    2,
                )

        return frame

    def start_dragging(self):
        """Inizia il processo di trascinamento."""
        import time

        self.is_dragging = True
        self.drag_start_time = time.time()
        logging.info("Iniziato trascinamento con gesto mano chiusa")

    def stop_dragging(self):
        """Termina il processo di trascinamento e simula il drop nell'area centrale."""
        import time

        if self.is_dragging and self.drag_start_time > 0:
            drag_duration = time.time() - self.drag_start_time
            self.is_dragging = False
            self.drag_start_time = 0.0

            # Simula il trascinamento nell'area centrale
            self.simulate_drag_to_center()

            logging.info(f"Trascinamento completato in {drag_duration:.2f} secondi")
        else:
            self.is_dragging = False
            self.drag_start_time = 0.0

    def simulate_drag_to_center(self):
        """Simula il trascinamento di un elemento nell'area centrale."""
        if hasattr(self, "main_window") and self.main_window:
            try:
                # Trova l'ultimo widget nella colonna A
                widgets = []
                for i in range(self.main_window.draggable_widgets_layout.count()):
                    item = self.main_window.draggable_widgets_layout.itemAt(i)
                    if item:
                        widget = item.widget()
                        if widget:
                            widgets.append(widget)

                if widgets:
                    # Prendi l'ultimo widget
                    last_widget = widgets[-1]
                    text = last_widget.text_label.text()

                    # Aggiungi il testo all'area centrale
                    current_text = (
                        self.main_window.work_area_main_text_edit.toPlainText()
                    )
                    new_text = current_text + f"\n\n[TRASCINATO]: {text}"

                    # Rimuovi il widget dalla colonna A
                    last_widget.setParent(None)
                    last_widget.deleteLater()

                    logging.info("Elemento trascinato con successo: {text}")

            except Exception:
                logging.error("Errore durante il trascinamento: {e}")

    def analyze_hand_advanced(self, contour, x, y, w, h, frame_width):
        """Analisi avanzata della mano con riconoscimento destra/sinistra e dita individuali - VERSIONE MEDIAPIPE-STYLE."""
        # Calcola il centro della mano
        center_x = x + w // 2
        center_y = y + h // 2

        # LOGICA MIGLIORATA: Usa approccio ibrido per migliore accuratezza
        # Prima prova con landmark simulati, poi fallback tradizionale
        try:
            # Step 1: Estrai landmark della mano (simulazione MediaPipe-style)
            hand_landmarks = self.extract_hand_landmarks(contour, x, y, w, h)

            if hand_landmarks and len(hand_landmarks) >= 21:
                # Step 2: Determina destra/sinistra usando landmark avanzati
                landmark_hand_type = self.classify_hand_with_landmarks(
                    hand_landmarks, center_x, frame_width
                )
                if landmark_hand_type != "unknown":
                    hand_type = landmark_hand_type
                    logging.debug(f"Mano classificata con landmark: {hand_type}")
                else:
                    # Fallback alla logica tradizionale
                    hand_type = self.determine_hand_orientation_advanced(
                        contour, x, y, w, h, center_x, center_y, frame_width
                    )
                    logging.debug(f"Fallback landmark - Mano: {hand_type}")
            else:
                # Fallback completo
                hand_type = self.determine_hand_orientation_advanced(
                    contour, x, y, w, h, center_x, center_y, frame_width
                )
                logging.debug(f"Fallback completo - Mano: {hand_type}")

        except Exception as e:
            logging.warning(f"Errore analisi ibrida, uso fallback semplice: {e}")
            # Fallback alla logica semplice
            hand_type = "left" if center_x < frame_width // 2 else "right"

        # Analisi della forma per contare le dita
        hull = cv2.convexHull(contour)
        hull_area = cv2.contourArea(hull)
        contour_area = cv2.contourArea(contour)

        if hull_area > 0:
            solidity = contour_area / hull_area
        else:
            solidity = 0

        # Calcola i difetti di convessità per le dita
        hull_indices = cv2.convexHull(contour, returnPoints=False)

        # Verifica che gli indici siano validi e in ordine monotono
        defects = None
        if hull_indices is not None and len(hull_indices) > 0:
            try:
                # Verifica che gli indici siano in ordine crescente
                if np.all(hull_indices[:-1] <= hull_indices[1:]):
                    defects = cv2.convexityDefects(contour, hull_indices)
                else:
                    # Se non sono in ordine, riordina
                    sorted_indices = np.sort(hull_indices.flatten())
                    defects = cv2.convexityDefects(
                        contour, sorted_indices.reshape(-1, 1)
                    )
            except cv2.error as e:
                # Se si verifica un errore, logga e continua senza difetti
                print(f"Errore in convexityDefects: {e}")
                defects = None

        finger_count = 0
        thumb_detected = False
        index_detected = False

        if defects is not None:
            for i in range(defects.shape[0]):
                s, e, f, d = defects[i, 0]
                start = tuple(contour[s][0])
                end = tuple(contour[e][0])
                far = tuple(contour[f][0])

                # Calcola la profondità del difetto
                a = math.sqrt((end[0] - start[0]) ** 2 + (end[1] - start[1]) ** 2)
                b = math.sqrt((far[0] - start[0]) ** 2 + (far[1] - start[1]) ** 2)
                c = math.sqrt((end[0] - far[0]) ** 2 + (end[1] - far[1]) ** 2)

                if a > 0:
                    area = math.sqrt(max(0, (s * (s - a) * (s - b) * (s - c))))
                    distance = (2 * area) / a
                else:
                    distance = 0

                # Conta le dita basandosi sulla profondità
                if distance > 20:
                    finger_count += 1

                    # Identifica pollice e indice basandosi sulla posizione
                    if hand_type == "right":
                        if (
                            far[0] > start[0] and far[0] > end[0]
                        ):  # Pollice a destra per mano destra
                            thumb_detected = True
                        elif finger_count == 1:  # Primo dito dopo il pollice
                            index_detected = True
                    else:  # Mano sinistra
                        if (
                            far[0] < start[0] and far[0] < end[0]
                        ):  # Pollice a sinistra per mano sinistra
                            thumb_detected = True
                        elif finger_count == 1:
                            index_detected = True

        # Determina il gesto basato su dita e solidità (LOGICA INVERTITA)
        if finger_count <= 2 or solidity < 0.65:
            gesture = "Open Hand"
        elif finger_count >= 4 and solidity > 0.75:
            gesture = "Closed Hand"
        else:
            gesture = "Partial Gesture"

        # Calcola la confidenza
        confidence = min(1.0, (finger_count * 0.2) + (solidity * 0.3) + 0.3)

        return {
            "hand_type": hand_type,
            "fingers": finger_count,
            "thumb": thumb_detected,
            "index": index_detected,
            "gesture": gesture,
            "confidence": confidence,
            "solidity": solidity,
        }

    def update_hand_tracking(self, detected_hands):
        """Aggiorna il tracking delle mani per il sistema multi-input."""
        # Reset delle posizioni precedenti
        for hand_type in ["left", "right"]:
            self.hand_tracking[hand_type]["position"] = None
            self.hand_tracking[hand_type]["confidence"] = 0

        # Aggiorna con le mani rilevate
        for x, y, w, h, hand_info in detected_hands:
            hand_type = hand_info["hand_type"]
            self.hand_tracking[hand_type]["position"] = (x + w // 2, y + h // 2)
            self.hand_tracking[hand_type]["fingers"] = hand_info["fingers"]
            self.hand_tracking[hand_type]["gesture"] = hand_info["gesture"]
            self.hand_tracking[hand_type]["confidence"] = hand_info["confidence"]

    def display_hand_statistics(self, frame, detected_hands):
        """Mostra le statistiche delle mani rilevate."""
        if detected_hands:
            left_count = sum(
                1 for _, _, _, _, info in detected_hands if info["hand_type"] == "left"
            )
            right_count = sum(
                1 for _, _, _, _, info in detected_hands if info["hand_type"] == "right"
            )

            stats_text = f"Mani rilevate: SX:{left_count} DX:{right_count}"
            cv2.putText(
                frame,
                stats_text,
                (10, 90),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 165, 0),
                2,
            )
        else:
            cv2.putText(
                frame,
                "Nessuna mano rilevata",
                (10, 90),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 165, 0),
                2,
            )

    def handle_advanced_hand_interaction(
        self, frame, hand_x, hand_y, hand_w, hand_h, hand_info
    ):
        """Gestisce l'interazione avanzata con l'interfaccia usando le mani."""
        if not hasattr(self, "main_window") or self.main_window is None:
            return frame

        # Coordinate della zona di interazione (colonna A)
        column_a_left = 50
        column_a_right = frame.shape[1] // 3
        column_a_top = 100
        column_a_bottom = frame.shape[0] - 100

        hand_center_x = hand_x + hand_w // 2
        hand_center_y = hand_y + hand_h // 2

        is_in_interaction_zone = (
            column_a_left < hand_center_x < column_a_right
            and column_a_top < hand_center_y < column_a_bottom
        )

        if is_in_interaction_zone:
            # Disegna la zona di interazione
            cv2.rectangle(
                frame,
                (column_a_left, column_a_top),
                (column_a_right, column_a_bottom),
                (0, 255, 255),
                2,
            )
            cv2.putText(
                frame,
                "ZONA INTERAZIONE",
                (column_a_left + 10, column_a_top + 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 255),
                2,
            )

            # Gestisci il trascinamento con timer
            if hand_info["gesture"] == "Closed Hand":
                if not self.is_dragging:
                    import time

                    current_time = time.time()

                    if self.drag_start_time == 0.0:
                        self.drag_start_time = current_time
                        self.drag_timer = 0
                    else:
                        self.drag_timer = current_time - self.drag_start_time

                    if self.drag_timer >= self.DRAG_THRESHOLD:
                        self.start_dragging()
                        cv2.putText(
                            frame,
                            "TRASCINAMENTO INIZIATO!",
                            (hand_center_x - 100, hand_center_y - 20),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.8,
                            (0, 255, 0),
                            2,
                        )
                    else:
                        remaining = int(self.DRAG_THRESHOLD - self.drag_timer)
                        cv2.putText(
                            frame,
                            f"Mantieni chiusa per {remaining}s",
                            (hand_center_x - 80, hand_center_y - 20),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.6,
                            (0, 165, 255),
                            2,
                        )
            else:
                if self.is_dragging:
                    self.stop_dragging()
                    cv2.putText(
                        frame,
                        "TRASCINAMENTO COMPLETATO!",
                        (hand_center_x - 120, hand_center_y - 20),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.8,
                        (0, 255, 0),
                        2,
                    )
                else:
                    self.drag_start_time = 0.0
                    self.drag_timer = 0

        return frame

    def webcam_to_ui_coordinates(
        self, webcam_x, webcam_y, frame_width, frame_height, ui_width, ui_height
    ):
        """Converte le coordinate dalla webcam alle coordinate dell'interfaccia utente."""
        # Calcola il rapporto di scala
        scale_x = ui_width / frame_width
        scale_y = ui_height / frame_height

        # Converti le coordinate
        ui_x = int(webcam_x * scale_x)
        ui_y = int(webcam_y * scale_y)

        return ui_x, ui_y

    def find_element_at_position(self, ui_x, ui_y):
        """Trova l'elemento dell'interfaccia alla posizione specificata."""
        if not hasattr(self, "main_window") or self.main_window is None:
            return None

        # Cerca nei widget della colonna A (pensierini)
        if (
            hasattr(self.main_window, "pensierini_widget")
            and self.main_window.pensierini_widget
        ):
            pensierini_layout = getattr(
                self.main_window.pensierini_widget, "pensierini_layout", None
            )
            if pensierini_layout:
                for i in range(pensierini_layout.count()):
                    item = pensierini_layout.itemAt(i)
                    if item and item.widget():
                        widget = item.widget()
                        # Controlla se il punto è dentro il widget
                        widget_rect = widget.geometry()
                        if widget_rect.contains(ui_x, ui_y):
                            return widget

        return None

    def update_drag_position(self, ui_x, ui_y):
        """Aggiorna la posizione dell'elemento durante il trascinamento."""
        if self.selected_widget and self.is_dragging:
            # Muovi il widget alla nuova posizione
            self.selected_widget.move(ui_x, ui_y)
            return True
        return False

    def stop(self):
        """Termina il thread in modo sicuro."""
        self._run_flag = False
        self.wait()
