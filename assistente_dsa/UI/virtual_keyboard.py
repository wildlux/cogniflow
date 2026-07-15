"""Tastiera virtuale a schermo per scrivere solo col puntatore.

Pensata per chi non può usare la tastiera fisica: si scrive con il mouse,
con il mano-mouse via webcam e, in prospettiva, con un collegamento BCI.

Caratteristiche:
 - tasti grandi (minimo 44 px, di norma di più) con layout QWERTY
   italiano, riga delle vocali accentate e pagina secondaria per numeri
   e punteggiatura;
 - scrive direttamente nel campo pensierini del footer (attraverso il
   suo cursore di testo) e ne mostra una copia in un'anteprima in sola
   lettura sopra i tasti, visto che la tastiera copre il campo;
 - predizione delle parole: fino a 5 suggerimenti sopra i tasti, da un
   dizionario di frequenza offline italiano + inglese, più le parole
   che l'utente usa davvero (apprese e salvate localmente);
 - dwell click (⏱️ Sosta): sostare col puntatore su un tasto equivale a
   premerlo — funziona sia col mouse sia col cursore interno del
   mano-mouse (fornito da pointer_provider);
 - scansione a singolo segnale (🔦): l'evidenziazione cicla prima le
   righe e poi i tasti; il segnale di selezione è la barra spaziatrice,
   Invio, oppure una chiamata a scan_select() — il punto di aggancio
   per il futuro collegamento brain-computer;
 - eco vocale (🔊): ogni lettera premuta e ogni parola completata può
   essere pronunciata dal TTS (callable "speak" passato dal chiamante).
"""

import bisect
import json
import os
import re

from PyQt6.QtCore import QEvent, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QCursor
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QPushButton,
    QSizePolicy,
    QStackedWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

# Parole più comuni, in ordine di frequenza: il peso decresce con la
# posizione. Bastano per la partenza a freddo; poi la tastiera impara
# le parole che l'utente scrive davvero.
PAROLE_ITALIANE = (
    "di che è la il non e un a per in una mi sono si lo ho ma io ti le "
    "cosa se no come qui più bene sei tu questo hai del era mio solo "
    "tutto della me molto fatto anche dove sta detto essere lei quando "
    "con lui ci noi voi loro questa quella cui già sempre ancora dopo "
    "prima adesso oggi domani ieri ora poi mai niente nulla qualcosa "
    "perché così allora quindi però anzi invece mentre senza sotto sopra "
    "dentro fuori vicino lontano grande piccolo nuovo vecchio bello "
    "brutto buono cattivo alto basso lungo corto caldo freddo facile "
    "difficile importante possibile vero falso giusto sbagliato pieno "
    "vuoto aperto chiuso primo ultimo altro stesso ogni alcuni tanti "
    "pochi troppo poco tanto meno ancora quasi forse certo davvero "
    "essere avere fare dire andare potere volere dovere sapere vedere "
    "dare stare venire uscire entrare partire tornare restare rimanere "
    "prendere mettere portare trovare pensare credere parlare chiedere "
    "rispondere capire sentire ascoltare guardare leggere scrivere "
    "contare studiare imparare insegnare giocare correre camminare "
    "mangiare bere dormire svegliarsi lavarsi vestirsi aiutare amare "
    "piacere sembrare diventare cominciare finire aprire chiudere "
    "casa scuola libro quaderno matita penna colore banco maestra "
    "maestro compagno amico amica bambino bambina ragazzo ragazza "
    "mamma papà nonno nonna fratello sorella famiglia gente persona "
    "uomo donna nome parola frase lettera numero storia disegno musica "
    "gioco festa regalo torta acqua pane latte frutta mela gatto cane "
    "animale albero fiore sole luna stella cielo mare monte città "
    "strada porta finestra tavolo sedia letto bagno cucina camera "
    "giorno notte mattina sera settimana mese anno tempo minuto "
    "lunedì martedì mercoledì giovedì venerdì sabato domenica "
    "uno due tre quattro cinque sei sette otto nove dieci cento mille "
    "rosso blu verde giallo bianco nero rosa viola arancione marrone "
    "grazie prego scusa ciao arrivederci buongiorno buonasera "
    "buonanotte piano forte insieme presto tardi subito"
).split()

