"""Test del classificatore dell'alfabeto manuale (sign_tracker).

Costruisce mani sintetiche (21 landmark) e verifica che le forme base
vengano riconosciute. Le coordinate sono normalizzate come quelle di
MediaPipe: origine in alto a sinistra, y che cresce verso il basso.
"""

import os
import sys
import tempfile
from collections import namedtuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Artificial_Intelligence.Video.sign_tracker import (
    SignAlphabetClassifier,
    SignMotionClassifier,
    SignTemplateStore,
)

LM = namedtuple("LM", "x y z")

# Basi delle dita (mcp), polso in basso, dita verso l'alto
WRIST = (0.50, 0.90)
MCP = {"index": (0.42, 0.70), "middle": (0.48, 0.69),
       "ring": (0.54, 0.70), "pinky": (0.60, 0.72)}
FINGER_SLOTS = {"index": (5, 6, 7, 8), "middle": (9, 10, 11, 12),
                "ring": (13, 14, 15, 16), "pinky": (17, 18, 19, 20)}


def finger(mcp, kind, direction=(0.0, -1.0), length=0.25):
    """Punti (mcp, pip, dip, tip) di un dito disteso/chiuso/a metà."""
    dx, dy = direction
    if kind == "ext":
        return [mcp,
                (mcp[0] + dx * length * 0.4, mcp[1] + dy * length * 0.4),
                (mcp[0] + dx * length * 0.7, mcp[1] + dy * length * 0.7),
                (mcp[0] + dx * length, mcp[1] + dy * length)]
    if kind == "curl":  # punta ripiegata verso il palmo
        return [mcp,
                (mcp[0], mcp[1] - 0.06),
                (mcp[0] + 0.01, mcp[1] - 0.01),
                (mcp[0] + 0.01, mcp[1] + 0.05)]
    if kind == "half":  # piegato a metà (uncino)
        return [mcp,
                (mcp[0], mcp[1] - 0.08),
                (mcp[0] + 0.01, mcp[1] - 0.11),
                (mcp[0] + 0.02, mcp[1] - 0.12)]
    raise ValueError(kind)


def hand(states, thumb, thumb_z=0.0):
    """Mano completa: states = {dito: ext|curl|half}, thumb = 4 punti."""
    pts = [None] * 21
    pts[0] = WRIST
    for i, t in enumerate(thumb):
        pts[1 + i] = t
    for name, slots in FINGER_SLOTS.items():
        for slot, pt in zip(slots, finger(MCP[name], states[name])):
            pts[slot] = pt
    return [LM(x, y, thumb_z if i == 4 else 0.0) for i, (x, y) in enumerate(pts)]


THUMB_OPEN = [(0.45, 0.85), (0.40, 0.80), (0.32, 0.72), (0.25, 0.65)]
THUMB_ACROSS = [(0.45, 0.85), (0.46, 0.80), (0.49, 0.77), (0.53, 0.75)]
THUMB_SIDE = [(0.44, 0.86), (0.42, 0.82), (0.40, 0.74), (0.39, 0.66)]
# Pollice infilato tra indice e medio (punta vicino alla nocca dell'indice)
THUMB_TUCKED_T = [(0.45, 0.85), (0.44, 0.78), (0.445, 0.71), (0.45, 0.65)]


def classify(states, thumb, thumb_z=0.0):
    return SignAlphabetClassifier.classify(hand(states, thumb, thumb_z))


ALL = {"index": "ext", "middle": "ext", "ring": "ext", "pinky": "ext"}
FIST = {"index": "curl", "middle": "curl", "ring": "curl", "pinky": "curl"}


def test_mano_aperta_e_spazio():
    assert classify(ALL, THUMB_OPEN) == "SPAZIO"


def test_lettera_b():
    assert classify(ALL, THUMB_ACROSS) == "B"


def test_lettera_d():
    states = dict(FIST, index="ext")
    assert classify(states, THUMB_ACROSS) == "D"


def test_lettera_l():
    states = dict(FIST, index="ext")
    assert classify(states, THUMB_OPEN) == "L"


def test_lettera_v():
    states = dict(FIST, index="ext", middle="ext")
    # dita divaricate: indice inclinato a sinistra, medio a destra
    pts = [None] * 21
    pts[0] = WRIST
    for i, t in enumerate(THUMB_ACROSS):
        pts[1 + i] = t
    for name, slots in FINGER_SLOTS.items():
        if name == "index":
            pieces = finger(MCP[name], "ext", direction=(-0.35, -0.94))
        elif name == "middle":
            pieces = finger(MCP[name], "ext", direction=(0.35, -0.94))
        else:
            pieces = finger(MCP[name], "curl")
        for slot, pt in zip(slots, pieces):
            pts[slot] = pt
    lms = [LM(x, y, 0.0) for x, y in pts]
    assert SignAlphabetClassifier.classify(lms) == "V"


