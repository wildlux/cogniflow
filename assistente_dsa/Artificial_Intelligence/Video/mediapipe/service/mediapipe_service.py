#!/usr/bin/env python3
"""
Servizio MediaPipe per esecuzione in macchina virtuale
Questo script fornisce un servizio HTTP per l'elaborazione MediaPipe
"""

import cv2
import numpy as np
import base64
import io
from PIL import Image
import logging
import json
import os

# Import condizionali per dipendenze opzionali
try:
    import mediapipe as mp

    MEDIAPIPE_AVAILABLE = True
except ImportError:
    mp = None
    MEDIAPIPE_AVAILABLE = False
    logging.warning("MediaPipe non disponibile. Installare con: pip install mediapipe")

try:
    from flask import Flask, request, jsonify

    FLASK_AVAILABLE = True
except ImportError:
    Flask = None
    request = None
    jsonify = None
    FLASK_AVAILABLE = False
    logging.warning("Flask non disponibile. Installare con: pip install flask")

# Configurazione logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Verifica dipendenze critiche
if not MEDIAPIPE_AVAILABLE or not FLASK_AVAILABLE:
    logging.error("MediaPipe service disabilitato: dipendenze mancanti")
    logging.error("Installare: pip install mediapipe flask")

    # Crea un'app minima per evitare errori
    class MockApp:
        def run(self, *args, **kwargs):
            logging.info("MediaPipe service disabilitato - dipendenze mancanti")

    app = MockApp()
else:
    app = Flask(__name__)

    # Inizializza MediaPipe
    mp_pose = mp.solutions.pose
    mp_hands = mp.solutions.hands
    mp_face_mesh = mp.solutions.face_mesh
    mp_drawing = mp.solutions.drawing_utils

    # Istanza globale dei detector
    pose_detector = None
hands_detector = None
face_mesh_detector = None


def initialize_detectors():
    """Inizializza i detector MediaPipe."""
    global pose_detector, hands_detector, face_mesh_detector

    try:
        pose_detector = mp_pose.Pose(
            min_detection_confidence=0.5, min_tracking_confidence=0.5
        )
        logger.info("Pose detector inizializzato")

        hands_detector = mp_hands.Hands(
            max_num_hands=2, min_detection_confidence=0.5, min_tracking_confidence=0.5
        )
        logger.info("Hands detector inizializzato")

        face_mesh_detector = mp_face_mesh.FaceMesh(
            max_num_faces=1, min_detection_confidence=0.5, min_tracking_confidence=0.5
        )
        logger.info("Face mesh detector inizializzato")

    except Exception as e:
        logger.error(f"Errore inizializzazione detector: {e}")
        return False

    return True


def decode_image(image_data):
    """Decodifica l'immagine da base64."""
    try:
        # Rimuovi il prefisso data:image/jpeg;base64,
        if "," in image_data:
            image_data = image_data.split(",")[1]

        image_bytes = base64.b64decode(image_data)
        image = Image.open(io.BytesIO(image_bytes))
        return cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    except Exception as e:
        logger.error(f"Errore decodifica immagine: {e}")
        return None


def encode_image(image):
    """Codifica l'immagine in base64."""
    try:
        if isinstance(image, np.ndarray):
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            image = Image.fromarray(image)

        buffer = io.BytesIO()
        image.save(buffer, format="JPEG")
        image_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
        return f"data:image/jpeg;base64,{image_base64}"
    except Exception as e:
        logger.error(f"Errore codifica immagine: {e}")
        return None


@app.route("/health", methods=["GET"])
def health_check():
    """Controllo stato del servizio."""
    return jsonify(
        {
            "status": "healthy",
            "detectors": {
                "pose": pose_detector is not None,
                "hands": hands_detector is not None,
                "face_mesh": face_mesh_detector is not None,
            },
        }
    )


