# webcam_manager.py - Gestione della webcam e rilevamento video

import cv2
import numpy as np
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtGui import QImage, QPixmap

# Rilevatore viso globale
face_cascade = None
try:
    # Prova l'approccio moderno cv2.data
    cv2_data = getattr(cv2, "data", None)
    if cv2_data is not None:
        haarcascades = getattr(cv2_data, "haarcascades", None)
        if haarcascades is not None:
            cascade_path = haarcascades + "haarcascade_frontalface_default.xml"
            face_cascade = cv2.CascadeClassifier(cascade_path)
    else:
        # Fallback al percorso vecchio
        import os
        cascade_path = os.path.join(
            os.path.dirname(cv2.__file__), "data", "haarcascade_frontalface_default.xml"
        )
        if os.path.exists(cascade_path):
            face_cascade = cv2.CascadeClassifier(cascade_path)
        else:
            # Prova percorsi comuni del sistema
            common_paths = [
                "/usr/share/opencv4/haarcascades/haarcascade_frontalface_default.xml",
                "/usr/local/share/opencv4/haarcascades/haarcascade_frontalface_default.xml",
                "/opt/homebrew/share/opencv4/haarcascades/haarcascade_frontalface_default.xml",
            ]
            for path in common_paths:
                if os.path.exists(path):
                    face_cascade = cv2.CascadeClassifier(path)
                    break

    if face_cascade is not None:
        print("Classificatore viso caricato correttamente")
    else:
        print("Impossibile trovare il classificatore viso")
except Exception as e:
    print(f"Errore nel caricare il classificatore di cascata: {e}")


class VideoThread(QThread):
    """Thread dedicato per la cattura video e rilevamento."""

    change_pixmap_signal = pyqtSignal(QImage)
    status_signal = pyqtSignal(str)

    def __init__(self, face_detection_enabled=True, hand_detection_enabled=True):
        super().__init__()
        self._run_flag = True
        self.face_detection_enabled = face_detection_enabled
        self.hand_detection_enabled = hand_detection_enabled
        self.hand_color_range = (np.array([0, 100, 100]), np.array([10, 255, 255]))

    def run(self):
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            self.status_signal.emit("❌ Webcam non disponibile")
            self._run_flag = False
            return

        while self._run_flag:
            ret, frame = self.cap.read()
            if ret:
                frame = cv2.flip(frame, 1)

                if self.face_detection_enabled and face_cascade is not None:
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    faces = face_cascade.detectMultiScale(gray, 1.1, 4)
                    for x, y, w, h in faces:
                        cv2.rectangle(frame, (x, y), (x + w, y + h), (46, 140, 219), 2)

                if self.hand_detection_enabled:
                    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
                    mask = cv2.inRange(
                        hsv, self.hand_color_range[0], self.hand_color_range[1]
                    )
                    contours, _ = cv2.findContours(
                        mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
                    )

                    if contours:
                        max_contour = max(contours, key=cv2.contourArea)
                        if cv2.contourArea(max_contour) > 5000:
                            (x, y, w, h) = cv2.boundingRect(max_contour)
                            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                            cv2.putText(
                                frame,
                                "Mano rilevata",
                                (x, y - 10),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                0.9,
                                (0, 255, 0),
                                2,
                            )

                rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = rgb_image.shape
                bytes_per_line = ch * w
                # Convert memoryview to bytes for QImage
                image_bytes = bytes(rgb_image.data)
                q_image = QImage(
                    image_bytes, w, h, bytes_per_line, QImage.Format.Format_RGB888
                )
                self.change_pixmap_signal.emit(q_image)

        self.cap.release()

    def stop(self):
        self._run_flag = False
        self.wait()