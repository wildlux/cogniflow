#!/usr/bin/env python3
"""
Settings Dialog - Dialog delle impostazioni per DSA Assistant
Interfaccia grafica completa per modificare tutte le configurazioni
"""

import sys
import subprocess
import sys
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QCheckBox,
    QGroupBox, QTabWidget, QWidget, QMessageBox, QScrollArea
)

# Import del sistema di configurazione globale
from main_03_configurazione_e_opzioni import (
    load_settings, save_settings, get_setting, set_setting
)

class SettingsDialog(QDialog):
    """Dialog completo per le impostazioni dell'applicazione DSA."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings = load_settings()

        self.setWindowTitle("Impostazioni DSA Assistant")
        self.setModal(True)
        self.resize(900, 700)

        # Applica stile al dialog
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #f8f9fa, stop:1 #e9ecef);
            }

            QGroupBox {
                font-weight: bold;
                border: 2px solid #4a90e2;
                border-radius: 8px;
                margin-top: 6px;
                padding-top: 10px;
                background: rgba(255, 255, 255, 0.9);
            }

            QGroupBox::title {
                color: #2c3e50;
                padding: 0 10px;
            }

            QLabel {
                color: #2c3e50;
                font-weight: bold;
            }

            QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {
                border: 2px solid #4a90e2;
                border-radius: 5px;
                padding: 5px;
                background: white;
            }

            QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {
                border-color: #357abd;
                background: #f8f9fa;
            }

            QPushButton {
                background-color: #4a90e2;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 16px;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: #357abd;
            }

            QTabWidget::pane {
                border: 1px solid #4a90e2;
                background: rgba(255, 255, 255, 0.9);
            }

            QTabBar::tab {
                background: #6c757d;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 5px 5px 0 0;
            }

            QTabBar::tab:selected {
                background: #4a90e2;
            }
        """)

        self.setup_ui()
        self.load_current_settings()

    def setup_ui(self):
        """Configura l'interfaccia utente del dialog."""
        layout = QVBoxLayout(self)

        # Titolo
        title_label = QLabel("Impostazioni DSA Assistant")
        title_label.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 10px;
        """)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # Tab widget per organizzare le impostazioni
        self.tab_widget = QTabWidget()

        # Crea i vari tab
        self.setup_general_tab()
        self.setup_ui_tab()
        self.setup_ai_tab()
        self.setup_test_tab()
        self.setup_personalize_tab()

        layout.addWidget(self.tab_widget)

        # Pulsanti di controllo
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        save_button = QPushButton("Salva Impostazioni")
        save_button.clicked.connect(self.save_settings)
        buttons_layout.addWidget(save_button)

        cancel_button = QPushButton("Annulla")
        cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_button)

        layout.addLayout(buttons_layout)

    def setup_general_tab(self):
        """Configura il tab generale."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Gruppo applicazione
        app_group = QGroupBox("Applicazione")
        app_layout = QVBoxLayout(app_group)

        # Nome applicazione
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Nome applicazione:"))
        self.app_name_edit = QLineEdit()
        name_layout.addWidget(self.app_name_edit)
        app_layout.addLayout(name_layout)

        # Tema
        theme_layout = QHBoxLayout()
        theme_layout.addWidget(QLabel("Tema:"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Chiaro", "Scuro", "Automatico"])
        theme_layout.addWidget(self.theme_combo)
        app_layout.addLayout(theme_layout)

        layout.addWidget(app_group)
        layout.addStretch()

        self.tab_widget.addTab(widget, "Generale")

    def setup_ui_tab(self):
        """Configura il tab interfaccia utente."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Gruppo dimensioni finestra
        size_group = QGroupBox("Dimensioni Finestra")
        size_layout = QVBoxLayout(size_group)

        # Larghezza finestra
        width_layout = QHBoxLayout()
        width_layout.addWidget(QLabel("Larghezza finestra:"))
        self.window_width_spin = QSpinBox()
        self.window_width_spin.setRange(800, 3000)
        width_layout.addWidget(self.window_width_spin)
        width_layout.addWidget(QLabel("px"))
        size_layout.addLayout(width_layout)

        # Altezza finestra
        height_layout = QHBoxLayout()
        height_layout.addWidget(QLabel("Altezza finestra:"))
        self.window_height_spin = QSpinBox()
        self.window_height_spin.setRange(600, 2000)
        height_layout.addWidget(self.window_height_spin)
        height_layout.addWidget(QLabel("px"))
        size_layout.addLayout(height_layout)

        layout.addWidget(size_group)
        layout.addStretch()

        self.tab_widget.addTab(widget, "Interfaccia")

    def setup_ai_tab(self):
        """Configura il tab intelligenza artificiale."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Gruppo configurazione AI
        ai_group = QGroupBox("Intelligenza Artificiale")
        ai_layout = QVBoxLayout(ai_group)

        # Trigger AI
        trigger_layout = QHBoxLayout()
        trigger_layout.addWidget(QLabel("Trigger per AI:"))
        self.ai_trigger_edit = QLineEdit()
        trigger_layout.addWidget(self.ai_trigger_edit)
        ai_layout.addLayout(trigger_layout)

        # Modello AI selezionato
        model_layout = QHBoxLayout()
        model_layout.addWidget(QLabel("Modello AI selezionato:"))
        self.ai_model_combo = QComboBox()
        self.ai_model_combo.addItems([
            "gemma:2b", "llama2:7b", "llama2:13b", "codellama:7b"
        ])
        model_layout.addWidget(self.ai_model_combo)
        ai_layout.addLayout(model_layout)

        layout.addWidget(ai_group)
        layout.addStretch()

        self.tab_widget.addTab(widget, "AI")

    def setup_test_tab(self):
        """Configura il tab di test per scopi di sviluppo."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Gruppo test input
        test_input_group = QGroupBox("Input di Test")
        test_input_layout = QVBoxLayout(test_input_group)

        # Campo di testo
        text_layout = QHBoxLayout()
        text_layout.addWidget(QLabel("Testo di prova:"))
        self.test_text_edit = QLineEdit()
        self.test_text_edit.setPlaceholderText("Inserisci testo di test...")
        text_layout.addWidget(self.test_text_edit)
        test_input_layout.addLayout(text_layout)

        # Campo numerico
        number_layout = QHBoxLayout()
        number_layout.addWidget(QLabel("Numero di test:"))
        self.test_number_spin = QSpinBox()
        self.test_number_spin.setRange(0, 1000)
        self.test_number_spin.setValue(42)
        number_layout.addWidget(self.test_number_spin)
        test_input_layout.addLayout(number_layout)

        layout.addWidget(test_input_group)

        # Gruppo test opzioni
        test_options_group = QGroupBox("Opzioni di Test")
        test_options_layout = QVBoxLayout(test_options_group)

        # Combo box
        combo_layout = QHBoxLayout()
        combo_layout.addWidget(QLabel("Opzione test:"))
        self.test_combo = QComboBox()
        self.test_combo.addItems(["Opzione 1", "Opzione 2", "Opzione 3", "Debug", "Release"])
        combo_layout.addWidget(self.test_combo)
        test_options_layout.addLayout(combo_layout)

        # Checkbox
        self.test_checkbox = QCheckBox("Abilita modalità test")
        self.test_checkbox.setChecked(True)
        test_options_layout.addWidget(self.test_checkbox)

        layout.addWidget(test_options_group)

        # Gruppo azioni test
        test_actions_group = QGroupBox("Azioni di Test")
        test_actions_layout = QVBoxLayout(test_actions_group)

        # Pulsante di test
        test_button = QPushButton("Esegui Test")
        test_button.clicked.connect(lambda: QMessageBox.information(self, "Test", "Test eseguito con successo!"))
        test_actions_layout.addWidget(test_button)

        # Label informativo
        info_label = QLabel("Questa è una scheda di test per scopi di sviluppo.\nPuoi aggiungere qui nuovi widget e funzionalità.")
        info_label.setStyleSheet("color: #666; font-style: italic;")
        test_actions_layout.addWidget(info_label)

        layout.addWidget(test_actions_group)
        layout.addStretch()

        self.tab_widget.addTab(widget, "Test")

    def setup_personalize_tab(self):
        """Configura il tab per personalizzare l'aspetto dell'interfaccia."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Scroll area per contenere tutti i controlli
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)

        # === SEZIONE FONT ===
        font_group = QGroupBox("🎨 Personalizzazione Font")
        font_group.setStyleSheet("QGroupBox { font-weight: bold; }")
        font_layout = QVBoxLayout(font_group)

        # Font family
        font_family_layout = QHBoxLayout()
        font_family_layout.addWidget(QLabel("Tipo di font:"))
        self.font_family_combo = QComboBox()

        # Carica tutti i font disponibili dalla libreria dei font installati nel sistema operativo
        system_fonts = []
        try:
            # Su Linux, usa fc-list per ottenere tutti i font disponibili
            if sys.platform.startswith('linux'):
                result = subprocess.run(['fc-list', ':family'], capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    raw_output = result.stdout.strip()
                    if raw_output:
                        # Parsing delle righe di output fc-list
                        font_lines = raw_output.split('\n')
                        for line in font_lines:
                            if line.strip() and ':' in line:
                                # Formato: /path/to/font.ttf: Font Name, Font Name 2
                                # Prendi solo la parte dopo i due punti
                                font_part = line.split(':', 1)[1].strip()
                                if font_part:
                                    # Ogni riga può contenere più font separati da virgola
                                    fonts_in_line = [f.strip() for f in font_part.split(',') if f.strip()]
                                    system_fonts.extend(fonts_in_line)

                        # Rimuovi duplicati e ordina alfabeticamente
                        system_fonts = list(set(system_fonts))
                        system_fonts.sort()

                        # Assicurati che OpenDyslexic sia nella lista (font per dislessia)
                        if "OpenDyslexic" not in system_fonts:
                            system_fonts.insert(0, "OpenDyslexic")  # Inserisci all'inizio

                        print(f"✅ Caricati {len(system_fonts)} font dal sistema Linux (solo nomi)")
                        print(f"🎨 Font per dislessia disponibile: {'OpenDyslexic' in system_fonts}")
                    else:
                        raise Exception("Nessun output da fc-list")
                else:
                    raise Exception(f"fc-list fallito con codice {result.returncode}")
            else:
                raise Exception("Sistema operativo non supportato per caricamento dinamico")

        except Exception as e:
            print(f"⚠️ Errore caricamento font di sistema: {e}")
            # Fallback alla lista di font comuni (incluso OpenDyslexic per dislessia)
            system_fonts = [
                "OpenDyslexic",  # Font per dislessia - PRIMA POSIZIONE
                "Arial", "Helvetica", "Times New Roman", "Courier New",
                "Verdana", "Georgia", "Palatino", "Garamond", "Bookman",
                "Comic Sans MS", "Trebuchet MS", "Arial Black", "Calibri",
                "Cambria", "Candara", "Consolas", "Constantia", "Corbel",
                "DejaVu Sans", "DejaVu Serif", "FreeMono", "FreeSans", "FreeSerif",
                "Liberation Mono", "Liberation Sans", "Liberation Serif",
                "Lucida Console", "Lucida Sans", "Lucida Sans Unicode",
                "Microsoft Sans Serif", "Monaco", "Segoe UI", "Tahoma", "Ubuntu"
            ]
        self.font_family_combo.addItems(system_fonts)

        # Imposta il font corrente dalle impostazioni o usa Arial come default
        current_font = get_setting('main_font_family', 'Arial')
        if current_font in system_fonts:
            self.font_family_combo.setCurrentText(current_font)
        else:
            # Se il font corrente non è disponibile, usa il primo disponibile
            if system_fonts:
                self.font_family_combo.setCurrentText(system_fonts[0])

        font_family_layout.addWidget(self.font_family_combo)
        font_layout.addLayout(font_family_layout)

        # Font size
        font_size_layout = QHBoxLayout()
        font_size_layout.addWidget(QLabel("Dimensione font:"))
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 24)
        # Carica la dimensione font dalle impostazioni esistenti
        current_font_size = get_setting('main_font_size', 14)
        self.font_size_spin.setValue(current_font_size)
        self.font_size_spin.setSuffix(" pt")
        font_size_layout.addWidget(self.font_size_spin)
        font_layout.addLayout(font_size_layout)

        # Font weight
        font_weight_layout = QHBoxLayout()
        font_weight_layout.addWidget(QLabel("Spessore font:"))
        self.font_weight_combo = QComboBox()
        self.font_weight_combo.addItems(["Normale", "Grassetto", "Corsivo", "Grassetto Corsivo"])
        # Carica il peso font dalle impostazioni esistenti
        current_font_weight = get_setting('main_font_weight', 'Normale')
        self.font_weight_combo.setCurrentText(current_font_weight)
        font_weight_layout.addWidget(self.font_weight_combo)
        font_layout.addLayout(font_weight_layout)

        scroll_layout.addWidget(font_group)

        # === SEZIONE COLORI TESTO ===
        text_color_group = QGroupBox("📝 Colori del Testo")
        text_color_group.setStyleSheet("QGroupBox { font-weight: bold; }")
        text_color_layout = QVBoxLayout(text_color_group)

        # Colori per categorie di testo
        text_categories = [
            ("Testo normale", "#333333"),
            ("Titoli e intestazioni", "#2c3e50"),
            ("Testo evidenziato", "#007bff"),
            ("Testo di errore", "#dc3545"),
            ("Testo di successo", "#28a745"),
            ("Testo di avviso", "#ffc107")
        ]

        self.text_color_buttons = {}
        for category, default_color in text_categories:
            color_layout = QHBoxLayout()
            color_layout.addWidget(QLabel(f"{category}:"))

            color_button = QPushButton()
            color_button.setFixedSize(60, 30)
            color_button.setStyleSheet(f"background-color: {default_color}; border: 1px solid #ccc;")
            color_button.clicked.connect(lambda checked, cat=category, btn=color_button: self.choose_color(cat, btn))
            color_layout.addWidget(color_button)

            # Label per mostrare il codice colore
            color_label = QLabel(default_color)
            color_label.setFixedWidth(80)
            color_layout.addWidget(color_label)

            color_layout.addStretch()
            text_color_layout.addLayout(color_layout)

            self.text_color_buttons[category] = (color_button, color_label)

        scroll_layout.addWidget(text_color_group)

        # === SEZIONE SFONDI PULSANTI ===
        button_bg_group = QGroupBox("🔘 Sfondi dei Pulsanti")
        button_bg_group.setStyleSheet("QGroupBox { font-weight: bold; }")
        button_bg_layout = QVBoxLayout(button_bg_group)

        # Sfondi per categorie di pulsanti
        button_categories = [
            ("Pulsanti principali", "#4a90e2", "#357abd"),
            ("Pulsanti secondari", "#6c757d", "#5a6268"),
            ("Pulsanti di successo", "#28a745", "#218838"),
            ("Pulsanti di pericolo", "#dc3545", "#c82333"),
            ("Pulsanti di avviso", "#ffc107", "#e0a800"),
            ("Pulsanti speciali", "#6f42c1", "#5a359a")
        ]

        self.button_bg_buttons = {}
        for category, default_bg, default_hover in button_categories:
            bg_layout = QHBoxLayout()
            bg_layout.addWidget(QLabel(f"{category}:"))

            # Pulsante per colore di sfondo normale
            bg_button = QPushButton("Sfondo")
            bg_button.setFixedSize(80, 30)
            bg_button.setStyleSheet(f"background-color: {default_bg}; color: white; border: none; border-radius: 4px;")
            bg_button.clicked.connect(lambda checked, cat=category, btn=bg_button, typ="bg": self.choose_button_color(cat, btn, typ))
            bg_layout.addWidget(bg_button)

            # Pulsante per colore hover
            hover_button = QPushButton("Hover")
            hover_button.setFixedSize(80, 30)
            hover_button.setStyleSheet(f"background-color: {default_hover}; color: white; border: none; border-radius: 4px;")
            hover_button.clicked.connect(lambda checked, cat=category, btn=hover_button, typ="hover": self.choose_button_color(cat, btn, typ))
            bg_layout.addWidget(hover_button)

            bg_layout.addStretch()
            button_bg_layout.addLayout(bg_layout)

            self.button_bg_buttons[category] = (bg_button, hover_button)

        scroll_layout.addWidget(button_bg_group)

        # === SEZIONE ANTEPRIMA ===
        preview_group = QGroupBox("👁️ Anteprima delle Modifiche")
        preview_group.setStyleSheet("QGroupBox { font-weight: bold; }")
        preview_layout = QVBoxLayout(preview_group)

        # Testo di anteprima
        self.preview_label = QLabel("Questo è un testo di anteprima per vedere come appariranno le tue personalizzazioni.")
        self.preview_label.setWordWrap(True)
        self.preview_label.setStyleSheet("padding: 10px; border: 1px solid #ddd; border-radius: 4px;")
        preview_layout.addWidget(self.preview_label)

        # Pulsanti di anteprima
        preview_buttons_layout = QHBoxLayout()
        self.preview_button1 = QPushButton("Pulsante Principale")
        self.preview_button2 = QPushButton("Pulsante Secondario")
        self.preview_button3 = QPushButton("Pulsante Speciale")

        preview_buttons_layout.addWidget(self.preview_button1)
        preview_buttons_layout.addWidget(self.preview_button2)
        preview_buttons_layout.addWidget(self.preview_button3)
        preview_buttons_layout.addStretch()

        preview_layout.addLayout(preview_buttons_layout)

        # Pulsante per applicare anteprima
        apply_preview_button = QPushButton("🔄 Aggiorna Anteprima")
        apply_preview_button.clicked.connect(self.update_preview)
        preview_layout.addWidget(apply_preview_button)

        scroll_layout.addWidget(preview_group)

        # === PULSANTI AZIONI ===
        actions_layout = QHBoxLayout()

        # Pulsante per applicare le modifiche
        apply_button = QPushButton("✅ Applica Modifiche")
        apply_button.setStyleSheet("QPushButton { background-color: #28a745; color: white; font-weight: bold; padding: 10px; }")
        apply_button.clicked.connect(self.apply_personalizations)
        actions_layout.addWidget(apply_button)

        # Pulsante per ripristinare i valori predefiniti
        reset_button = QPushButton("🔄 Ripristina Predefiniti")
        reset_button.setStyleSheet("QPushButton { background-color: #ffc107; color: black; font-weight: bold; padding: 10px; }")
        reset_button.clicked.connect(self.reset_personalizations)
        actions_layout.addWidget(reset_button)

        actions_layout.addStretch()

        scroll_layout.addLayout(actions_layout)
        scroll_layout.addStretch()

        scroll_area.setWidget(scroll_widget)
        layout.addWidget(scroll_area)

        self.tab_widget.addTab(widget, "🎨 Personalizza")

    def choose_color(self, category, button):
        """Permette di scegliere un colore per una categoria di testo."""
        from PyQt6.QtWidgets import QColorDialog

        current_color = button.palette().color(button.backgroundRole())
        color = QColorDialog.getColor(current_color, self, f"Scegli colore per {category}")

        if color.isValid():
            color_hex = color.name()
            button.setStyleSheet(f"background-color: {color_hex}; border: 1px solid #ccc;")
            # Trova la label corrispondente e aggiorna il testo
            for cat, (btn, label) in self.text_color_buttons.items():
                if cat == category:
                    label.setText(color_hex)
                    break

    def choose_button_color(self, category, button, color_type):
        """Permette di scegliere un colore per una categoria di pulsante."""
        from PyQt6.QtWidgets import QColorDialog

        current_color = button.palette().color(button.backgroundRole())
        color = QColorDialog.getColor(current_color, self, f"Scegli colore {color_type} per {category}")

        if color.isValid():
            color_hex = color.name()
            button.setStyleSheet(f"background-color: {color_hex}; color: white; border: none; border-radius: 4px;")

    def update_preview(self):
        """Aggiorna l'anteprima con le impostazioni correnti."""
        try:
            # Aggiorna il font del testo di anteprima
            font_family = self.font_family_combo.currentText()
            font_size = self.font_size_spin.value()
            font_weight = self.font_weight_combo.currentText()

            weight_map = {
                "Normale": "normal",
                "Grassetto": "bold",
                "Corsivo": "italic",
                "Grassetto Corsivo": "bold italic"
            }

            font_style = f"font-family: '{font_family}'; font-size: {font_size}pt; font-weight: {weight_map.get(font_weight, 'normal')};"
            self.preview_label.setStyleSheet(f"padding: 10px; border: 1px solid #ddd; border-radius: 4px; {font_style}")

            # Aggiorna i pulsanti di anteprima (implementazione futura)
            QMessageBox.information(self, "Anteprima", "Anteprima aggiornata con le impostazioni correnti!")

        except Exception as e:
            QMessageBox.warning(self, "Errore Anteprima", f"Errore nell'aggiornamento dell'anteprima:\n{str(e)}")

    def apply_personalizations(self):
        """Applica le personalizzazioni all'interfaccia principale e salva nel file settings.json."""
        try:
            # Raccogli tutte le impostazioni dai controlli
            font_family = self.font_family_combo.currentText()
            font_size = self.font_size_spin.value()
            font_weight = self.font_weight_combo.currentText()

            # Salva le impostazioni nel file settings.json
            set_setting('main_font_family', font_family)
            set_setting('main_font_size', font_size)
            set_setting('main_font_weight', font_weight)

            print(f"✅ Impostazioni font salvate:")
            print(f"   - Font: {font_family}")
            print(f"   - Dimensione: {font_size}pt")
            print(f"   - Peso: {font_weight}")

            # Qui implementeremo la logica per applicare le modifiche all'interfaccia principale
            QMessageBox.information(self, "Personalizzazioni Salvate",
                                  f"✅ Le personalizzazioni sono state salvate con successo!\n\n"
                                  f"🎨 Font: {font_family}\n"
                                  f"📏 Dimensione: {font_size}pt\n"
                                  f"💪 Peso: {font_weight}\n\n"
                                  f"Le impostazioni sono state salvate nel file settings.json.")

        except Exception as e:
            QMessageBox.critical(self, "Errore", f"Errore nell'applicazione delle personalizzazioni:\n{str(e)}")

    def reset_personalizations(self):
        """Ripristina tutte le personalizzazioni ai valori predefiniti dal settings_manager."""
        try:
            # Ripristina font ai valori di default (OpenDyslexic per dislessia)
            default_font_family = 'OpenDyslexic'
            default_font_size = 14
            default_font_weight = 'Normale'

            # Imposta i valori di default nei controlli
            if default_font_family in [self.font_family_combo.itemText(i) for i in range(self.font_family_combo.count())]:
                self.font_family_combo.setCurrentText(default_font_family)
            else:
                # Se il font di default non è disponibile, usa il primo della lista
                if self.font_family_combo.count() > 0:
                    self.font_family_combo.setCurrentText(self.font_family_combo.itemText(0))

            self.font_size_spin.setValue(default_font_size)
            self.font_weight_combo.setCurrentText(default_font_weight)

            print(f"🔄 Impostazioni font ripristinate ai valori predefiniti:")
            print(f"   - Font: {default_font_family}")
            print(f"   - Dimensione: {default_font_size}pt")
            print(f"   - Peso: {default_font_weight}")

            QMessageBox.information(self, "Ripristino Completato",
                                  f"✅ Le personalizzazioni sono state ripristinate ai valori predefiniti!\n\n"
                                  f"🎨 Font: {default_font_family}\n"
                                  f"📏 Dimensione: {default_font_size}pt\n"
                                  f"💪 Peso: {default_font_weight}")

            # Ripristina colori testo
            default_text_colors = {
                "Testo normale": "#333333",
                "Titoli e intestazioni": "#2c3e50",
                "Testo evidenziato": "#007bff",
                "Testo di errore": "#dc3545",
                "Testo di successo": "#28a745",
                "Testo di avviso": "#ffc107"
            }

            for category, color in default_text_colors.items():
                if category in self.text_color_buttons:
                    button, label = self.text_color_buttons[category]
                    button.setStyleSheet(f"background-color: {color}; border: 1px solid #ccc;")
                    label.setText(color)

            # Ripristina sfondi pulsanti
            default_button_colors = {
                "Pulsanti principali": ("#4a90e2", "#357abd"),
                "Pulsanti secondari": ("#6c757d", "#5a6268"),
                "Pulsanti di successo": ("#28a745", "#218838"),
                "Pulsanti di pericolo": ("#dc3545", "#c82333"),
                "Pulsanti di avviso": ("#ffc107", "#e0a800"),
                "Pulsanti speciali": ("#6f42c1", "#5a359a")
            }

            for category, (bg_color, hover_color) in default_button_colors.items():
                if category in self.button_bg_buttons:
                    bg_button, hover_button = self.button_bg_buttons[category]
                    bg_button.setStyleSheet(f"background-color: {bg_color}; color: white; border: none; border-radius: 4px;")
                    hover_button.setStyleSheet(f"background-color: {hover_color}; color: white; border: none; border-radius: 4px;")

            QMessageBox.information(self, "Ripristino", "Tutte le personalizzazioni sono state ripristinate ai valori predefiniti!")

        except Exception as e:
            QMessageBox.critical(self, "Errore", f"Errore nel ripristino delle personalizzazioni:\n{str(e)}")

    def load_current_settings(self):
        """Carica le impostazioni attuali nei controlli."""
        try:
            # Generale
            self.app_name_edit.setText(get_setting('application.app_name', 'CogniFlow'))
            self.theme_combo.setCurrentText(get_setting('application.theme', 'Chiaro'))

            # UI
            self.window_width_spin.setValue(get_setting('ui.window_width', 1200))
            self.window_height_spin.setValue(get_setting('ui.window_height', 800))

            # AI
            self.ai_trigger_edit.setText(get_setting('ai.ai_trigger', '++++'))
            self.ai_model_combo.setCurrentText(get_setting('ai.selected_ai_model', 'gemma:2b'))

            # Test
            self.test_text_edit.setText(get_setting('test.test_text', 'Test di sviluppo'))
            self.test_number_spin.setValue(get_setting('test.test_number', 42))
            self.test_combo.setCurrentText(get_setting('test.test_option', 'Opzione 1'))
            self.test_checkbox.setChecked(get_setting('test.test_enabled', True))

        except Exception as e:
            QMessageBox.warning(self, "Errore", f"Errore nel caricamento delle impostazioni: {e}")

    def save_settings(self):
        """Salva le impostazioni modificate."""
        try:
            # Generale
            set_setting('application.app_name', self.app_name_edit.text())
            set_setting('application.theme', self.theme_combo.currentText())

            # UI
            set_setting('ui.window_width', self.window_width_spin.value())
            set_setting('ui.window_height', self.window_height_spin.value())

            # Font settings (aggiunto per salvare tipo, dimensione e spessore font)
            if hasattr(self, 'font_family_combo'):
                set_setting('main_font_family', self.font_family_combo.currentText())
            if hasattr(self, 'font_size_spin'):
                set_setting('main_font_size', self.font_size_spin.value())
            if hasattr(self, 'font_weight_combo'):
                set_setting('main_font_weight', self.font_weight_combo.currentText())

            # AI
            set_setting('ai.ai_trigger', self.ai_trigger_edit.text())
            set_setting('ai.selected_ai_model', self.ai_model_combo.currentText())

            # Test
            set_setting('test.test_text', self.test_text_edit.text())
            set_setting('test.test_number', self.test_number_spin.value())
            set_setting('test.test_option', self.test_combo.currentText())
            set_setting('test.test_enabled', self.test_checkbox.isChecked())

            print("✅ Tutte le impostazioni salvate nel file settings.json")
            QMessageBox.information(self, "Successo", "Impostazioni salvate con successo!")
            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Errore", f"Errore nel salvataggio delle impostazioni: {e}")