@app.route("/detect/pose", methods=["POST"])
def detect_pose():
    """Rileva la posa nel frame fornito."""
    try:
        data = request.get_json()
        if not data or "image" not in data:
            return jsonify({"error": "Immagine mancante"}), 400

        frame = decode_image(data["image"])
        if frame is None:
            return jsonify({"error": "Errore decodifica immagine"}), 400

        if pose_detector is None:
            return jsonify({"error": "Pose detector non inizializzato"}), 500

        # Converti in RGB per MediaPipe
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Rileva la posa
        results = pose_detector.process(rgb_frame)

        # Prepara la risposta
        response = {"detected": results.pose_landmarks is not None, "landmarks": []}

        if results.pose_landmarks:
            for landmark in results.pose_landmarks.landmark:
                response["landmarks"].append(
                    {
                        "x": landmark.x,
                        "y": landmark.y,
                        "z": landmark.z,
                        "visibility": landmark.visibility,
                    }
                )

        # Disegna i landmark sul frame se richiesto
        if data.get("draw_landmarks", False):
            annotated_frame = frame.copy()
            if results.pose_landmarks:
                mp_drawing.draw_landmarks(
                    annotated_frame, results.pose_landmarks, mp_pose.POSE_CONNECTIONS
                )
            response["annotated_image"] = encode_image(annotated_frame)

        return jsonify(response)

    except Exception as e:
        logger.error(f"Errore rilevamento posa: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/detect/hands", methods=["POST"])
def detect_hands():
    """Rileva le mani nel frame fornito."""
    try:
        data = request.get_json()
        if not data or "image" not in data:
            return jsonify({"error": "Immagine mancante"}), 400

        frame = decode_image(data["image"])
        if frame is None:
            return jsonify({"error": "Errore decodifica immagine"}), 400

        if hands_detector is None:
            return jsonify({"error": "Hands detector non inizializzato"}), 500

        # Converti in RGB per MediaPipe
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Rileva le mani
        results = hands_detector.process(rgb_frame)

        # Prepara la risposta
        response = {"detected": results.multi_hand_landmarks is not None, "hands": []}

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                hand_data = []
                for landmark in hand_landmarks.landmark:
                    hand_data.append(
                        {"x": landmark.x, "y": landmark.y, "z": landmark.z}
                    )
                response["hands"].append(hand_data)

        # Disegna i landmark sul frame se richiesto
        if data.get("draw_landmarks", False):
            annotated_frame = frame.copy()
            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    mp_drawing.draw_landmarks(
                        annotated_frame, hand_landmarks, mp_hands.HAND_CONNECTIONS
                    )
            response["annotated_image"] = encode_image(annotated_frame)

        return jsonify(response)

    except Exception as e:
        logger.error(f"Errore rilevamento mani: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/detect/face", methods=["POST"])
def detect_face():
    """Rileva il mesh facciale nel frame fornito."""
    try:
        data = request.get_json()
        if not data or "image" not in data:
            return jsonify({"error": "Immagine mancante"}), 400

        frame = decode_image(data["image"])
        if frame is None:
            return jsonify({"error": "Errore decodifica immagine"}), 400

        if face_mesh_detector is None:
            return jsonify({"error": "Face mesh detector non inizializzato"}), 500

        # Converti in RGB per MediaPipe
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Rileva il mesh facciale
        results = face_mesh_detector.process(rgb_frame)

        # Prepara la risposta
        response = {"detected": results.multi_face_landmarks is not None, "faces": []}

        if results.multi_face_landmarks:
            for face_landmarks in results.multi_face_landmarks:
                face_data = []
                for landmark in face_landmarks.landmark:
                    face_data.append(
                        {"x": landmark.x, "y": landmark.y, "z": landmark.z}
                    )
                response["faces"].append(face_data)

        return jsonify(response)

    except Exception as e:
        logger.error(f"Errore rilevamento faccia: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    logger.info("Avvio servizio MediaPipe...")

    if not initialize_detectors():
        logger.error("Impossibile inizializzare i detector MediaPipe")
        exit(1)

    # Ottieni la porta dalle variabili d'ambiente
    port = int(os.getenv("MEDIAPIPE_SERVICE_PORT", "8001"))

    logger.info(f"Servizio MediaPipe disponibile su porta {port}")
    app.run(host="0.0.0.0", port=port, debug=False)
