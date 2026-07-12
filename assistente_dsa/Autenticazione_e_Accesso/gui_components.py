import sys
import json
import os
from typing import cast

# GUI Components module
# Contains all GUI-related classes and dialogs

try:
    from PyQt6.QtWidgets import (
        QApplication, QDialog, QVBoxLayout, QLabel, QFormLayout,
        QLineEdit, QPushButton, QMainWindow, QWidget, QMessageBox
    )
    from PyQt6.QtCore import Qt, QTimer
    pyqt_available = True
except ImportError:
    pyqt_available = False
    print("PyQt6 not available - GUI components will not function")
    # Don't define dummy classes, just set the flag


# Import LoginDialog from separate module
from login_dialog import LoginDialog


class AdminSetupDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🔐 DSA Assistant - Setup Amministratore")
        self.setModal(True)
        self.setFixedSize(450, 300)

        layout = QVBoxLayout(self)
        title_label = QLabel("🔐 Setup Amministratore Sicuro")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        desc_label = QLabel("Crea un account amministratore sicuro per il sistema")
        desc_label.setStyleSheet("font-size: 12px; color: #666; margin: 5px;")
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(desc_label)

        form_layout = QFormLayout()
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username (min 3 caratteri)")
        self.username_input.setStyleSheet("padding: 5px; border: 1px solid #ccc; border-radius: 3px;")
        form_layout.addRow("👤 Username:", self.username_input)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password (min 8 caratteri)")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setStyleSheet("padding: 5px; border: 1px solid #ccc; border-radius: 3px;")
        form_layout.addRow("🔒 Password:", self.password_input)

        self.confirm_input = QLineEdit()
        self.confirm_input.setPlaceholderText("Conferma password")
        self.confirm_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_input.setStyleSheet("padding: 5px; border: 1px solid #ccc; border-radius: 3px;")
        form_layout.addRow("🔒 Conferma:", self.confirm_input)
        layout.addLayout(form_layout)

        buttons_layout = QVBoxLayout()
        self.create_button = QPushButton("✅ Crea Amministratore")
        self.create_button.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; border: none; border-radius: 5px; padding: 10px; font-size: 14px; font-weight: bold; margin: 5px; } QPushButton:hover { background-color: #45a049; }")
        self.create_button.clicked.connect(self.validate_and_create)
        buttons_layout.addWidget(self.create_button)

        self.cancel_button = QPushButton("❌ Annulla")
        self.cancel_button.setStyleSheet("QPushButton { background-color: #f44336; color: white; border: none; border-radius: 5px; padding: 10px; font-size: 14px; font-weight: bold; margin: 5px; } QPushButton:hover { background-color: #da190b; }")
        self.cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(self.cancel_button)
        layout.addLayout(buttons_layout)

        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #f44336; font-size: 12px; margin: 5px;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)

        self.username_input.returnPressed.connect(self.validate_and_create)
        self.password_input.returnPressed.connect(self.validate_and_create)
        self.confirm_input.returnPressed.connect(self.validate_and_create)
        self.admin_data = None

    def validate_and_create(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        confirm = self.confirm_input.text().strip()

        if not username or len(username) < 3:
            self.status_label.setText("❌ Username deve essere di almeno 3 caratteri")
            self.status_label.setStyleSheet("color: #f44336; font-size: 12px;")
            self.username_input.setFocus()
            return

        if len(password) < 8:
            self.status_label.setText("❌ Password deve essere di almeno 8 caratteri")
            self.status_label.setStyleSheet("color: #f44336; font-size: 12px;")
            self.password_input.setFocus()
            return

        if password != confirm:
            self.status_label.setText("❌ Le password non corrispondono")
            self.status_label.setStyleSheet("color: #f44336; font-size: 12px;")
            self.confirm_input.clear()
            self.confirm_input.setFocus()
            return

        self.admin_data = {"username": username, "password": password}
        self.status_label.setText("✅ Amministratore creato con successo!")
        self.status_label.setStyleSheet("color: #4CAF50; font-size: 12px;")
        QTimer.singleShot(1500, self.accept)

    def get_admin_data(self):
        return self.admin_data


class LauncherMainWindow(QMainWindow):
    def __init__(self, authenticated_user=None):
        super().__init__()
        self.authenticated_user = authenticated_user
        self.setWindowTitle("🚀 DSA Assistant Launcher")
        self.setFixedSize(600, 400)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        title_label = QLabel("🚀 DSA Assistant Launcher")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold; margin: 20px;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        if self.authenticated_user:
            user_info = QLabel(f"👤 Utente: {self.authenticated_user['full_name']}\n👥 Gruppo: {self.authenticated_user.get('group', 'N/A')}")
            user_info.setStyleSheet("font-size: 14px; margin: 10px;")
            user_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(user_info)

        self.launch_button = QPushButton("✈️ Avvia Aircraft")
        self.launch_button.setStyleSheet("QPushButton { background-color: #2196F3; color: white; border: none; border-radius: 10px; padding: 15px 30px; font-size: 16px; font-weight: bold; margin: 20px; } QPushButton:hover { background-color: #1976D2; }")
        self.launch_button.clicked.connect(self.launch_application)
        layout.addWidget(self.launch_button)

        self.exit_button = QPushButton("❌ Esci")
        self.exit_button.setStyleSheet("QPushButton { background-color: #757575; color: white; border: none; border-radius: 5px; padding: 10px 20px; font-size: 14px; margin: 10px; } QPushButton:hover { background-color: #616161; }")
        self.exit_button.clicked.connect(self.close)
        layout.addWidget(self.exit_button)

        self.status_label = QLabel("✅ Pronto per l'avvio")
        self.status_label.setStyleSheet("font-size: 12px; color: #4CAF50; margin: 10px;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)

    def launch_application(self):
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            aircraft_script = os.path.join(current_dir, "main_01_Aircraft.py")

            if not os.path.exists(aircraft_script):
                QMessageBox.critical(self, "Errore", f"Script non trovato: {aircraft_script}")
                return

            env = os.environ.copy()
            if self.authenticated_user:
                env["DSA_USERNAME"] = self.authenticated_user["username"]
                env["DSA_FULL_NAME"] = self.authenticated_user["full_name"]
                env["DSA_GROUP"] = self.authenticated_user.get("group", "Guest")
                try:
                    from Autenticazione_e_Accesso.auth_manager import AUTH_AVAILABLE, auth_manager
                    if AUTH_AVAILABLE and auth_manager:
                        permissions = auth_manager.get_user_permissions(self.authenticated_user["username"])
                        env["DSA_PERMISSIONS"] = json.dumps(permissions)
                except ImportError:
                    pass

            import subprocess
            cmd = [sys.executable, aircraft_script]
            subprocess.Popen(cmd, cwd=current_dir, env=env)

            self.status_label.setText("✅ Applicazione avviata!")
            self.status_label.setStyleSheet("color: #4CAF50; font-size: 12px;")
            QTimer.singleShot(2000, self.close)

        except Exception as e:
            QMessageBox.critical(self, "Errore", f"Errore avvio applicazione: {str(e)}")
            self.status_label.setText("❌ Errore avvio applicazione")
            self.status_label.setStyleSheet("color: #f44336; font-size: 12px;")