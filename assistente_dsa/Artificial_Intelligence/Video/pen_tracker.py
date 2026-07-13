"""Tracciamento della punta di una penna via webcam: disegno "in aria".

Si tiene in mano una penna (o qualsiasi oggetto) con la punta/cappuccio di
colore acceso rivolta VERSO IL BASSO e la si muove davanti alla webcam: la
punta viene seguita e disegna sul canvas, come una penna che scrive a
mezz'aria. Nascondere la punta (girare la penna o coprirla con la mano)
equivale a sollevarla dal foglio: il tratto si interrompe.

Il rilevamento è una segmentazione colore in HSV: veloce, offline e senza
modelli. L'immagine è specchiata, così muovere la mano a destra disegna a
destra.
"""

import cv2
import numpy as np
from PyQt6.QtCore import QThread, pyqtSignal


class PenTrackerThread(QThread):
    """Segue la punta colorata della penna ed emette posizioni normalizzate."""

    # (x, y) in 0..1 rispetto al frame, e se la punta è visibile
    pen_position = pyqtSignal(float, float, bool)
    status = pyqtSignal(str)

    # Intervalli HSV per il colore della punta (il rosso è a cavallo dello 0)
    COLOR_RANGES = {
        "blu": [((100, 120, 70), (130, 255, 255))],
        "verde": [((40, 80, 70), (85, 255, 255))],
        "rosso": [((0, 130, 80), (10, 255, 255)),
                  ((170, 130, 80), (180, 255, 255))],
        "giallo": [((20, 120, 120), (35, 255, 255))],
    }
    MIN_AREA = 150  # pixel: sotto questa soglia è rumore, non la punta
    SMOOTHING = 0.5  # peso della nuova posizione (anti-tremolio)

    def __init__(self, color="blu", camera_index=0, parent=None):
        super().__init__(parent)
        self.color = color  # modificabile al volo dalla combo dei colori
        self.camera_index = camera_index
        self._running = True
        self._sx = None
        self._sy = None

    @classmethod
    def detect_tip(cls, frame_bgr, color):
        """Trova la punta nel frame: (nx, ny) normalizzati oppure None.

        La punta è il punto PIÙ IN BASSO della zona del colore cercato,
        coerente con la penna tenuta con la punta rivolta verso il basso.
        """
        hsv = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2HSV)
        mask = None
        for lo, hi in cls.COLOR_RANGES.get(color, cls.COLOR_RANGES["blu"]):
            m = cv2.inRange(hsv, np.array(lo), np.array(hi))
            mask = m if mask is None else cv2.bitwise_or(mask, m)
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.dilate(mask, kernel, iterations=1)
        contours, _ = cv2.findContours(
            mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        if not contours:
            return None
        biggest = max(contours, key=cv2.contourArea)
        if cv2.contourArea(biggest) < cls.MIN_AREA:
            return None
        points = biggest.reshape(-1, 2)
        tip = points[points[:, 1].argmax()]  # y massima = punto più in basso
        h, w = frame_bgr.shape[:2]
        return float(tip[0]) / w, float(tip[1]) / h

    def run(self):
        cap = cv2.VideoCapture(self.camera_index)
        if not cap.isOpened():
            self.status.emit(
                "Webcam non disponibile (già in uso da un'altra funzione?)"
            )
            return
        self.status.emit(
            f"Penna in aria attiva: mostra la punta {self.color} alla webcam"
        )
        while self._running:
            ok, frame = cap.read()
            if not ok:
                self.status.emit("La webcam non fornisce più immagini")
                break
            frame = cv2.flip(frame, 1)  # specchio: movimento naturale
            tip = self.detect_tip(frame, self.color)
            if tip is None:
                # Punta nascosta = penna sollevata: il tratto si interrompe
                self._sx = self._sy = None
                self.pen_position.emit(0.0, 0.0, False)
            else:
                nx, ny = tip
                if self._sx is None:
                    self._sx, self._sy = nx, ny
                else:
                    a = self.SMOOTHING
                    self._sx = a * nx + (1 - a) * self._sx
                    self._sy = a * ny + (1 - a) * self._sy
                self.pen_position.emit(self._sx, self._sy, True)
            self.msleep(33)  # ~30 fps
        cap.release()

    def stop(self):
        self._running = False
        self.wait(2000)
