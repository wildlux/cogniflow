#!/usr/bin/env python3
"""
Test script to verify pensierini creation from footer functionality
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QVBoxLayout,
    QWidget,
    QLineEdit,
    QPushButton,
    QLabel,
)
from PyQt6.QtCore import Qt
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class TestPensieriniFooter(QMainWindow):
    """Test window to verify pensierini footer functionality"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Test Pensierini Footer")
        self.setGeometry(100, 100, 400, 200)

        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Create layout
        layout = QVBoxLayout(central_widget)

        # Footer pensierini input (simulating the real one)
        self.footer_pensierini_input = QLineEdit()
        self.footer_pensierini_input.setPlaceholderText(
            "💭 Scrivi pensierino rapido..."
        )
        layout.addWidget(QLabel("Footer Pensierini Input:"))
        layout.addWidget(self.footer_pensierini_input)

        # Send button
        send_button = QPushButton("📤 Invia Pensierino")
        send_button.clicked.connect(self.send_footer_pensierino)
        layout.addWidget(send_button)

        # Connect return pressed
        self.footer_pensierini_input.returnPressed.connect(self.send_footer_pensierino)

        # Results area
        self.results_label = QLabel("Results will appear here...")
        self.results_label.setWordWrap(True)
        layout.addWidget(QLabel("Test Results:"))
        layout.addWidget(self.results_label)

        # Initialize pensierini list
        self.pensierini_list = []

    def send_footer_pensierino(self):
        """Test the send_footer_pensierino functionality"""
        try:
            # Get text from input
            text = self.footer_pensierini_input.text().strip()

            if not text:
                self.results_label.setText(
                    "❌ Campo vuoto! Scrivi qualcosa prima di inviare."
                )
                return

            # Simulate creating a pensierino widget
            pensierino_text = f"💭 {text}"

            # Add to our test list
            self.pensierini_list.append(pensierino_text)

            # Clear input
            self.footer_pensierini_input.clear()

            # Update results
            results_text = f"✅ Pensierino creato con successo!\n\n"
            results_text += f"📝 Testo: {pensierino_text}\n\n"
            results_text += f"📊 Totale pensierini: {len(self.pensierini_list)}\n\n"
            results_text += "Lista pensierini:\n" + "\n".join(
                f"• {p}" for p in self.pensierini_list[-5:]
            )  # Show last 5

            self.results_label.setText(results_text)

            # Log success
            logging.info(f"💭 Pensierino inviato: {text[:50]}...")

        except Exception as e:
            error_msg = f"❌ Errore durante l'invio del pensierino: {str(e)}"
            self.results_label.setText(error_msg)
            logging.error(f"Error in send_footer_pensierino: {e}")


def main():
    """Main test function"""
    app = QApplication(sys.argv)

    # Create test window
    test_window = TestPensieriniFooter()
    test_window.show()

    # Run the application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
