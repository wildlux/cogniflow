"""Scrittura con l'alfabeto manuale (dattilologia) via webcam.

Si compita una parola lettera per lettera con i segni dell'alfabeto
manuale a una mano (quello usato anche nella LIS per fare lo spelling):
la webcam riconosce la forma della mano e, tenendo il segno fermo per
circa un secondo, la lettera viene "digitata" nel campo di testo.

Gesti speciali:
 - mano aperta (5 dita distese) = SPAZIO
 - mano aperta con le dita verso il BASSO = CANCELLA (backspace)
 - per ripetere la stessa lettera due volte, nascondere un attimo la
   mano e rifare il segno

Il riconoscimento è geometrico, sui 21 punti della mano di MediaPipe:
funziona offline e senza addestramento. Le lettere statiche coperte sono
A B C D E F G H I K L M N O P Q R S T U V W X Y; J e Z si ottengono
partendo dal segno statico (I per la J, D per la Z) e disegnando in aria
la traiettoria della lettera (SignMotionClassifier).
L'anteprima nella barra mostra la lettera candidata prima che venga
scritta: se non è quella voluta basta aggiustare la mano.

Con la calibrazione (SignTemplateStore) l'utente può registrare i PROPRI
segni: i landmark d'esempio vengono confrontati per primi e, se la mano
è abbastanza vicina a un campione, vincono sulla geometria generica —
utile soprattutto per le lettere "a pugno" (A E S T N M).
"""

import json
import math
import os
import time
from collections import deque

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

# Campioni personali registrati con la calibrazione (uno o più per lettera)
TEMPLATES_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "Save",
    "SETUP_TOOLS_&_Data",
    "segni_calibrati.json",
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
            if points_down(5, 8) and points_down(9, 12):
                return "CANCELLA"  # mano aperta rovesciata = backspace
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


class SignMotionClassifier:
    """Riconosce le lettere che richiedono un movimento: J e Z.

    Riceve la forma statica di partenza ("I" per la J, "D" per la Z) e la
    traiettoria della punta del dito (mignolo per la J, indice per la Z)
    come lista di punti (x, y) in coordinate immagine normalizzate.
    La J è una discesa quasi verticale chiusa da un uncino laterale; la Z
    sono tre tratti con due inversioni orizzontali che scendono. Restituisce
    "J", "Z" oppure None.
    """

    MIN_SPAN = 0.06  # sotto questa ampiezza è solo tremolio, non un tratto

    @classmethod
    def classify(cls, shape, path):
        if len(path) < 6:
            return None
        xs = [pt[0] for pt in path]
        ys = [pt[1] for pt in path]
        w = max(xs) - min(xs)
        h = max(ys) - min(ys)
        if max(w, h) < cls.MIN_SPAN:
            return None
        if shape == "I":
            return "J" if cls._is_j(cls._resample(path, 16), w, h) else None
        if shape == "D":
            return "Z" if cls._is_z(cls._resample(path, 24), w, h) else None
        return None

    @staticmethod
    def _resample(path, n):
        """Ricampiona la traiettoria in n punti equidistanti lungo il tratto."""
        pts = [tuple(p) for p in path]
        dists = [0.0]
        for a, b in zip(pts, pts[1:]):
            dists.append(dists[-1] + _d(a, b))
        total = dists[-1]
        if total < 1e-9:
            return [pts[0]] * n
        out = []
        j = 0
        for i in range(n):
            target = total * i / (n - 1)
            while j < len(dists) - 2 and dists[j + 1] < target:
                j += 1
            seg = (dists[j + 1] - dists[j]) or 1e-9
            t = (target - dists[j]) / seg
            (ax, ay), (bx, by) = pts[j], pts[j + 1]
            out.append((ax + (bx - ax) * t, ay + (by - ay) * t))
        return out

    @staticmethod
    def _is_j(pts, w, h):
        # Prima parte (~60%): discesa quasi verticale; coda: uncino di lato
        k = int(len(pts) * 0.6)
        dx1 = pts[k][0] - pts[0][0]
        dy1 = pts[k][1] - pts[0][1]  # y cresce verso il basso
        dx2 = pts[-1][0] - pts[k][0]
        dy2 = pts[-1][1] - pts[k][1]
        return (
            h > 1e-6
            and h >= w  # la J è più alta che larga (la Z è il contrario)
            and dy1 >= 0.4 * h
            and abs(dx1) <= 0.6 * dy1
            and abs(dx2) >= 0.3 * h
            and dy2 <= 0.3 * h
        )

    @staticmethod
    def _is_z(pts, w, h):
        # Tre tratti orizzontali/diagonali con due inversioni: →, ↙, →
        if w < 1e-6:
            return False
        runs = []  # segni di dx dei tratti consecutivi, jitter escluso
        for a, b in zip(pts, pts[1:]):
            dx = b[0] - a[0]
            if abs(dx) < 0.03 * w:
                continue
            s = 1 if dx > 0 else -1
            if not runs or runs[-1] != s:
                runs.append(s)
        net_down = pts[-1][1] - pts[0][1]
        return (
            len(runs) == 3
            and runs[0] == runs[2] == -runs[1]
            and net_down >= 0.5 * h
            and w >= 0.5 * h
        )


