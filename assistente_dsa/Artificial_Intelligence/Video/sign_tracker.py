"""Scrittura con l'alfabeto manuale (dattilologia) via webcam.

Si compita una parola lettera per lettera con i segni dell'alfabeto
manuale a una mano (quello usato anche nella LIS per fare lo spelling):
la webcam riconosce la forma della mano e, tenendo il segno fermo per
circa un secondo, la lettera viene "digitata" nel campo di testo.

Gesti speciali:
 - mano aperta (5 dita distese) = SPAZIO
 - per ripetere la stessa lettera due volte, nascondere un attimo la
   mano e rifare il segno

Il riconoscimento è geometrico, sui 21 punti della mano di MediaPipe:
funziona offline e senza addestramento, ma copre solo le lettere con
forma STATICA. Lettere supportate:
A B C D E F G H I K L M N O P Q R S T U V W X Y
(mancano J e Z, che richiedono un movimento).
L'anteprima nella barra mostra la lettera candidata prima che venga
scritta: se non è quella voluta basta aggiustare la mano.
"""

import math
import os
import time

import cv2
from PyQt6.QtCore import QThread, pyqtSignal

try:
    import mediapipe as mp
    from mediapipe.tasks.python import BaseOptions
    from mediapipe.tasks.python import vision as mp_vision

    MEDIAPIPE_OK = True
except ImportError:
    MEDIAPIPE_OK = False

MODEL_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "models", "hand_landmarker.task"
)


