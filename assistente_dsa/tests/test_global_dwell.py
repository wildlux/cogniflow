"""Test del dwell click su tutta l'interfaccia (UI/global_dwell.py).

Finestra offscreen con un pulsante, un'etichetta e un campo di testo;
il puntatore è finto (pointer_provider) e i tick vengono chiamati a
mano, con il tempo di sosta accorciato per non rallentare i test.
"""

import os
import sys
import time

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtCore import QPoint
from PyQt6.QtWidgets import (
    QApplication,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QWidget,
)

app = QApplication.instance() or QApplication([])

from UI.global_dwell import GlobalDwellClicker

DWELL_MS = 60  # sosta accorciata per i test


class _RecordingEdit(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.presses = 0

    def mousePressEvent(self, a0):
        self.presses += 1
        super().mousePressEvent(a0)


def _make_window():
    win = QMainWindow()
    central = QWidget()
    win.setCentralWidget(central)
    win.setGeometry(0, 0, 400, 300)

    win.button = QPushButton("premi", central)
    win.button.setGeometry(10, 10, 120, 40)
    win.clicks = 0
    win.button.clicked.connect(lambda: setattr(win, "clicks", win.clicks + 1))

    win.label = QLabel("solo testo", central)
    win.label.setGeometry(10, 60, 120, 30)

    win.edit = _RecordingEdit(central)
    win.edit.setGeometry(10, 100, 150, 30)

    win.show()
    app.processEvents()

    win.pointer = None  # posizione finta del puntatore (coordinate central)
    clicker = GlobalDwellClicker(
        win,
        pointer_provider=lambda: (
            None if win.pointer is None else central.mapToGlobal(win.pointer)
        ),
    )
    clicker.DWELL_MS = DWELL_MS
    return win, clicker


def _dwell(clicker, ticks=3):
    """Simula la sosta: tick, attesa oltre il tempo di dwell, tick."""
    clicker._tick()
    time.sleep(DWELL_MS / 1000 + 0.03)
    for _ in range(ticks):
        clicker._tick()
    # animateClick dei pulsanti rilascia dopo ~100 ms
    time.sleep(0.12)
    app.processEvents()


def test_sosta_su_pulsante_clicca_una_volta_sola():
    win, clicker = _make_window()
    win.pointer = QPoint(50, 30)  # sopra il pulsante
    _dwell(clicker)
    assert win.clicks == 1
    # restare fermi non deve produrre altri click
    _dwell(clicker)
    assert win.clicks == 1


def test_spostarsi_e_tornare_riarma_la_sosta():
    win, clicker = _make_window()
    win.pointer = QPoint(50, 30)
    _dwell(clicker)
    assert win.clicks == 1
    win.pointer = QPoint(70, 75)  # via dal pulsante (etichetta)
    clicker._tick()
    win.pointer = QPoint(50, 30)  # e ritorno
    _dwell(clicker)
    assert win.clicks == 2


def test_etichetta_e_sfondo_non_cliccano():
    win, clicker = _make_window()
    win.pointer = QPoint(70, 75)  # etichetta: non interattiva
    _dwell(clicker)
    win.pointer = QPoint(300, 250)  # sfondo vuoto
    _dwell(clicker)
    assert win.clicks == 0 and win.edit.presses == 0
    assert not clicker.ring.isVisible()


def test_sosta_su_campo_di_testo_invia_il_click():
    win, clicker = _make_window()
    win.pointer = QPoint(50, 115)  # sopra il campo di testo
    _dwell(clicker)
    assert win.edit.presses == 1


def test_anello_visibile_durante_la_sosta():
    win, clicker = _make_window()
    win.pointer = QPoint(50, 30)
    clicker._tick()  # sosta appena iniziata
    assert clicker.ring.isVisible()
    win.pointer = None  # puntatore sparito: QCursor.pos() fuori finestra
    win.pointer = QPoint(300, 250)  # sfondo: la sosta si annulla
    clicker._tick()
    assert not clicker.ring.isVisible()


def test_spegnimento_azzera_tutto():
    win, clicker = _make_window()
    win.pointer = QPoint(50, 30)
    clicker._tick()
    clicker.set_enabled(False)
    assert not clicker.ring.isVisible()
    assert win.clicks == 0


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