ENGLISH_WORDS = (
    "the of and to a in is you that it he was for on are as with his "
    "they I at be this have from or one had by word but not what all "
    "were we when your can said there use an each which she do how "
    "their if will up other about out many then them these so some her "
    "would make like him into time has look two more write go see "
    "number no way could people my than first water been call who its "
    "now find long down day did get come made may part over new sound "
    "take only little work know place year live me back give most very "
    "after thing our just name good sentence man think say great where "
    "help through much before line right too mean old any same tell boy "
    "follow came want show also around form three small set put end "
    "does another well large must big even such because turn here why "
    "ask went men read need land different home us move try kind hand "
    "picture again change off play spell air away animal house point "
    "page letter mother answer found study still learn should world "
    "high every near add food between own below country plant last "
    "school father keep tree never start city earth eye light thought "
    "head under story saw left don't few while along might close "
    "something seem next hard open example begin life always those both "
    "paper together got group often run"
).split()

# Dizionari di sistema (solo completamento, senza frequenza): usati come
# ultima risorsa quando le liste di frequenza non bastano.
SYSTEM_WORDLISTS = ("/usr/share/dict/italian", "/usr/share/dict/american-english")

_WORD_RE = re.compile(r"[a-zA-Zàèéìòù']+$")


class WordPredictor:
    """Suggerisce completamenti di parola da dizionari di frequenza offline.

    Tre livelli, in ordine di priorità: parole apprese dall'utente
    (pesate per quanto le usa), liste di frequenza integrate (italiano +
    inglese), dizionari di sistema se presenti (solo in coda).
    """

    def __init__(self, learned_path=None):
        self.learned_path = learned_path
        self.learned = {}
        if learned_path and os.path.exists(learned_path):
            try:
                with open(learned_path, encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, dict):
                    self.learned = {str(k): int(v) for k, v in data.items()}
            except (OSError, ValueError):
                self.learned = {}

        self.frequent = {}
        for rank, w in enumerate(PAROLE_ITALIANE):
            self.frequent.setdefault(w, len(PAROLE_ITALIANE) - rank)
        for rank, w in enumerate(ENGLISH_WORDS):
            # L'inglese pesa un po' meno: a parità, vince l'italiano
            self.frequent.setdefault(w.lower(), (len(ENGLISH_WORDS) - rank) // 2)

        self._system_words = None  # caricati pigramente al primo uso

    def _load_system_words(self):
        if self._system_words is not None:
            return self._system_words
        words = set()
        for path in SYSTEM_WORDLISTS:
            try:
                with open(path, encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        w = line.strip().lower()
                        if len(w) > 2 and "'" not in w:
                            words.add(w)
            except OSError:
                continue
        self._system_words = sorted(words)
        return self._system_words

    def suggest(self, prefix, n=5):
        """Fino a n parole che iniziano con prefix (case-insensitive)."""
        prefix = (prefix or "").strip()
        if len(prefix) < 1:
            return []
        low = prefix.lower()

        scored = []
        for word, weight in self.learned.items():
            if word.startswith(low) and word != low:
                scored.append((weight + 10_000, word))  # le sue parole vincono
        for word, weight in self.frequent.items():
            if word.startswith(low) and word != low:
                scored.append((weight, word))
        scored.sort(reverse=True)
        out = []
        for _w, word in scored:
            if word not in out:
                out.append(word)
            if len(out) >= n:
                break

        # I dizionari di sistema (senza frequenza) solo come riserva: meglio
        # 3 suggerimenti buoni che 5 con parole rare in mezzo
        if len(out) < 3 and len(low) >= 3:
            sys_words = self._load_system_words()
            i = bisect.bisect_left(sys_words, low)
            while i < len(sys_words) and sys_words[i].startswith(low):
                w = sys_words[i]
                if w != low and w not in out:
                    out.append(w)
                    if len(out) >= n:
                        break
                i += 1

        # Rispetta la maiuscola iniziale di quello che si sta scrivendo
        if prefix[0].isupper():
            out = [w.capitalize() for w in out]
        return out

    def learn(self, word):
        """Registra che l'utente ha scritto questa parola (e salva)."""
        word = (word or "").strip().lower()
        if len(word) < 2 or not _WORD_RE.match(word):
            return
        self.learned[word] = self.learned.get(word, 0) + 1
        if self.learned_path:
            try:
                os.makedirs(os.path.dirname(self.learned_path), exist_ok=True)
                with open(self.learned_path, "w", encoding="utf-8") as f:
                    json.dump(self.learned, f, ensure_ascii=False)
            except OSError:
                pass


class VirtualKeyboardWidget(QWidget):
    """Tastiera a schermo integrata nell'area comune del footer.

    Scrive nel QTextDocument passato (quello del campo pensierini),
    mostrandolo in un'anteprima sopra i tasti. Vedi il docstring del
    modulo per dwell, scansione ed eco vocale.
    """

    key_pressed = pyqtSignal(str)  # tasto premuto (per log/telemetria)
    word_completed = pyqtSignal(str)  # parola conclusa da spazio/suggerimento
    send_requested = pyqtSignal()  # tasto 📤: invia il pensierino

    KEY_MIN = 44  # px, requisito di accessibilità (meglio di più)
    DWELL_MS = 900  # sosta sul tasto prima del click automatico
    SCAN_MS = 900  # passo della scansione righe/tasti

    ROWS_LETTERS = [
        ["à", "è", "é", "ì", "ò", "ù", "'"],
        ["q", "w", "e", "r", "t", "y", "u", "i", "o", "p"],
        ["a", "s", "d", "f", "g", "h", "j", "k", "l"],
        ["⇧", "z", "x", "c", "v", "b", "n", "m", "⌫"],
        ["123", ",", "spazio", ".", "📤"],
    ]
    ROWS_SYMBOLS = [
        ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0"],
        ["+", "-", "*", "/", "=", "%", "€", "$", "@", "#"],
        ["!", "?", ":", ";", '"', "(", ")", "⌫"],
        ["ABC", ",", "spazio", ".", "📤"],
    ]

    def __init__(
        self,
        target_edit=None,
        speak=None,
        pointer_provider=None,
        learned_words_path=None,
        parent=None,
    ):
        super().__init__(parent)
        self.target = target_edit  # QTextEdit in cui scrivere davvero
        self._speak = speak
        self._pointer_provider = pointer_provider
        self.predictor = WordPredictor(learned_words_path)
        self._shift = False

        root = QVBoxLayout(self)
        root.setContentsMargins(4, 4, 4, 4)
        root.setSpacing(4)

        # --- Anteprima: copia in sola lettura del campo pensierini -----
        # (niente documento condiviso: se il campo venisse distrutto prima
        # della tastiera, l'anteprima resterebbe con un puntatore pendente)
        self.preview = QTextEdit()
        self.preview.setReadOnly(True)
        self.preview.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.preview.setPlaceholderText("💭 Il testo scritto appare qui...")
        self.preview.setMaximumHeight(64)
        self.preview.setStyleSheet(
            "QTextEdit { background: rgba(255,255,255,0.95);"
            " border: 1px solid #dee2e6; border-radius: 6px;"
            " padding: 4px 8px; font-size: 13px; color: #495057; }"
        )
        root.addWidget(self.preview)

        # --- Barra dei suggerimenti -------------------------------------
        self.suggest_row = QHBoxLayout()
        self.suggest_row.setSpacing(4)
        self.suggest_buttons = []
        for _ in range(5):
            b = QPushButton("")
            b.setVisible(False)
            b.setMinimumHeight(self.KEY_MIN)
            b.setSizePolicy(
                QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
            )
            b.setStyleSheet(self._suggest_style())
            b.clicked.connect(self._on_suggestion)
            self.suggest_buttons.append(b)
            self.suggest_row.addWidget(b)
        root.addLayout(self.suggest_row)

        # --- Pagine di tasti: lettere e numeri/punteggiatura ------------
        self.pages = QStackedWidget()
        self._page_rows = []  # per pagina: liste di righe di QPushButton
        for rows in (self.ROWS_LETTERS, self.ROWS_SYMBOLS):
            page, buttons = self._build_page(rows)
            self.pages.addWidget(page)
            self._page_rows.append(buttons)
        self.pages.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        root.addWidget(self.pages, 1)

        # --- Barra delle modalità: sosta, scansione, eco ----------------
        modes = QHBoxLayout()
        modes.setSpacing(4)

        def _mode_btn(label, tip):
            b = QPushButton(label)
            b.setCheckable(True)
            b.setToolTip(tip)
            b.setMinimumHeight(30)
            b.setStyleSheet(self._mode_style())
            modes.addWidget(b)
            return b

        self.dwell_btn = _mode_btn(
            "⏱️ Sosta",
            "Dwell click: ferma il puntatore su un tasto per premerlo, "
            "senza dover cliccare. Funziona col mouse e col mano-mouse.",
        )
        self.dwell_btn.toggled.connect(self._toggle_dwell)
        self.scan_btn = _mode_btn(
            "🔦 Scansione",
            "Scansione a singolo segnale: l'evidenziazione passa da una "
            "riga all'altra; SPAZIO o INVIO (o un segnale esterno) sceglie "
            "la riga e poi il tasto. Pensata per il futuro collegamento BCI.",
        )
        self.scan_btn.toggled.connect(self._toggle_scan)
        self.echo_btn = _mode_btn(
            "🔊 Eco",
            "Eco vocale: ogni lettera premuta e ogni parola completata "
            "viene letta ad alta voce.",
        )
        modes.addStretch()
        root.addLayout(modes)

        # Dwell: sonda periodica della posizione del puntatore
        self._dwell_timer = QTimer(self)
        self._dwell_timer.setInterval(100)
        self._dwell_timer.timeout.connect(self._dwell_tick)
        self._dwell_key = None
        self._dwell_since = 0
        self._dwell_fired = None

        # Scansione: righe -> tasti
        self._scan_timer = QTimer(self)
        self._scan_timer.setInterval(self.SCAN_MS)
        self._scan_timer.timeout.connect(self._scan_tick)
        self._scan_row = 0
        self._scan_key = None  # None = sta ciclando le righe

        if self.target is not None:
            self.target.textChanged.connect(self._sync_preview)
        self._sync_preview()

    def _sync_preview(self):
        """Ricopia il testo del campo nell'anteprima e aggiorna i suggerimenti."""
        if self.target is not None:
            text = self.target.toPlainText()
            if self.preview.toPlainText() != text:
                self.preview.setPlainText(text)
                sb = self.preview.verticalScrollBar()
                if sb is not None:
                    sb.setValue(sb.maximum())  # si vede sempre l'ultima riga
        self._refresh_suggestions()

    # ------------------------------------------------------------------
    # Costruzione dei tasti
    # ------------------------------------------------------------------

    def _key_style(self):
        return (
            "QPushButton { background: #ffffff; color: #2c3e50;"
            " border: 1px solid #ccc; border-radius: 8px;"
            " font-size: 18px; font-weight: bold; padding: 2px; }"
            "QPushButton:hover { background: #eef4ff; border-color: #4a90e2; }"
            "QPushButton:pressed { background: #d6e6ff; }"
            'QPushButton[scan="true"] { background: #fff3cd;'
            " border: 3px solid #f0a020; }"
            'QPushButton[dwell="true"] { background: #d6e6ff;'
            " border: 3px solid #2196f3; }"
        )

    def _suggest_style(self):
        return (
            "QPushButton { background: #f1f7ff; color: #1565c0;"
            " border: 1px solid #bcd7ff; border-radius: 8px;"
            " font-size: 15px; padding: 2px 6px; }"
            "QPushButton:hover { background: #d6e6ff; }"
            'QPushButton[scan="true"] { background: #fff3cd;'
            " border: 3px solid #f0a020; }"
            'QPushButton[dwell="true"] { background: #d6e6ff;'
            " border: 3px solid #2196f3; }"
        )

    def _mode_style(self):
        return (
            "QPushButton { background: #ffffff; color: #495057;"
            " border: 1px solid #ccc; border-radius: 6px;"
            " font-size: 12px; padding: 2px 10px; }"
            "QPushButton:checked { background: #d6e6ff;"
            " border-color: #2196f3; color: #1565c0; }"
        )

    def _build_page(self, rows):
        page = QWidget()
        grid = QVBoxLayout(page)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(4)
        buttons_rows = []
        for row in rows:
            hl = QHBoxLayout()
            hl.setSpacing(4)
            btn_row = []
            for label in row:
                b = QPushButton("spazio" if label == "spazio" else label)
                b.setMinimumSize(self.KEY_MIN, self.KEY_MIN)
                b.setSizePolicy(
                    QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
                )
                b.setStyleSheet(self._key_style())
                b.setFocusPolicy(Qt.FocusPolicy.NoFocus)  # il focus resta al testo
                if label == "spazio":
                    hl.addWidget(b, 4)  # barra spazio larga
                elif label in ("⇧", "⌫", "123", "ABC", "📤"):
                    hl.addWidget(b, 2)
                else:
                    hl.addWidget(b, 1)
                b.clicked.connect(lambda _c, k=label: self._on_key(k))
                btn_row.append(b)
            grid.addLayout(hl)
            buttons_rows.append(btn_row)
        return page, buttons_rows

    # ------------------------------------------------------------------
    # Scrittura
    # ------------------------------------------------------------------

    def _cursor(self):
        if self.target is None:
            return None
        return self.target.textCursor()

    def _insert(self, text):
        cur = self._cursor()
        if cur is None:
            return
        cur.insertText(text)
        self.target.setTextCursor(cur)

    def _current_prefix(self):
        """La parola (parziale) subito prima del cursore."""
        cur = self._cursor()
        if cur is None:
            return ""
        block_text = cur.block().text()[: cur.positionInBlock()]
        m = _WORD_RE.search(block_text)
        return m.group(0) if m else ""

    def _on_key(self, key):
        self.key_pressed.emit(key)
        if key == "⇧":
            self._shift = not self._shift
            return
        if key == "123":
            self.pages.setCurrentIndex(1)
            self._scan_reset()
            return
        if key == "ABC":
            self.pages.setCurrentIndex(0)
            self._scan_reset()
            return
        if key == "⌫":
            cur = self._cursor()
            if cur is not None:
                cur.deletePreviousChar()
                self.target.setTextCursor(cur)
            return
        if key == "📤":
            self.send_requested.emit()
            return
        if key == "spazio":
            word = self._current_prefix()
            self._insert(" ")
            if word:
                self.predictor.learn(word)
                self.word_completed.emit(word)
                self._echo(word)
            return

        ch = key.upper() if self._shift and len(key) == 1 else key
        if self._shift:
            self._shift = False  # maiuscola singola, come nei telefoni
        self._insert(ch)
        if ch.isalpha():
            self._echo(ch)
        if key in ".,!?:;":
            word_before = self._current_prefix()
            if word_before:
                self.predictor.learn(word_before)

    def _on_suggestion(self):
        btn = self.sender()
        word = btn.text()
        if not word:
            return
        prefix = self._current_prefix()
        cur = self._cursor()
        if cur is None:
            return
        for _ in range(len(prefix)):
            cur.deletePreviousChar()
        cur.insertText(word + " ")
        self.target.setTextCursor(cur)
        self.predictor.learn(word)
        self.word_completed.emit(word)
        self._echo(word)

    def _refresh_suggestions(self):
        words = self.predictor.suggest(self._current_prefix(), n=5)
        for btn, word in zip(self.suggest_buttons, words + [""] * 5):
            btn.setText(word)
            btn.setVisible(bool(word))

    def _echo(self, text):
        if self._speak is not None and self.echo_btn.isChecked():
            try:
                self._speak(text)
            except Exception:
                pass  # l'eco non deve mai bloccare la scrittura

    # ------------------------------------------------------------------
    # Dwell click (sosta sul tasto = pressione)
    # ------------------------------------------------------------------

    def _toggle_dwell(self, on):
        if on:
            self._dwell_timer.start()
        else:
            self._dwell_timer.stop()
            self._set_dwell_mark(None)

    def _pointer_pos(self):
        """Posizione globale del puntatore: mano-mouse se attivo, sennò mouse."""
        if self._pointer_provider is not None:
            try:
                pos = self._pointer_provider()
            except Exception:
                pos = None
            if pos is not None:
                return pos
        return QCursor.pos()

    def _key_under_pointer(self):
        w = self.childAt(self.mapFromGlobal(self._pointer_pos()))
        while w is not None and w is not self:
            if isinstance(w, QPushButton):
                return w
            w = w.parentWidget()
        return None

    def _set_dwell_mark(self, btn):
        for old in self.findChildren(QPushButton):
            if old.property("dwell"):
                old.setProperty("dwell", False)
                old.style().unpolish(old)
                old.style().polish(old)
        if btn is not None:
            btn.setProperty("dwell", True)
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def _dwell_tick(self):
        import time

        btn = self._key_under_pointer()
        now = time.monotonic()
        if btn is not self._dwell_key:
            self._dwell_key = btn
            self._dwell_since = now
            self._dwell_fired = None
            self._set_dwell_mark(btn)
            return
        if btn is None or btn is self._dwell_fired:
            return
        if (now - self._dwell_since) * 1000 >= self.DWELL_MS:
            self._dwell_fired = btn  # una pressione sola finché non si esce
            btn.animateClick()

    # ------------------------------------------------------------------
    # Scansione a singolo segnale (righe -> tasti)
    # ------------------------------------------------------------------

    def _scan_rows(self):
        """Le righe scandibili: suggerimenti (se presenti) + tasti della pagina."""
        rows = []
        visible_suggests = [b for b in self.suggest_buttons if b.isVisible()]
        if visible_suggests:
            rows.append(visible_suggests)
        rows.extend(self._page_rows[self.pages.currentIndex()])
        return rows

    def _toggle_scan(self, on):
        self._scan_reset()
        if on:
            # SPAZIO/INVIO devono fare da segnale anche quando il focus
            # è nel campo di anteprima
            self.preview.installEventFilter(self)
            self._scan_timer.start()
            self._scan_mark()
        else:
            self.preview.removeEventFilter(self)
            self._scan_timer.stop()

    def eventFilter(self, obj, event):
        if (
            obj is self.preview
            and self.scan_btn.isChecked()
            and event.type() == QEvent.Type.KeyPress
            and event.key()
            in (Qt.Key.Key_Space, Qt.Key.Key_Return, Qt.Key.Key_Enter)
        ):
            self.scan_select()
            return True
        return super().eventFilter(obj, event)

    def _scan_reset(self):
        self._scan_row = 0
        self._scan_key = None
        self._clear_scan_marks()

    def _clear_scan_marks(self):
        for b in self.findChildren(QPushButton):
            if b.property("scan"):
                b.setProperty("scan", False)
                b.style().unpolish(b)
                b.style().polish(b)

    def _scan_mark(self):
        """Evidenzia la riga corrente, o il singolo tasto corrente."""
        self._clear_scan_marks()
        rows = self._scan_rows()
        if not rows:
            return
        self._scan_row %= len(rows)
        row = rows[self._scan_row]
        targets = row if self._scan_key is None else [row[self._scan_key % len(row)]]
        for b in targets:
            b.setProperty("scan", True)
            b.style().unpolish(b)
            b.style().polish(b)

    def _scan_tick(self):
        rows = self._scan_rows()
        if not rows:
            return
        if self._scan_key is None:
            self._scan_row = (self._scan_row + 1) % len(rows)
        else:
            self._scan_key = (self._scan_key + 1) % len(rows[self._scan_row])
        self._scan_mark()

    def scan_select(self):
        """Il "segnale": sceglie la riga evidenziata, poi il tasto.

        Chiamabile dall'esterno (gesto, soffio, futuro BCI); da tastiera
        fisica corrisponde a SPAZIO o INVIO quando la scansione è attiva.
        """
        if not self.scan_btn.isChecked():
            return
        rows = self._scan_rows()
        if not rows:
            return
        if self._scan_key is None:
            self._scan_key = 0  # entra nella riga: ora cicla i tasti
        else:
            row = rows[self._scan_row % len(rows)]
            row[self._scan_key % len(row)].animateClick()
            self._scan_key = None  # torna a ciclare le righe
        self._scan_timer.start()  # riparte il passo, per non "bruciare" il primo
        self._scan_mark()

    def keyPressEvent(self, event):
        if self.scan_btn.isChecked() and event.key() in (
            Qt.Key.Key_Space,
            Qt.Key.Key_Return,
            Qt.Key.Key_Enter,
        ):
            self.scan_select()
            event.accept()
            return
        super().keyPressEvent(event)
