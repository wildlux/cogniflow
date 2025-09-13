import os
import sys
import json
import hashlib
import datetime
import subprocess
import shlex
import secrets
from typing import Optional, Any, cast

# Security utilities module
# Contains encryption, rate limiting, security checks, and related functions

class SecureEncryptor:
    """
    Encryptor sicuro che usa AES-256 con chiave derivata da password
    """
    def __init__(self, key: Optional[str] = None):
        if key is None:
            # Usa variabile d'ambiente o genera chiave sicura
            key = os.environ.get("DSA_ENCRYPTION_KEY", self._generate_secure_key())

        # Deriva chiave sicura da password usando PBKDF2
        salt = secrets.token_bytes(16)
        self.key = hashlib.pbkdf2_hmac(
            'sha256',
            key.encode('utf-8'),
            salt,
            100000,
            dklen=32
        )
        self.salt = salt

    def _generate_secure_key(self) -> str:
        """Genera una chiave sicura casuale"""
        return secrets.token_hex(32)

    def encrypt(self, data: str) -> str:
        """
        Crittografa i dati usando AES-256-GCM
        """
        try:
            from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
            from cryptography.hazmat.backends import default_backend
            import base64

            # Genera nonce casuale
            nonce = secrets.token_bytes(12)

            # Crea cipher AES-GCM
            cipher = Cipher(
                algorithms.AES(self.key),
                modes.GCM(nonce),
                backend=default_backend()
            )
            encryptor = cipher.encryptor()

            # Crittografa i dati
            data_bytes = data.encode('utf-8')
            ciphertext = encryptor.update(data_bytes) + encryptor.finalize()

            # Combina salt, nonce, tag e ciphertext
            encrypted_data = self.salt + nonce + encryptor.tag + ciphertext
            return base64.b64encode(encrypted_data).decode()

        except ImportError:
            # Fallback se cryptography non è disponibile
            print("⚠️  Cryptography library not available, using simple encryption")
            return self._simple_encrypt(data)
        except Exception as e:
            log_security_event("ENCRYPTION_ERROR", f"Encryption failed: {str(e)}", "ERROR")
            raise ValueError("Encryption failed")

    def decrypt(self, encrypted_data: str) -> str:
        """
        Decrittografa i dati usando AES-256-GCM
        """
        try:
            from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
            from cryptography.hazmat.backends import default_backend
            import base64

            # Decodifica i dati
            encrypted_bytes = base64.b64decode(encrypted_data.encode())

            # Estrai componenti
            if len(encrypted_bytes) < 44:  # 16 salt + 12 nonce + 16 tag minimum
                raise ValueError("Invalid encrypted data format")

            salt = encrypted_bytes[:16]
            nonce = encrypted_bytes[16:28]
            tag = encrypted_bytes[28:44]
            ciphertext = encrypted_bytes[44:]

            # Crea cipher AES-GCM
            cipher = Cipher(
                algorithms.AES(self.key),
                modes.GCM(nonce, tag),
                backend=default_backend()
            )
            decryptor = cipher.decryptor()

            # Decrittografa i dati
            plaintext = decryptor.update(ciphertext) + decryptor.finalize()
            return plaintext.decode('utf-8')

        except ImportError:
            # Fallback se cryptography non è disponibile
            print("⚠️  Cryptography library not available, using simple decryption")
            return self._simple_decrypt(encrypted_data)
        except Exception as e:
            log_security_event("DECRYPTION_ERROR", f"Decryption failed: {str(e)}", "ERROR")
            raise ValueError("Decryption failed")

    def _simple_encrypt(self, data: str) -> str:
        """Metodo di crittografia semplice come fallback"""
        try:
            import base64
            key_bytes = self.key[:32]  # Usa solo primi 32 byte
            data_bytes = data.encode()
            encrypted = bytearray(byte ^ key_bytes[i % len(key_bytes)] for i, byte in enumerate(data_bytes))
            return base64.b64encode(encrypted).decode()
        except Exception as e:
            print(f"Simple encryption error: {e}")
            return data

    def _simple_decrypt(self, encrypted_data: str) -> str:
        """Metodo di decrittografia semplice come fallback"""
        try:
            import base64
            key_bytes = self.key[:32]
            encrypted_bytes = base64.b64decode(encrypted_data.encode())
            decrypted = bytearray(byte ^ key_bytes[i % len(key_bytes)] for i, byte in enumerate(encrypted_bytes))
            return decrypted.decode()
        except Exception as e:
            print(f"Simple decryption error: {e}")
            return encrypted_data


