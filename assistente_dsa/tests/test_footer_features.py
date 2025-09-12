#!/usr/bin/env python3
"""
Test script per verificare le nuove funzionalità del footer:
1. Campo pensierini con pulsante invio
2. Guida rapida
"""

import sys
import os
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QVBoxLayout,
    QWidget,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QLabel,
)
from PyQt6.QtCore import Qt


class TestFooterFeatures(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Test Footer Features")
        self.setGeometry(100, 100, 800, 200)

        # Widget centrale
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)

        # Simula il footer con le nuove funzionalità
        footer_layout = QHBoxLayout()

        # Campo pensierini (come nel footer)
        pensierini_layout = QHBoxLayout()
        self.footer_pensierini_input = QLineEdit()
        self.footer_pensierini_input.setPlaceholderText(
            "💭 Scrivi pensierino rapido..."
        )
        self.footer_pensierini_input.setMinimumWidth(200)
        self.footer_pensierini_input.setMaximumWidth(300)
        self.footer_pensierini_input.returnPressed.connect(self.send_footer_pensierino)
        pensierini_layout.addWidget(self.footer_pensierini_input)

        self.footer_send_pensierino_button = QPushButton("📤 Invia")
        self.footer_send_pensierino_button.clicked.connect(self.send_footer_pensierino)
        pensierini_layout.addWidget(self.footer_send_pensierino_button)

        footer_layout.addLayout(pensierini_layout)

        # Pulsante cassetta attrezzi
        self.toggle_tools_button = QPushButton("🔧 Visualizza cassetta degli attrezzi")
        footer_layout.addWidget(self.toggle_tools_button)

        footer_layout.addStretch()

        # Pulsante webcam
        self.webcam_button = QPushButton("📹 Webcam")
        footer_layout.addWidget(self.webcam_button)

        # Guida rapida
        self.quick_help_button = QPushButton("❓ Guida")
        self.quick_help_button.clicked.connect(self.show_quick_help)
        footer_layout.addWidget(self.quick_help_button)

        layout.addLayout(footer_layout)

        # Area di log per i test
        self.log_area = QLabel("Log dei pensierini inviati:\n")
        self.log_area.setStyleSheet(
            "border: 1px solid #ccc; padding: 10px; background: #f9f9f9;"
        )
        self.log_area.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.addWidget(self.log_area)

    def send_footer_pensierino(self):
        """Simula l'invio di un pensierino."""
        text = self.footer_pensierini_input.text().strip()
        if text:
            current_log = self.log_area.text()
            self.log_area.setText(f"{current_log}💭 {text}\n")
            self.footer_pensierini_input.clear()
        else:
            print("Campo vuoto!")

    def show_quick_help(self):
        """Mostra guida rapida."""
        from PyQt6.QtWidgets import QMessageBox

        QMessageBox.information(
            self,
            "Guida Rapida",
            "Questa è la guida rapida!\n\n"
            "• Campo pensierini: Scrivi e premi Invio\n"
            "• Pulsante Invia: Invia il pensierino\n"
            "• Guida: Mostra questa finestra\n\n"
            "Funzionalità implementate con successo! ✅",
        )


def main():
    app = QApplication(sys.argv)
    window = TestFooterFeatures()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
