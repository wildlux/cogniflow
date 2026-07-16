"""Test del gesto di selezione a due mani (visual_background).

Verifica le pose sui 21 landmark sintetici della mano:
- "I": solo indice disteso e rivolto in alto → punto di inizio;
- indice+pollice rivolti in basso ("/\\") → punto di fine.
"""

import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Artificial_Intelligence.Video.visual_background import (
    finger_states,
    selection_pose,
)


def mano_chiusa(wx=100, wy=300):
    """21 landmark di una mano chiusa (tutte le dita piegate)."""
    pts = [(wx, wy)] * 21
    for mcp in (5, 9, 13, 17):
        pts[mcp] = (wx, wy - 50)
    for tip, pip in ((8, 6), (12, 10), (16, 14), (20, 18)):
        pts[pip] = (wx, wy - 60)  # falange media
        pts[tip] = (wx, wy - 40)  # punta più vicina al polso: dito piegato
    pts[2] = (wx + 20, wy - 20)  # nocca del pollice
    pts[4] = (wx + 10, wy - 10)  # pollice piegato
    return pts


def test_mano_chiusa_nessuna_posa():
    pts = mano_chiusa()
    fingers, extended = finger_states(pts)
    assert extended == 0
    assert selection_pose(pts, fingers, extended) == (False, False)


def test_posa_inizio_indice_in_alto():
    wx, wy = 100, 300
    pts = mano_chiusa(wx, wy)
    pts[6] = (wx, wy - 80)
    pts[8] = (wx, wy - 150)  # indice disteso, punta sopra la nocca
    fingers, extended = finger_states(pts)
    assert extended == 1 and fingers["indice"]
    assert selection_pose(pts, fingers, extended) == (True, False)


def test_posa_fine_indice_e_pollice_in_basso():
    wx, wy = 400, 200
    pts = mano_chiusa(wx, wy)
    pts[5] = (wx, wy + 50)
    pts[6] = (wx, wy + 80)
    pts[8] = (wx, wy + 150)  # indice disteso verso il basso
    pts[2] = (wx - 20, wy + 20)
    pts[4] = (wx - 40, wy + 130)  # pollice disteso verso il basso
    fingers, extended = finger_states(pts)
    assert fingers["indice"]
    assert selection_pose(pts, fingers, extended) == (False, True)


def test_indice_in_basso_non_e_inizio():
    wx, wy = 100, 300
    pts = mano_chiusa(wx, wy)
    pts[5] = (wx, wy + 50)
    pts[6] = (wx, wy + 80)
    pts[8] = (wx, wy + 150)  # indice disteso ma verso il basso
    fingers, extended = finger_states(pts)
    start, _end = selection_pose(pts, fingers, extended)
    assert start is False


def test_mano_aperta_nessuna_posa():
    wx, wy = 100, 300
    pts = mano_chiusa(wx, wy)
    for tip, pip in ((8, 6), (12, 10), (16, 14), (20, 18)):
        pts[pip] = (wx, wy - 80)
        pts[tip] = (wx, wy - 150)  # tutte le dita distese in alto
    fingers, extended = finger_states(pts)
    assert extended == 4
    assert selection_pose(pts, fingers, extended) == (False, False)


def test_video_thread_ha_il_segnale():
    from Artificial_Intelligence.Video.visual_background import VideoThread

    assert hasattr(VideoThread, "two_hand_select_signal")
