#!/usr/bin/env python3
"""
Test script per verificare la funzionalità del campo nome progetto
con placeholder dinamico e sfondo semi-trasparente.
"""

import sys
import os
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QVBoxLayout,
    QWidget,
    QLineEdit,
    QLabel,
)
from PyQt6.QtCore import Qt


class TestProjectNameInput(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Test Campo Nome Progetto")
        self.setGeometry(100, 100, 400, 200)

        # Widget centrale
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)

        # Etichetta di istruzioni
        instructions = QLabel("Test del campo nome progetto:")
        instructions.setStyleSheet("font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(instructions)

        # Campo nome progetto (stessa implementazione del main)
        self.project_name_input = QLineEdit()
        self.project_name_input.setPlaceholderText("Nome progetto...")
        self.project_name_input.textChanged.connect(
            self.update_project_name_input_style
        )
        layout.addWidget(self.project_name_input)

        # Etichetta di stato
        self.status_label = QLabel("Campo vuoto - placeholder: 'Nome progetto...'")
        self.status_label.setStyleSheet("margin-top: 20px; color: #666;")
        layout.addWidget(self.status_label)

        layout.addStretch()

        # Inizializza lo stile
        self.update_project_name_input_style()

    def update_project_name_input_style(self):
        """Aggiorna lo stile del campo nome progetto in base al contenuto."""
        if self.project_name_input.text().strip():
            # Campo con contenuto: placeholder diverso e sfondo semi-trasparente
            self.project_name_input.setPlaceholderText("Inserisci nome progetto")
            self.project_name_input.setStyleSheet(
                """
                QLineEdit {
                    background: rgba(40, 167, 69, 0.1);
                    border: 1px solid #28a745;
                    border-radius: 4px;
                    padding: 4px 8px;
                    color: #155724;
                    font-weight: bold;
                }
            """
            )
            self.status_label.setText(
                "Campo con contenuto - placeholder: 'Inserisci nome progetto'\nSfondo: verde semi-trasparente"
            )
        else:
            # Campo vuoto: placeholder originale e sfondo normale
            self.project_name_input.setPlaceholderText("Nome progetto...")
            self.project_name_input.setStyleSheet(
                """
                QLineEdit {
                    background: rgba(255, 255, 255, 0.95);
                    border: 1px solid #dee2e6;
                    border-radius: 4px;
                    padding: 4px 8px;
                    color: #495057;
                }
            """
            )
            self.status_label.setText(
                "Campo vuoto - placeholder: 'Nome progetto...'\nSfondo: normale"
            )


def main():
    app = QApplication(sys.argv)
    window = TestProjectNameInput()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
