"""Calibrazione dei segni dell'alfabeto manuale (dattilologia).

L'utente registra i PROPRI segni: sceglie una lettera, tiene la mano
ferma davanti alla webcam e la finestra cattura alcuni fotogrammi di
landmark, li media e li salva come campione personale. Al riconoscimento
i campioni vengono confrontati per primi e, se la mano è abbastanza
vicina, vincono sulla geometria generica — utile soprattutto per le
lettere "a pugno" (A E S T N M), che si somigliano molto.

I campioni finiscono in Save/SETUP_TOOLS_&_Data/segni_calibrati.json
(via SignTemplateStore); ogni lettera tiene al massimo gli ultimi 5.
"""

import string

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

try:
    from Artificial_Intelligence.Video.sign_tracker import (
        SignLanguageThread,
        SignTemplateStore,
    )
except ImportError:  # avvio come pacchetto installato
    from assistente_dsa.Artificial_Intelligence.Video.sign_tracker import (
        SignLanguageThread,
        SignTemplateStore,
    )

COUNTDOWN_S = 3  # secondi per mettersi in posa
CAPTURE_FRAMES = 10  # fotogrammi mediati in un campione


class SignCalibrationDialog(QDialog):
    """Registra campioni personali delle lettere dell'alfabeto manuale."""

    def __init__(self, parent=None, templates_path=None):
        super().__init__(parent)
        self.setWindowTitle("🎯 Calibra i tuoi segni")
        self.setMinimumWidth(420)
        self.store = SignTemplateStore(templates_path)
        self._last_landmarks = None
        self._capture_buffer = None  # None = non in cattura
        self._countdown = 0

        layout = QVBoxLayout(self)
        info = QLabel(
            "Scegli una lettera, premi Registra e tieni il TUO segno fermo "
            "davanti alla webcam: dopo il conto alla rovescia viene salvato "
            "come campione personale. Più campioni della stessa lettera "
            "(anche con angolazioni un po' diverse) rendono il "
            "riconoscimento più preciso."
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        row = QHBoxLayout()
        row.addWidget(QLabel("Lettera:"))
        self.letter_combo = QComboBox()
        self.letter_combo.addItems(list(string.ascii_uppercase))
        self.letter_combo.setMinimumHeight(36)
        row.addWidget(self.letter_combo)
        self.record_btn = QPushButton("📸 Registra")
        self.record_btn.setMinimumHeight(36)
        self.record_btn.clicked.connect(self._start_capture)
        row.addWidget(self.record_btn)
        self.forget_btn = QPushButton("🗑 Dimentica")
        self.forget_btn.setToolTip("Cancella i campioni salvati per questa lettera")
        self.forget_btn.setMinimumHeight(36)
        self.forget_btn.clicked.connect(self._forget_letter)
        row.addWidget(self.forget_btn)
        row.addStretch()
        layout.addLayout(row)

        self.live_label = QLabel("Accensione della webcam…")
        self.live_label.setStyleSheet("font-size: 15px; padding: 6px;")
        layout.addWidget(self.live_label)

        self.counts_label = QLabel("")
        self.counts_label.setWordWrap(True)
        self.counts_label.setStyleSheet("color: #555;")
        layout.addWidget(self.counts_label)
        self._refresh_counts()

        buttons = QHBoxLayout()
        buttons.addStretch()
        close_btn = QPushButton("Chiudi")
        close_btn.setMinimumHeight(36)
        close_btn.clicked.connect(self.accept)
        buttons.addWidget(close_btn)
        layout.addLayout(buttons)

        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._tick)

        # La webcam serve solo qui: il thread emette i landmark grezzi e
        # come anteprima la lettera che la geometria generica riconosce.
        self.thread = SignLanguageThread(
            emit_landmarks=True, templates_path=templates_path
        )
        self.thread.hand_sample.connect(self._on_landmarks)
        self.thread.candidate.connect(self._on_candidate)
        self.thread.status.connect(self.live_label.setText)
        self.thread.start()

    # --- webcam ---------------------------------------------------------

    def _on_landmarks(self, points):
        self._last_landmarks = points
        if self._capture_buffer is not None and self._countdown == 0:
            self._capture_buffer.append(points)
            if len(self._capture_buffer) >= CAPTURE_FRAMES:
                self._save_sample()

    def _on_candidate(self, letter, _progress):
        if self._capture_buffer is not None:
            return  # durante la cattura la barra mostra il conto/avanzamento
        if letter:
            self.live_label.setText(f"La geometria vede: 🤟 {letter}")
        else:
            self.live_label.setText("Mostra la mano alla webcam")

    # --- cattura --------------------------------------------------------

    def _start_capture(self):
        if self._capture_buffer is not None:
            return
        self._capture_buffer = []
        self._countdown = COUNTDOWN_S
        self.record_btn.setEnabled(False)
        self.live_label.setText(
            f"Preparati: {self._countdown}… tieni il segno fermo"
        )
        self._timer.start()

    def _tick(self):
        self._countdown -= 1
        if self._countdown > 0:
            self.live_label.setText(
                f"Preparati: {self._countdown}… tieni il segno fermo"
            )
        elif self._countdown == 0:
            self.live_label.setText("📸 Sto registrando, non muovere la mano…")
        elif self._countdown <= -6:
            # in ~6 s la mano non si è mai vista: si rinuncia al campione
            self._capture_buffer = None
            self._countdown = 0
            self._timer.stop()
            self.record_btn.setEnabled(True)
            self.live_label.setText(
                "Non ho visto la mano: campione non salvato, riprova"
            )

    def _save_sample(self):
        frames = self._capture_buffer
        self._capture_buffer = None
        self._timer.stop()
        self.record_btn.setEnabled(True)
        letter = self.letter_combo.currentText()
        if not frames:
            self.live_label.setText("Nessuna mano vista: campione non salvato")
            return
        n = len(frames)
        avg = [
            (
                sum(f[i][0] for f in frames) / n,
                sum(f[i][1] for f in frames) / n,
            )
            for i in range(21)
        ]
        self.store.add_sample(letter, avg)
        self.store.save()
        self._refresh_counts()
        self.live_label.setText(f"✅ Campione salvato per la lettera {letter}")

    def _forget_letter(self):
        letter = self.letter_combo.currentText()
        self.store.forget(letter)
        self.store.save()
        self._refresh_counts()
        self.live_label.setText(f"Campioni della lettera {letter} cancellati")

    def _refresh_counts(self):
        counts = self.store.counts()
        if counts:
            testo = ", ".join(f"{le} ({n})" for le, n in counts.items())
            self.counts_label.setText(f"Lettere calibrate: {testo}")
        else:
            self.counts_label.setText(
                "Nessuna lettera calibrata: vale la geometria generica."
            )

    # --- chiusura -------------------------------------------------------

    def closeEvent(self, event):
        self._timer.stop()
        if self.thread is not None:
            self.thread.stop()
            self.thread = None
        super().closeEvent(event)

    def accept(self):
        self._timer.stop()
        if self.thread is not None:
            self.thread.stop()
            self.thread = None
        super().accept()
