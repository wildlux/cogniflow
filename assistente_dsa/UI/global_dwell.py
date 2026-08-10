"""Dwell click su tutta l'interfaccia: sostare = cliccare.

Per chi muove un puntatore (mouse, mano-mouse via webcam, domani BCI) ma
non riesce a cliccare: fermando il puntatore per circa un secondo sopra
un elemento interattivo (pulsanti, caselle, campi di testo, liste, ...)
il click parte da solo. Un anello di avanzamento accanto al puntatore
mostra il comando che "carica"; spostandosi prima del tempo si annulla.

Regole:
 - scatta solo su widget interattivi, non sullo sfondo o sulle etichette;
 - un click solo per sosta: per ricliccare lo stesso elemento bisogna
   spostarsi (anche poco) e tornarci;
 - dentro la tastiera virtuale, se la sua "⏱️ Sosta" è già accesa, vale
   quella (stessa logica, evidenziazione del tasto migliore);
 - mentre il mano-mouse sta trascinando un pensierino il dwell tace.

Funziona nella finestra principale (l'anello è un figlio del
centralWidget, come il cursore del mano-mouse); nelle finestre di
dialogo modali il puntatore resta gestito da mouse/mano come sempre.
"""

import time

from PyQt6.QtCore import QObject, QPoint, QPointF, Qt, QTimer, QEvent
from PyQt6.QtGui import QColor, QCursor, QMouseEvent, QPainter, QPen
from PyQt6.QtWidgets import (
    QAbstractButton,
    QAbstractItemView,
    QAbstractSlider,
    QApplication,
    QComboBox,
    QLineEdit,
    QPlainTextEdit,
    QTabBar,
    QTextEdit,
    QWidget,
)

# Widget su cui la sosta ha senso: tutto il resto (sfondi, etichette,
# contenitori) viene ignorato per non generare click a sorpresa.
INTERACTIVE_TYPES = (
    QAbstractButton,
    QAbstractSlider,
    QAbstractItemView,
    QComboBox,
    QLineEdit,
    QPlainTextEdit,
    QTabBar,
    QTextEdit,
)


class DwellProgressRing(QWidget):
    """Anello che si riempie accanto al puntatore durante la sosta."""

    SIZE = 34

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setFixedSize(self.SIZE, self.SIZE)
        self.progress = 0.0
        self.hide()

    def set_progress(self, p):
        self.progress = max(0.0, min(1.0, p))
        self.update()

    def paintEvent(self, a0):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        margin = 4
        rect = self.rect().adjusted(margin, margin, -margin, -margin)
        # binario dell'anello
        painter.setPen(QPen(QColor(0, 0, 0, 60), 4))
        painter.drawArc(rect, 0, 360 * 16)
        # avanzamento (parte da ore 12, in senso orario)
        pen = QPen(QColor("#1565c0"), 4)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.drawArc(rect, 90 * 16, -int(360 * 16 * self.progress))
        painter.end()


