#!/usr/bin/env python3
"""
Simple test script to verify pensierini creation from footer functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLineEdit, QPushButton, QLabel, QScrollArea
from PyQt6.QtCore import Qt
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class TestSimplePensierini(QMainWindow):
    """Simple test window to verify pensierini footer functionality"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Test Simple Pensierini Footer")
        self.setGeometry(100, 100, 600, 400)

        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Create main layout
        main_layout = QVBoxLayout(central_widget)

        # Footer pensierini input section
        footer_group = QWidget()
        footer_layout = QVBoxLayout(footer_group)

        self.footer_pensierini_input = QLineEdit()
        self.footer_pensierini_input.setPlaceholderText("💭 Scrivi pensierino rapido...")
        footer_layout.addWidget(QLabel("Footer Pensierini Input:"))
        footer_layout.addWidget(self.footer_pensierini_input)

        # Send button
        send_button = QPushButton("📤 Invia Pensierino")
        send_button.clicked.connect(self.send_footer_pensierino)
        footer_layout.addWidget(send_button)

        # Connect return pressed
        self.footer_pensierini_input.returnPressed.connect(self.send_footer_pensierino)

        main_layout.addWidget(footer_group)

        # Pensierini display area (simulating Column A)
        pensierini_group = QWidget()
        pensierini_layout = QVBoxLayout(pensierini_group)

        pensierini_label = QLabel("📌 Column A - Pensierini:")
        pensierini_layout.addWidget(pensierini_label)

        # Scroll area for pensierini
        self.pensierini_scroll = QScrollArea()
        self.pensierini_scroll.setWidgetResizable(True)
        self.pensierini_scroll.setMinimumHeight(200)

        # Container for pensierini
        self.pensierini_container = QWidget()
        self.pensierini_layout = QVBoxLayout(self.pensierini_container)
        self.pensierini_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.pensierini_scroll.setWidget(self.pensierini_container)
        pensierini_layout.addWidget(self.pensierini_scroll)

        main_layout.addWidget(pensierini_group)

        # Status label
        self.status_label = QLabel("Ready to test pensierini creation...")
        main_layout.addWidget(self.status_label)

        # Initialize counters
        self.pensierini_count = 0

    def send_footer_pensierino(self):
        """Test the send_footer_pensierino functionality"""
        try:
            # Get text from input
            text = self.footer_pensierini_input.text().strip()

            if not text:
                self.status_label.setText("❌ Campo vuoto! Scrivi qualcosa prima di inviare.")
                return

            # Create a simple pensierino widget (simulating DraggableTextWidget)
            pensierino_label = QLabel(f"💭 {text}")
            pensierino_label.setWordWrap(True)
            pensierino_label.setStyleSheet("""
                QLabel {
                    background-color: #e8f4f8;
                    border: 2px solid #4a90e2;
                    border-radius: 8px;
                    padding: 10px;
                    margin: 5px;
                    font-size: 12px;
                }
            """)

            # Add to pensierini layout
            self.pensierini_layout.addWidget(pensierino_label)
            self.pensierini_count += 1

            # Clear input
            self.footer_pensierini_input.clear()

            # Update status
            self.status_label.setText(f"✅ Pensierino creato con successo! Totale: {self.pensierini_count}")

            # Log success
            logging.info(f"💭 Pensierino inviato: {text[:50]}...")

        except Exception as e:
            error_msg = f"❌ Errore durante l'invio del pensierino: {str(e)}"
            self.status_label.setText(error_msg)
            logging.error(f"Error in send_footer_pensierino: {e}")

def main():
    """Main test function"""
    app = QApplication(sys.argv)

    # Create test window
    test_window = TestSimplePensierini()
    test_window.show()

    print("Simple test application started successfully!")
    print("Testing pensierini creation from footer...")

    # Run the application
    sys.exit(app.exec())

if __name__ == "__main__":
    main()