# Mantiene compatibilità con il vecchio nome
class SimpleEncryptor(SecureEncryptor):
    """Alias per compatibilità - usa SecureEncryptor"""
    pass


class SimpleRateLimiter:
    def __init__(self, max_attempts: int = 5, window_seconds: int = 300):
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self.attempts = {}

    def is_allowed(self, key: str) -> bool:
        now = datetime.datetime.now().timestamp()
        key_attempts = [t for t in self.attempts.get(key, []) if now - t < self.window_seconds]
        if len(key_attempts) >= self.max_attempts:
            return False
        key_attempts.append(now)
        self.attempts[key] = key_attempts
        return True

    def record_failure(self, key: str):
        now = datetime.datetime.now().timestamp()
        if key not in self.attempts:
            self.attempts[key] = []
        self.attempts[key].append(now)


def log_security_event(event_type: str, details: str, severity: str = "INFO"):
    """
    Registra eventi di sicurezza in modo sicuro
    """
    # Lista di parole chiave sensibili da proteggere
    sensitive_keywords = [
        "password", "hash", "key", "token", "secret", "private",
        "credential", "auth", "session", "cookie", "jwt"
    ]

    # Protegge i dettagli sensibili
    safe_details = "DETAILS_PROTECTED" if any(
        keyword in details.lower() for keyword in sensitive_keywords
    ) else details

    # Log su console (solo per development)
    if os.environ.get("DEV_MODE", "false").lower() == "true":
        print(f"[SECURITY {severity}] {event_type}: {safe_details}")

    # Log su file sicuro
    try:
        # Crea directory sicura se non esiste
        log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Save", "LOGS")
        os.makedirs(log_dir, exist_ok=True)

        log_file = os.path.join(log_dir, "security.log")

        # Scrivi in append mode con encoding sicuro
        with open(log_file, "a", encoding="utf-8") as f:
            timestamp = datetime.datetime.now().isoformat()
            log_entry = f"{timestamp} [{severity}] {event_type}: {safe_details}\n"
            f.write(log_entry)

        # Ruota il file di log se diventa troppo grande (max 10MB)
        if os.path.getsize(log_file) > 10 * 1024 * 1024:
            backup_file = f"{log_file}.backup"
            os.rename(log_file, backup_file)
            log_security_event("LOG_ROTATION", f"Security log rotated to {backup_file}", "INFO")

    except Exception as e:
        # Non stampare l'errore per evitare information disclosure
        if os.environ.get("DEV_MODE", "false").lower() == "true":
            print(f"Security logging error: {type(e).__name__}")


def get_health_status():
    return {"status": "limited", "message": "Security systems not available"}


def conditional_decorator(decorator_func, name: str):
    def decorator(func):
        return decorator_func(name)(func) if decorator_func else func
    return decorator


def _sanitize_command(cmd: str | list[str]) -> list[str]:
    """
    Sanitizza i comandi per prevenire injection attacks
    """
    if isinstance(cmd, str):
        # Usa shlex.split per parsing sicuro
        try:
            parts = shlex.split(cmd)
        except ValueError as e:
            log_security_event("COMMAND_SANITIZATION_ERROR", f"Invalid command format: {str(e)}", "WARNING")
            raise ValueError("Invalid command format")

        # Valida ogni parte del comando
        for part in parts:
            if not part or not part.strip():
                raise ValueError("Empty command part detected")
            # Controlla caratteri pericolosi
            dangerous_chars = [';', '&', '|', '`', '$', '(', ')', '<', '>', '[', ']', '{', '}', '*', '?']
            if any(char in part for char in dangerous_chars):
                log_security_event("COMMAND_SANITIZATION_WARNING", f"Potentially dangerous character in command: {part}", "WARNING")

        return [shlex.quote(part) for part in parts]

    elif isinstance(cmd, list):
        sanitized = []
        for part in cmd:
            part_str = str(part)
            if not part_str or not part_str.strip():
                raise ValueError("Empty command part detected")
            sanitized.append(shlex.quote(part_str))
        return sanitized
    else:
        raise ValueError("Invalid command type")


def check_package(package: str) -> tuple[str, bool]:
    try:
        __import__(package)
        return package, True
    except ImportError:
        return package, False