def test_lettera_u():
    # indice e medio distesi paralleli e vicini
    states = dict(FIST, index="ext", middle="ext")
    assert classify(states, THUMB_ACROSS) == "U"


def test_lettera_w():
    states = dict(FIST, index="ext", middle="ext", ring="ext")
    assert classify(states, THUMB_ACROSS) == "W"


def test_lettera_i():
    states = dict(FIST, pinky="ext")
    assert classify(states, THUMB_ACROSS) == "I"


def test_lettera_y():
    states = dict(FIST, pinky="ext")
    assert classify(states, THUMB_OPEN) == "Y"


def test_lettera_a():
    assert classify(FIST, THUMB_SIDE) == "A"


def test_lettera_t():
    assert classify(FIST, THUMB_TUCKED_T) == "T"


def test_mano_non_riconosciuta():
    # forma senza senso: medio+mignolo distesi, il resto chiuso
    states = dict(FIST, middle="ext", pinky="ext")
    assert classify(states, THUMB_ACROSS) is None


def test_gesto_cancella():
    # mano aperta rovesciata: polso in alto, dita distese verso il basso
    pts = [None] * 21
    pts[0] = (0.50, 0.30)
    thumb = [(0.45, 0.35), (0.40, 0.40), (0.32, 0.48), (0.25, 0.55)]
    for i, t in enumerate(thumb):
        pts[1 + i] = t
    mcp_down = {"index": (0.42, 0.50), "middle": (0.48, 0.51),
                "ring": (0.54, 0.50), "pinky": (0.60, 0.48)}
    for name, slots in FINGER_SLOTS.items():
        pieces = finger(mcp_down[name], "ext", direction=(0.0, 1.0))
        for slot, pt in zip(slots, pieces):
            pts[slot] = pt
    lms = [LM(x, y, 0.0) for x, y in pts]
    assert SignAlphabetClassifier.classify(lms) == "CANCELLA"


# --- Lettere con movimento: J e Z -----------------------------------------

def _percorso_j():
    """Discesa verticale chiusa da un uncino verso sinistra."""
    path = [(0.50, 0.30 + i * 0.03) for i in range(11)]  # giù fino a 0.60
    path += [(0.47, 0.62), (0.44, 0.63), (0.41, 0.63), (0.38, 0.62),
             (0.35, 0.60)]
    return path


def _percorso_z():
    """Tre tratti: destra, diagonale in basso a sinistra, ancora destra."""
    path = [(0.30 + i * 0.05, 0.30) for i in range(7)]  # → fino a 0.60
    path += [(0.60 - i * 0.05, 0.30 + i * 0.042) for i in range(1, 7)]  # ↙
    path += [(0.30 + i * 0.05, 0.55) for i in range(1, 7)]  # → fino a 0.60
    return path


def test_movimento_j():
    assert SignMotionClassifier.classify("I", _percorso_j()) == "J"


def test_movimento_z():
    assert SignMotionClassifier.classify("D", _percorso_z()) == "Z"


def test_movimento_forma_sbagliata():
    # la traiettoria vale solo con la forma statica di partenza giusta
    assert SignMotionClassifier.classify("D", _percorso_j()) is None
    assert SignMotionClassifier.classify("I", _percorso_z()) is None


def test_discesa_dritta_non_e_j():
    # senza l'uncino finale una discesa verticale non deve scrivere J
    path = [(0.50, 0.30 + i * 0.03) for i in range(14)]
    assert SignMotionClassifier.classify("I", path) is None


def test_tremolio_non_e_movimento():
    # piccoli spostamenti (mano quasi ferma) non producono lettere
    path = [(0.50 + 0.005 * (i % 2), 0.40 + 0.004 * (i % 3)) for i in range(20)]
    assert SignMotionClassifier.classify("I", path) is None
    assert SignMotionClassifier.classify("D", path) is None


# --- Calibrazione: campioni personali --------------------------------------

def test_calibrazione_match_e_persistenza():
    hand_a = hand(FIST, THUMB_SIDE)
    hand_aperta = hand(ALL, THUMB_OPEN)
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "segni.json")
        store = SignTemplateStore(path)
        assert store.match(hand_a) is None  # vuoto: nessun campione
        store.add_sample("A", hand_a)
        assert store.match(hand_a) == "A"
        assert store.match(hand_aperta) is None  # troppo diversa
        store.save()
        ricaricato = SignTemplateStore(path)
        assert ricaricato.match(hand_a) == "A"
        assert ricaricato.counts() == {"A": 1}
        ricaricato.forget("A")
        assert ricaricato.match(hand_a) is None


if __name__ == "__main__":
    failed = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"  OK   {name}")
            except AssertionError as e:
                failed += 1
                print(f"  FAIL {name}: {e}")
    sys.exit(1 if failed else 0)
