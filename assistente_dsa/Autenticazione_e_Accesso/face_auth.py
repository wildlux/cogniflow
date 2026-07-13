"""Accesso con riconoscimento facciale: opzione SECONDARIA al login.

Pensato per chi non può usare fisicamente la tastiera: dopo una prima
registrazione (fatta da un accesso normale con password), si entra
guardando la webcam.

Privacy e consenso:
- la telecamera si accende SOLO dopo un consenso esplicito dell'utente;
- le immagini del viso restano su questo computer, nella cartella
  ``Save/AUTH/faces/<utente>/``, e non vengono inviate da nessuna parte;
- l'accesso col viso si può disattivare eliminando quella cartella
  (o con FaceAuthManager.remove_user).

Nota di sicurezza: il riconoscimento LBPH è una comodità di accesso per
l'accessibilità, NON è robusto come una password (una foto stampata può
ingannarlo). Per questo resta un'opzione e non sostituisce l'accesso
tradizionale.
"""

import glob
import os
import shutil
import time

import cv2
import numpy as np
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import (
    QDialog,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

FACE_SIZE = (200, 200)
LBPH_THRESHOLD = 70.0  # confidenza LBPH: più bassa = più somigliante
MATCHES_REQUIRED = 6  # frame concordi prima di accettare il riconoscimento
ENROLL_SAMPLES = 12  # campioni del viso salvati alla registrazione
RECOGNIZE_TIMEOUT = 25  # secondi prima di rinunciare


def _find_face_cascade():
    """Trova il classificatore Haar del viso: alcune installazioni di OpenCV
    (pip) non includono i file di dati, che però il sistema ha altrove."""
    candidates = [
        os.path.join(cv2.data.haarcascades, "haarcascade_frontalface_default.xml"),
        "/usr/share/opencv4/haarcascades/haarcascade_frontalface_default.xml",
        "/usr/local/share/opencv4/haarcascades/haarcascade_frontalface_default.xml",
        "/usr/share/opencv/haarcascades/haarcascade_frontalface_default.xml",
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return None


class FaceAuthManager:
    """Registra e riconosce i visi degli utenti, tutto in locale."""

    def __init__(self, data_dir=None):
        base = data_dir or os.path.join(os.path.dirname(__file__), "Save", "AUTH")
        self.faces_dir = os.path.join(base, "faces")
        os.makedirs(self.faces_dir, exist_ok=True)
        cascade = _find_face_cascade()
        self._detector = cv2.CascadeClassifier(cascade) if cascade else None
        self._recognizer = None
        self._labels = []

    def available(self):
        """True se OpenCV ha il modulo di riconoscimento (opencv-contrib)."""
        return (
            hasattr(cv2, "face")
            and self._detector is not None
            and not self._detector.empty()
        )

    def enrolled_users(self):
        """Utenti che hanno registrato il viso."""
        if not os.path.isdir(self.faces_dir):
            return []
        return sorted(
            d for d in os.listdir(self.faces_dir)
            if os.path.isdir(os.path.join(self.faces_dir, d))
        )

    def is_enrolled(self, username):
        return username in self.enrolled_users()

    def extract_face(self, frame_bgr):
        """Estrae il viso più grande dal frame.

        Ritorna (ritaglio 200x200 in scala di grigi, rettangolo) oppure
        (None, None) se nessun viso è inquadrato.
        """
        if self._detector is None or self._detector.empty():
            return None, None
        gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
        faces = self._detector.detectMultiScale(
            gray, scaleFactor=1.2, minNeighbors=5, minSize=(80, 80)
        )
        if len(faces) == 0:
            return None, None
        x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
        crop = cv2.resize(gray[y:y + h, x:x + w], FACE_SIZE)
        crop = cv2.equalizeHist(crop)  # riduce l'effetto dell'illuminazione
        return crop, (x, y, w, h)

    def enroll(self, username, samples):
        """Salva i campioni del viso dell'utente (immagini già ritagliate)."""
        dest = os.path.join(self.faces_dir, username)
        os.makedirs(dest, exist_ok=True)
        for i, img in enumerate(samples):
            cv2.imwrite(os.path.join(dest, f"campione_{i:02d}.png"), img)
        try:
            os.chmod(dest, 0o700)
        except OSError:
            pass
        self._recognizer = None  # forza il ri-addestramento

    def remove_user(self, username):
        """Elimina i dati del viso di un utente (revoca del consenso)."""
        dest = os.path.join(self.faces_dir, username)
        if os.path.isdir(dest):
            shutil.rmtree(dest)
        self._recognizer = None

    def _train(self):
        images, labels = [], []
        self._labels = self.enrolled_users()
        for idx, user in enumerate(self._labels):
            for path in sorted(
                glob.glob(os.path.join(self.faces_dir, user, "*.png"))
            ):
                img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
                if img is not None:
                    images.append(cv2.resize(img, FACE_SIZE))
                    labels.append(idx)
        if not images:
            return False
        self._recognizer = cv2.face.LBPHFaceRecognizer_create()
        self._recognizer.train(images, np.array(labels))
        return True

    def recognize(self, face_img):
        """Riconosce un viso ritagliato: (username, confidenza) o (None, conf).

        La confidenza LBPH è una distanza: più bassa = più somigliante.
        """
        if self._recognizer is None and not self._train():
            return None, None
        label, conf = self._recognizer.predict(face_img)
        if conf > LBPH_THRESHOLD or label >= len(self._labels):
            return None, conf
        return self._labels[label], conf


face_auth_manager = FaceAuthManager()


def ask_camera_consent(parent, scopo):
    """Chiede il consenso esplicito ad accendere la telecamera. True se sì."""
    risposta = QMessageBox.question(
        parent,
        "📷 Consenso telecamera",
        f"Per {scopo} serve accendere la telecamera.\n\n"
        "• Le immagini del viso restano SOLO su questo computer\n"
        "  (cartella Save/AUTH/faces) e non vengono inviate a nessuno.\n"
        "• Puoi revocare il consenso quando vuoi eliminando quella cartella.\n"
        "• L'accesso col viso è una comodità: è meno sicuro della password.\n\n"
        "Vuoi accendere la telecamera adesso?",
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        QMessageBox.StandardButton.No,
    )
    return risposta == QMessageBox.StandardButton.Yes


class FaceCameraDialog(QDialog):
    """Anteprima webcam per registrare il viso o riconoscerlo al login."""

    def __init__(self, mode="recognize", username=None, parent=None):
        super().__init__(parent)
        self.mode = mode
        self.username = username
        self.result_username = None
        self._samples = []
        self._votes = {}
        self._tick_count = 0

        if mode == "enroll":
            self.setWindowTitle("📷 Registrazione del viso")
            istruzioni = (
                "Guarda la telecamera e muovi leggermente la testa:\n"
                "vengono salvati alcuni campioni del tuo viso."
            )
        else:
            self.setWindowTitle("📷 Accesso con il viso")
            istruzioni = "Guarda la telecamera per farti riconoscere."

        layout = QVBoxLayout(self)
        info = QLabel(istruzioni)
        info.setWordWrap(True)
        layout.addWidget(info)

        self.preview = QLabel()
        self.preview.setFixedSize(480, 360)
        self.preview.setStyleSheet("background:#111; border-radius:6px;")
        self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.preview)

        self.status_label = QLabel("Accensione della telecamera…")
        self.status_label.setStyleSheet("font-size: 13px; margin: 4px;")
        layout.addWidget(self.status_label)

        cancel = QPushButton("❌ Annulla")
        cancel.setMinimumHeight(40)
        cancel.clicked.connect(self.reject)
        layout.addWidget(cancel)

        self._cap = cv2.VideoCapture(0)
        self._deadline = time.monotonic() + RECOGNIZE_TIMEOUT
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        if self._cap.isOpened():
            self._timer.start(33)
        else:
            self.status_label.setText(
                "❌ Webcam non disponibile (già in uso o assente)"
            )

    def _tick(self):
        ok, frame = self._cap.read()
        if not ok:
            self.status_label.setText("❌ La webcam non fornisce immagini")
            self._timer.stop()
            return
        frame = cv2.flip(frame, 1)
        crop, rect = face_auth_manager.extract_face(frame)
        if rect is not None:
            x, y, w, h = rect
            cv2.rectangle(frame, (x, y), (x + w, y + h), (60, 200, 60), 2)
        self._show_frame(frame)
        self._tick_count += 1

        if crop is None:
            self.status_label.setText("🔎 Inquadra bene il viso…")
        elif self.mode == "enroll":
            # Un campione ogni ~10 frame, per avere pose leggermente diverse
            if self._tick_count % 10 == 0:
                self._samples.append(crop)
                self.status_label.setText(
                    f"📸 Campioni raccolti: {len(self._samples)}/{ENROLL_SAMPLES}"
                )
            if len(self._samples) >= ENROLL_SAMPLES:
                face_auth_manager.enroll(self.username, self._samples)
                self.status_label.setText("✅ Viso registrato!")
                self._timer.stop()
                QTimer.singleShot(800, self.accept)
                return
        else:
            user, conf = face_auth_manager.recognize(crop)
            if user is not None:
                self._votes[user] = self._votes.get(user, 0) + 1
                self.status_label.setText(f"🔎 Riconoscimento… {user}")
                if self._votes[user] >= MATCHES_REQUIRED:
                    self.result_username = user
                    self.status_label.setText(f"✅ Bentornato, {user}!")
                    self._timer.stop()
                    QTimer.singleShot(600, self.accept)
                    return
            else:
                self.status_label.setText("🔎 Viso non riconosciuto…")

        if time.monotonic() > self._deadline:
            self.status_label.setText(
                "⏱️ Tempo scaduto: viso non riconosciuto. "
                "Puoi entrare con la password."
            )
            self._timer.stop()
            QTimer.singleShot(2500, self.reject)

    def _show_frame(self, frame_bgr):
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        h, w, _c = rgb.shape
        img = QImage(rgb.data, w, h, 3 * w, QImage.Format.Format_RGB888)
        self.preview.setPixmap(
            QPixmap.fromImage(img).scaled(
                self.preview.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )

    def done(self, result):
        # Spegne SEMPRE la telecamera all'uscita, qualunque sia l'esito
        self._timer.stop()
        if self._cap is not None and self._cap.isOpened():
            self._cap.release()
        super().done(result)
