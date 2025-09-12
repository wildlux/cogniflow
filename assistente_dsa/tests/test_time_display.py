#!/usr/bin/env python3
"""
Test script to verify time display without dashes
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QPushButton
from PyQt6.QtCore import Qt
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class TestTimeDisplay(QMainWindow):
    """Test window to verify time display without dashes"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Test Time Display")
        self.setGeometry(100, 100, 400, 200)

        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Create layout
        layout = QVBoxLayout(central_widget)

        # Test labels (simulating the real ones)
        self.left_time_label = QLabel("⌚️")
        self.unified_time_label = QLabel("⌚️")

        layout.addWidget(QLabel("Left Time Label (iniziale):"))
        layout.addWidget(self.left_time_label)

        layout.addWidget(QLabel("Unified Time Label (iniziale):"))
        layout.addWidget(self.unified_time_label)

        # Test buttons
        test_status_button = QPushButton("Test Status Update")
        test_status_button.clicked.connect(self.test_status_update)
        layout.addWidget(test_status_button)

        test_time_button = QPushButton("Test Time Update")
        test_time_button.clicked.connect(self.test_time_update)
        layout.addWidget(test_time_button)

        # Status label
        self.status_label = QLabel("Ready for testing...")
        layout.addWidget(self.status_label)

    def test_status_update(self):
        """Test status update without time"""
        status_text = "Sistema attivo"

        # Simulate the logic from main application
        if hasattr(self, 'unified_time_label'):
            current_time = self.unified_time_label.text().split(' ')[1] if len(self.unified_time_label.text().split(' ')) > 1 else ""
            if current_time:
                self.unified_time_label.setText(f"⌚️ {current_time} | {status_text}")
            else:
                self.unified_time_label.setText(f"⌚️ {status_text}")

        self.status_label.setText("Status update test completed")

    def test_time_update(self):
        """Test time update with actual time"""
        from datetime import datetime
        now = datetime.now()
        time_str = now.strftime("%H:%M")

        # Simulate time update
        if hasattr(self, 'unified_time_label'):
            current_time = self.unified_time_label.text().split(' ')[1] if len(self.unified_time_label.text().split(' ')) > 1 else ""
            if current_time:
                self.unified_time_label.setText(f"⌚️ {time_str} | Sistema attivo")
            else:
                self.unified_time_label.setText(f"⌚️ {time_str} | Sistema attivo")

        self.status_label.setText(f"Time update test completed: {time_str}")

def main():
    """Main test function"""
    app = QApplication(sys.argv)

    # Create test window
    test_window = TestTimeDisplay()
    test_window.show()

    print("Test application started successfully!")
    print("Testing time display without dashes...")

    # Run the application
    sys.exit(app.exec())

if __name__ == "__main__":
    main()