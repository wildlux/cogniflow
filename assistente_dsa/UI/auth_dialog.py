#!/usr/bin/env python3
"""
Dialog per l'autenticazione utenti
Interfaccia grafica per login e gestione utenti
"""

import sys
import os
from datetime import datetime
from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QMessageBox,
    QTabWidget,
    QWidget,
    QTableWidget,
    QTableWidgetItem,
    QFormLayout,
    QComboBox,
    QGroupBox,
    QTextEdit,
    QProgressBar,
    QCheckBox,
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QIcon

# Import del sistema di autenticazione
try:
    from core.user_auth_manager import get_auth_manager, User, UserGroup

    AUTH_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Sistema di autenticazione non disponibile: {e}")
    AUTH_AVAILABLE = False
    get_auth_manager = None
    User = None
    UserGroup = None


class LoginDialog(QDialog):
    """Dialog per il login degli utenti"""

    def __init__(self):
        super().__init__()
        self.auth_manager = (
            get_auth_manager() if AUTH_AVAILABLE and get_auth_manager else None
        )
        self.current_user = None

        self.setWindowTitle("DSA Assistant - Autenticazione")
        self.setModal(True)
        self.setFixedSize(400, 300)
        self.setStyleSheet(
            """
            QDialog {
                background-color: #f5f5f5;
                border-radius: 10px;
            }
            QLabel {
                color: #333;
                font-size: 12px;
            }
            QLineEdit {
                padding: 8px;
                border: 1px solid #ccc;
                border-radius: 5px;
                font-size: 12px;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3e8e41;
            }
        """
        )

        self.setup_ui()

    def setup_ui(self):
        """Configura l'interfaccia utente"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Titolo
        title_label = QLabel("🔐 DSA Assistant Login")
        title_label.setStyleSheet(
            "font-size: 18px; font-weight: bold; color: #333; margin-bottom: 10px;"
        )
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # Form login
        form_layout = QFormLayout()

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Inserisci username")
        form_layout.addRow("Username:", self.username_input)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Inserisci password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        form_layout.addRow("Password:", self.password_input)

        layout.addLayout(form_layout)

        # Checkbox per mostrare/nascondere password
        self.show_password_cb = QCheckBox("Mostra password")
        self.show_password_cb.stateChanged.connect(self.toggle_password_visibility)
        layout.addWidget(self.show_password_cb)

        # Pulsante login
        self.login_button = QPushButton("🔑 Login")
        self.login_button.clicked.connect(self.attempt_login)
        layout.addWidget(self.login_button)

        # Status label
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #d32f2f; font-size: 11px;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)

        # Pulsante gestione utenti (solo per admin)
        self.manage_users_button = QPushButton("👥 Gestisci Utenti")
        self.manage_users_button.clicked.connect(self.open_user_management)
        self.manage_users_button.hide()  # Nascosto di default
        layout.addWidget(self.manage_users_button)

        # Connetti eventi
        self.username_input.returnPressed.connect(self.attempt_login)
        self.password_input.returnPressed.connect(self.attempt_login)

    def toggle_password_visibility(self):
        """Mostra/nasconde la password"""
        if self.show_password_cb.isChecked():
            self.password_input.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.password_input.setEchoMode(QLineEdit.EchoMode.Password)

    def attempt_login(self):
        """Tentativo di login"""
        if not AUTH_AVAILABLE or not self.auth_manager:
            QMessageBox.warning(
                self, "Errore", "Sistema di autenticazione non disponibile"
            )
            return

        username = self.username_input.text().strip()
        password = self.password_input.text().strip()

        if not username or not password:
            self.status_label.setText("❌ Inserisci username e password")
            return

        self.login_button.setEnabled(False)
        self.login_button.setText("🔄 Autenticazione...")
        self.status_label.setText("")

        # Tentativo di autenticazione
        user = self.auth_manager.authenticate_user(username, password)

        if user:
            self.current_user = user
            if self.auth_manager:
                permissions = self.auth_manager.get_user_permissions(user)

                # Mostra pulsante gestione utenti se admin
                if permissions.get("user_management", False):
                    self.manage_users_button.show()

            self.status_label.setStyleSheet("color: #4caf50; font-size: 11px;")
            self.status_label.setText(f"✅ Benvenuto, {user.full_name}!")

            # Chiudi dialog dopo un breve delay
            QTimer.singleShot(1500, self.accept)
        else:
            self.status_label.setText("❌ Username o password non validi")
            self.login_button.setEnabled(True)
            self.login_button.setText("🔑 Login")

    def open_user_management(self):
        """Apre la finestra di gestione utenti"""
        if not self.current_user:
            return

        permissions = self.auth_manager.get_user_permissions(self.current_user)
        if not permissions.get("user_management", False):
            QMessageBox.warning(
                self, "Accesso Negato", "Non hai i permessi per gestire gli utenti"
            )
            return

        user_mgmt = UserManagementDialog(self.auth_manager, self.current_user)
        user_mgmt.exec()

    def get_current_user(self):
        """Restituisce l'utente attualmente autenticato"""
        return self.current_user