def validate_input(input_str: str, max_length: int = 1000, allowed_chars: Optional[str] = None) -> bool:
    """
    Valida l'input dell'utente per prevenire injection attacks
    """
    if not isinstance(input_str, str):
        return False

    # Controlla lunghezza massima
    if len(input_str) > max_length:
        log_security_event("INPUT_VALIDATION_ERROR", f"Input too long: {len(input_str)} > {max_length}", "WARNING")
        return False

    # Controlla caratteri permessi se specificati
    if allowed_chars:
        if not all(char in allowed_chars for char in input_str):
            log_security_event("INPUT_VALIDATION_ERROR", "Invalid characters in input", "WARNING")
            return False

    # Controlla pattern pericolosi
    dangerous_patterns = [
        "<script", "javascript:", "onload=", "onerror=",
        "SELECT ", "INSERT ", "UPDATE ", "DELETE ", "DROP ",
        "../../../", "..\\", "passwd", "/etc/"
    ]

    input_lower = input_str.lower()
    for pattern in dangerous_patterns:
        if pattern.lower() in input_lower:
            log_security_event("INPUT_VALIDATION_ERROR", f"Dangerous pattern detected: {pattern}", "ERROR")
            return False

    return True


def generate_secure_token(length: int = 32) -> str:
    """
    Genera un token sicuro per sessioni/autenticazione
    """
    return secrets.token_urlsafe(length)


def hash_password_secure(password: str, salt: Optional[str] = None) -> str:
    """
    Hash sicuro delle password con PBKDF2
    """
    if salt is None:
        salt = secrets.token_hex(16)

    key = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100000,  # Numero di iterazioni
        dklen=32
    )

    return f"pbkdf2_sha256${salt}${key.hex()}"


def verify_password_secure(password: str, hashed_password: str) -> bool:
    """
    Verifica password con hash sicuro
    """
    try:
        method, salt, key = hashed_password.split('$', 2)
        if method != 'pbkdf2_sha256':
            return False

        new_key = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000,
            dklen=32
        )

        return secrets.compare_digest(new_key.hex(), key)
    except (ValueError, IndexError):
        return False


def check_file_permissions(file_path: str) -> dict:
    """
    Controlla i permessi di un file per sicurezza
    """
    try:
        import stat
        st = os.stat(file_path)
        permissions = stat.filemode(st.st_mode)

        # Controlla se il file è leggibile da altri utenti
        world_readable = bool(st.st_mode & stat.S_IROTH)
        world_writable = bool(st.st_mode & stat.S_IWOTH)

        return {
            "permissions": permissions,
            "world_readable": world_readable,
            "world_writable": world_writable,
            "owner_readable": bool(st.st_mode & stat.S_IRUSR),
            "owner_writable": bool(st.st_mode & stat.S_IWUSR),
            "secure": not (world_readable or world_writable)
        }
    except Exception as e:
        log_security_event("FILE_PERMISSION_CHECK_ERROR", f"Failed to check permissions for {file_path}: {str(e)}", "ERROR")
        return {"error": str(e)}


def secure_file_operation(file_path: str, operation: str, data: Optional[str] = None) -> tuple[bool, Optional[str]]:
    """
    Esegue operazioni su file in modo sicuro
    """
    try:
        # Controlla permessi prima dell'operazione
        if os.path.exists(file_path):
            perms = check_file_permissions(file_path)
            if not perms.get("secure", False):
                log_security_event("INSECURE_FILE_OPERATION", f"File {file_path} has insecure permissions", "WARNING")

        # Crea directory se non esiste
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        # Esegue l'operazione
        if operation == "write" and data is not None:
            # Scrivi in modo sicuro con permessi restrittivi
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(data)
            # Imposta permessi sicuri (solo owner può leggere/scrivere)
            os.chmod(file_path, 0o600)

        elif operation == "read":
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            log_security_event("SECURE_FILE_OPERATION", f"Successfully read {file_path}", "INFO")
            return True, content

        elif operation == "delete":
            os.remove(file_path)
            log_security_event("SECURE_FILE_OPERATION", f"Successfully deleted {file_path}", "INFO")
            return True, None

        log_security_event("SECURE_FILE_OPERATION", f"Successfully performed {operation} on {file_path}", "INFO")
        return True, None

    except Exception as e:
        log_security_event("SECURE_FILE_OPERATION_ERROR", f"Failed {operation} on {file_path}: {str(e)}", "ERROR")
        return False, None


