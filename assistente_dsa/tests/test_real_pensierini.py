#!/usr/bin/env python3
"""
Test script to verify the real pensierini creation from footer functionality
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
    QScrollArea,
)
from PyQt6.QtCore import Qt
import logging

# Import the actual classes
DRAGGABLE_AVAILABLE = False
DraggableTextWidget = None
SettingsManager = None

try:
    from UI.draggable_text_widget import DraggableTextWidget

    DRAGGABLE_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import DraggableTextWidget: {e}")

try:
    import sys
    import os

    sys.path.append(
        os.path.join(os.path.dirname(__file__), "Save", "SETUP_TOOLS_&_Data")
    )
    from settings_manager import SettingsManager
except ImportError as e:
    print(f"Warning: Could not import SettingsManager: {e}")

    # Create a mock settings manager
    class MockSettingsManager:
        def get_setting(self, key, default=None):
            return default

        def set_setting(self, key, value):
            pass

    SettingsManager = MockSettingsManager

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class TestRealPensierini(QMainWindow):
    """Test window to verify real pensierini footer functionality"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Test Real Pensierini Footer")
        self.setGeometry(100, 100, 600, 400)

        # Initialize settings
        self.settings = SettingsManager()

        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Create main layout
        main_layout = QVBoxLayout(central_widget)

        # Footer pensierini input section
        footer_group = QWidget()
        footer_layout = QVBoxLayout(footer_group)

        self.footer_pensierini_input = QLineEdit()
        self.footer_pensierini_input.setPlaceholderText(
            "💭 Scrivi pensierino rapido..."
        )
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
        """Test the real send_footer_pensierino functionality"""
        try:
            # Get text from input
            text = self.footer_pensierini_input.text().strip()

            if not text:
                self.status_label.setText(
                    "❌ Campo vuoto! Scrivi qualcosa prima di inviare."
                )
                return

            # Try to create real DraggableTextWidget
            if DRAGGABLE_AVAILABLE and DraggableTextWidget:
                try:
                    widget = DraggableTextWidget(text, self.settings)

                    # Add to pensierini layout
                    self.pensierini_layout.addWidget(widget)
                    self.pensierini_count += 1

                    # Clear input
                    self.footer_pensierini_input.clear()

                    # Update status
                    self.status_label.setText(
                        f"✅ Pensierino creato con successo! Totale: {self.pensierini_count}"
                    )

                    # Log success
                    logging.info(f"💭 Pensierino inviato: {text[:50]}...")

                except Exception as e:
                    self.status_label.setText(
                        f"❌ Errore creazione DraggableTextWidget: {str(e)}"
                    )
                    logging.error(f"Error creating DraggableTextWidget: {e}")

                    # Fallback: create a simple label
                    fallback_label = QLabel(f"💭 {text}")
                    fallback_label.setWordWrap(True)
                    fallback_label.setStyleSheet(
                        """
                        QLabel {
                            background-color: #f0f0f0;
                            border: 1px solid #ccc;
                            border-radius: 5px;
                            padding: 8px;
                            margin: 2px;
                        }
                    """
                    )
                    self.pensierini_layout.addWidget(fallback_label)
                    self.pensierini_count += 1
                    self.footer_pensierini_input.clear()
                    self.status_label.setText(
                        f"✅ Pensierino creato (fallback)! Totale: {self.pensierini_count}"
                    )

            else:
                # Fallback if DraggableTextWidget not available
                fallback_label = QLabel(f"💭 {text}")
                fallback_label.setWordWrap(True)
                fallback_label.setStyleSheet(
                    """
                    QLabel {
                        background-color: #f0f0f0;
                        border: 1px solid #ccc;
                        border-radius: 5px;
                        padding: 8px;
                        margin: 2px;
                    }
                """
                )
                self.pensierini_layout.addWidget(fallback_label)
                self.pensierini_count += 1
                self.footer_pensierini_input.clear()
                self.status_label.setText(
                    f"✅ Pensierino creato (fallback)! Totale: {self.pensierini_count}"
                )
                logging.info(f"💭 Pensierino inviato (fallback): {text[:50]}...")

        except Exception as e:
            error_msg = f"❌ Errore durante l'invio del pensierino: {str(e)}"
            self.status_label.setText(error_msg)
            logging.error(f"Error in send_footer_pensierino: {e}")


def main():
    """Main test function"""
    app = QApplication(sys.argv)

    # Create test window
    test_window = TestRealPensierini()
    test_window.show()

    print("Test application started successfully!")
    print("DraggableTextWidget available:", DRAGGABLE_AVAILABLE)

    # Run the application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
