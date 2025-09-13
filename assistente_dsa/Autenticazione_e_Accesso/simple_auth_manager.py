"""
Modulo dedicato alla gestione dell'autenticazione utente
Contiene la classe SimpleAuthManager e le sue dipendenze
"""

import os
import json
import hashlib
import secrets
from datetime import datetime
from typing import cast, Optional, Any, Dict

try:
    from .security_utils import encryptor, rate_limiter, log_security_event
except ImportError:
    from Autenticazione_e_Accesso.security_utils import encryptor, rate_limiter, log_security_event

class SimpleAuthManager:
    """
    Gestore autenticazione utenti con crittografia sicura
    """

    def __init__(self):
        self.data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Save", "AUTH")
        os.makedirs(self.data_dir, exist_ok=True)
        self.users_file = os.path.join(self.data_dir, "users.json")
        self._load_users()

    def _load_users(self):
        """Carica gli utenti dal file crittografato"""
        if os.path.exists(self.users_file):
            try:
                with open(self.users_file, "r", encoding="utf-8") as f:
                    encrypted_data = f.read()
                try:
                    decrypted_data = encryptor.decrypt(encrypted_data)
                    self.users = json.loads(decrypted_data)
                except Exception:
                    self.users = json.loads(encrypted_data)
            except Exception:
                self.users = {}
        else:
            self.users = {}
            self._create_default_admin()

    def _create_default_admin(self):
        """Crea amministratore predefinito se non esiste"""
        print("⚠️  ATTENZIONE: Nessun utente amministratore trovato!")
        print("🔧 Eseguire setup sicuro iniziale per creare amministratore")
        admin_user = {
            "username": "admin",
            "password_hash": "",
            "full_name": "System Administrator",
            "group": "Administrator",
            "is_active": False,
            "created_at": datetime.now().isoformat(),
            "last_login": None,
            "requires_setup": True,
        }
        self.users["admin"] = admin_user
        self._save_users()

    def _save_users(self):
        """Salva gli utenti in file crittografato"""
        try:
            users_json = json.dumps(self.users, indent=2, ensure_ascii=False)
            encrypted_data = encryptor.encrypt(users_json)
            with open(self.users_file, "w", encoding="utf-8") as f:
                f.write(encrypted_data)
        except Exception:
            try:
                with open(self.users_file, "w", encoding="utf-8") as f:
                    json.dump(self.users, f, indent=2, ensure_ascii=False)
            except Exception:
                pass

    def _hash_password_secure(self, password: str) -> str:
        """Hash sicuro con PBKDF2 e salt"""
        salt = secrets.token_hex(16)
        key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000)
        return f"{salt}${key.hex()}"

    def _verify_password_secure(self, password: str, hash: str) -> bool:
        """Verifica password con hash sicuro"""
        try:
            salt, key = hash.split("$", 1)
            new_key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000)
            return new_key.hex() == key
        except Exception:
            return False

    def authenticate(self, username: str, password: str):
        """Autentica un utente"""
        if not rate_limiter.is_allowed(f"auth_{username}"):
            print("❌ Troppi tentativi di accesso. Riprova più tardi.")
            return None

        if username not in self.users:
            rate_limiter.record_failure(f"auth_{username}")
            return None

        user = self.users[username]
        if not user.get("is_active", True):
            rate_limiter.record_failure(f"auth_{username}")
            return None

        password_hash = user["password_hash"]
        if password_hash.startswith("$"):
            if not self._verify_password_secure(password, password_hash):
                rate_limiter.record_failure(f"auth_{username}")
                return None
        else:
            if password_hash != hashlib.sha256(password.encode()).hexdigest():
                rate_limiter.record_failure(f"auth_{username}")
                return None

        user["last_login"] = datetime.now().isoformat()
        self._save_users()
        return user

    def setup_secure_admin(self):
        """Setup sicuro dell'amministratore"""
        print("🔐 SETUP AMMINISTRATORE SICURO")
        print("================================")

        while True:
            username = input("Username amministratore: ").strip()
            if not username or len(username) < 3:
                print("❌ Username deve essere di almeno 3 caratteri")
                continue
            break

        while True:
            password = input("Password amministratore (min 8 caratteri): ").strip()
            if len(password) < 8:
                print("❌ Password deve essere di almeno 8 caratteri")
                continue
            confirm = input("Conferma password: ").strip()
            if password != confirm:
                print("❌ Password non corrispondono")
                continue
            break

        admin_user = {
            "username": username,
            "password_hash": self._hash_password_secure(password),
            "full_name": "System Administrator",
            "group": "Administrator",
            "is_active": True,
            "created_at": datetime.now().isoformat(),
            "last_login": None,
            "requires_setup": False,
        }

        self.users[username] = admin_user
        self._save_users()
        print(f"✅ Amministratore '{username}' creato con successo!")
        print("🔒 Password hash sicura implementata")
        return True

    def get_user_permissions(self, username: str) -> Dict[str, bool]:
        """Restituisce i permessi dell'utente"""
        user = self.users.get(username)
        if not user:
            return {"system_access": False}
        group = user.get("group", "Guest")
        permissions = {
            "Administrator": {"system_access": True, "user_management": True, "ai_access": True},
            "Teacher": {"system_access": True, "user_management": False, "ai_access": True},
            "Student": {"system_access": True, "user_management": False, "ai_access": True},
            "Guest": {"system_access": True, "user_management": False, "ai_access": False},
        }
        return permissions.get(group, {"system_access": False})

    def create_user(self, username: str, password: str, full_name: str, group: str = "Student") -> bool:
        """Crea un nuovo utente"""
        if username in self.users:
            return False

        user = {
            "username": username,
            "password_hash": self._hash_password_secure(password),
            "full_name": full_name,
            "group": group,
            "is_active": True,
            "created_at": datetime.now().isoformat(),
            "last_login": None,
            "requires_setup": False,
        }

        self.users[username] = user
        self._save_users()
        return True

    def delete_user(self, username: str) -> bool:
        """Elimina un utente"""
        if username not in self.users:
            return False
        del self.users[username]
        self._save_users()
        return True

    def list_users(self) -> Dict[str, Dict[str, Any]]:
        """Restituisce lista degli utenti (senza password)"""
        return {username: {k: v for k, v in user.items() if k != "password_hash"}
                for username, user in self.users.items()}

# Istanza globale
auth_manager = SimpleAuthManager()