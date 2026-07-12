"""
Modulo principale delle interfacce grafiche
Importa i dialoghi dai moduli specializzati
"""

import os, json, subprocess
from typing import cast, Optional, Any

try:
    from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, QLabel, QMessageBox
    from PyQt6.QtCore import Qt, QTimer
    pyqt_available = True
except ImportError:
    pyqt_available = False

# Import dei dialoghi dai moduli specializzati
try:
    from .login_dialog import LoginDialog
    from .admin_setup_dialog import AdminSetupDialog
except ImportError:
    from login_dialog import LoginDialog
    from admin_setup_dialog import AdminSetupDialog

class LauncherMainWindow(QMainWindow):
    """Main window for the launcher after login."""
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
        """Avvia l'applicazione principale"""
        try:
            from assistente_dsa.core.auth_module import auth_manager, AUTH_AVAILABLE
            from assistente_dsa.core.security_module import _sanitize_command

            current_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            aircraft_script = os.path.join(current_dir, "main_01_Aircraft.py")

            if not os.path.exists(aircraft_script):
                QMessageBox.critical(self, "Errore", f"Script non trovato: {aircraft_script}")
                return

            env = os.environ.copy()
            if self.authenticated_user:
                env["DSA_USERNAME"] = self.authenticated_user["username"]
                env["DSA_FULL_NAME"] = self.authenticated_user["full_name"]
                env["DSA_GROUP"] = self.authenticated_user.get("group", "Guest")
                if AUTH_AVAILABLE and auth_manager:
                    permissions = auth_manager.get_user_permissions(self.authenticated_user["username"])
                    env["DSA_PERMISSIONS"] = json.dumps(permissions)

            cmd = [os.sys.executable, aircraft_script]
            subprocess.Popen(cmd, cwd=current_dir, env=env)

            self.status_label.setText("✅ Applicazione avviata!")
            self.status_label.setStyleSheet("color: #4CAF50; font-size: 12px;")
            QTimer.singleShot(2000, self.close)

        except Exception as e:
            QMessageBox.critical(self, "Errore", f"Errore avvio applicazione: {str(e)}")
            self.status_label.setText("❌ Errore avvio applicazione")
            self.status_label.setStyleSheet("color: #f44336; font-size: 12px;")

def open_launcher_gui():
    """Open the launcher GUI with authentication or bypass."""
    if not pyqt_available:
        print("❌ PyQt6 not available. Cannot open GUI window.")
        return

    from assistente_dsa.core.config_module import get_setting

    app = QApplication.instance()
    if app is None:
        app = QApplication([])

    bypass_login = cast(bool, get_setting("startup.bypass_login", False))

    if bypass_login:
        print("🔓 Bypass login abilitato - Avvio diretto dell'applicazione principale...")
        current_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        aircraft_script = os.path.join(current_dir, "main_01_Aircraft.py")

        if os.path.exists(aircraft_script):
            cmd = [os.sys.executable, aircraft_script]
            sanitized_cmd = _sanitize_command(cmd)
            try:
                subprocess.Popen(sanitized_cmd, cwd=current_dir)
                print("✅ Applicazione principale avviata con successo")
            except Exception as e:
                print("❌ Errore avvio applicazione principale: Controlla i log per dettagli")
                try:
                    with open(os.path.join(os.path.dirname(os.path.dirname(__file__)), "error.log"), "a") as f:
                        f.write(f"{os.sys.executable}: Errore avvio app - {type(e).__name__}\n")
                except Exception:
                    pass
        else:
            print(f"❌ Script applicazione principale non trovato: {aircraft_script}")
        return

    print("🔐 Bypass login disabilitato - Richiesta autenticazione...")
    login_dialog = LoginDialog()
    result = login_dialog.exec()
    if result == QDialog.DialogCode.Accepted:
        print("✅ Login riuscito - Avvio launcher...")
        window = LauncherMainWindow(login_dialog.authenticated_user)
        window.show()
        app.exec()
    else:
        print("❌ Login annullato o fallito - Applicazione non avviata")
        return

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
            from assistente_dsa.core.auth_module import auth_manager, AUTH_AVAILABLE
            from assistente_dsa.core.security_module import _sanitize_command

            current_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            aircraft_script = os.path.join(current_dir, "main_01_Aircraft.py")

            if not os.path.exists(aircraft_script):
                QMessageBox.critical(self, "Errore", f"Script non trovato: {aircraft_script}")
                return

            env = os.environ.copy()
            if self.authenticated_user:
                env["DSA_USERNAME"] = self.authenticated_user["username"]
                env["DSA_FULL_NAME"] = self.authenticated_user["full_name"]
                env["DSA_GROUP"] = self.authenticated_user.get("group", "Guest")
                if AUTH_AVAILABLE and auth_manager:
                    permissions = auth_manager.get_user_permissions(self.authenticated_user["username"])
                    env["DSA_PERMISSIONS"] = json.dumps(permissions)

            cmd = [os.sys.executable, aircraft_script]
            subprocess.Popen(cmd, cwd=current_dir, env=env)

            self.status_label.setText("✅ Applicazione avviata!")
            self.status_label.setStyleSheet("color: #4CAF50; font-size: 12px;")
            QTimer.singleShot(2000, self.close)

        except Exception as e:
            QMessageBox.critical(self, "Errore", f"Errore avvio applicazione: {str(e)}")
            self.status_label.setText("❌ Errore avvio applicazione")
            self.status_label.setStyleSheet("color: #f44336; font-size: 12px;")

def open_launcher_gui():
    if not pyqt_available:
        print("❌ PyQt6 not available. Cannot open GUI window.")
        return

    from assistente_dsa.core.config_module import get_setting

    app = QApplication.instance()
    if app is None:
        app = QApplication([])

    bypass_login = cast(bool, get_setting("startup.bypass_login", False))

    if bypass_login:
        print("🔓 Bypass login abilitato - Avvio diretto dell'applicazione principale...")
        current_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        aircraft_script = os.path.join(current_dir, "main_01_Aircraft.py")

        if os.path.exists(aircraft_script):
            cmd = [os.sys.executable, aircraft_script]
            sanitized_cmd = _sanitize_command(cmd)
            try:
                subprocess.Popen(sanitized_cmd, cwd=current_dir)
                print("✅ Applicazione principale avviata con successo")
            except Exception as e:
                print("❌ Errore avvio applicazione principale: Controlla i log per dettagli")
                try:
                    with open(os.path.join(os.path.dirname(os.path.dirname(__file__)), "error.log"), "a") as f:
                        f.write(f"{os.sys.executable}: Errore avvio app - {type(e).__name__}\n")
                except Exception:
                    pass
        else:
            print(f"❌ Script applicazione principale non trovato: {aircraft_script}")
        return

    print("🔐 Bypass login disabilitato - Richiesta autenticazione...")
    login_dialog = LoginDialog()
    result = login_dialog.exec()
    if result == QDialog.DialogCode.Accepted:
        print("✅ Login riuscito - Avvio launcher...")
        window = LauncherMainWindow(login_dialog.authenticated_user)
        window.show()
        app.exec()
    else:
        print("❌ Login annullato o fallito - Applicazione non avviata")
        return