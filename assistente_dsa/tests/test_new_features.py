#!/usr/bin/env python3
"""
Test delle nuove funzionalità per l'interfaccia:
- Orari in basso a sinistra e destra ⌚️
- Icona lettura ad alta voce 💬🔊
- Pulsante creazione pensierini 💭
"""

import sys
import os
from datetime import datetime
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTextEdit, QScrollArea, QFrame, QMessageBox,
    QInputDialog
)

# Import delle componenti necessarie
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from UI.draggable_text_widget import DraggableTextWidget
from main_03_configurazione_e_opzioni import get_config, load_settings

class TestWindow(QMainWindow):
    """Finestra di test per le nuove funzionalità."""

    def __init__(self):
        super().__init__()
        self.settings = load_settings()
        self.pensierini_widgets = []

        self.setWindowTitle("🧪 Test Nuove Funzionalità")
        self.setGeometry(100, 100, 1000, 700)

        # Widget centrale
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Layout principale
        main_layout = QVBoxLayout(central_widget)

        # Titolo
        title_label = QLabel("🧪 Test delle Nuove Funzionalità")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #495057;
                padding: 10px;
                text-align: center;
            }
        """)
        main_layout.addWidget(title_label)

        # Area per i pensierini di test
        pensierini_group = QFrame()
        pensierini_group.setFrameStyle(QFrame.Shape.Box)
        pensierini_group.setStyleSheet("""
            QFrame {
                background: rgba(248, 249, 250, 0.8);
                border: 2px solid #dee2e6;
                border-radius: 10px;
                margin: 10px;
            }
        """)

        pensierini_layout = QVBoxLayout(pensierini_group)

        # Titolo sezione pensierini
        pensierini_title = QLabel("📝 Pensierini di Test (con 💬🔊 per lettura)")
        pensierini_title.setStyleSheet("font-weight: bold; font-size: 14px; color: #495057;")
        pensierini_layout.addWidget(pensierini_title)

        # Scroll area per i pensierini
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_widget = QWidget()
        self.pensierini_layout = QVBoxLayout(scroll_widget)
        self.pensierini_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll_area.setWidget(scroll_widget)
        pensierini_layout.addWidget(scroll_area)

        # Aggiungi alcuni pensierini di test
        self.add_test_pensierini()

        main_layout.addWidget(pensierini_group)

        # Footer con le nuove funzionalità
        footer_layout = QHBoxLayout()

        # Orario a sinistra
        self.left_time_label = QLabel("⌚️")
        self.left_time_label.setStyleSheet("""
            QLabel {
                color: #495057;
                font-size: 12px;
                padding: 5px 10px;
                background: rgba(255, 255, 255, 0.9);
                border-radius: 8px;
                border: 1px solid #dee2e6;
                font-weight: bold;
                min-width: 140px;
            }
        """)
        footer_layout.addWidget(self.left_time_label)

        # Pulsante creazione pensierino
        create_button = QPushButton("💭 Nuovo Pensierino")
        create_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(40, 167, 69, 0.8), stop:1 rgba(34, 197, 94, 0.8));
                border: 1px solid #28a745;
                border-radius: 6px;
                padding: 8px 12px;
                font-weight: bold;
                color: white;
                min-height: 30px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(34, 197, 94, 0.8), stop:1 rgba(40, 167, 69, 0.8));
            }
        """)
        create_button.clicked.connect(self.create_new_pensierino)
        footer_layout.addWidget(create_button)

        footer_layout.addStretch()  # Spazio centrale

        # Status label
        status_label = QLabel("🧪 Finestra di test attiva")
        status_label.setStyleSheet("""
            QLabel {
                color: #6c757d;
                font-size: 11px;
                padding: 5px 10px;
                background: rgba(255, 255, 255, 0.8);
                border-radius: 5px;
                border: 1px solid #ddd;
            }
        """)
        footer_layout.addWidget(status_label)

        # Orario a destra
        self.right_time_label = QLabel("⌚️")
        self.right_time_label.setStyleSheet("""
            QLabel {
                color: #495057;
                font-size: 12px;
                padding: 5px 10px;
                background: rgba(255, 255, 255, 0.9);
                border-radius: 8px;
                border: 1px solid #dee2e6;
                font-weight: bold;
                min-width: 140px;
            }
        """)
        footer_layout.addWidget(self.right_time_label)

        main_layout.addLayout(footer_layout)

        # Timer per aggiornare gli orari
        self.time_update_timer = QTimer()
        self.time_update_timer.timeout.connect(self._update_time_labels)
        self.time_update_timer.start(60000)  # Ogni minuto

        # Aggiorna immediatamente
        self._update_time_labels()

        print("🧪 Finestra di test creata con successo!")
        print("Funzionalità da testare:")
        print("  - ⌚️ Orari in basso a sinistra e destra")
        print("  - 💬🔊 Lettura ad alta voce nei pensierini")
        print("  - 💭 Creazione nuovi pensierini")

    def add_test_pensierini(self):
        """Aggiunge alcuni pensierini di test."""
        test_texts = [
            "Questo è un pensierino di test. Clicca sull'icona 💬🔊 per ascoltarlo!",
            "La sintesi vocale dovrebbe funzionare correttamente con questo testo.",
            "Prova a creare un nuovo pensierino usando il pulsante 💭 nel footer.",
            "Gli orari in basso dovrebbero aggiornarsi automaticamente ogni minuto."
        ]

        for text in test_texts:
            widget = DraggableTextWidget(text, self.settings)
            self.pensierini_layout.addWidget(widget)
            self.pensierini_widgets.append(widget)

    def create_new_pensierino(self):
        """Crea un nuovo pensierino tramite dialogo."""
        try:
            text, ok = QInputDialog.getMultiLineText(
                self,
                "💭 Crea Nuovo Pensierino",
                "Inserisci il testo del pensierino:",
                ""
            )

            if ok and text and text.strip():
                widget = DraggableTextWidget(text.strip(), self.settings)
                self.pensierini_layout.addWidget(widget)
                self.pensierini_widgets.append(widget)

                QMessageBox.information(
                    self,
                    "✅ Pensierino Creato",
                    f"Nuovo pensierino aggiunto:\n\n{text.strip()[:100]}{'...' if len(text.strip()) > 100 else ''}"
                )

                print(f"💭 Nuovo pensierino creato: {text.strip()[:50]}...")

        except Exception as e:
            QMessageBox.critical(self, "❌ Errore", f"Errore nella creazione del pensierino:\n{str(e)}")

    def _update_time_labels(self):
        """Aggiorna le etichette degli orari."""
        try:
            now = datetime.now()
            time_str = now.strftime("⌚️ %d/%m/%Y %H:%M")

            self.left_time_label.setText(time_str)
            self.right_time_label.setText(time_str)

        except Exception as e:
            print(f"Errore nell'aggiornamento degli orari: {e}")

def main():
    """Funzione principale per avviare la finestra di test."""
    app = QApplication(sys.argv)

    # Stile globale
    app.setStyleSheet("""
        QWidget {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #f8f9fa, stop:1 #e9ecef);
            color: #212529;
        }
    """)

    window = TestWindow()
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()