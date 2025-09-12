#!/usr/bin/env python3
"""
Settings Dialog - Dialog delle impostazioni per DSA Assistant
Interfaccia grafica completa per modificare tutte le configurazioni
"""

import subprocess
import sys
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QCheckBox,
    QGroupBox, QTabWidget, QWidget, QMessageBox, QScrollArea, QGridLayout, QFrame
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


        self.setModal(True)

        # Imposta sfondo bianco per tutto il dialog
        self.setStyleSheet("""
            QDialog {
                background-color: white;
                color: black;
            }
            QTabWidget::pane {
                background-color: white;
            }
            QTabBar {
                background-color: white;
            }
            QTabBar::tab {
                background-color: white;
                color: black;
                border: 1px solid #cccccc;
                padding: 8px 16px;
            }
            QTabBar::tab:selected {
                background-color: #f0f0f0;
                color: black;
            }
            QGroupBox {
                background-color: white;
                border: 1px solid #cccccc;
                border-radius: 5px;
                margin-top: 10px;
            }
            QGroupBox::title {
                color: black;
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QLabel {
                color: black;
            }
            QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QCheckBox {
                background-color: white;
                color: black;
                border: 1px solid #cccccc;
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

        save_button = QPushButton("💾 Salva Impostazioni")
        save_button.setStyleSheet("QPushButton { background-color: #28a745; color: white; font-weight: bold; padding: 12px 24px; min-width: 180px; } QPushButton:hover { background-color: #218838; }")
        save_button.clicked.connect(self.save_settings)
        buttons_layout.addWidget(save_button)

        cancel_button = QPushButton("❌ Annulla")
        cancel_button.setStyleSheet("QPushButton { background-color: #dc3545; color: white; font-weight: bold; padding: 12px 24px; min-width: 120px; } QPushButton:hover { background-color: #c82333; }")
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

        # Checkbox per bypass login
        self.bypass_login_checkbox = QCheckBox("Bypass login")
        self.bypass_login_checkbox.setToolTip("Se abilitato, salta la finestra di login e avvia direttamente l'applicazione")
        app_layout.addWidget(self.bypass_login_checkbox)

        layout.addWidget(app_group)
        layout.addStretch()

        self.tab_widget.addTab(widget, "Generale")

    def setup_startup_tab(self):
        """Configura il tab avvio applicazione."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Gruppo impostazioni avvio
        startup_group = QGroupBox("Impostazioni di Avvio")
        startup_layout = QVBoxLayout(startup_group)

        # Checkbox per bypassare login
        self.bypass_login_checkbox = QCheckBox("Bypass login e launcher")
        self.bypass_login_checkbox.setToolTip("Se abilitato, salta la finestra di login e il launcher, avviando direttamente l'applicazione principale")
        startup_layout.addWidget(self.bypass_login_checkbox)

        # Checkbox per avvio automatico applicazione principale
        self.auto_start_checkbox = QCheckBox("Avvio automatico applicazione principale")
        self.auto_start_checkbox.setToolTip("Se abilitato, avvia automaticamente l'applicazione principale dopo il login")
        startup_layout.addWidget(self.auto_start_checkbox)

        layout.addWidget(startup_group)
        layout.addStretch()

        self.tab_widget.addTab(widget, "Avvio")

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
        test_button = QPushButton("🚀 Esegui Test")
        test_button.setStyleSheet("QPushButton { background-color: #17a2b8; color: white; font-weight: bold; padding: 10px 20px; min-width: 140px; } QPushButton:hover { background-color: #138496; }")
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

                        print("✅ Caricati {len(system_fonts)} font dal sistema Linux (solo nomi)")
                        print("🎨 Font per dislessia disponibile: {'OpenDyslexic' in system_fonts}")
                    else:
                        raise Exception("Nessun output da fc-list")
                else:
                    raise Exception("fc-list fallito con codice {result.returncode}")
            else:
                raise Exception("Sistema operativo non supportato per caricamento dinamico")

        except Exception:
            print("⚠️ Errore caricamento font di sistema: {e}")
            # Fallback alla lista di font comuni (incluso OpenDyslexic per dislessia)
            system_fonts = [
                "OpenDyslexic",  # Font per dislessia - PRIMA POSIZIONE
                "Arial", "Helvetica", "Times New Roman", "Courier New",
                "Verdana", "Georgia", "Palatino", "Garamond", "Bookman",
                "Comic Sans MS", "Trebuchet MS", "Arial Black", "Calibri",
                "Cambria", "Candara", "Consolas", "Constantia", "Corbel",
                "DejaVu Sans", "DejaVu Seri", "FreeMono", "FreeSans", "FreeSerif",
                "Liberation Mono", "Liberation Sans", "Liberation Serif",
                "Lucida Console", "Lucida Sans", "Lucida Sans Unicode",
                "Microsoft Sans Seri", "Monaco", "Segoe UI", "Tahoma", "Ubuntu"
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



        # === SEZIONE ANTEPRIMA (Stile Windows XP) ===
        preview_group = QGroupBox("👁️ Anteprima Finestra Demo")
        preview_group.setStyleSheet("QGroupBox { font-weight: bold; }")
        preview_layout = QVBoxLayout(preview_group)

        # Finestra demo professionale (simula una finestra dell'app)
        demo_window = QFrame()
        demo_window.setFrameStyle(QFrame.Shape.Box)
        demo_window.setStyleSheet("""
            QFrame {
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #f0f0f0, stop:1 #e0e0e0);
                border: 2px solid #808080;
                border-radius: 5px;
            }
        """)
        demo_layout = QVBoxLayout(demo_window)
        demo_layout.setContentsMargins(0, 0, 0, 0)

        # Barra del titolo professionale
        title_bar = QHBoxLayout()
        title_bar.setContentsMargins(5, 5, 5, 5)
        title_icon = QLabel("📄")
        title_icon.setStyleSheet("font-size: 16px;")
        title_bar.addWidget(title_icon)
        title_label = QLabel("CogniFlow - Finestra Demo Professionale")
        title_label.setStyleSheet("font-weight: bold; color: #000080; font-size: 12px;")
        title_bar.addWidget(title_label)
        title_bar.addStretch()
        minimize_button = QPushButton("_")
        minimize_button.setFixedSize(25, 20)
        minimize_button.setStyleSheet("QPushButton { background-color: #c0c0c0; border: 1px solid #808080; } QPushButton:hover { background-color: #d0d0d0; }")
        title_bar.addWidget(minimize_button)
        close_button = QPushButton("X")
        close_button.setFixedSize(25, 20)
        close_button.setStyleSheet("QPushButton { background-color: #c0c0c0; border: 1px solid #808080; color: red; font-weight: bold; } QPushButton:hover { background-color: #ffcccc; }")
        title_bar.addWidget(close_button)
        demo_layout.addLayout(title_bar)

        # Barra menu
        menu_bar = QHBoxLayout()
        menu_bar.setContentsMargins(5, 0, 5, 0)
        file_menu = QPushButton("File")
        file_menu.setStyleSheet("QPushButton { background-color: transparent; color: black; border: none; text-align: left; padding: 2px 10px; } QPushButton:hover { background-color: #e0e0e0; }")
        file_menu.clicked.connect(lambda: self.change_demo_color("menu"))
        menu_bar.addWidget(file_menu)
        edit_menu = QPushButton("Modifica")
        edit_menu.setStyleSheet("QPushButton { background-color: transparent; color: black; border: none; text-align: left; padding: 2px 10px; } QPushButton:hover { background-color: #e0e0e0; }")
        edit_menu.clicked.connect(lambda: self.change_demo_color("menu"))
        menu_bar.addWidget(edit_menu)
        view_menu = QPushButton("Visualizza")
        view_menu.setStyleSheet("QPushButton { background-color: transparent; color: black; border: none; text-align: left; padding: 2px 10px; } QPushButton:hover { background-color: #e0e0e0; }")
        view_menu.clicked.connect(lambda: self.change_demo_color("menu"))
        menu_bar.addWidget(view_menu)
        menu_bar.addStretch()
        demo_layout.addLayout(menu_bar)

        # Barra strumenti
        toolbar = QHBoxLayout()
        toolbar.setContentsMargins(5, 0, 5, 5)
        self.toolbar_button1 = QPushButton("📂")
        self.toolbar_button1.setFixedSize(30, 30)
        self.toolbar_button1.setStyleSheet("QPushButton { background-color: #f0f0f0; border: 1px solid #c0c0c0; } QPushButton:hover { background-color: #e0e0e0; }")
        self.toolbar_button1.clicked.connect(lambda: self.change_demo_color("toolbar"))
        toolbar.addWidget(self.toolbar_button1)
        self.toolbar_button2 = QPushButton("💾")
        self.toolbar_button2.setFixedSize(30, 30)
        self.toolbar_button2.setStyleSheet("QPushButton { background-color: #f0f0f0; border: 1px solid #c0c0c0; } QPushButton:hover { background-color: #e0e0e0; }")
        self.toolbar_button2.clicked.connect(lambda: self.change_demo_color("toolbar"))
        toolbar.addWidget(self.toolbar_button2)
        self.toolbar_button3 = QPushButton("🔍")
        self.toolbar_button3.setFixedSize(30, 30)
        self.toolbar_button3.setStyleSheet("QPushButton { background-color: #f0f0f0; border: 1px solid #c0c0c0; } QPushButton:hover { background-color: #e0e0e0; }")
        self.toolbar_button3.clicked.connect(lambda: self.change_demo_color("toolbar"))
        toolbar.addWidget(self.toolbar_button3)
        toolbar.addStretch()
        demo_layout.addLayout(toolbar)

        # Area contenuto principale
        content_area = QHBoxLayout()
        content_area.setContentsMargins(10, 10, 10, 10)

        # Pannello sinistro (albero o lista)
        left_panel = QVBoxLayout()
        left_label = QPushButton("Progetti")
        left_label.setStyleSheet("font-weight: bold; color: black; padding: 5px; border: none; background: transparent; text-align: left;")
        left_label.clicked.connect(lambda: self.change_demo_color("panel"))
        left_panel.addWidget(left_label)
        self.left_item1 = QPushButton("📄 Documento 1")
        self.left_item1.setStyleSheet("color: black; padding: 2px 5px; border: none; background: transparent; text-align: left;")
        self.left_item1.clicked.connect(lambda: self.change_demo_color("item"))
        left_panel.addWidget(self.left_item1)
        self.left_item2 = QPushButton("📄 Documento 2")
        self.left_item2.setStyleSheet("color: black; padding: 2px 5px; border: none; background: transparent; text-align: left;")
        self.left_item2.clicked.connect(lambda: self.change_demo_color("item"))
        left_panel.addWidget(self.left_item2)
        left_panel.addStretch()
        content_area.addLayout(left_panel, 1)

        # Separatore
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.VLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        content_area.addWidget(separator)

        # Area centrale (editor)
        center_area = QVBoxLayout()
        center_label = QPushButton("Editor di Testo")
        center_label.setStyleSheet("font-weight: bold; color: black; padding: 5px; border: none; background: transparent; text-align: left;")
        center_label.clicked.connect(lambda: self.change_demo_color("panel"))
        center_area.addWidget(center_label)
        self.demo_text = QLabel("Questo è il contenuto dell'editor.\nClicca sui pulsanti per cambiare i colori.")
        self.demo_text.setWordWrap(True)
        self.demo_text.setStyleSheet("color: black; padding: 10px; background-color: white; border: 1px solid #c0c0c0; min-height: 60px;")
        center_area.addWidget(self.demo_text)
        content_area.addLayout(center_area, 3)

        demo_layout.addLayout(content_area)

        # Barra di stato
        status_bar = QHBoxLayout()
        status_bar.setContentsMargins(5, 0, 5, 5)
        self.status_label = QLabel("Pronto - Clicca sugli elementi per personalizzare i colori")
        self.status_label.setStyleSheet("color: black; padding: 2px;")
        status_bar.addWidget(self.status_label)
        status_bar.addStretch()
        self.status_button = QPushButton("Info")
        self.status_button.setStyleSheet("QPushButton { background-color: #f0f0f0; border: 1px solid #c0c0c0; padding: 2px 10px; } QPushButton:hover { background-color: #e0e0e0; }")
        self.status_button.clicked.connect(lambda: self.change_demo_color("status"))
        status_bar.addWidget(self.status_button)
        demo_layout.addLayout(status_bar)

        preview_layout.addWidget(demo_window)

        # Istruzioni
        instructions = QLabel("Clicca sugli elementi della finestra demo per cambiarne i colori!")
        instructions.setStyleSheet("color: #666; font-style: italic; padding: 5px;")
        preview_layout.addWidget(instructions)



        scroll_layout.addWidget(preview_group)

        # === PULSANTI AZIONI ===
        actions_layout = QHBoxLayout()

        # Pulsante per applicare le modifiche
        apply_button = QPushButton("✅ Applica Modifiche")
        apply_button.setStyleSheet("QPushButton { background-color: #28a745; color: white; font-weight: bold; padding: 12px 24px; min-width: 200px; min-height: 45px; } QPushButton:hover { background-color: #218838; }")
        apply_button.clicked.connect(self.apply_personalizations)
        actions_layout.addWidget(apply_button)

        # Pulsante per ripristinare i valori predefiniti
        reset_button = QPushButton("🔄 Ripristina Predefiniti")
        reset_button.setStyleSheet("QPushButton { background-color: #fd7e14; color: white; font-weight: bold; padding: 12px 24px; min-width: 200px; min-height: 45px; } QPushButton:hover { background-color: #e8680f; }")
        reset_button.clicked.connect(self.reset_personalizations)
        actions_layout.addWidget(reset_button)

        actions_layout.addStretch()

        scroll_layout.addLayout(actions_layout)
        scroll_layout.addStretch()

        scroll_area.setWidget(scroll_widget)
        layout.addWidget(scroll_area)

        self.tab_widget.addTab(widget, "🎨 Personalizza")

    def choose_color(self, category, button):
        """Permette di scegliere un colore per una categoria (semplificato)."""
        from PyQt6.QtWidgets import QColorDialog

        current_color = button.palette().color(button.backgroundRole())
        color = QColorDialog.getColor(current_color, self, f"Scegli colore per {category}")

        if color.isValid():
            color_hex = color.name()
            button.setStyleSheet(f"background-color: {color_hex}; border: 1px solid #ccc;")
            # Aggiorna il colore del pulsante (senza salvare etichette)

    def choose_button_color(self, category, button, color_type):
        """Permette di scegliere un colore per una categoria di pulsante."""
        from PyQt6.QtWidgets import QColorDialog

        current_color = button.palette().color(button.backgroundRole())
        color = QColorDialog.getColor(current_color, self, "Scegli colore {color_type} per {category}")

        if color.isValid():
            color_hex = color.name()
            button.setStyleSheet("background-color: {color_hex}; color: white; border: none; border-radius: 4px;")

    def choose_button_text_color(self, button_id, button):
        """Permette di scegliere un colore del testo per un pulsante specifico."""
        from PyQt6.QtWidgets import QColorDialog

        current_color = button.palette().color(button.backgroundRole())
        color = QColorDialog.getColor(current_color, self, f"Scegli colore testo per {button_id}")

        if color.isValid():
            color_hex = color.name()
            button.setStyleSheet(f"background-color: {color_hex}; border: 2px solid #000000; border-radius: 4px;")

            # Trova la label corrispondente e aggiorna il testo
            # Cerca in tutti i dizionari di pulsanti
            all_button_dicts = [
                getattr(self, 'main_button_color_buttons', {}),
                getattr(self, 'transcription_button_colors', {}),
                getattr(self, 'ai_button_colors', {}),
                getattr(self, 'knowledge_button_colors', {}),
                getattr(self, 'utility_button_colors', {}),
                getattr(self, 'iot_button_colors', {})
            ]

            for button_dict in all_button_dicts:
                if button_id in button_dict:
                    _, label = button_dict[button_id]
                    label.setText(color_hex)
                    break

    def update_preview(self):
        """Aggiorna l'anteprima con le impostazioni correnti."""
        try:
            # Aggiorna il font del testo demo
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
            self.demo_text.setStyleSheet(f"color: black; padding: 5px; {font_style}")

            QMessageBox.information(self, "Anteprima", "Anteprima aggiornata con le impostazioni correnti!")

        except Exception as e:
            QMessageBox.warning(self, "Errore Anteprima", f"Errore nell'aggiornamento dell'anteprima:\n{str(e)}")

    def change_demo_color(self, element):
        """Cambia il colore di un elemento della demo."""
        from PyQt6.QtWidgets import QColorDialog

        if element == "button":
            # Per pulsanti toolbar
            current_color = self.toolbar_button1.palette().color(self.toolbar_button1.backgroundRole())
            color = QColorDialog.getColor(current_color, self, "Scegli colore per pulsanti demo")
            if color.isValid():
                color_hex = color.name()
                self.toolbar_button1.setStyleSheet(f"QPushButton {{ background-color: {color_hex}; border: 1px solid #c0c0c0; }} QPushButton:hover {{ background-color: {self.lighten_color(color_hex)}; }}")
                self.toolbar_button2.setStyleSheet(f"QPushButton {{ background-color: {color_hex}; border: 1px solid #c0c0c0; }} QPushButton:hover {{ background-color: {self.lighten_color(color_hex)}; }}")
                self.toolbar_button3.setStyleSheet(f"QPushButton {{ background-color: {color_hex}; border: 1px solid #c0c0c0; }} QPushButton:hover {{ background-color: {self.lighten_color(color_hex)}; }}")
        elif element == "menu":
            # Per barra menu
            color = QColorDialog.getColor(Qt.GlobalColor.white, self, "Scegli colore per barra menu")
            if color.isValid():
                color_hex = color.name()
                # Aggiorna stili menu (simplificato)
                self.status_label.setText(f"Menu color changed to {color_hex}")
        elif element == "toolbar":
            # Già gestito in button
            pass
        elif element == "panel":
            # Per pannelli
            color = QColorDialog.getColor(Qt.GlobalColor.lightGray, self, "Scegli colore per pannelli")
            if color.isValid():
                color_hex = color.name()
                self.demo_text.setStyleSheet(f"color: black; padding: 10px; background-color: {color_hex}; border: 1px solid #c0c0c0; min-height: 60px;")
        elif element == "text":
            # Per testo
            color = QColorDialog.getColor(Qt.GlobalColor.black, self, "Scegli colore per testo")
            if color.isValid():
                color_hex = color.name()
                self.demo_text.setStyleSheet(f"color: {color_hex}; padding: 10px; background-color: white; border: 1px solid #c0c0c0; min-height: 60px;")
        elif element == "item":
            # Per elementi lista
            color = QColorDialog.getColor(Qt.GlobalColor.black, self, "Scegli colore per elementi lista")
            if color.isValid():
                color_hex = color.name()
                self.left_item1.setStyleSheet(f"color: {color_hex}; padding: 2px 5px;")
                self.left_item2.setStyleSheet(f"color: {color_hex}; padding: 2px 5px;")
        elif element == "status":
            # Per barra stato
            color = QColorDialog.getColor(Qt.GlobalColor.white, self, "Scegli colore per barra stato")
            if color.isValid():
                color_hex = color.name()
                self.status_label.setStyleSheet(f"color: black; padding: 2px; background-color: {color_hex};")

    def lighten_color(self, color_hex):
        """Schiarisci un colore per hover."""
        # Semplice schiarimento (aggiungi offset)
        if color_hex.startswith('#') and len(color_hex) == 7:
            r = int(color_hex[1:3], 16)
            g = int(color_hex[3:5], 16)
            b = int(color_hex[5:7], 16)
            r = min(255, r + 20)
            g = min(255, g + 20)
            b = min(255, b + 20)
            return f"#{r:02x}{g:02x}{b:02x}"
        return color_hex



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

            # Salva i colori dei pulsanti
            button_text_colors = {}

            # Per ora, non salvare colori pulsanti specifici (semplificato)

            # Salva i colori nel file settings.json
            colors = get_setting('colors', {})
            colors['button_text_colors'] = button_text_colors
            set_setting('colors', colors)

            print("✅ Impostazioni font salvate:")
            print("   - Font: {font_family}")
            print("   - Dimensione: {font_size}pt")
            print("   - Peso: {font_weight}")
            print("✅ Colori pulsanti salvati: {len(button_text_colors)} pulsanti")

            # Qui implementeremo la logica per applicare le modifiche all'interfaccia principale
            QMessageBox.information(self, "Personalizzazioni Salvate",
                                      "✅ Le personalizzazioni sono state salvate con successo!\n\n"
                                      "🎨 Font: {font_family}\n"
                                      "📏 Dimensione: {font_size}pt\n"
                                      "💪 Peso: {font_weight}\n\n"
                                      "⚠️ Riavvia l'applicazione per applicare le modifiche all'interfaccia principale.\n"
                                      "Le impostazioni sono state salvate nel file settings.json.")

        except Exception:
            QMessageBox.critical(self, "Errore", "Errore nell'applicazione delle personalizzazioni:\n{str(e)}")

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

            print("🔄 Impostazioni font ripristinate ai valori predefiniti:")
            print("   - Font: {default_font_family}")
            print("   - Dimensione: {default_font_size}pt")
            print("   - Peso: {default_font_weight}")

            QMessageBox.information(self, "Ripristino Completato",
                                    "✅ Le personalizzazioni sono state ripristinate ai valori predefiniti!\n\n"
                                    "🎨 Font: {default_font_family}\n"
                                    "📏 Dimensione: {default_font_size}pt\n"
                                    "💪 Peso: {default_font_weight}")

            # Ripristino colori testo rimosso (semplificato)

            # Ripristino sfondi semplificato (rimosso)

            QMessageBox.information(self, "Ripristino", "Tutte le personalizzazioni sono state ripristinate ai valori predefiniti!")

        except Exception:
            QMessageBox.critical(self, "Errore", "Errore nel ripristino delle personalizzazioni:\n{str(e)}")

    def load_current_settings(self):
        """Carica le impostazioni attuali nei controlli."""
        try:
            # Generale
            self.app_name_edit.setText(get_setting('application.app_name', 'CogniFlow'))
            self.theme_combo.setCurrentText(get_setting('application.theme', 'Chiaro'))
            self.bypass_login_checkbox.setChecked(get_setting('startup.bypass_login', False))

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
            set_setting('startup.bypass_login', self.bypass_login_checkbox.isChecked())

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

        except Exception:
            QMessageBox.critical(self, "Errore", "Errore nel salvataggio delle impostazioni: {e}")
