"""Test dell'attiva/disattiva dell'inchiostro della penna in aria.

Verifica il dwell dell'indice (alzato per PEN_DWELL_S apre/chiude il
rubinetto, abbassato prima annulla) e la sincronizzazione nei due sensi
con l'interruttore 💧 della barra del canvas. I metodi reali di
MainWindow (_on_pen_tip, _set_canvas_ink) vengono agganciati a un oggetto
finto con i soli widget necessari, senza avviare l'applicazione.
"""

import os
import sys
import time
import types

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import QApplication, QLabel, QPushButton, QWidget

app = QApplication.instance() or QApplication([])

import main_01_Aircraft as m

DWELL = 0.15  # dwell accorciato per non rallentare i test


class _RecordingCanvas(QWidget):
    """Canvas finto: registra l'ultima chiamata ad air_pen_point."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.last = None

    def air_pen_point(self, nx, ny, visible, ink=False):
        self.last = (nx, ny, visible, ink)


class _FakeStack:
    def currentIndex(self):
        return 1  # pagina canvas visibile


class _Fake:
    """Contenitore vuoto (SimpleNamespace non regge le connessioni Qt)."""


def _make_fake():
    """Oggetto minimo con i metodi veri di MainWindow e i widget necessari."""
    fake = _Fake()
    fake._on_pen_tip = types.MethodType(m.MainWindow._on_pen_tip, fake)
    fake._set_canvas_ink = types.MethodType(m.MainWindow._set_canvas_ink, fake)
    fake.PEN_DWELL_S = DWELL

    central = QWidget()
    central.resize(100, 100)
    canvas = _RecordingCanvas(central)
    canvas.setGeometry(0, 0, 100, 100)
    fake.centralWidget = lambda: central
    fake.footer_canvas = canvas
    fake.footer_input_stack = _FakeStack()

    drawing = types.SimpleNamespace()
    drawing.hint_label = QLabel()
    drawing.ink_button = QPushButton()
    drawing.ink_button.setCheckable(True)
    drawing.ink_button.toggled.connect(fake._set_canvas_ink)
    fake.footer_drawing = drawing
    fake._central = central  # tiene vivi i widget
    return fake


def _frames(fake, index_up, n, pause=0.0):
    for _ in range(n):
        fake._on_pen_tip(0.5, 0.5, index_up)
        if pause:
            time.sleep(pause)


def test_dwell_apre_e_chiude_il_rubinetto():
    fake = _make_fake()
    _frames(fake, True, 2)  # alzata appena iniziata: ancora niente
    assert getattr(fake, "_canvas_ink_on", False) is False
    time.sleep(DWELL + 0.05)
    fake._on_pen_tip(0.5, 0.5, True)  # sosta completata: si apre
    assert fake._canvas_ink_on is True
    assert fake.footer_drawing.ink_button.isChecked() is True
    # tenere l'indice su ancora NON deve richiudere (scatta una volta sola)
    _frames(fake, True, 3)
    assert fake._canvas_ink_on is True
    # indice giù, poi nuova alzata completa: si richiude
    _frames(fake, False, 4)
    fake._on_pen_tip(0.5, 0.5, True)
    time.sleep(DWELL + 0.05)
    fake._on_pen_tip(0.5, 0.5, True)
    assert fake._canvas_ink_on is False
    assert fake.footer_drawing.ink_button.isChecked() is False


def test_alzata_breve_non_cambia_nulla():
    fake = _make_fake()
    _frames(fake, True, 3)  # alzata più corta del dwell
    _frames(fake, False, 4)
    assert getattr(fake, "_canvas_ink_on", False) is False
    assert fake.footer_drawing.ink_button.isChecked() is False


def test_pulsante_equivale_al_gesto():
    fake = _make_fake()
    fake.footer_drawing.ink_button.setChecked(True)  # click sul pulsante
    assert fake._canvas_ink_on is True
    fake._on_pen_tip(0.5, 0.5, False)  # la punta ora scrive
    assert fake.footer_canvas.last[2:] == (True, True)
    fake.footer_drawing.ink_button.setChecked(False)
    assert fake._canvas_ink_on is False
    fake._on_pen_tip(0.5, 0.5, False)
    assert fake.footer_canvas.last[2:] == (True, False)


def test_mano_fuori_inquadratura_solleva_la_penna():
    fake = _make_fake()
    fake._on_pen_tip(-1.0, -1.0, False)
    assert fake.footer_canvas.last == (0.0, 0.0, False, False)


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
