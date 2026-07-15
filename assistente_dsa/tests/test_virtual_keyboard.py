"""Test della tastiera virtuale a schermo (UI/virtual_keyboard).

Girano offscreen (QT_QPA_PLATFORM=offscreen): verificano scrittura nel
documento condiviso, maiuscola singola, cambio pagina, predizione delle
parole, apprendimento e scansione a singolo segnale.
"""

import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import QApplication, QTextEdit

from UI.virtual_keyboard import VirtualKeyboardWidget, WordPredictor

app = QApplication.instance() or QApplication(sys.argv)


def make_kb():
    editor = QTextEdit()
    kb = VirtualKeyboardWidget(target_edit=editor)
    return kb, editor


def test_scrive_nel_documento_condiviso():
    kb, editor = make_kb()
    for k in ("c", "i", "a", "o"):
        kb._on_key(k)
    assert editor.toPlainText() == "ciao"


def test_maiuscola_singola():
    kb, editor = make_kb()
    kb._on_key("⇧")
    kb._on_key("c")
    kb._on_key("i")
    assert editor.toPlainText() == "Ci"  # la maiuscola vale per una lettera


def test_backspace_e_spazio():
    kb, editor = make_kb()
    for k in ("c", "a", "s", "e", "⌫", "a", "spazio"):
        kb._on_key(k)
    assert editor.toPlainText() == "casa "


def test_cambio_pagina_numeri():
    kb, editor = make_kb()
    kb._on_key("123")
    assert kb.pages.currentIndex() == 1
    kb._on_key("4")
    kb._on_key("ABC")
    assert kb.pages.currentIndex() == 0
    assert editor.toPlainText() == "4"


def test_predizione_parole():
    p = WordPredictor()
    sugg = p.suggest("cas")
    assert "casa" in sugg
    sugg_en = p.suggest("wat")
    assert "water" in sugg_en
    # Prefisso maiuscolo -> suggerimenti con l'iniziale maiuscola
    assert all(s[0].isupper() for s in p.suggest("Cas"))


def test_apprendimento_parole(tmp_path=None):
    import tempfile

    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "apprese.json")
        p = WordPredictor(learned_path=path)
        p.learn("zampirone")
        assert "zampirone" in p.suggest("zam")
        # Ricaricando da file, la parola resta
        p2 = WordPredictor(learned_path=path)
        assert "zampirone" in p2.suggest("zamp")


def test_suggerimento_completa_la_parola():
    kb, editor = make_kb()
    for k in ("c", "a", "s"):
        kb._on_key(k)
    app.processEvents()
    btn = kb.suggest_buttons[0]
    assert btn.isVisibleTo(kb) and btn.text()
    parola = btn.text()
    btn.click()
    assert editor.toPlainText() == parola + " "


def test_scansione_singolo_segnale():
    kb, editor = make_kb()
    kb.scan_btn.setChecked(True)
    premuti = []
    kb.key_pressed.connect(premuti.append)
    kb.scan_select()  # entra nella riga evidenziata
    kb.scan_select()  # preme il tasto evidenziato
    for _ in range(20):  # animateClick scatta dopo ~100 ms
        app.processEvents()
        import time

        time.sleep(0.02)
    assert premuti, "la doppia selezione deve premere un tasto"


def test_tasto_invia():
    kb, editor = make_kb()
    inviato = []
    kb.send_requested.connect(lambda: inviato.append(True))
    kb._on_key("📤")
    assert inviato


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
