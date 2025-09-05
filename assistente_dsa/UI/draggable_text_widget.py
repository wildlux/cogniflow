import logging
import pyttsx3
import os
from PyQt6.QtCore import Qt, QMimeData, QTimer
from PyQt6.QtGui import QDrag
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QMessageBox, QInputDialog

# Constants
WIDGET_MIN_HEIGHT = 60
BUTTON_DEFAULT_SIZE = (25, 25)
DEFAULT_FONT_SIZE = 12
DRAG_DISTANCE_THRESHOLD = 10

WIDGET_STYLE_SHEET = """
    QFrame {
        background: rgba(255, 255, 255, 0.7);
        border-radius: 15px;
        margin: 5px;
        color: black;
    }
    QPushButton {
        background-color: rgba(0, 0, 0, 0.2);
        border: 1px solid rgba(0, 0, 0, 0.3);
        border-radius: 12px;
        padding: 5px 10px;
        color: white;
        font-weight: bold;
    }
    QPushButton:hover {
        background-color: rgba(0, 0, 0, 0.3);
    }
    QLabel {
        color: black;
    }
"""


class DraggableTextWidget(QFrame):
    """Widget di testo trascinabile per l'interfaccia."""

    def __init__(self, text, settings, parent=None):
        super().__init__(parent)

        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setFrameShadow(QFrame.Shadow.Raised)
        self.setMinimumHeight(WIDGET_MIN_HEIGHT)
        self.setStyleSheet(WIDGET_STYLE_SHEET)

        self.settings = settings
        self.original_text = text
        self.is_selected = False

        # Text-to-speech engine
        self.tts_engine = None
        self.is_reading = False
        self.is_paused = False

        layout = QHBoxLayout(self)
        self.text_label = QLabel(text)
        self.text_label.setStyleSheet(f"font-weight: bold; font-size: {DEFAULT_FONT_SIZE}px;")
        self.text_label.setWordWrap(True)
        self.text_label.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.text_label.customContextMenuRequested.connect(self.show_context_menu)

        # Installa event filter sul QLabel per intercettare i click
        self.text_label.installEventFilter(self)

        layout.addWidget(self.text_label, 1)

        button_layout = QVBoxLayout()

        # Read button
        self.read_button = QPushButton("📖")
        self.read_button.setFixedSize(*BUTTON_DEFAULT_SIZE)
        self.read_button.setToolTip("Leggi")
        self.read_button.clicked.connect(self.start_reading)

        # Pause button (initially hidden)
        self.pause_button = QPushButton("⏸️")
        self.pause_button.setFixedSize(*BUTTON_DEFAULT_SIZE)
        self.pause_button.setToolTip("Pausa")
        self.pause_button.clicked.connect(self.pause_reading)
        self.pause_button.hide()

        # Stop button (initially hidden)
        self.stop_button = QPushButton("⏹️")
        self.stop_button.setFixedSize(*BUTTON_DEFAULT_SIZE)
        self.stop_button.setToolTip("Ferma")
        self.stop_button.clicked.connect(self.stop_reading)
        self.stop_button.hide()

        self.edit_button = QPushButton("✏️")
        self.edit_button.setFixedSize(*BUTTON_DEFAULT_SIZE)
        self.edit_button.setToolTip("Modifica")
        self.edit_button.clicked.connect(self.edit_text)

        self.delete_button = QPushButton("❌")
        self.delete_button.setFixedSize(*BUTTON_DEFAULT_SIZE)
        self.delete_button.setToolTip("Elimina")
        self.delete_button.clicked.connect(self.delete_self)

        button_layout.addWidget(self.read_button)
        button_layout.addWidget(self.pause_button)
        button_layout.addWidget(self.stop_button)
        button_layout.addWidget(self.edit_button)
        button_layout.addWidget(self.delete_button)
        layout.addLayout(button_layout)

        self.setAcceptDrops(True)
        self.start_pos = None

    def show_context_menu(self, pos):
        """Mostra il menu contestuale per il widget."""
        from PyQt6.QtWidgets import QMenu

        context_menu = QMenu(self)
        edit_action = context_menu.addAction("Modifica Testo")
        action = context_menu.exec(self.mapToGlobal(pos))
        if action == edit_action:
            self.edit_text()

    def mouseReleaseEvent(self, a0):
        """Gestisce il rilascio del mouse per click singolo."""
        if a0 and a0.button() == Qt.MouseButton.LeftButton:
            # Controlla se il click è avvenuto sul QLabel
            label_rect = self.text_label.geometry()
            click_pos = a0.pos()

            if label_rect.contains(click_pos):
                self.toggle_selection()
                self.show_metadata_in_details()

            # Reset start_pos
            self.start_pos = None
        super().mouseReleaseEvent(a0)

    def mouseDoubleClickEvent(self, a0):
        """Gestisce il doppio click per modificare il testo."""
        self.edit_text()

    def edit_text(self):
        """Apre una finestra di dialogo per modificare il testo del widget."""
        new_text, ok = QInputDialog.getMultiLineText(
            self, "Modifica Testo", "Modifica il contenuto del widget:",
            self.text_label.text()
        )
        if ok and new_text.strip():
            self.text_label.setText(new_text.strip())
            logging.info(f"Testo del widget modificato: {new_text[:50]}...")

    def mousePressEvent(self, a0):
        """Gestisce l'evento di pressione del mouse per iniziare il trascinamento."""
        if a0 and a0.button() == Qt.MouseButton.LeftButton:
            self.start_pos = a0.pos()
        super().mousePressEvent(a0)

    def mouseMoveEvent(self, a0):
        """Gestisce il movimento del mouse per il trascinamento."""
        if (self.start_pos is not None and self.text_label and a0 is not None and
                a0.buttons() == Qt.MouseButton.LeftButton):
            current_pos = a0.pos()
            if current_pos.x() >= 0 and current_pos.y() >= 0:
                distance = (current_pos - self.start_pos).manhattanLength()
                if distance > DRAG_DISTANCE_THRESHOLD:
                    # Annulla eventuali timer di click se attivi
                    if hasattr(self, '_click_timer') and self._click_timer.isActive():
                        self._click_timer.stop()

                    drag = QDrag(self)
                    mime = QMimeData()
                    mime.setText(self.text_label.text())
                    mime.setData("application/x-draggable-widget", b"widget")
                    drag.setMimeData(mime)
                    drag.setPixmap(self.grab())
                    result = drag.exec(Qt.DropAction.MoveAction)
                    if result == Qt.DropAction.MoveAction:
                        # Non eliminare mai il widget originale - lascia sempre una copia
                        # Il widget originale rimane al suo posto, viene solo creato un nuovo widget nella destinazione
                        pass
        super().mouseMoveEvent(a0)

    def delete_self(self):
        """Rimuove il widget dall'interfaccia."""
        self.stop_reading()  # Stop any ongoing reading
        self.setParent(None)
        self.deleteLater()

    def start_reading(self):
        """Avvia la lettura del testo."""
        if self.is_reading:
            return

        try:
            if self.tts_engine is None:
                self.tts_engine = pyttsx3.init()

            self.is_reading = True
            self.is_paused = False

            # Hide read button, show pause and stop buttons
            self.read_button.hide()
            self.pause_button.show()
            self.stop_button.show()

            # Start reading
            text_to_read = self.text_label.text()
            self.tts_engine.say(text_to_read)
            self.tts_engine.runAndWait()

            # Reset when finished
            self.reset_reading_buttons()

        except Exception as e:
            QMessageBox.warning(self, "Errore Lettura", f"Errore durante la lettura: {str(e)}")
            self.reset_reading_buttons()

    def pause_reading(self):
        """Mette in pausa o riprende la lettura."""
        if self.tts_engine is None:
            return

        if self.is_paused:
            # Resume reading
            self.tts_engine.runAndWait()
            self.pause_button.setText("⏸️")
            self.pause_button.setToolTip("Pausa")
            self.is_paused = False
        else:
            # Pause reading
            self.tts_engine.stop()
            self.pause_button.setText("▶️")
            self.pause_button.setToolTip("Riprendi")
            self.is_paused = True

    def stop_reading(self):
        """Ferma la lettura e ricomincia dall'inizio."""
        if self.tts_engine:
            self.tts_engine.stop()
        self.reset_reading_buttons()

    def reset_reading_buttons(self):
        """Resetta i pulsanti di lettura allo stato iniziale."""
        self.is_reading = False
        self.is_paused = False

        self.read_button.show()
        self.pause_button.hide()
        self.stop_button.hide()

        self.pause_button.setText("⏸️")
        self.pause_button.setToolTip("Pausa")

    def toggle_selection(self):
        """Alterna lo stato di selezione del widget."""
        # Deseleziona tutti gli altri pensierini prima
        self._deselect_others()

        # Alterna la selezione di questo widget
        self.is_selected = not self.is_selected
        self.update_selection_style()

    def _deselect_others(self):
        """Deseleziona tutti gli altri pensierini."""
        # Trova il layout dei pensierini
        pensierini_layout = self._find_pensierini_layout()
        if pensierini_layout:
            for i in range(pensierini_layout.count()):
                item = pensierini_layout.itemAt(i)
                if item:
                    widget = item.widget()
                    if widget and widget != self and hasattr(widget, 'is_selected'):
                        widget.is_selected = False
                        widget.update_selection_style()

    def _find_pensierini_layout(self):
        """Trova il layout dei pensierini risalendo la gerarchia."""
        current = self.parent()
        while current is not None:
            # Controlla se è un layout che contiene pensierini
            if hasattr(current, 'count') and hasattr(current, 'itemAt'):
                # Verifica se contiene DraggableTextWidget
                for i in range(current.count()):
                    item = current.itemAt(i)
                    if item and hasattr(item.widget(), 'text_label'):
                        return current
            current = current.parent()
        return None

    def update_selection_style(self):
        """Aggiorna lo stile del widget in base allo stato di selezione."""
        base_style = WIDGET_STYLE_SHEET

        if self.is_selected:
            # Stile per widget selezionato - MOLTO EVIDENTE
            selected_style = """
                QFrame {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 rgba(0, 123, 255, 0.3), stop:1 rgba(0, 123, 255, 0.15));
                    border-radius: 18px;
                    margin: 3px;
                    color: black;
                    border: 6px solid #007bff;
                    box-shadow: 0 0 40px rgba(0, 123, 255, 1.0),
                               0 0 80px rgba(0, 123, 255, 0.8),
                               inset 0 0 20px rgba(0, 123, 255, 0.4);
                    transform: scale(1.02);
                }
                QPushButton {
                    background-color: rgba(0, 123, 255, 0.6);
                    border: 3px solid rgba(0, 123, 255, 0.8);
                    border-radius: 15px;
                    padding: 8px 16px;
                    color: white;
                    font-weight: bold;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background-color: rgba(0, 123, 255, 0.7);
                    border-color: rgba(0, 123, 255, 1.0);
                    box-shadow: 0 0 15px rgba(0, 123, 255, 0.8);
                }
                QLabel {
                    color: #0056b3;
                    font-weight: bold;
                    font-size: 14px;
                    text-shadow: 0 0 8px rgba(0, 123, 255, 0.6);
                }
            """
            self.setStyleSheet(selected_style)

            # Modifica il testo per indicare selezione attiva con icona più prominente
            original_text = self.original_text
            if not original_text.startswith("⭐ "):
                self.text_label.setText(f"⭐ {original_text}")
        else:
            # Stile normale
            self.setStyleSheet(base_style)

            # Ripristina il testo originale
            original_text = self.original_text
            if original_text.startswith("⭐ "):
                self.text_label.setText(original_text[2:])  # Rimuovi "⭐ "
            else:
                self.text_label.setText(original_text)

    def show_metadata_in_details(self):
        """Analizza il contenuto del widget e mostra i metadati nei dettagli."""
        text = self.text_label.text().strip()

        # Trova la finestra principale per accedere alla funzione show_text_in_details
        main_window = self._find_main_window()
        if not main_window:
            return

        # Analizza il contenuto
        metadata = self._analyze_content(text)

        # Mostra i metadati nei dettagli
        main_window.show_text_in_details(metadata)

    def _find_main_window(self):
        """Trova la finestra principale risalendo la gerarchia dei widget."""
        current = self.parent()
        depth = 0
        while current is not None and depth < 10:  # Limite per evitare loop infiniti
            if hasattr(current, 'show_text_in_details') and callable(getattr(current, 'show_text_in_details', None)):
                return current
            current = current.parent()
            depth += 1
        return None

    def _analyze_content(self, text):
        """Analizza il contenuto e restituisce i metadati appropriati."""
        if not text:
            return "📝 Contenuto vuoto"

        # Controlla se è un percorso file
        if os.path.exists(text) or (len(text.split()) == 1 and '.' in text):
            return self._analyze_file(text)

        # Controlla se è una singola parola
        words = text.split()
        if len(words) == 1:
            return self._analyze_single_word(text)

        # Analizza come frase completa
        return self._analyze_sentence(text)

    def _analyze_file(self, file_path):
        """Analizza un file e restituisce le informazioni."""
        metadata = f"📁 Analisi File\n\n"
        metadata += f"📂 Percorso: {file_path}\n"

        if os.path.exists(file_path):
            try:
                stat = os.stat(file_path)
                metadata += f"📏 Dimensione: {stat.st_size} bytes\n"
                metadata += f"📅 Modificato: {stat.st_mtime}\n"

                if os.path.isfile(file_path):
                    metadata += f"📄 Tipo: File\n"
                    # Estensione
                    _, ext = os.path.splitext(file_path)
                    if ext:
                        metadata += f"🏷️ Estensione: {ext}\n"
                else:
                    metadata += f"📁 Tipo: Directory\n"
            except Exception as e:
                metadata += f"❌ Errore nell'analisi: {str(e)}\n"
        else:
            metadata += f"❌ File non trovato\n"

        return metadata

    def _analyze_single_word(self, word):
        """Analizza una singola parola e restituisce analisi grammaticale."""
        metadata = f"🔤 Analisi Grammaticale: {word}\n\n"

        # Analisi grammaticale di base
        if word.endswith(('are', 'ere', 'ire')):
            metadata += self._analyze_verb(word)
        elif word.endswith(('a', 'e', 'i', 'o', 'u')):
            metadata += self._analyze_noun(word)
        else:
            metadata += f"❓ Tipo di parola non identificato\n"

        # Etimologia di base (molto semplificata)
        metadata += f"\n📚 Etimologia:\n"
        metadata += self._get_basic_etymology(word)

        return metadata

    def _analyze_verb(self, verb):
        """Analizza un verbo e mostra le coniugazioni."""
        metadata = f"🏃 Tipo: Verbo\n"

        # Identifica la coniugazione
        if verb.endswith('are'):
            conjugation = "1ª coniugazione (-are)"
            stem = verb[:-3]
        elif verb.endswith('ere'):
            conjugation = "2ª coniugazione (-ere)"
            stem = verb[:-3]
        elif verb.endswith('ire'):
            conjugation = "3ª coniugazione (-ire)"
            stem = verb[:-3]
        else:
            return "❓ Verbo non riconosciuto\n"

        metadata += f"📊 Coniugazione: {conjugation}\n"
        metadata += f"🔍 Radice: {stem}\n\n"

        # Mostra coniugazioni principali (semplificate)
        metadata += f"📝 Coniugazioni principali:\n"
        metadata += f"• Presente: {stem}o, {stem}i, {stem}a...\n"
        metadata += f"• Imperfetto: {stem}avo, {stem}avi, {stem}ava...\n"
        metadata += f"• Futuro: {stem}erò, {stem}erai, {stem}erà...\n"
        metadata += f"• Passato remoto: {stem}ai, {stem}asti, {stem}ò...\n"
        metadata += f"• Congiuntivo: che {stem}i, che {stem}i, che {stem}i...\n"

        return metadata

    def _analyze_noun(self, noun):
        """Analizza un nome e mostra le declinazioni."""
        metadata = f"🏷️ Tipo: Nome\n"

        # Identifica genere (molto semplificato)
        if noun.endswith(('a', 'e')):
            gender = "Femminile"
        elif noun.endswith(('o', 'e')):
            gender = "Maschile"
        else:
            gender = "Genere non identificato"

        metadata += f"⚧ Genere: {gender}\n"

        # Numero
        if noun.endswith('i') or noun.endswith('e'):
            number = "Plurale"
        else:
            number = "Singolare"

        metadata += f"🔢 Numero: {number}\n\n"

        # Declinazioni (semplificate per italiano)
        metadata += f"📝 Declinazioni:\n"
        if gender == "Maschile":
            if number == "Singolare":
                metadata += f"• Nominativo: {noun}\n"
                metadata += f"• Genitivo: del {noun}\n"
                metadata += f"• Dativo: al {noun}\n"
                metadata += f"• Accusativo: il {noun}\n"
            else:
                metadata += f"• Nominativo: {noun}\n"
                metadata += f"• Genitivo: dei {noun}\n"
                metadata += f"• Dativo: ai {noun}\n"
                metadata += f"• Accusativo: i {noun}\n"
        else:
            if number == "Singolare":
                metadata += f"• Nominativo: {noun}\n"
                metadata += f"• Genitivo: della {noun}\n"
                metadata += f"• Dativo: alla {noun}\n"
                metadata += f"• Accusativo: la {noun}\n"
            else:
                metadata += f"• Nominativo: {noun}\n"
                metadata += f"• Genitivo: delle {noun}\n"
                metadata += f"• Dativo: alle {noun}\n"
                metadata += f"• Accusativo: le {noun}\n"

        return metadata

    def _analyze_sentence(self, text):
        """Analizza una frase completa con analisi logica e grammaticale."""
        words = text.split()
        metadata = f"📝 Analisi Frase Completa\n\n"
        metadata += f"📊 Numero parole: {len(words)}\n"
        metadata += f"📏 Lunghezza totale: {len(text)} caratteri\n\n"

        # Analisi logica della frase
        metadata += f"🧠 Analisi Logica:\n"
        logical_analysis = self._analyze_logical_structure(text, words)
        metadata += logical_analysis + "\n"

        # Analisi grammaticale delle singole parole
        metadata += f"🔤 Analisi Grammaticale delle Parole:\n"
        for i, word in enumerate(words, 1):
            clean_word = word.strip('.,!?;:"').lower()
            if clean_word:
                metadata += f"{i}. {word}\n"
                word_analysis = self._analyze_word_in_context(clean_word, i, words)
                if word_analysis:
                    metadata += f"   {word_analysis}\n"

        return metadata

    def _analyze_logical_structure(self, text, words):
        """Analizza la struttura logica della frase."""
        analysis = ""

        # Identifica il verbo (semplificato)
        verbs = []
        subjects = []
        objects = []

        for i, word in enumerate(words):
            clean_word = word.strip('.,!?;:"').lower()
            if clean_word.endswith(('are', 'ere', 'ire', 'are', 'ere', 'ire')):
                verbs.append((clean_word, i))
            elif i == 0 or (i > 0 and words[i-1].lower() in ['il', 'lo', 'la', 'i', 'gli', 'le', 'un', 'una', 'uno']):
                subjects.append((clean_word, i))

        # Struttura base
        if verbs:
            analysis += f"🏃 Verbo principale: {verbs[0][0]}\n"
        if subjects:
            analysis += f"👤 Soggetto: {subjects[0][0]}\n"

        # Tipo di frase
        if text.endswith('?'):
            analysis += f"❓ Tipo: Frase interrogativa\n"
        elif text.endswith('!'):
            analysis += f"⚡ Tipo: Frase esclamativa\n"
        else:
            analysis += f"📝 Tipo: Frase dichiarativa\n"

        # Complessi
        if len(words) > 3:
            analysis += f"📋 Struttura: Frase complessa\n"
        else:
            analysis += f"📄 Struttura: Frase semplice\n"

        return analysis

    def _analyze_word_in_context(self, word, position, all_words):
        """Analizza una parola nel contesto della frase."""
        analysis = ""

        # Determina la funzione grammaticale
        if position == 0:
            analysis += "Funzione: Soggetto"
        elif word in ['il', 'lo', 'la', 'i', 'gli', 'le', 'un', 'una', 'uno', 'del', 'della', 'dei', 'delle']:
            analysis += "Funzione: Articolo determinativo"
        elif word in ['di', 'a', 'da', 'in', 'con', 'su', 'per', 'tra', 'fra']:
            analysis += "Funzione: Preposizione"
        elif word in ['e', 'o', 'ma', 'però', 'quindi', 'allora']:
            analysis += "Funzione: Congiunzione"
        elif word.endswith(('are', 'ere', 'ire')):
            analysis += "Funzione: Verbo"
        elif word.endswith(('a', 'e', 'i', 'o', 'u')) and len(word) > 2:
            analysis += "Funzione: Nome/Sostantivo"
        else:
            analysis += "Funzione: Aggettivo/Avverbio/Altro"

        # Analisi morfologica di base
        if word.endswith(('are', 'ere', 'ire')):
            analysis += " | Tipo: Verbo"
            if word.endswith('are'):
                analysis += " | Coniugazione: 1ª (-are)"
            elif word.endswith('ere'):
                analysis += " | Coniugazione: 2ª (-ere)"
            elif word.endswith('ire'):
                analysis += " | Coniugazione: 3ª (-ire)"
        elif word.endswith(('a', 'e', 'i', 'o')):
            if word.endswith('a') or word.endswith('e'):
                analysis += " | Genere: Femminile"
            else:
                analysis += " | Genere: Maschile"

            if word.endswith(('i', 'e')):
                analysis += " | Numero: Plurale"
            else:
                analysis += " | Numero: Singolare"

        return analysis

    def _get_basic_etymology(self, word):
        """Restituisce etimologia di base semplificata."""
        etymologies = {
            "volare": "Dal latino 'volare' = volare, derivato da 'volo' = volo",
            "mangiare": "Dal latino 'manducare' = masticare, mangiare",
            "correre": "Dal latino 'currere' = correre",
            "dormire": "Dal latino 'dormire' = dormire",
            "casa": "Dal latino 'casa' = capanna, abitazione",
            "libro": "Dal latino 'liber' = libro, corteccia",
            "acqua": "Dal latino 'aqua' = acqua",
            "fuoco": "Dal latino 'focus' = focolare",
        }

        return etymologies.get(word.lower(), f"📖 Etimologia non disponibile per '{word}'\nOrigine: Probabilmente dal latino o da altre lingue indoeuropee")

    def eventFilter(self, obj, event):
        """Intercetta gli eventi del QLabel per gestire i click."""
        if obj == self.text_label:
            if event.type() == event.Type.MouseButtonPress and event.button() == Qt.MouseButton.LeftButton:
                self._label_click_start = event.pos()
                return False  # Non consumare l'evento

            elif event.type() == event.Type.MouseButtonRelease and event.button() == Qt.MouseButton.LeftButton:
                if hasattr(self, '_label_click_start'):
                    # Verifica se è stato un click breve (non un drag)
                    start_pos = self._label_click_start
                    end_pos = event.pos()
                    distance = (end_pos - start_pos).manhattanLength()

                    if distance < DRAG_DISTANCE_THRESHOLD:
                        self.toggle_selection()
                        self.show_metadata_in_details()

                    delattr(self, '_label_click_start')
                return False  # Non consumare l'evento

        return super().eventFilter(obj, event)