class GlobalDwellClicker(QObject):
    """Sonda il puntatore e trasforma la sosta in un click sintetico."""

    DWELL_MS = 900  # come la tastiera virtuale
    TICK_MS = 100
    MOVE_RESET_PX = 14  # spostarsi oltre questo raggio riparte il conteggio

    def __init__(self, main_window, pointer_provider=None):
        super().__init__(main_window)
        self.win = main_window
        # Posizione globale del puntatore "vero": il mano-mouse muove un
        # cursore interno, quindi QCursor.pos() da solo non basta.
        self._pointer_provider = pointer_provider
        self.ring = DwellProgressRing(main_window.centralWidget())
        self._timer = QTimer(self)
        self._timer.setInterval(self.TICK_MS)
        self._timer.timeout.connect(self._tick)
        self._anchor = None  # widget interattivo su cui si sta sostando
        self._origin = None  # punto (globale) in cui è iniziata la sosta
        self._since = 0.0
        self._fired = False

    def set_enabled(self, on):
        if on:
            self._timer.start()
        else:
            self._timer.stop()
            self._reset()

    def _reset(self, anchor=None, origin=None):
        self._anchor = anchor
        self._origin = origin
        self._since = time.monotonic()
        self._fired = False
        if anchor is None:
            self.ring.hide()

    # ------------------------------------------------------------------

    def _pointer_pos(self):
        """Posizione globale del puntatore: mano-mouse se acceso, se no mouse."""
        if self._pointer_provider is not None:
            pos = self._pointer_provider()
            if pos is not None:
                return pos
        return QCursor.pos()

    def _target_at(self, global_pos):
        """(antenato interattivo, widget profondo) sotto il puntatore.

        Cerca prima nel popup attivo (tendine dei combo, menù), altrimenti
        dentro il centralWidget (come il mano-mouse). L'antenato interattivo
        fa da àncora della sosta; il widget profondo (per le aree a
        scorrimento è il viewport) è il destinatario del click sintetico,
        come per un click vero. Restituisce (None, None) se sotto il
        puntatore non c'è nulla di cliccabile.
        """
        popup = QApplication.activePopupWidget()
        if popup is not None:
            local = popup.mapFromGlobal(global_pos)
            if not popup.rect().contains(local):
                return None, None  # popup aperto ma puntatore fuori
            deep = popup.childAt(local) or popup
            root = None  # il popup stesso delimita la risalita
        else:
            central = self.win.centralWidget()
            if central is None:
                return None, None
            local = central.mapFromGlobal(global_pos)
            if not central.rect().contains(local):
                return None, None
            deep = central.childAt(local)
            root = central
        w = deep
        while w is not None and w is not root:
            if isinstance(w, INTERACTIVE_TYPES):
                return w, deep
            if popup is not None and w is popup:
                break
            w = w.parentWidget()
        return None, None

    def _keyboard_handles_it(self, widget):
        """True se il widget è nella tastiera virtuale con la SUA sosta accesa."""
        kb = getattr(self.win, "virtual_keyboard", None)
        if kb is None or not kb.isVisible():
            return False
        dwell_btn = getattr(kb, "dwell_btn", None)
        if dwell_btn is None or not dwell_btn.isChecked():
            return False
        w = widget
        while w is not None:
            if w is kb:
                return True
            w = w.parentWidget()
        return False

    def _tick(self):
        # Mentre il mano-mouse trascina o tiene premuto, la sosta tace
        hand = getattr(self.win, "hand_mouse", None)
        if hand is not None and getattr(hand, "pressed", False):
            self._reset()
            return

        pos = self._pointer_pos()
        target, deep = self._target_at(pos)
        if target is not None and self._keyboard_handles_it(target):
            target = None
        if target is None:
            self._reset()
            return

        now = time.monotonic()
        if target is not self._anchor:
            self._reset(target, pos)
        elif (pos - self._origin).manhattanLength() > self.MOVE_RESET_PX:
            # ci si è spostati: nuovo punto di sosta nello stesso widget
            # (e si può ricliccare un elemento già cliccato)
            self._reset(target, pos)

        if self._fired:
            return
        held_ms = (now - self._since) * 1000
        self._show_ring(pos, held_ms / self.DWELL_MS)
        if held_ms >= self.DWELL_MS:
            self._fired = True
            self.ring.hide()
            self._click(target, deep, pos)

    def _show_ring(self, global_pos, progress):
        central = self.win.centralWidget()
        if central is None:
            return
        local = central.mapFromGlobal(global_pos)
        # accanto al puntatore, non sotto: resta visibile mentre si sosta
        self.ring.move(local.x() + 10, local.y() - self.ring.height() - 4)
        self.ring.set_progress(min(1.0, progress))
        self.ring.show()
        self.ring.raise_()

    def _click(self, target, deep, global_pos):
        """Click sintetico: pressione e rilascio nello stesso punto.

        I pulsanti passano da animateClick (feedback visivo compreso);
        per il resto gli eventi vanno al widget profondo sotto il
        puntatore (il viewport nelle aree a scorrimento), dove arriverebbe
        anche un click vero.
        """
        if isinstance(target, QAbstractButton):
            target.animateClick()
            return
        receiver = deep or target
        local = QPointF(receiver.mapFromGlobal(global_pos))
        for etype, buttons in (
            (QEvent.Type.MouseButtonPress, Qt.MouseButton.LeftButton),
            (QEvent.Type.MouseButtonRelease, Qt.MouseButton.NoButton),
        ):
            event = QMouseEvent(
                etype,
                local,
                QPointF(global_pos),
                Qt.MouseButton.LeftButton,
                buttons,
                Qt.KeyboardModifier.NoModifier,
            )
            QApplication.sendEvent(receiver, event)
