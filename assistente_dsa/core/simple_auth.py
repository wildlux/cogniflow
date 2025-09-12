#!/usr/bin/env python3
"""
Sistema di autenticazione semplificato per DSA Assistant
"""

import os
import json
import hashlib
from datetime import datetime
from typing import Dict, Optional


class SimpleAuthManager:
    """Gestore autenticazione semplificato"""

    def __init__(self):
        # Crea directory per i dati se non esiste
        # Path corretto: dalla root del progetto
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        self.data_dir = os.path.join(project_root, "Save", "AUTH")
        os.makedirs(self.data_dir, exist_ok=True)

        self.users_file = os.path.join(self.data_dir, "users.json")
        self.groups_file = os.path.join(self.data_dir, "groups.json")

        self._load_data()

    def _load_data(self):
        """Carica dati utenti e gruppi"""
        # Carica utenti
        if os.path.exists(self.users_file):
            try:
                with open(self.users_file, 'r', encoding='utf-8') as f:
                    self.users = json.load(f)
            except:
                self.users = {}
        else:
            self.users = {}

        # Carica gruppi
        if os.path.exists(self.groups_file):
            try:
                with open(self.groups_file, 'r', encoding='utf-8') as f:
                    self.groups = json.load(f)
            except:
                self.groups = {}
        else:
            self.groups = {}

        # Crea gruppi predefiniti se non esistono
        self._create_default_groups()

        # Crea utente admin se non esiste
        self._create_default_admin()

    def _save_data(self):
        """Salva dati su file"""
        try:
            with open(self.users_file, 'w', encoding='utf-8') as f:
                json.dump(self.users, f, indent=2, ensure_ascii=False)

            with open(self.groups_file, 'w', encoding='utf-8') as f:
                json.dump(self.groups, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Errore salvataggio dati autenticazione: {e}")

    def _create_default_groups(self):
        """Crea gruppi predefiniti"""
        default_groups = {
            "Administrator": {
                "description": "Amministratore completo",
                "permissions": {
                    "system_access": True,
                    "user_management": True,
                    "settings_management": True,
                    "ai_access": True,
                    "file_management": True,
                    "network_access": True,
                    "debug_tools": True
                }
            },
            "Teacher": {
                "description": "Insegnante",
                "permissions": {
                    "system_access": True,
                    "user_management": False,
                    "settings_management": False,
                    "ai_access": True,
                    "file_management": True,
                    "network_access": True,
                    "debug_tools": False
                }
            },
            "Student": {
                "description": "Studente",
                "permissions": {
                    "system_access": True,
                    "user_management": False,
                    "settings_management": False,
                    "ai_access": True,
                    "file_management": True,
                    "network_access": False,
                    "debug_tools": False
                }
            },
            "Guest": {
                "description": "Accesso ospite",
                "permissions": {
                    "system_access": True,
                    "user_management": False,
                    "settings_management": False,
                    "ai_access": False,
                    "file_management": False,
                    "network_access": False,
                    "debug_tools": False
                }
            }
        }

        for group_name, group_data in default_groups.items():
            if group_name not in self.groups:
                self.groups[group_name] = group_data

        self._save_data()

    def _create_default_admin(self):
        """Crea utente amministratore predefinito"""
        if "admin" not in self.users:
            admin_user = {
                "username": "admin",
                "password_hash": self._hash_password("admin123"),
                "full_name": "System Administrator",
                "email": "admin@dsassistant.local",
                "group": "Administrator",
                "is_active": True,
                "created_at": datetime.now().isoformat(),
                "last_login": None,
                "login_attempts": 0,
                "locked_until": None
            }
            self.users["admin"] = admin_user
            self._save_data()
            print("✅ Utente amministratore creato: admin / admin123")

    def _hash_password(self, password: str) -> str:
        """Hash della password"""
        return hashlib.sha256(password.encode()).hexdigest()

    def authenticate(self, username: str, password: str) -> Optional[Dict]:
        """Autentica un utente"""
        if username not in self.users:
            return None

        user = self.users[username]

        if not user.get("is_active", True):
            return None

        # Verifica password
        if user["password_hash"] != self._hash_password(password):
            user["login_attempts"] = user.get("login_attempts", 0) + 1
            self._save_data()
            return None

        # Reset tentativi e aggiorna last_login
        user["login_attempts"] = 0
        user["last_login"] = datetime.now().isoformat()
        self._save_data()

        return user

    def get_user_permissions(self, username: str) -> Dict:
        """Ottieni permessi dell'utente"""
        if username not in self.users:
            return {}

        user = self.users[username]
        group_name = user.get("group", "Guest")

        if group_name not in self.groups:
            return {}

        return self.groups[group_name].get("permissions", {})

    def create_user(self, username: str, password: str, full_name: str, email: str, group: str = "Student") -> bool:
        """Crea un nuovo utente"""
        if username in self.users:
            return False

        if group not in self.groups:
            return False

        new_user = {
            "username": username,
            "password_hash": self._hash_password(password),
            "full_name": full_name,
            "email": email,
            "group": group,
            "is_active": True,
            "created_at": datetime.now().isoformat(),
            "last_login": None,
            "login_attempts": 0,
            "locked_until": None
        }

        self.users[username] = new_user
        self._save_data()
        return True

    def get_all_users(self) -> Dict:
        """Ottieni tutti gli utenti"""
        return self.users

    def get_all_groups(self) -> Dict:
        """Ottieni tutti i gruppi"""
        return self.groups


# Istanza globale
auth_manager = SimpleAuthManager()


def get_auth_manager():
    """Restituisce il gestore autenticazione"""
    return auth_manager


def initialize_auth():
    """Inizializza il sistema di autenticazione"""
    global auth_manager
    auth_manager = SimpleAuthManager()
    return auth_manager