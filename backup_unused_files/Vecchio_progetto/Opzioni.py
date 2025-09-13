# Opzioni.py - Dialog per la configurazione dell'applicazione

import logging
import requests
from PyQt6.QtWidgets import (
    QDialog,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QComboBox,
    QLineEdit,
    QGroupBox,
    QTabWidget,
    QCheckBox,
    QSlider,
    QMessageBox,
)
from PyQt6.QtCore import Qt


class ConfigurationDialog(QDialog):
    """Dialog per la configurazione dell'applicazione."""

    def __init__(self, parent=None, settings=None):
        super().__init__(parent)
        self.setWindowTitle("⚙️ Menu di Configurazione")
        self.setModal(True)
        self.resize(600, 500)
        self.settings = settings or {}

        self.setup_ui()
        self.load_settings()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        header_layout = QHBoxLayout()
        title_label = QLabel("⚙️ Menu di Configurazione")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #4a90e2;")
        close_button = QPushButton("❌")
        close_button.setFixedSize(30, 30)
        close_button.clicked.connect(self.accept)

        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(close_button)
        layout.addLayout(header_layout)

        self.tab_widget = QTabWidget()
        self.setup_ai_tab()
        self.setup_ui_tab()
        self.setup_gestures_tab()
        layout.addWidget(self.tab_widget)

        bottom_layout = QHBoxLayout()
        bottom_layout.addStretch()

        close_menu_btn = QPushButton("Chiudi Menu")
        close_menu_btn.clicked.connect(self.accept)

        log_btn = QPushButton("Scarica Log Emozioni")
        log_btn.clicked.connect(self.download_log)

        bottom_layout.addWidget(close_menu_btn)
        bottom_layout.addWidget(log_btn)
        layout.addLayout(bottom_layout)

    def setup_ai_tab(self):
        ai_widget = QWidget()
        layout = QVBoxLayout(ai_widget)

        ai_group = QGroupBox("Selezione AI")
        ai_layout = QVBoxLayout(ai_group)
        self.ollama_model_combo = QComboBox()
        self.ollama_model_combo.addItem("Seleziona un modello")
        ai_layout.addWidget(QLabel("Modello Ollama:"))
        ai_layout.addWidget(self.ollama_model_combo)

        test_ollama_btn = QPushButton("Testa Connessione & Modelli")
        test_ollama_btn.clicked.connect(self.test_ollama_connection)
        ai_layout.addWidget(test_ollama_btn)

        self.ollama_status_label = QLabel("Stato: Inattivo")
        self.ollama_status_label.setStyleSheet("color: #4a90e2;")
        ai_layout.addWidget(self.ollama_status_label)
        layout.addWidget(ai_group)

        trigger_group = QGroupBox("Trigger per AI")
        trigger_layout = QVBoxLayout(trigger_group)
        trigger_layout.addWidget(
            QLabel("Imposta una parola d'ordine per inviare il testo all'AI:")
        )
        self.ai_trigger_input = QLineEdit("++++")
        trigger_layout.addWidget(self.ai_trigger_input)
        layout.addWidget(trigger_group)

        layout.addStretch()
        self.tab_widget.addTab(ai_widget, "Configurazione AI")

        self.test_ollama_connection()

    def setup_ui_tab(self):
        ui_widget = QWidget()
        layout = QVBoxLayout(ui_widget)

        layout.addWidget(QLabel("Tema & Colori Cursore"))
        layout.addWidget(QLabel("Scegli il tema dell'interfaccia:"))

        theme_layout = QHBoxLayout()
        self.current_theme_btn = QPushButton("Tema Attuale")
        self.current_theme_btn.setCheckable(True)
        self.current_theme_btn.setChecked(True)
        self.school_theme_btn = QPushButton("Tema Scuola")
        self.school_theme_btn.setCheckable(True)

        theme_layout.addWidget(self.current_theme_btn)
        theme_layout.addWidget(self.school_theme_btn)
        layout.addLayout(theme_layout)

        colors_layout = QHBoxLayout()
        colors_layout.addWidget(QLabel("Colore mano sinistra:"))
        colors_layout.addWidget(QPushButton("—"))
        colors_layout.addWidget(QLabel("Colore mano destra:"))
        colors_layout.addWidget(QPushButton("—"))
        colors_layout.addWidget(QLabel("Colore viso:"))
        colors_layout.addWidget(QPushButton("—"))
        layout.addLayout(colors_layout)

        layout.addWidget(QLabel("Layout Elementi"))
        layout.addWidget(QLabel("Dimensioni degli elementi contenuti:"))

        self.size_combo = QComboBox()
        self.size_combo.addItems(["Adatta al testo", "Piccolo", "Medio", "Grande"])
        layout.addWidget(self.size_combo)

        layout.addWidget(QLabel("Visualizzazione Elementi"))
        layout.addWidget(QLabel("Scegli come visualizzare testo e icone:"))

        self.visualization_combo = QComboBox()
        self.visualization_combo.addItems(
            ["Testo con Icona", "Solo Testo", "Solo Icona"]
        )
        layout.addWidget(self.visualization_combo)

        layout.addWidget(QLabel("Posizione Icone"))
        layout.addWidget(QLabel("Scegli la posizione delle icone negli elementi:"))

        self.icon_position_combo = QComboBox()
        self.icon_position_combo.addItems(
            ["In alto", "In basso", "A sinistra", "A destra"]
        )
        layout.addWidget(self.icon_position_combo)

        layout.addStretch()
        self.tab_widget.addTab(ui_widget, "Comportamento & UI")

    def setup_gestures_tab(self):
        gestures_widget = QWidget()
        layout = QVBoxLayout(gestures_widget)

        layout.addWidget(QLabel("Riconoscimento Vocale"))
        layout.addWidget(QLabel("Seleziona la lingua per il microfono:"))

        self.language_combo = QComboBox()
        self.language_combo.addItems(["Italiano", "English", "Français", "Deutsch"])
        layout.addWidget(self.language_combo)

        layout.addWidget(QLabel("Riconoscimento Facciale"))
        face_layout = QVBoxLayout()
        face_layout.addWidget(
            QLabel('Attiva la funzione d\'emergenza "genitore empatico":')
        )

        self.face_recognition_cb = QCheckBox("Abilita")
        face_layout.addWidget(self.face_recognition_cb)
        layout.addLayout(face_layout)

        layout.addWidget(QLabel("Dispositivo Esterno"))
        layout.addWidget(QLabel("Collega Arduino o altri dispositivi via USB."))

        connect_device_btn = QPushButton("🔗 Collega Dispositivo Esterno")
        layout.addWidget(connect_device_btn)

        layout.addWidget(QLabel("Feedback Sonoro"))
        layout.addWidget(QLabel("Attiva/disattiva i suoni per i gesti:"))

        self.sound_cb = QCheckBox("Abilita Suoni")
        self.sound_cb.setChecked(True)
        layout.addWidget(self.sound_cb)

        layout.addWidget(QLabel("Volume:"))
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(50)
        layout.addWidget(self.volume_slider)

        layout.addWidget(QLabel("Gesti Mano"))
        layout.addWidget(QLabel("Timeout per la selezione (in ms):"))

        self.timeout_input = QLineEdit("500")
        layout.addWidget(self.timeout_input)

        layout.addStretch()
        self.tab_widget.addTab(gestures_widget, "Gesti & Suoni")

    def test_ollama_connection(self):
        """Testa la connessione a Ollama e recupera i modelli."""
        self.ollama_status_label.setText("Stato: Test in corso...")
        self.ollama_model_combo.clear()
        try:
            models = self.get_ollama_models()
            if models:
                self.ollama_status_label.setText("Stato: ✅ Connesso a Ollama")
                self.ollama_model_combo.addItems(models)
                self.ollama_model_combo.setCurrentIndex(0)
            else:
                self.ollama_status_label.setText(
                    "Stato: ⚠️ Connesso, ma nessun modello trovato"
                )
        except requests.exceptions.ConnectionError:
            self.ollama_status_label.setText("Stato: ❌ Errore di connessione")
            QMessageBox.critical(
                self,
                "Errore di Connessione",
                "Impossibile connettersi al server Ollama. Assicurati che sia in esecuzione.",
            )
        except Exception as e:
            self.ollama_status_label.setText(f"Stato: ❌ Errore - {e}")
            QMessageBox.critical(self, "Errore", f"Si è verificato un errore: {e}")

    def get_ollama_models(self):
        """Recupera la lista dei modelli da Ollama."""
        try:
            response = requests.get("http://localhost:11434/api/tags")
            response.raise_for_status()
            data = response.json()
            models = [model["name"] for model in data.get("models", [])]
            return models
        except Exception as e:
            raise

    def download_log(self):
        """Scarica il log delle emozioni"""
        QMessageBox.information(
            self, "Download Log", "Funzionalità non ancora implementata."
        )

    def load_settings(self):
        """Carica le impostazioni salvate"""
        pass

    def get_settings(self):
        """Restituisce le impostazioni correnti."""
        return {
            "ai_trigger": self.ai_trigger_input.text(),
            "ollama_model": self.ollama_model_combo.currentText(),
            "language": self.language_combo.currentText(),
            "face_recognition": self.face_recognition_cb.isChecked(),
            "sound_enabled": self.sound_cb.isChecked(),
            "volume": self.volume_slider.value(),
            "timeout": self.timeout_input.text(),
            "theme": "current" if self.current_theme_btn.isChecked() else "school",
            "element_size": self.size_combo.currentText(),
            "visualization": self.visualization_combo.currentText(),
            "icon_position": self.icon_position_combo.currentText(),
        }