class UserManagementDialog(QDialog):
    """Dialog per la gestione degli utenti"""

    def __init__(self, auth_manager, current_user):
        super().__init__()
        self.auth_manager = auth_manager
        self.current_user = current_user

        self.setWindowTitle("Gestione Utenti - DSA Assistant")
        self.setModal(True)
        self.setFixedSize(800, 600)

        self.setup_ui()
        self.load_users()

    def setup_ui(self):
        """Configura l'interfaccia utente"""
        layout = QVBoxLayout(self)

        # Tabs
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # Tab utenti
        self.users_tab = QWidget()
        self.setup_users_tab()
        self.tabs.addTab(self.users_tab, "👥 Utenti")

        # Tab gruppi
        self.groups_tab = QWidget()
        self.setup_groups_tab()
        self.tabs.addTab(self.groups_tab, "🔒 Gruppi")

        # Tab log
        self.logs_tab = QWidget()
        self.setup_logs_tab()
        self.tabs.addTab(self.logs_tab, "📋 Log Accessi")

        # Pulsanti
        buttons_layout = QHBoxLayout()

        self.refresh_button = QPushButton("🔄 Aggiorna")
        self.refresh_button.clicked.connect(self.load_users)
        buttons_layout.addWidget(self.refresh_button)

        self.close_button = QPushButton("❌ Chiudi")
        self.close_button.clicked.connect(self.accept)
        buttons_layout.addWidget(self.close_button)

        layout.addLayout(buttons_layout)

    def setup_users_tab(self):
        """Configura il tab degli utenti"""
        layout = QVBoxLayout(self.users_tab)

        # Tabella utenti
        self.users_table = QTableWidget()
        self.users_table.setColumnCount(6)
        self.users_table.setHorizontalHeaderLabels(
            ["Username", "Nome Completo", "Email", "Gruppo", "Stato", "Ultimo Accesso"]
        )
        layout.addWidget(self.users_table)

        # Pulsanti azioni
        actions_layout = QHBoxLayout()

        self.add_user_button = QPushButton("➕ Aggiungi Utente")
        self.add_user_button.clicked.connect(self.add_user)
        actions_layout.addWidget(self.add_user_button)

        self.edit_user_button = QPushButton("✏️ Modifica Utente")
        self.edit_user_button.clicked.connect(self.edit_user)
        actions_layout.addWidget(self.edit_user_button)

        self.delete_user_button = QPushButton("🗑️ Elimina Utente")
        self.delete_user_button.clicked.connect(self.delete_user)
        actions_layout.addWidget(self.delete_user_button)

        layout.addLayout(actions_layout)

    def setup_groups_tab(self):
        """Configura il tab dei gruppi"""
        layout = QVBoxLayout(self.groups_tab)

        # Tabella gruppi
        self.groups_table = QTableWidget()
        self.groups_table.setColumnCount(3)
        self.groups_table.setHorizontalHeaderLabels(
            ["Nome Gruppo", "Descrizione", "Permessi"]
        )
        layout.addWidget(self.groups_table)

        # Pulsanti azioni
        actions_layout = QHBoxLayout()

        self.add_group_button = QPushButton("➕ Aggiungi Gruppo")
        self.add_group_button.clicked.connect(self.add_group)
        actions_layout.addWidget(self.add_group_button)

        self.edit_group_button = QPushButton("✏️ Modifica Gruppo")
        self.edit_group_button.clicked.connect(self.edit_group)
        actions_layout.addWidget(self.edit_group_button)

        layout.addLayout(actions_layout)

    def setup_logs_tab(self):
        """Configura il tab dei log"""
        layout = QVBoxLayout(self.logs_tab)

        # Tabella log
        self.logs_table = QTableWidget()
        self.logs_table.setColumnCount(5)
        self.logs_table.setHorizontalHeaderLabels(
            ["Timestamp", "Utente", "Azione", "Successo", "IP"]
        )
        layout.addWidget(self.logs_table)

        # Pulsanti
        actions_layout = QHBoxLayout()

        self.refresh_logs_button = QPushButton("🔄 Aggiorna Log")
        self.refresh_logs_button.clicked.connect(self.load_logs)
        actions_layout.addWidget(self.refresh_logs_button)

        layout.addLayout(actions_layout)

    def load_users(self):
        """Carica la lista degli utenti"""
        if not self.auth_manager:
            return

        users = self.auth_manager.get_all_users()
        groups = {g.id: g.name for g in self.auth_manager.get_user_groups()}

        self.users_table.setRowCount(len(users))

        for row, user in enumerate(users):
            self.users_table.setItem(row, 0, QTableWidgetItem(user.username))
            self.users_table.setItem(row, 1, QTableWidgetItem(user.full_name))
            self.users_table.setItem(row, 2, QTableWidgetItem(user.email))
            self.users_table.setItem(
                row, 3, QTableWidgetItem(groups.get(user.group_id, "Unknown"))
            )
            self.users_table.setItem(
                row, 4, QTableWidgetItem("Attivo" if user.is_active else "Disattivo")
            )
            self.users_table.setItem(row, 5, QTableWidgetItem(user.last_login or "Mai"))

        self.load_groups()
        self.load_logs()

    def load_groups(self):
        """Carica la lista dei gruppi"""
        if not self.auth_manager:
            return

        groups = self.auth_manager.get_user_groups()
        self.groups_table.setRowCount(len(groups))

        for row, group in enumerate(groups):
            self.groups_table.setItem(row, 0, QTableWidgetItem(group.name))
            self.groups_table.setItem(row, 1, QTableWidgetItem(group.description))

            # Mostra permessi come stringa
            permissions_str = ", ".join([k for k, v in group.permissions.items() if v])
            self.groups_table.setItem(row, 2, QTableWidgetItem(permissions_str))

    def load_logs(self):
        """Carica i log degli accessi"""
        if not self.auth_manager:
            return

        logs = self.auth_manager.get_access_logs()
        self.logs_table.setRowCount(len(logs))

        for row, log in enumerate(logs):
            self.logs_table.setItem(row, 0, QTableWidgetItem(log["timestamp"]))
            self.logs_table.setItem(row, 1, QTableWidgetItem(log["username"]))
            self.logs_table.setItem(row, 2, QTableWidgetItem(log["action"]))
            self.logs_table.setItem(
                row, 3, QTableWidgetItem("Sì" if log["success"] else "No")
            )
            self.logs_table.setItem(row, 4, QTableWidgetItem(log["ip_address"] or ""))

    def add_user(self):
        """Aggiunge un nuovo utente"""
        dialog = UserDialog(self.auth_manager)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_users()

    def edit_user(self):
        """Modifica un utente esistente"""
        current_row = self.users_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Selezione", "Seleziona un utente dalla tabella")
            return

        username = self.users_table.item(current_row, 0).text()
        dialog = UserDialog(self.auth_manager, username)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_users()

    def delete_user(self):
        """Elimina un utente"""
        current_row = self.users_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Selezione", "Seleziona un utente dalla tabella")
            return

        username = self.users_table.item(current_row, 0).text()

        if username == self.current_user.username:
            QMessageBox.warning(
                self, "Errore", "Non puoi eliminare il tuo stesso account"
            )
            return

        reply = QMessageBox.question(
            self,
            "Conferma Eliminazione",
            f"Sei sicuro di voler eliminare l'utente '{username}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Nota: Questa funzionalità richiederebbe l'implementazione di un metodo delete_user
            QMessageBox.information(
                self,
                "Info",
                "Funzionalità di eliminazione utente non ancora implementata",
            )

    def add_group(self):
        """Aggiunge un nuovo gruppo"""
        QMessageBox.information(
            self, "Info", "Funzionalità di aggiunta gruppo non ancora implementata"
        )

    def edit_group(self):
        """Modifica un gruppo esistente"""
        QMessageBox.information(
            self, "Info", "Funzionalità di modifica gruppo non ancora implementata"
        )


class UserDialog(QDialog):
    """Dialog per aggiungere/modificare utenti"""

    def __init__(self, auth_manager, username=None):
        super().__init__()
        self.auth_manager = auth_manager
        self.username = username
        self.is_edit = username is not None

        self.setWindowTitle(
            "Aggiungi Utente" if not self.is_edit else f"Modifica Utente: {username}"
        )
        self.setModal(True)
        self.setFixedSize(400, 500)

        self.setup_ui()
        if self.is_edit:
            self.load_user_data()

    def setup_ui(self):
        """Configura l'interfaccia utente"""
        layout = QVBoxLayout(self)

        # Form
        form_group = QGroupBox("Dati Utente")
        form_layout = QFormLayout(form_group)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username univoco")
        form_layout.addRow("Username:", self.username_input)

        self.full_name_input = QLineEdit()
        self.full_name_input.setPlaceholderText("Nome completo")
        form_layout.addRow("Nome Completo:", self.full_name_input)

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("email@esempio.com")
        form_layout.addRow("Email:", self.email_input)

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("Password sicura")
        form_layout.addRow("Password:", self.password_input)

        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_password_input.setPlaceholderText("Conferma password")
        form_layout.addRow("Conferma Password:", self.confirm_password_input)

        # Gruppi
        self.group_combo = QComboBox()
        groups = self.auth_manager.get_user_groups()
        for group in groups:
            self.group_combo.addItem(f"{group.name} - {group.description}", group.id)
        form_layout.addRow("Gruppo:", self.group_combo)

        layout.addWidget(form_group)

        # Pulsanti
        buttons_layout = QHBoxLayout()

        self.save_button = QPushButton("💾 Salva")
        self.save_button.clicked.connect(self.save_user)
        buttons_layout.addWidget(self.save_button)

        self.cancel_button = QPushButton("❌ Annulla")
        self.cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(self.cancel_button)

        layout.addLayout(buttons_layout)

        if self.is_edit:
            self.password_input.setPlaceholderText("Lascia vuoto per mantenere attuale")
            self.confirm_password_input.setPlaceholderText(
                "Lascia vuoto per mantenere attuale"
            )

    def load_user_data(self):
        """Carica i dati dell'utente da modificare"""
        # Questa funzionalità richiederebbe l'implementazione di un metodo get_user_by_username
        QMessageBox.information(
            self, "Info", "Caricamento dati utente non ancora implementato"
        )

    def save_user(self):
        """Salva il nuovo utente o le modifiche"""
        if not self.username_input or not self.full_name_input or not self.email_input:
            QMessageBox.warning(self, "Errore", "Errore nell'interfaccia utente")
            return

        username = self.username_input.text().strip()
        full_name = self.full_name_input.text().strip()
        email = self.email_input.text().strip()
        password = self.password_input.text() if self.password_input else ""
        confirm_password = (
            self.confirm_password_input.text() if self.confirm_password_input else ""
        )
        group_id = self.group_combo.currentData() if self.group_combo else None

        # Validazioni
        if not username or not full_name or not email:
            QMessageBox.warning(self, "Errore", "Compila tutti i campi obbligatori")
            return

        if not self.is_edit and not password:
            QMessageBox.warning(self, "Errore", "Inserisci una password")
            return

        if password != confirm_password:
            QMessageBox.warning(self, "Errore", "Le password non coincidono")
            return

        # Crea utente
        if self.auth_manager.create_user(
            username, password, full_name, email, self.get_group_name_by_id(group_id)
        ):
            QMessageBox.information(
                self,
                "Successo",
                (
                    "Utente creato con successo!"
                    if not self.is_edit
                    else "Utente modificato con successo!"
                ),
            )
            self.accept()
        else:
            QMessageBox.warning(
                self, "Errore", "Errore nella creazione/modifica dell'utente"
            )

    def get_group_name_by_id(self, group_id):
        """Ottieni il nome del gruppo dall'ID"""
        groups = self.auth_manager.get_user_groups()
        for group in groups:
            if group.id == group_id:
                return group.name
        return "Student"


def show_login_dialog():
    """Mostra il dialog di login"""
    if not AUTH_AVAILABLE:
        QMessageBox.warning(None, "Errore", "Sistema di autenticazione non disponibile")
        return None

    dialog = LoginDialog()
    result = dialog.exec()

    if result == QDialog.DialogCode.Accepted:
        return dialog.get_current_user()
    return None


if __name__ == "__main__":
    app = QApplication(sys.argv)
    user = show_login_dialog()
    if user:
        print(f"Login riuscito: {user.full_name} ({user.username})")
    else:
        print("Login fallito o annullato")
