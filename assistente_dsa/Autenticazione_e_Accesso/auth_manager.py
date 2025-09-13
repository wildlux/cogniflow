import os
import json
import hashlib
import datetime
import secrets
from typing import Any, Dict
from .security_utils import encryptor

# Authentication manager module
# Contains user authentication, password hashing, and user management

class SimpleAuthManager:
    data_dir: str
    users_file: str
    users: dict[str, dict[str, Any]]

    def __init__(self):
        self.data_dir = os.path.join(os.path.dirname(__file__), "Save", "AUTH")
        os.makedirs(self.data_dir, exist_ok=True)
        self.users_file = os.path.join(self.data_dir, "users.json")
        self._load_users()

    def _load_users(self):
        if os.path.exists(self.users_file):
            try:
                with open(self.users_file, "r", encoding="utf-8") as f:
                    encrypted_data = f.read()

                # Prova a decrittografare, se fallisce assume che non sia crittografato
                try:
                    decrypted_data = encryptor.decrypt(encrypted_data)
                    self.users = json.loads(decrypted_data)
                except Exception as decrypt_error:
                    # Fallback: assume che i dati non siano crittografati
                    print(f"Decryption failed, trying plain JSON: {decrypt_error}")
                    self.users = json.loads(encrypted_data)

            except Exception as e:
                print(f"Errore caricamento utenti: {type(e).__name__}")
                self.users = {}
        else:
            self.users = {}
            # Crea utente admin predefinito
            self._create_default_admin()

    def _create_default_admin(self):
        # Rimossa password hardcoded - ora richiede setup sicuro
        print("⚠️  ATTENZIONE: Nessun utente amministratore trovato!")
        print("🔧 Eseguire setup sicuro iniziale per creare amministratore")
        print(
            '💡 Comando suggerito: python -c "from auth_manager import SimpleAuthManager; auth = SimpleAuthManager(); auth.setup_secure_admin()"'
        )

        # Crea utente placeholder disabilitato
        admin_user = {
            "username": "admin",
            "password_hash": "",  # Password vuota - richiede setup
            "full_name": "System Administrator",
            "group": "Administrator",
            "is_active": False,  # Disabilitato fino al setup sicuro
            "created_at": datetime.datetime.now().isoformat(),
            "last_login": None,
            "requires_setup": True,
        }
        self.users["admin"] = admin_user
        self._save_users()

    def _save_users(self):
        try:
            # Crittografa i dati prima di salvarli
            users_json = json.dumps(self.users, indent=2, ensure_ascii=False)
            encrypted_data = encryptor.encrypt(users_json)

            with open(self.users_file, "w", encoding="utf-8") as f:
                f.write(encrypted_data)
        except Exception as e:
            print(f"Errore salvataggio utenti: {type(e).__name__}")
            # Fallback: salva senza crittografia se la crittografia fallisce
            try:
                with open(self.users_file, "w", encoding="utf-8") as f:
                    json.dump(self.users, f, indent=2, ensure_ascii=False)
            except Exception as e2:
                print(f"Errore salvataggio fallback: {type(e2).__name__}")

    def _hash_password_secure(self, password: str) -> str:
        """Hash sicuro con salt usando PBKDF2"""
        salt = secrets.token_hex(16)  # 32 caratteri hex = 16 bytes
        key = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000
        )
        return f"{salt}${key.hex()}"

    def _verify_password_secure(self, password: str, hash: str) -> bool:
        """Verifica password con hash sicuro"""
        try:
            salt, key = hash.split("$", 1)
            new_key = hashlib.pbkdf2_hmac(
                "sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000
            )
            return new_key.hex() == key
        except Exception as e:
            print(f"Password verification error: {e}")
            return False

    def authenticate(self, username: str, password: str):
        # Rate limiting per prevenire brute force
        from .security_utils import rate_limiter
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

        # Supporta sia hash vecchio che nuovo per retrocompatibilità
        password_hash = user["password_hash"]
        if password_hash.startswith("$"):  # Nuovo formato con salt
            if not self._verify_password_secure(password, password_hash):
                rate_limiter.record_failure(f"auth_{username}")
                return None
        else:  # Vecchio formato SHA256 (da migrare)
            if password_hash != hashlib.sha256(password.encode()).hexdigest():
                rate_limiter.record_failure(f"auth_{username}")
                return None

        user["last_login"] = datetime.datetime.now().isoformat()
        self._save_users()
        return user

    def setup_secure_admin(self):
        """Setup sicuro dell'amministratore con password complessa tramite GUI"""
        try:
            from PyQt6.QtWidgets import QApplication, QDialog, QMessageBox
            pyqt_available = True
        except ImportError:
            pyqt_available = False

        if not pyqt_available:
            print("❌ PyQt6 non disponibile - setup tramite terminale")
            return self._setup_secure_admin_terminal()

        # Crea applicazione Qt se non esiste
        app = QApplication.instance()  # type: ignore
        if app is None:
            app = QApplication([])  # type: ignore

        # Finestra di setup amministratore
        from gui_components import AdminSetupDialog
        setup_dialog = AdminSetupDialog()
        if setup_dialog.exec() == QDialog.DialogCode.Accepted:  # type: ignore
            admin_data = setup_dialog.get_admin_data()
            if admin_data:
                admin_user = {
                    "username": admin_data["username"],
                    "password_hash": self._hash_password_secure(admin_data["password"]),
                    "full_name": "System Administrator",
                    "group": "Administrator",
                    "is_active": True,
                    "created_at": datetime.datetime.now().isoformat(),
                    "last_login": None,
                    "requires_setup": False,
                }

                self.users[admin_data["username"]] = admin_user
                self._save_users()

                _ = QMessageBox.information(
                    None,  # type: ignore
                    "DSA Assistant - Successo",
                    f"✅ Amministratore '{admin_data['username']}' creato con successo!\n🔒 Password hash sicura implementata"
                )
                return True

        return False

    def _setup_secure_admin_terminal(self):
        """Setup amministratore tramite terminale (fallback)"""
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

        # Crea amministratore sicuro
        admin_user = {
            "username": username,
            "password_hash": self._hash_password_secure(password),
            "full_name": "System Administrator",
            "group": "Administrator",
            "is_active": True,
            "created_at": datetime.datetime.now().isoformat(),
            "last_login": None,
            "requires_setup": False,
        }

        self.users[username] = admin_user
        self._save_users()
        print(f"✅ Amministratore '{username}' creato con successo!")
        print("🔒 Password hash sicura implementata")
        return True

    def get_user_permissions(self, username: str) -> dict[str, bool]:
        user = self.users.get(username)
        if not user:
            return {"system_access": False}
        group = user.get("group", "Guest")
        # Permessi semplificati
        permissions = {
            "Administrator": {
                "system_access": True,
                "user_management": True,
                "ai_access": True,
            },
            "Teacher": {
                "system_access": True,
                "user_management": False,
                "ai_access": True,
            },
            "Student": {
                "system_access": True,
                "user_management": False,
                "ai_access": True,
            },
            "Guest": {
                "system_access": True,
                "user_management": False,
                "ai_access": False,
            },
        }
        return permissions.get(group, {"system_access": False})


AUTH_AVAILABLE = True
auth_manager = SimpleAuthManager()


def get_auth_manager():
    return auth_manager