class SignTemplateStore:
    """Campioni personali dei segni, registrati con la calibrazione.

    Ogni campione è la mano normalizzata (polso nell'origine, scala =
    distanza polso→nocca del medio): il confronto è la distanza media dei
    21 punti dal campione. Se la mano vista è abbastanza vicina a un
    campione, la sua lettera vince sulla geometria generica.
    """

    MATCH_THRESHOLD = 0.22  # distanza media massima (in unità di mano)
    MAX_SAMPLES = 5  # per lettera: i più recenti sostituiscono i più vecchi

    def __init__(self, path=None):
        self.path = path or TEMPLATES_PATH
        self.templates = {}  # lettera -> [campione, ...]; campione = 21 (x,y)
        self.load()

    @staticmethod
    def normalize(landmarks):
        """Mano → 21 punti (x, y) con polso nell'origine e scala unitaria."""
        pts = [
            (getattr(lm, "x", None), getattr(lm, "y", None))
            if hasattr(lm, "x")
            else (lm[0], lm[1])
            for lm in landmarks
        ]
        ox, oy = pts[0]
        size = _d(pts[0], pts[9]) or 1e-6
        return [((x - ox) / size, (y - oy) / size) for x, y in pts]

    def match(self, landmarks):
        """Lettera del campione più vicino, o None se nessuno è abbastanza vicino."""
        if not self.templates:
            return None
        probe = self.normalize(landmarks)
        best_letter, best_dist = None, None
        for letter, samples in self.templates.items():
            for sample in samples:
                dist = sum(_d(a, b) for a, b in zip(probe, sample)) / len(probe)
                if best_dist is None or dist < best_dist:
                    best_letter, best_dist = letter, dist
        if best_dist is not None and best_dist <= self.MATCH_THRESHOLD:
            return best_letter
        return None

    def add_sample(self, letter, landmarks):
        samples = self.templates.setdefault(letter.upper(), [])
        samples.append(self.normalize(landmarks))
        del samples[: -self.MAX_SAMPLES]

    def forget(self, letter):
        self.templates.pop(letter.upper(), None)

    def counts(self):
        return {letter: len(s) for letter, s in sorted(self.templates.items())}

    def load(self):
        try:
            with open(self.path, encoding="utf-8") as f:
                raw = json.load(f)
            self.templates = {
                letter: [[tuple(pt) for pt in sample] for sample in samples]
                for letter, samples in raw.items()
            }
        except (OSError, ValueError):
            self.templates = {}

    def save(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.templates, f)


