#!/usr/bin/env python3
"""
User Authentication and Authorization Manager
Sistema di gestione utenti, gruppi e permessi per DSA Assistant
"""

import sqlite3
import hashlib
import os
import json
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Union, Any
from dataclasses import dataclass


class User:
    """Classe per rappresentare un utente"""

    def __init__(
        self,
        id,
        username,
        full_name,
        email,
        group_id,
        is_active,
        created_at,
        last_login=None,
    ):
        self.id = id
        self.username = username
        self.full_name = full_name
        self.email = email
        self.group_id = group_id
        self.is_active = is_active
        self.created_at = created_at
        self.last_login = last_login


@dataclass
class UserGroup:
    """Classe per rappresentare un gruppo di utenti"""

    id: int
    name: str
    description: str
    permissions: Dict[str, bool]


class UserAuthManager:
    """Gestore dell'autenticazione e autorizzazione utenti"""

    def __init__(self, db_path=None):
        if db_path is None:
            # Percorso predefinito per il database
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            db_dir = os.path.join(base_dir, "Save", "DATABASE")
            os.makedirs(db_dir, exist_ok=True)
            db_path = os.path.join(db_dir, "users.db")

        self.db_path = db_path
        self._setup_validation_patterns()

    def _setup_validation_patterns(self):
        """Imposta i pattern di validazione per input sicuri."""
        self.validation_patterns = {
            'username': re.compile(r'^[a-zA-Z0-9_-]{3,30}$'),
            'email': re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'),
            'password': re.compile(r'^.{8,128}$'),
        }

    def _validate_username(self, username: str) -> bool:
        """Valida username con controlli di sicurezza."""
        if not username or not isinstance(username, str):
            return False
        username = username.strip()
        return bool(self.validation_patterns['username'].match(username))

    def _validate_email(self, email: str) -> bool:
        """Valida email con controlli di sicurezza."""
        if not email or not isinstance(email, str):
            return False
        email = email.strip().lower()
        return bool(self.validation_patterns['email'].match(email))

    def _validate_password(self, password: str) -> bool:
        """Valida password con controlli di complessità."""
        if not password or not isinstance(password, str):
            return False
        if len(password) < 8:
            return False

        # Controlla complessità minima
        has_upper = bool(re.search(r'[A-Z]', password))
        has_lower = bool(re.search(r'[a-z]', password))
        has_digit = bool(re.search(r'[0-9]', password))

        return has_upper and has_lower and has_digit

    def _sanitize_input(self, input_str: str, max_length: int = 1000) -> str:
        """Sanitizza input rimuovendo caratteri pericolosi."""
        if not isinstance(input_str, str):
            return ""
        # Rimuovi caratteri null e di controllo
        sanitized = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', input_str)
        # Limita lunghezza
        return sanitized.strip()[:max_length]
        if db_path is None:
            # Percorso predefinito per il database
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            db_dir = os.path.join(base_dir, "Save", "DATABASE")
            os.makedirs(db_dir, exist_ok=True)
            db_path = os.path.join(db_dir, "users.db")

        self.db_path = db_path
        self._initialize_database()

    def _initialize_database(self):
        """Inizializza il database e crea le tabelle se non esistono"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Tabella utenti
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    full_name TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    group_id INTEGER NOT NULL,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TEXT NOT NULL,
                    last_login TEXT,
                    login_attempts INTEGER DEFAULT 0,
                    locked_until TEXT,
                    FOREIGN KEY (group_id) REFERENCES user_groups (id)
                )
            """
            )

            # Tabella gruppi
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS user_groups (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    description TEXT,
                    permissions TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """
            )

            # Tabella log accessi
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS access_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    action TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    ip_address TEXT,
                    user_agent TEXT,
                    success BOOLEAN DEFAULT 1,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """
            )

            conn.commit()

            # Crea gruppi predefiniti se non esistono
            self._create_default_groups()

    def _create_default_groups(self):
        """Crea i gruppi predefiniti con i relativi permessi"""
        default_groups = [
            {
                "name": "Administrator",
                "description": "Amministratore completo del sistema",
                "permissions": {
                    "system_access": True,
                    "user_management": True,
                    "settings_management": True,
                    "ai_access": True,
                    "file_management": True,
                    "network_access": True,
                    "debug_tools": True,
                },
            },
            {
                "name": "Teacher",
                "description": "Insegnante con accesso alle funzionalità didattiche",
                "permissions": {
                    "system_access": True,
                    "user_management": False,
                    "settings_management": False,
                    "ai_access": True,
                    "file_management": True,
                    "network_access": True,
                    "debug_tools": False,
                },
            },
            {
                "name": "Student",
                "description": "Studente con accesso limitato",
                "permissions": {
                    "system_access": True,
                    "user_management": False,
                    "settings_management": False,
                    "ai_access": True,
                    "file_management": True,
                    "network_access": False,
                    "debug_tools": False,
                },
            },
            {
                "name": "Guest",
                "description": "Accesso ospite limitato",
                "permissions": {
                    "system_access": True,
                    "user_management": False,
                    "settings_management": False,
                    "ai_access": False,
                    "file_management": False,
                    "network_access": False,
                    "debug_tools": False,
                },
            },
        ]

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            for group in default_groups:
                # Verifica se il gruppo esiste già
                cursor.execute(
                    "SELECT id FROM user_groups WHERE name = ?", (group["name"],)
                )
                if not cursor.fetchone():
                    cursor.execute(
                        """
                        INSERT INTO user_groups (name, description, permissions, created_at)
                        VALUES (?, ?, ?, ?)
                    """,
                        (
                            group["name"],
                            group["description"],
                            json.dumps(group["permissions"]),
                            datetime.now().isoformat(),
                        ),
                    )

            conn.commit()

    def _hash_password(self, password: str) -> str:
        """Hash della password con salt"""
        salt = os.urandom(32)
        key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000)
        return salt.hex() + key.hex()

    def _verify_password(self, password: str, hash: str) -> bool:
        """Verifica la password"""
        try:
            salt = bytes.fromhex(hash[:64])
            key = bytes.fromhex(hash[64:])
            new_key = hashlib.pbkdf2_hmac(
                "sha256", password.encode("utf-8"), salt, 100000
            )
            return key == new_key
        except (ValueError, TypeError):
            return False

    def create_user(
        self,
        username: str,
        password: str,
        full_name: str,
        email: str,
        group_name: str = "Student",
    ) -> bool:
        """Crea un nuovo utente con validazione sicura"""
        try:
            # Validazione input sicura
            if not self._validate_username(username):
                print("❌ Username non valido")
                return False

            if not self._validate_email(email):
                print("❌ Email non valida")
                return False

            if not self._validate_password(password):
                print("❌ Password non valida (deve contenere maiuscole, minuscole e numeri)")
                return False

            # Sanitizza input
            username = self._sanitize_input(username, 30)
            full_name = self._sanitize_input(full_name, 100)
            email = self._sanitize_input(email.lower(), 254)

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Verifica se l'utente esiste già
                cursor.execute(
                    "SELECT id FROM users WHERE username = ? OR email = ?",
                    (username, email),
                )
                if cursor.fetchone():
                    return False

                # Ottieni l'ID del gruppo
                cursor.execute(
                    "SELECT id FROM user_groups WHERE name = ?", (group_name,)
                )
                group_row = cursor.fetchone()
                if not group_row:
                    return False

                group_id = group_row[0]
                password_hash = self._hash_password(password)

                # Crea l'utente
                cursor.execute(
                    """
                    INSERT INTO users (username, password_hash, full_name, email, group_id, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """,
                    (
                        username,
                        password_hash,
                        full_name,
                        email,
                        group_id,
                        datetime.now().isoformat(),
                    ),
                )

                conn.commit()
                return True

        except sqlite3.Error:
            return False

    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Autentica un utente e restituisce i suoi dati"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Ottieni i dati dell'utente
                cursor.execute(
                    """
                    SELECT u.id, u.username, u.password_hash, u.full_name, u.email,
                           u.group_id, u.is_active, u.created_at, u.last_login,
                           u.login_attempts, u.locked_until
                    FROM users u
                    WHERE u.username = ?
                """,
                    (username,),
                )

                row = cursor.fetchone()
                if not row:
                    return None

                (
                    user_id,
                    db_username,
                    password_hash,
                    full_name,
                    email,
                    group_id,
                    is_active,
                    created_at,
                    last_login,
                    login_attempts,
                    locked_until,
                ) = row

                # Verifica se l'utente è attivo
                if not is_active:
                    return None

                # Verifica se l'account è bloccato
                if (
                    locked_until
                    and datetime.fromisoformat(locked_until) > datetime.now()
                ):
                    return None

                # Verifica la password
                if not self._verify_password(password, password_hash):
                    # Incrementa i tentativi di login falliti
                    new_attempts = login_attempts + 1
                    if new_attempts >= 5:
                        # Blocca l'account per 15 minuti
                        locked_until = (datetime.now().replace(minute=15)).isoformat()
                        cursor.execute(
                            """
                            UPDATE users SET login_attempts = ?, locked_until = ? WHERE id = ?
                        """,
                            (new_attempts, locked_until, user_id),
                        )
                    else:
                        cursor.execute(
                            """
                            UPDATE users SET login_attempts = ? WHERE id = ?
                        """,
                            (new_attempts, user_id),
                        )
                    conn.commit()
                    return None

                # Login riuscito - resetta i tentativi e aggiorna last_login
                cursor.execute(
                    """
                    UPDATE users SET login_attempts = 0, locked_until = NULL, last_login = ? WHERE id = ?
                """,
                    (datetime.now().isoformat(), user_id),
                )

                # Registra l'accesso nel log
                cursor.execute(
                    """
                    INSERT INTO access_logs (user_id, action, timestamp, success)
                    VALUES (?, ?, ?, ?)
                """,
                    (user_id, "login", datetime.now().isoformat(), True),
                )

                conn.commit()

                return User(
                    id=user_id,
                    username=db_username,
                    full_name=full_name,
                    email=email,
                    group_id=group_id,
                    is_active=is_active,
                    created_at=created_at,
                    last_login=last_login,
                )

        except sqlite3.Error:
            return None

    def get_user_permissions(self, user: User) -> Dict[str, bool]:
        """Ottieni i permessi dell'utente basati sul suo gruppo"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute(
                    "SELECT permissions FROM user_groups WHERE id = ?", (user.group_id,)
                )
                row = cursor.fetchone()
                if row:
                    return json.loads(row[0])
                return {}

        except (sqlite3.Error, json.JSONDecodeError):
            return {}

    def get_all_users(self) -> List[User]:
        """Ottieni tutti gli utenti"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    SELECT id, username, full_name, email, group_id, is_active, created_at, last_login
                    FROM users
                    ORDER BY username
                """
                )

                users = []
                for row in cursor.fetchall():
                    users.append(User(*row))

                return users

        except sqlite3.Error:
            return []

    def get_user_groups(self) -> List[UserGroup]:
        """Ottieni tutti i gruppi"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    SELECT id, name, description, permissions, created_at
                    FROM user_groups
                    ORDER BY name
                """
                )

                groups = []
                for row in cursor.fetchall():
                    groups.append(
                        UserGroup(
                            id=row[0],
                            name=row[1],
                            description=row[2],
                            permissions=json.loads(row[3]),
                        )
                    )

                return groups

        except (sqlite3.Error, json.JSONDecodeError):
            return []

    def create_default_admin(self):
        """Crea un utente amministratore predefinito se non esiste"""
        # Verifica se esiste già un admin
        users = self.get_all_users()
        if any(user.username == "admin" for user in users):
            return

        print("🔐 CONFIGURAZIONE INIZIALE AMMINISTRATORE RICHIESTA")
        print("=" * 60)
        print("⚠️  PRIMA CONFIGURAZIONE SICURA DEL SISTEMA")
        print("🔑 È necessario creare il primo account amministratore")
        print("=" * 60)

        # Richiedi configurazione sicura invece di usare password debole
        try:
            success = self._setup_secure_initial_admin()
            if success:
                print("✅ Configurazione amministratore completata con successo!")
                print("🔒 Sistema pronto per l'uso sicuro")
            else:
                print("❌ Configurazione amministratore fallita")
                print("💡 Riprova o contatta il supporto tecnico")
        except KeyboardInterrupt:
            print("\n❌ Configurazione annullata dall'utente")
        except Exception as e:
            print(f"❌ Errore durante la configurazione: {e}")

    def _setup_secure_initial_admin(self):
        """Configurazione sicura del primo amministratore"""
        import getpass
        import secrets

        while True:
            print("\n👤 CONFIGURAZIONE ACCOUNT AMMINISTRATORE")
            username = input("Username amministratore (default: admin): ").strip()
            if not username:
                username = "admin"

            if len(username) < 3:
                print("❌ Username deve essere di almeno 3 caratteri")
                continue

            # Verifica che l'username non esista già
            users = self.get_all_users()
            if any(user.username == username for user in users):
                print(f"❌ Username '{username}' già esistente")
                continue
            break

        while True:
            try:
                password = getpass.getpass("Password amministratore (min 12 caratteri): ")
                if len(password) < 12:
                    print("❌ Password deve essere di almeno 12 caratteri")
                    continue

                # Verifica complessità password
                has_upper = any(c.isupper() for c in password)
                has_lower = any(c.islower() for c in password)
                has_digit = any(c.isdigit() for c in password)
                has_special = any(not c.isalnum() for c in password)

                if not (has_upper and has_lower and has_digit and has_special):
                    print("❌ Password deve contenere maiuscole, minuscole, numeri e caratteri speciali")
                    continue

                confirm = getpass.getpass("Conferma password: ")
                if password != confirm:
                    print("❌ Le password non corrispondono")
                    continue
                break
            except KeyboardInterrupt:
                print("\n❌ Configurazione annullata")
                return False

        full_name = input("Nome completo amministratore (default: System Administrator): ").strip()
        if not full_name:
            full_name = "System Administrator"

        email = input("Email amministratore (default: admin@dsassistant.local): ").strip()
        if not email:
            email = "admin@dsassistant.local"

        # Crea l'utente con password sicura
        success = self.create_user(
            username=username,
            password=password,
            full_name=full_name,
            email=email,
            group_name="Administrator",
        )

        if success:
            print(f"\n✅ Amministratore creato con successo!")
            print(f"👤 Username: {username}")
            print(f"📧 Email: {email}")
            print(f"👥 Gruppo: Administrator")
            print("\n🔐 CONSIGLI DI SICUREZZA:")
            print("- Cambia regolarmente la password")
            print("- Non condividere le credenziali")
            print("- Usa password uniche per account diversi")
            return True
        else:
            print("❌ Errore nella creazione dell'amministratore")
            return False

    def change_password(
        self, user_id: int, old_password: str, new_password: str
    ) -> bool:
        """Cambia la password di un utente"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Verifica la password attuale
                cursor.execute(
                    "SELECT password_hash FROM users WHERE id = ?", (user_id,)
                )
                row = cursor.fetchone()
                if not row or not self._verify_password(old_password, row[0]):
                    return False

                # Aggiorna la password
                new_hash = self._hash_password(new_password)
                cursor.execute(
                    """
                    UPDATE users SET password_hash = ? WHERE id = ?
                """,
                    (new_hash, user_id),
                )

                conn.commit()
                return True

        except sqlite3.Error:
            return False

    def get_access_logs(self, limit: int = 100) -> List[Dict]:
        """Ottieni i log degli accessi"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    SELECT a.timestamp, u.username, a.action, a.success, a.ip_address
                    FROM access_logs a
                    LEFT JOIN users u ON a.user_id = u.id
                    ORDER BY a.timestamp DESC
                    LIMIT ?
                """,
                    (limit,),
                )

                logs = []
                for row in cursor.fetchall():
                    logs.append(
                        {
                            "timestamp": row[0],
                            "username": row[1] or "Unknown",
                            "action": row[2],
                            "success": bool(row[3]),
                            "ip_address": row[4],
                        }
                    )

                return logs

        except sqlite3.Error:
            return []


# Istanza globale del gestore autenticazione
auth_manager = UserAuthManager()


def get_auth_manager() -> UserAuthManager:
    """Restituisce l'istanza globale del gestore autenticazione"""
    return auth_manager


def initialize_auth_system():
    """Inizializza il sistema di autenticazione"""
    auth_manager._initialize_database()
    auth_manager.create_default_admin()