def check_dependency_vulnerabilities() -> tuple[bool, list[str]]:
    vulnerabilities = []
    safe = True
    print("🔍 Checking dependency vulnerabilities...")

    vulnerable_packages = {"PyQt6": ["6.0.0", "6.0.1", "6.0.2"], "requests": ["2.20.0", "2.20.1"], "urllib3": ["1.24.0", "1.24.1", "1.24.2"]}

    try:
        result = subprocess.run([sys.executable, "-m", "pip_audit", "--format", "json"], capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            audit_data = json.loads(result.stdout)
            for vuln in audit_data:
                vulnerabilities.append(f"{vuln['name']} {vuln['version']}: {vuln['description']}")
                safe = False
            print("✅ Dependency audit completed using pip-audit")
            return safe, vulnerabilities
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    try:
        from importlib.metadata import distributions
        installed_packages = {dist.name: dist.version for dist in distributions()}
        for package, vulnerable_versions in vulnerable_packages.items():
            if package in installed_packages and installed_packages[package] in vulnerable_versions:
                vulnerabilities.append(f"{package} {installed_packages[package]}: Known vulnerable version")
                safe = False
        print("✅ Manual dependency vulnerability check completed")
        return safe, vulnerabilities
    except Exception as e:
        vulnerabilities.append(f"Could not check vulnerabilities: {e}")
        return False, vulnerabilities


def check_security_headers() -> tuple[bool, list[str]]:
    issues = []
    safe = True
    print("🔍 Checking security configurations...")

    if os.environ.get("PYTHON_ENV") == "development":
        issues.append("Application running in development mode")
        safe = False

    sensitive_files = ["requirements.txt", os.path.join("assistente_dsa", "Save", "AUTH", "users.json"), os.path.join("assistente_dsa", "Save", "SETUP_TOOLS_&_Data", "settings.json")]

    for file_path in sensitive_files:
        if os.path.exists(file_path) and os.name != 'nt':
            import stat
            if os.stat(file_path).st_mode & stat.S_IROTH:
                issues.append(f"File {file_path} is world-readable")
                safe = False

    if os.environ.get("DEBUG") == "true":
        issues.append("Debug mode is enabled")
        safe = False

    return safe, issues


def check_directory(dir_path: str) -> tuple[str, bool]:
    return os.path.basename(dir_path), os.path.exists(dir_path)


def perform_security_checks():
    print("🔍 Performing security and usability checks...")

    if sys.version_info < (3, 8):
        log_security_event("VERSION_CHECK", "Python 3.8+ required", "ERROR")
        print("❌ ERROR: Python 3.8 or higher required")
        return False

    log_security_event("VERSION_CHECK", f"Python {sys.version} detected", "INFO")
    print(f"✅ Python version: {sys.version}")

    try:
        if os.geteuid() == 0:
            log_security_event("PERMISSION_CHECK", "Running as root", "WARNING")
            print("⚠️  WARNING: Running as root - this may pose security risks")
    except AttributeError:
        pass

    try:
        test_file = os.path.join(os.getcwd(), ".test_write")
        with open(test_file, "w") as f:
            f.write("test")
        os.remove(test_file)
        log_security_event("PERMISSION_CHECK", "Write permissions verified", "INFO")
        print("✅ Write permissions verified")
    except Exception as e:
        log_security_event("PERMISSION_CHECK", f"No write permissions: {e}", "ERROR")
        print(f"❌ ERROR: No write permissions in current directory: {e}")
        return False

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    required_dirs = ["Save", "Screenshot", "assistente_dsa"]
    for dir_name in required_dirs:
        dir_path = os.path.join(project_root, dir_name)
        exists = os.path.exists(dir_path)
        if not exists:
            log_security_event("DIRECTORY_CHECK", f"Directory '{dir_name}' missing", "WARNING")
            print(f"⚠️  WARNING: Required directory '{dir_name}' not found")
        else:
            log_security_event("DIRECTORY_CHECK", f"Directory '{dir_name}' exists", "INFO")
            print(f"✅ Directory '{dir_name}' exists")

    required_packages = ["PyQt6", "subprocess", "os", "sys", "cv2", "numpy"]
    missing_packages = []
    for package in required_packages:
        try:
            available = check_package(package)[1]
            if available:
                log_security_event("PACKAGE_CHECK", f"Package '{package}' available", "INFO")
                print(f"✅ Package '{package}' available")
            else:
                missing_packages.append(package)
                log_security_event("PACKAGE_CHECK", f"Package '{package}' missing", "WARNING")
                print(f"❌ Package '{package}' missing")
        except Exception as e:
            missing_packages.append(package)
            log_security_event("PACKAGE_CHECK", f"Package '{package}' check failed: {e}", "WARNING")
            print(f"⚠️  Package '{package}' check failed: {e}")

    if missing_packages:
        log_security_event("PACKAGE_CHECK", f"Missing packages: {', '.join(missing_packages)}", "WARNING")
        print(f"⚠️  WARNING: Missing packages: {', '.join(missing_packages)}")
        print("Please install missing packages using: pip install <package>")

    return True


# Global instances
encryptor = SimpleEncryptor()
rate_limiter = SimpleRateLimiter()