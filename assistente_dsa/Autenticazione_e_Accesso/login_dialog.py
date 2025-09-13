import sys
import os
from typing import cast

# Login Dialog module
# Contains the login dialog class

try:
    from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QFormLayout, QLineEdit, QPushButton
    from PyQt6.QtCore import Qt, QTimer
    from PyQt6.QtGui import QPixmap, QIcon
    pyqt_available = True
except ImportError:
    pyqt_available = False
    print("PyQt6 not available - Login dialog will not function")


class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🔐 DSA Assistant - Login")
        self.setModal(True)
        self.setFixedSize(450, 350)  # Increased size to accommodate logo
        self.authenticated_user = None

        layout = QVBoxLayout(self)

        # Add logo
        logo_label = QLabel()
        logo_path = os.path.join(os.path.dirname(__file__), "ICO-fonts-wallpaper", "ICONA.png")
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
            scaled_pixmap = pixmap.scaled(80, 80, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            logo_label.setPixmap(scaled_pixmap)
        else:
            logo_label.setText("🚀")  # Fallback emoji if logo not found
            logo_label.setStyleSheet("font-size: 48px;")
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_label.setStyleSheet("margin: 10px;")
        layout.addWidget(logo_label)

        title_label = QLabel("🔐 DSA Assistant")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin: 5px; color: #2196F3;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        subtitle_label = QLabel("Autenticazione Richiesta")
        subtitle_label.setStyleSheet("font-size: 12px; color: #666; margin-bottom: 10px;")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle_label)

        form_layout = QFormLayout()
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Inserisci username")
        self.username_input.setStyleSheet("padding: 5px; border: 1px solid #ccc; border-radius: 3px;")
        form_layout.addRow("👤 Username:", self.username_input)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Inserisci password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setStyleSheet("padding: 5px; border: 1px solid #ccc; border-radius: 3px;")
        form_layout.addRow("🔒 Password:", self.password_input)
        layout.addLayout(form_layout)

        buttons_layout = QVBoxLayout()
        self.login_button = QPushButton("🔐 Login")
        self.login_button.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; border: none; border-radius: 5px; padding: 10px; font-size: 14px; font-weight: bold; margin: 5px; } QPushButton:hover { background-color: #45a049; }")
        self.login_button.clicked.connect(self.attempt_login)
        buttons_layout.addWidget(self.login_button)

        self.cancel_button = QPushButton("❌ Annulla")
        self.cancel_button.setStyleSheet("QPushButton { background-color: #f44336; color: white; border: none; border-radius: 5px; padding: 10px; font-size: 14px; font-weight: bold; margin: 5px; } QPushButton:hover { background-color: #da190b; }")
        self.cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(self.cancel_button)
        layout.addLayout(buttons_layout)

        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #f44336; font-size: 12px; margin: 5px;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)

        self.username_input.returnPressed.connect(self.attempt_login)
        self.password_input.returnPressed.connect(self.attempt_login)

        # Add forgot password link
        forgot_password_label = QLabel('<a href="#" style="color: #2196F3; text-decoration: none;">Password dimenticata?</a>')
        forgot_password_label.setStyleSheet("font-size: 11px; margin: 5px;")
        forgot_password_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        forgot_password_label.setOpenExternalLinks(False)
        forgot_password_label.linkActivated.connect(self.show_password_reset)
        layout.addWidget(forgot_password_label)

    def attempt_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()

        if not username or not password:
            self.status_label.setText("❌ Inserisci username e password")
            self.status_label.setStyleSheet("color: #f44336; font-size: 12px;")
            return

        try:
            from auth_manager import AUTH_AVAILABLE, auth_manager
            if AUTH_AVAILABLE and auth_manager:
                user = auth_manager.authenticate(username, password)
                if user:
                    self.status_label.setText(f"✅ Benvenuto, {user['full_name']}!")
                    self.status_label.setStyleSheet("color: #4CAF50; font-size: 12px;")
                    self.authenticated_user = user
                    QTimer.singleShot(1000, self.accept)
                else:
                    self.status_label.setText("❌ Credenziali non valide")
                    self.status_label.setStyleSheet("color: #f44336; font-size: 12px;")
                    self.password_input.clear()
                    self.password_input.setFocus()
            else:
                self.status_label.setText("❌ Sistema di autenticazione non disponibile")
                self.status_label.setStyleSheet("color: #f44336; font-size: 12px;")
        except ImportError:
            self.status_label.setText("❌ Errore caricamento autenticazione")
            self.status_label.setStyleSheet("color: #f44336; font-size: 12px;")

    def show_password_reset(self):
        """Show password reset dialog"""
        try:
            from password_reset_dialog import PasswordResetDialog
            reset_dialog = PasswordResetDialog(self)
            reset_dialog.exec()
        except ImportError:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(
                self,
                "Funzionalità non disponibile",
                "La funzionalità di reset password non è ancora implementata.\n\nContatta l'amministratore per assistenza."
            )