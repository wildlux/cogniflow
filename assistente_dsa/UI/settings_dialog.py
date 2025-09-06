#!/usr/bin/env python3
"""
Settings Dialog - Dialog delle impostazioni per DSA Assistant
Interfaccia grafica completa per modificare tutte le configurazioni
"""

import sys
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QCheckBox,
    QGroupBox, QTabWidget, QWidget, QMessageBox
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

            # AI
            set_setting('ai.ai_trigger', self.ai_trigger_edit.text())
            set_setting('ai.selected_ai_model', self.ai_model_combo.currentText())

            # Test
            set_setting('test.test_text', self.test_text_edit.text())
            set_setting('test.test_number', self.test_number_spin.value())
            set_setting('test.test_option', self.test_combo.currentText())
            set_setting('test.test_enabled', self.test_checkbox.isChecked())

            QMessageBox.information(self, "Successo", "Impostazioni salvate con successo!")
            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Errore", f"Errore nel salvataggio delle impostazioni: {e}")