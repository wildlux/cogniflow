#!/usr/bin/env python3
"""
Test script to verify footer buttons functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QHBoxLayout, QLineEdit, QPushButton, QLabel
from PyQt6.QtCore import Qt
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class TestFooterButtons(QMainWindow):
    """Test window to verify footer buttons functionality"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Test Footer Buttons")
        self.setGeometry(100, 100, 500, 200)

        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Create main layout
        layout = QVBoxLayout(central_widget)

        # Simulate footer pensierini layout
        pensierini_footer_layout = QHBoxLayout()
        pensierini_footer_layout.setSpacing(8)

        # Footer input field
        self.footer_pensierini_input = QLineEdit()
        self.footer_pensierini_input.setPlaceholderText("💭 Scrivi pensierino rapido...")
        self.footer_pensierini_input.setMinimumWidth(200)
        pensierini_footer_layout.addWidget(self.footer_pensierini_input)

        # Send button
        send_button = QPushButton("📤 Invia")
        send_button.clicked.connect(self.send_footer_pensierino)
        pensierini_footer_layout.addWidget(send_button)

        # Clear input button
        clear_input_button = QPushButton("🧽 Cancella testo")
        clear_input_button.clicked.connect(self.clear_input_text)
        pensierini_footer_layout.addWidget(clear_input_button)

        # Clear all button
        clear_all_button = QPushButton("🗑️ Cancella tutto")
        clear_all_button.clicked.connect(self.clear_all_pensierini_with_confirmation)
        pensierini_footer_layout.addWidget(clear_all_button)

        layout.addLayout(pensierini_footer_layout)

        # Status label
        self.status_label = QLabel("Test ready - Type something and test the buttons")
        layout.addWidget(self.status_label)

        # Test counter
        self.test_counter = 0

    def send_footer_pensierino(self):
        """Test send functionality"""
        text = self.footer_pensierini_input.text().strip()
        if text:
            self.test_counter += 1
            self.status_label.setText(f"✅ Sent: '{text}' (#{self.test_counter})")
            self.footer_pensierini_input.clear()
        else:
            self.status_label.setText("❌ Empty text - write something first")

    def clear_input_text(self):
        """Test clear input functionality"""
        self.footer_pensierini_input.clear()
        self.status_label.setText("✅ Input field cleared")

    def clear_all_pensierini_with_confirmation(self):
        """Test clear all functionality"""
        self.footer_pensierini_input.clear()
        self.test_counter = 0
        self.status_label.setText("✅ All cleared (simulation)")

def main():
    """Main test function"""
    app = QApplication(sys.argv)

    # Create test window
    test_window = TestFooterButtons()
    test_window.show()

    print("Footer buttons test started successfully!")
    print("Testing footer button layout and functionality...")

    # Run the application
    sys.exit(app.exec())

if __name__ == "__main__":
    main()