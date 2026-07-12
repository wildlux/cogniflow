import sys
import os
import secrets
import string
from typing import cast

# Password Reset Dialog module
# Contains the password reset functionality

try:
    from PyQt6.QtWidgets import (
        QDialog, QVBoxLayout, QLabel, QFormLayout, QLineEdit,
        QPushButton, QMessageBox, QHBoxLayout, QProgressBar
    )
    from PyQt6.QtCore import Qt, QTimer
    pyqt_available = True
except ImportError:
    pyqt_available = False
    print("PyQt6 not available - Password reset dialog will not function")


class PasswordResetDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🔑 Reset Password - DSA Assistant")
        self.setModal(True)
        self.setFixedSize(400, 300)

        self.reset_code = None
        self.user_email = None
        self.step = 1  # 1: email input, 2: code verification, 3: new password

        self.setup_ui()

    def setup_ui(self):
        """Setup the UI based on current step"""
        # Clear existing layout
        if self.layout():
            while self.layout().count():
                child = self.layout().takeAt(0)
                if child.widget():
                    child.widget().deleteLater()

        layout = QVBoxLayout(self)

        # Title
        title_label = QLabel("🔑 Reset Password")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px; color: #2196F3;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        if self.step == 1:
            self.setup_email_step(layout)
        elif self.step == 2:
            self.setup_code_step(layout)
        elif self.step == 3:
            self.setup_password_step(layout)

        # Close button
        close_button = QPushButton("❌ Chiudi")
        close_button.clicked.connect(self.reject)
        layout.addWidget(close_button)

    def setup_email_step(self, layout):
        """Setup email input step"""
        desc_label = QLabel("Inserisci la tua email per ricevere un codice di reset:")
        desc_label.setStyleSheet("font-size: 12px; margin: 5px;")
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(desc_label)

        form_layout = QFormLayout()
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("esempio@email.com")
        self.email_input.setStyleSheet("padding: 5px; border: 1px solid #ccc; border-radius: 3px;")
        form_layout.addRow("📧 Email:", self.email_input)
        layout.addLayout(form_layout)

        send_button = QPushButton("📤 Invia Codice")
        send_button.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; border: none; border-radius: 5px; padding: 10px; font-size: 12px; font-weight: bold; margin: 5px; } QPushButton:hover { background-color: #45a049; }")
        send_button.clicked.connect(self.send_reset_code)
        layout.addWidget(send_button)

    def setup_code_step(self, layout):
        """Setup code verification step"""
        desc_label = QLabel(f"Inserisci il codice ricevuto via email per {self.user_email}:")
        desc_label.setStyleSheet("font-size: 12px; margin: 5px;")
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(desc_label)

        form_layout = QFormLayout()
        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("123456")
        self.code_input.setStyleSheet("padding: 5px; border: 1px solid #ccc; border-radius: 3px;")
        self.code_input.setMaxLength(6)
        form_layout.addRow("🔢 Codice:", self.code_input)
        layout.addLayout(form_layout)

        buttons_layout = QHBoxLayout()
        resend_button = QPushButton("🔄 Invia Nuovo Codice")
        resend_button.clicked.connect(self.send_reset_code)
        buttons_layout.addWidget(resend_button)

        verify_button = QPushButton("✅ Verifica Codice")
        verify_button.setStyleSheet("QPushButton { background-color: #2196F3; color: white; border: none; border-radius: 5px; padding: 10px; font-size: 12px; font-weight: bold; margin: 5px; } QPushButton:hover { background-color: #1976D2; }")
        verify_button.clicked.connect(self.verify_code)
        buttons_layout.addWidget(verify_button)

        layout.addLayout(buttons_layout)

    def setup_password_step(self, layout):
        """Setup new password step"""
        desc_label = QLabel("Inserisci la nuova password:")
        desc_label.setStyleSheet("font-size: 12px; margin: 5px;")
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(desc_label)

        form_layout = QFormLayout()
        self.new_password_input = QLineEdit()
        self.new_password_input.setPlaceholderText("Nuova password (min 8 caratteri)")
        self.new_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.new_password_input.setStyleSheet("padding: 5px; border: 1px solid #ccc; border-radius: 3px;")
        form_layout.addRow("🔒 Password:", self.new_password_input)

        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setPlaceholderText("Conferma password")
        self.confirm_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_password_input.setStyleSheet("padding: 5px; border: 1px solid #ccc; border-radius: 3px;")
        form_layout.addRow("🔒 Conferma:", self.confirm_password_input)
        layout.addLayout(form_layout)

        reset_button = QPushButton("🔄 Reset Password")
        reset_button.setStyleSheet("QPushButton { background-color: #FF9800; color: white; border: none; border-radius: 5px; padding: 10px; font-size: 12px; font-weight: bold; margin: 5px; } QPushButton:hover { background-color: #F57C00; }")
        reset_button.clicked.connect(self.reset_password)
        layout.addWidget(reset_button)

    def send_reset_code(self):
        """Send reset code to user's email"""
        if self.step == 1:
            email = self.email_input.text().strip()
        else:
            email = self.user_email

        if not email:
            QMessageBox.warning(self, "Errore", "Inserisci un indirizzo email valido.")
            return

        # Check if user exists
        try:
            from auth_manager import auth_manager
            if email not in auth_manager.users:
                QMessageBox.warning(self, "Errore", "Email non trovata nel sistema.")
                return

            user = auth_manager.users[email]
            if not user.get('email'):
                QMessageBox.warning(self, "Errore", "Questo account non ha un'email associata.")
                return

        except ImportError:
            QMessageBox.critical(self, "Errore", "Sistema di autenticazione non disponibile.")
            return

        # Generate reset code
        self.reset_code = ''.join(secrets.choice(string.digits) for _ in range(6))
        self.user_email = email

        # In a real implementation, this would send an email
        # For now, we'll show it in a message box for testing
        QMessageBox.information(
            self,
            "Codice di Reset",
            f"Codice di reset inviato a {email}\n\nCodice: {self.reset_code}\n\n(In produzione questo sarebbe inviato via email)"
        )

        self.step = 2
        self.setup_ui()

    def verify_code(self):
        """Verify the reset code"""
        entered_code = self.code_input.text().strip()

        if not entered_code:
            QMessageBox.warning(self, "Errore", "Inserisci il codice di reset.")
            return

        if entered_code == self.reset_code:
            self.step = 3
            self.setup_ui()
        else:
            QMessageBox.warning(self, "Errore", "Codice non valido. Riprova.")

    def reset_password(self):
        """Reset the user's password"""
        new_password = self.new_password_input.text().strip()
        confirm_password = self.confirm_password_input.text().strip()

        if not new_password or len(new_password) < 8:
            QMessageBox.warning(self, "Errore", "La password deve essere di almeno 8 caratteri.")
            return

        if new_password != confirm_password:
            QMessageBox.warning(self, "Errore", "Le password non corrispondono.")
            return

        try:
            from auth_manager import auth_manager
            if self.user_email in auth_manager.users:
                # Hash the new password
                hashed_password = auth_manager._hash_password_secure(new_password)
                auth_manager.users[self.user_email]['password_hash'] = hashed_password
                auth_manager._save_users()

                QMessageBox.information(
                    self,
                    "Successo",
                    "Password resettata con successo!\n\nOra puoi accedere con la nuova password."
                )
                self.accept()
            else:
                QMessageBox.critical(self, "Errore", "Utente non trovato.")

        except ImportError:
            QMessageBox.critical(self, "Errore", "Impossibile salvare la nuova password.")