class SignLanguageThread(QThread):
    """Webcam -> landmark della mano -> lettera confermata dopo una pausa.

    Emette candidate(lettera, progresso 0..1) mentre il segno viene
    tenuto fermo e letter_ready(lettera) quando è confermato. Come per
    la penna in aria, la webcam serve a una funzione alla volta.
    """

    letter_ready = pyqtSignal(str)  # lettera confermata ("A".."Z", " " o "\b")
    candidate = pyqtSignal(str, float)  # anteprima: lettera e avanzamento
    status = pyqtSignal(str)
    hand_sample = pyqtSignal(list)  # 21 (x, y, z) per la calibrazione

    DWELL_S = 0.9  # per quanto tenere fermo il segno prima di scriverlo

    # Lettere in movimento: forma statica di partenza -> punta da seguire
    MOTION_TIPS = {"I": 20, "D": 8}  # I+traiettoria = J, D+traiettoria = Z
    MOTION_START = 0.05  # spostamento (in 0.25 s) che avvia la traiettoria
    MOTION_STOP = 0.015  # sotto questo spostamento la traiettoria è finita

    def __init__(self, camera_index=0, parent=None, emit_landmarks=False,
                 templates_path=None):
        super().__init__(parent)
        self.camera_index = camera_index
        self._running = True
        self._emit_landmarks = emit_landmarks
        self._templates = SignTemplateStore(templates_path)

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
        motion = None  # traiettoria in corso per J/Z: {shape, tip, path}
        recent = deque()  # (t, x, y) recenti della punta, per capire se si muove
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

            lms = None
            letter = None
            if result is not None and result.hand_landmarks:
                lms = result.hand_landmarks[0]
                if self._emit_landmarks:
                    self.hand_sample.emit([(lm.x, lm.y, lm.z) for lm in lms])
                # I segni calibrati dall'utente hanno la precedenza sulla
                # geometria generica.
                letter = self._templates.match(lms)
                if letter is None:
                    letter = SignAlphabetClassifier.classify(lms)

            now = time.monotonic()

            # --- Traiettoria in corso (J/Z): si registra finché la mano
            # si muove, poi si classifica il tratto disegnato.
            if motion is not None:
                if lms is None:
                    self._finish_motion(motion)
                    motion = None
                    recent.clear()
                else:
                    tip = lms[motion["tip"]]
                    motion["path"].append((tip.x, tip.y))
                    recent.append((now, tip.x, tip.y))
                    while recent and now - recent[0][0] > 0.35:
                        recent.popleft()
                    if now - motion["t0"] > 0.35 and self._span(recent) < self.MOTION_STOP:
                        self._finish_motion(motion)
                        motion = None
                        recent.clear()
                        candidate = None  # il conteggio statico riparte da zero
                since = now  # durante il movimento niente lettere statiche
                self.msleep(33)
                continue

            # --- Avvio della traiettoria: la forma è I o D, non ancora
            # scritta, e la punta si sta spostando davvero.
            if lms is not None and letter in self.MOTION_TIPS and not emitted:
                tip = lms[self.MOTION_TIPS[letter]]
                recent.append((now, tip.x, tip.y))
                while recent and now - recent[0][0] > 0.25:
                    recent.popleft()
                if self._span(recent) > self.MOTION_START:
                    motion = {
                        "shape": letter,
                        "tip": self.MOTION_TIPS[letter],
                        "path": [(x, y) for _, x, y in recent],
                        "t0": now,
                    }
                    target = "J" if letter == "I" else "Z"
                    self.candidate.emit(f"{letter}→{target}?", 0.0)
                    since = now
                    self.msleep(33)
                    continue
            else:
                recent.clear()

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
                    if letter == "SPAZIO":
                        self.letter_ready.emit(" ")
                    elif letter == "CANCELLA":
                        self.letter_ready.emit("\b")
                    else:
                        self.letter_ready.emit(letter)

            self.msleep(33)  # ~30 fps
        cap.release()
        landmarker.close()

    @staticmethod
    def _span(recent):
        """Ampiezza dello spostamento nei punti recenti (diagonale del box)."""
        if len(recent) < 2:
            return 0.0
        xs = [x for _, x, _ in recent]
        ys = [y for _, _, y in recent]
        return math.hypot(max(xs) - min(xs), max(ys) - min(ys))

    def _finish_motion(self, motion):
        """Chiude la traiettoria e scrive J/Z se il tratto corrisponde."""
        letter = SignMotionClassifier.classify(motion["shape"], motion["path"])
        if letter:
            self.letter_ready.emit(letter)
            self.candidate.emit(letter, 1.0)
        else:
            self.candidate.emit("", 0.0)

    def reload_templates(self):
        """Ricarica i segni calibrati (dopo una sessione di calibrazione)."""
        self._templates.load()

    def stop(self):
        self._running = False
        self.wait(2000)
