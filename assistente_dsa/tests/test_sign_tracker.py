"""Test del classificatore dell'alfabeto manuale (sign_tracker).

Costruisce mani sintetiche (21 landmark) e verifica che le forme base
vengano riconosciute. Le coordinate sono normalizzate come quelle di
MediaPipe: origine in alto a sinistra, y che cresce verso il basso.
"""

import os
import sys
from collections import namedtuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Artificial_Intelligence.Video.sign_tracker import SignAlphabetClassifier

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