def _d(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


class SignAlphabetClassifier:
    """Classifica la forma della mano in una lettera dell'alfabeto manuale.

    Lavora sui 21 landmark normalizzati di MediaPipe (0 = polso; pollice
    1-4; indice 5-8; medio 9-12; anulare 13-16; mignolo 17-20). Ogni dito
    è ridotto a uno stato: E (disteso), C (chiuso), H (a metà, piegato);
    la combinazione degli stati più la posizione del pollice decide la
    lettera. Restituisce "SPAZIO" per la mano aperta, None se la forma
    non è riconosciuta.
    """

    EXT_RATIO = 1.25  # punta ben oltre la nocca = dito disteso
    CURL_RATIO = 1.00  # punta più vicina al polso della nocca = dito chiuso

    @classmethod
    def classify(cls, landmarks):
        p = [(lm.x, lm.y) for lm in landmarks]
        z = [lm.z for lm in landmarks]
        size = _d(p[0], p[9])  # polso -> nocca del medio: scala della mano
        if size < 1e-6:
            return None

        def near(a, b, t):
            return _d(p[a], p[b]) < t * size

        def state(pip, tip):
            r = _d(p[0], p[tip]) / max(_d(p[0], p[pip]), 1e-6)
            if r >= cls.EXT_RATIO:
                return "E"
            if r <= cls.CURL_RATIO:
                return "C"
            return "H"

        idx = state(6, 8)
        mid = state(10, 12)
        rng = state(14, 16)
        pnk = state(18, 20)
        fingers = idx + mid + rng + pnk

        # Pollice: "aperto" se lontano dalla base del mignolo,
        # "dritto" se la punta è ben oltre la sua articolazione.
        thumb_open = _d(p[4], p[17]) / size > 0.9
        thumb_straight = _d(p[0], p[4]) / max(_d(p[0], p[2]), 1e-6) > 1.35

        def points_up(mcp, tip):
            dx = abs(p[tip][0] - p[mcp][0])
            dy = p[mcp][1] - p[tip][1]  # y cresce verso il basso
            return dy > dx

        def points_down(mcp, tip):
            dx = abs(p[tip][0] - p[mcp][0])
            dy = p[tip][1] - p[mcp][1]
            return dy > dx

        # --- Mano aperta / B: quattro dita distese ---------------------
        if fingers == "EEEE":
            return "SPAZIO" if thumb_open else "B"

        # --- Tre dita distese ------------------------------------------
        if fingers == "EEEC":
            return "W"
        if idx in "CH" and mid == "E" and rng == "E" and pnk == "E":
            # indice piegato sul pollice, le altre tre distese
            if near(4, 8, 0.45):
                return "F"
            return None

        # --- Indice e medio distesi ------------------------------------
        if fingers == "EECC":
            # pollice infilato tra indice e medio = K (in su) / P (in giù)
            if near(4, 10, 0.4) and thumb_straight:
                return "P" if points_down(9, 12) else "K"
            # dita incrociate = R: rispetto all'asse del medio, la punta
            # dell'indice passa dal lato opposto a quello della sua nocca
            axis = (p[12][0] - p[9][0], p[12][1] - p[9][1])
            perp = (-axis[1], axis[0])
            s_mcp = (p[5][0] - p[9][0]) * perp[0] + (p[5][1] - p[9][1]) * perp[1]
            s_tip = (p[8][0] - p[12][0]) * perp[0] + (p[8][1] - p[12][1]) * perp[1]
            if s_mcp * s_tip < 0:
                return "R"
            if _d(p[8], p[12]) / size < 0.35:  # dita unite
                return "U" if points_up(5, 8) else "H"
            return "V"

        # --- Solo indice disteso ---------------------------------------
        if fingers == "ECCC":
            if thumb_open and thumb_straight:
                if points_up(5, 8):
                    return "L"
                return "Q" if points_down(5, 8) else "G"
            return "D"

        # --- Solo mignolo disteso --------------------------------------
        if fingers == "CCCE":
            return "Y" if thumb_open else "I"

        # --- Indice a uncino, il resto chiuso = X ----------------------
        if fingers == "HCCC" and not thumb_open:
            return "X"

        # --- Dita a metà: C oppure O -----------------------------------
        if "E" not in fingers and ("H" in (idx, mid)):
            if near(4, 8, 0.4) and near(4, 12, 0.5):
                return "O"  # punte raccolte sul pollice: cerchio chiuso
            if not near(4, 8, 0.4):
                return "C"  # arco aperto tra pollice e dita
            return None

        # --- Pugno chiuso: A E S T N M in base al pollice --------------
        if fingers == "CCCC":
            tips_cx = (p[8][0] + p[12][0]) / 2
            tips_cy = (p[8][1] + p[12][1]) / 2
            if _d(p[4], (tips_cx, tips_cy)) / size < 0.35:
                return "E"  # punte delle dita appoggiate sul pollice
            # A: pollice dritto DI LATO al pugno, cioè oltre la colonna
            # dell'indice sul lato opposto al mignolo. T/N/M invece hanno
            # il pollice infilato TRA le dita (lato interno).
            side = (p[5][0] - p[17][0], p[5][1] - p[17][1])
            side_n = math.hypot(*side) or 1e-6
            lat = (
                (p[4][0] - p[6][0]) * side[0] + (p[4][1] - p[6][1]) * side[1]
            ) / side_n
            if thumb_straight and lat > 0.1 * size:
                return "A"
            # Pollice piegato DAVANTI alle dita (più vicino alla camera) = S
            if z[4] < z[6] - 0.03 and near(4, 10, 0.6):
                return "S"
            # Altrimenti il pollice è infilato sotto 1/2/3 dita: T N M
            anchors = {6: "T", 10: "N", 14: "M"}
            best = min(anchors, key=lambda i: _d(p[4], p[i]))
            if _d(p[4], p[best]) / size < 0.6:
                return anchors[best]
            return None

        return None


class SignLanguageThread(QThread):
    """Webcam -> landmark della mano -> lettera confermata dopo una pausa.

    Emette candidate(lettera, progresso 0..1) mentre il segno viene
    tenuto fermo e letter_ready(lettera) quando è confermato. Come per
    la penna in aria, la webcam serve a una funzione alla volta.
    """

    letter_ready = pyqtSignal(str)  # lettera confermata ("A".."Z" o " ")
    candidate = pyqtSignal(str, float)  # anteprima: lettera e avanzamento
    status = pyqtSignal(str)

    DWELL_S = 0.9  # per quanto tenere fermo il segno prima di scriverlo

    def __init__(self, camera_index=0, parent=None):
        super().__init__(parent)
        self.camera_index = camera_index
        self._running = True

    def _make_landmarker(self):
        if not MEDIAPIPE_OK:
            self.status.emit("MediaPipe non installato: segni non disponibili")
            return None
        if not os.path.exists(MODEL_PATH):
            self.status.emit("Modello hand_landmarker.task mancante")
            return None
        try:
            options = mp_vision.HandLandmarkerOptions(
                base_options=BaseOptions(model_asset_path=MODEL_PATH),
                running_mode=mp_vision.RunningMode.VIDEO,
                num_hands=1,
                min_hand_detection_confidence=0.5,
                min_hand_presence_confidence=0.5,
                min_tracking_confidence=0.5,
            )
            return mp_vision.HandLandmarker.create_from_options(options)
        except Exception as e:  # modello corrotto, ABI, ecc.
            self.status.emit(f"Riconoscimento mano non inizializzabile: {e}")
            return None

    def run(self):
        landmarker = self._make_landmarker()
        if landmarker is None:
            return
        cap = cv2.VideoCapture(self.camera_index)
        if not cap.isOpened():
            self.status.emit(
                "Webcam non disponibile (già in uso da un'altra funzione?)"
            )
            landmarker.close()
            return
        self.status.emit(
            "Segni attivi: fai una lettera dell'alfabeto manuale e tienila ferma"
        )

        last_ts = 0
        candidate = None
        since = 0.0
        emitted = False
        while self._running:
            ok, frame = cap.read()
            if not ok:
                self.status.emit("La webcam non fornisce più immagini")
                break
            frame = cv2.flip(frame, 1)  # specchio: come guardarsi allo specchio
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
            ts = int(time.monotonic() * 1000)
            if ts <= last_ts:
                ts = last_ts + 1  # il timestamp deve crescere sempre
            last_ts = ts
            try:
                result = landmarker.detect_for_video(mp_image, ts)
            except Exception:
                result = None

            letter = None
            if result is not None and result.hand_landmarks:
                letter = SignAlphabetClassifier.classify(result.hand_landmarks[0])

            now = time.monotonic()
            if letter != candidate:
                # nuova forma (o mano sparita): riparte il conteggio, e si
                # sblocca la possibilità di riscrivere la stessa lettera
                candidate = letter
                since = now
                emitted = False
                self.candidate.emit(letter or "", 0.0)
            elif letter is not None:
                held = now - since
                self.candidate.emit(letter, min(1.0, held / self.DWELL_S))
                if held >= self.DWELL_S and not emitted:
                    emitted = True
                    self.letter_ready.emit(" " if letter == "SPAZIO" else letter)

            self.msleep(33)  # ~30 fps
        cap.release()
        landmarker.close()

    def stop(self):
        self._running = False
        self.wait(2000)
