#!/usr/bin/env python3
"""
MediaPipe Bridge per integrare VideoThread con QML
"""

import logging
import os
import sys
from PyQt6.QtCore import QObject, pyqtSignal, QThread, pyqtSlot
from PyQt6.QtGui import QPixmap

# Aggiungi il percorso per importare i moduli
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

# Import VideoThread
try:
    from ...visual_background import VideoThread
    VIDEO_THREAD_AVAILABLE = True
except ImportError:
    VideoThread = None
    VIDEO_THREAD_AVAILABLE = False
    logging.warning("VideoThread non disponibile - funzionalità MediaPipe limitate")


class MediaPipeBridge(QObject):
    """Bridge per collegare MediaPipe/VideoThread al QML"""

    # Segnali per comunicare con QML
    webcamToggled = pyqtSignal(bool)  # webcam enabled/disabled
    detectionToggled = pyqtSignal(bool)  # detection enabled/disabled
    detectionOptionChanged = pyqtSignal(str)  # detection option changed
    videoFrameReceived = pyqtSignal(QPixmap)  # video frame pixmap
    statusChanged = pyqtSignal(str)  # status message
    handPositionChanged = pyqtSignal(int, int)  # hand x, y coordinates
    gestureDetected = pyqtSignal(str)  # gesture type
    humanDetected = pyqtSignal(list)  # list of human bounding boxes
    humanPositionChanged = pyqtSignal(int, int)  # human center position

    def __init__(self, parent=None):
        super().__init__(parent)
        self.video_thread = None
        self.webcam_enabled = False
        self.detection_enabled = False
        self.selected_detection = "Pose"

    @pyqtSlot()
    def toggleWebcam(self):
        """Attiva/disattiva la webcam"""
        if not VIDEO_THREAD_AVAILABLE:
            self.statusChanged.emit("VideoThread non disponibile")
            return

        if self.webcam_enabled:
            self._stopWebcam()
        else:
            self._startWebcam()

    @pyqtSlot()
    def toggleDetection(self):
        """Attiva/disattiva il rilevamento"""
        if not self.webcam_enabled:
            self.statusChanged.emit("Attiva prima la webcam")
            return

        self.detection_enabled = not self.detection_enabled
        self.detectionToggled.emit(self.detection_enabled)

        if self.video_thread:
            # Abilita/disabilita i rilevamenti in base al tipo selezionato
            if self.selected_detection == "Pose":
                self.video_thread.human_detection_enabled = self.detection_enabled
            elif self.selected_detection == "Hands":
                self.video_thread.hand_detection_enabled = self.detection_enabled
                self.video_thread.gesture_recognition_enabled = self.detection_enabled
            elif self.selected_detection == "Face":
                self.video_thread.face_detection_enabled = self.detection_enabled
            elif self.selected_detection == "Holistic":
                self.video_thread.human_detection_enabled = self.detection_enabled
                self.video_thread.hand_detection_enabled = self.detection_enabled
                self.video_thread.face_detection_enabled = self.detection_enabled

        status = "Rilevamento attivo" if self.detection_enabled else "Rilevamento disattivo"
        self.statusChanged.emit(status)

    @pyqtSlot(str)
    def changeDetectionOption(self, option):
        """Cambia l'opzione di rilevamento"""
        self.selected_detection = option
        self.detectionOptionChanged.emit(option)

        if self.video_thread and self.detection_enabled:
            # Reset all detection types
            self.video_thread.human_detection_enabled = False
            self.video_thread.hand_detection_enabled = False
            self.video_thread.gesture_recognition_enabled = False
            self.video_thread.face_detection_enabled = False

            # Enable selected detection type
            if option == "Pose":
                self.video_thread.human_detection_enabled = True
            elif option == "Hands":
                self.video_thread.hand_detection_enabled = True
                self.video_thread.gesture_recognition_enabled = True
            elif option == "Face":
                self.video_thread.face_detection_enabled = True
            elif option == "Holistic":
                self.video_thread.human_detection_enabled = True
                self.video_thread.hand_detection_enabled = True
                self.video_thread.face_detection_enabled = True

        self.statusChanged.emit(f"Rilevamento: {option}")

    def _startWebcam(self):
        """Avvia la webcam"""
        if not VIDEO_THREAD_AVAILABLE:
            self.statusChanged.emit("VideoThread non disponibile")
            return

        try:
            self.video_thread = VideoThread()
            self.video_thread.change_pixmap_signal.connect(self._onVideoFrameReceived)
            self.video_thread.status_signal.connect(self._onStatusChanged)
            self.video_thread.hand_position_signal.connect(self._onHandPositionChanged)
            self.video_thread.gesture_detected_signal.connect(self._onGestureDetected)
            self.video_thread.human_detected_signal.connect(self._onHumanDetected)
            self.video_thread.human_position_signal.connect(self._onHumanPositionChanged)

            # Configure detection settings
            self.video_thread.use_mediapipe_service = True
            self.video_thread.human_detection_enabled = self.detection_enabled and self.selected_detection in ["Pose", "Holistic"]
            self.video_thread.hand_detection_enabled = self.detection_enabled and self.selected_detection in ["Hands", "Holistic"]
            self.video_thread.gesture_recognition_enabled = self.detection_enabled and self.selected_detection in ["Hands", "Holistic"]
            self.video_thread.face_detection_enabled = self.detection_enabled and self.selected_detection in ["Face", "Holistic"]

            self.video_thread.start()
            self.webcam_enabled = True
            self.webcamToggled.emit(True)
            self.statusChanged.emit("Webcam avviata")

        except Exception as e:
            logging.error(f"Errore avvio webcam: {e}")
            self.statusChanged.emit(f"Errore avvio webcam: {str(e)}")

    def _stopWebcam(self):
        """Ferma la webcam"""
        if self.video_thread:
            self.video_thread.stop()
            self.video_thread = None

        self.webcam_enabled = False
        self.detection_enabled = False
        self.webcamToggled.emit(False)
        self.detectionToggled.emit(False)
        self.statusChanged.emit("Webcam fermata")

    def _onVideoFrameReceived(self, pixmap):
        """Callback quando arriva un frame video"""
        self.videoFrameReceived.emit(pixmap)

    def _onStatusChanged(self, status):
        """Callback per cambio stato"""
        self.statusChanged.emit(status)

    def _onHandPositionChanged(self, x, y):
        """Callback per posizione mano"""
        self.handPositionChanged.emit(x, y)

    def _onGestureDetected(self, gesture):
        """Callback per gesto rilevato"""
        self.gestureDetected.emit(gesture)

    def _onHumanDetected(self, humans):
        """Callback per umani rilevati"""
        self.humanDetected.emit(humans)

    def _onHumanPositionChanged(self, x, y):
        """Callback per posizione umana"""
        self.humanPositionChanged.emit(x, y)

    @pyqtSlot()
    def cleanup(self):
        """Pulisce le risorse"""
        self._stopWebcam()


# Istanza globale del bridge
mediapipe_bridge = MediaPipeBridge()


def register_mediapipe_bridge(engine):
    """Registra il bridge MediaPipe nel contesto QML"""
    engine.rootContext().setContextProperty("mediaPipeBridge", mediapipe_bridge)
    return mediapipe_bridge


if __name__ == "__main__":
    print("🔧 MediaPipe Bridge per QML")
    print("Questo file fornisce l'integrazione tra QML e MediaPipe/VideoThread")
