"""
Security module providing encryption, rate limiting, command sanitization, logging, and health status functions.
"""

import os, json, hashlib, base64, shlex, subprocess
from datetime import datetime
from typing import cast, Optional, Any

class SimpleEncryptor:
    """Simple encryption class using XOR with a key."""

    def __init__(self, key: Optional[str] = None):
        """Initialize the encryptor with an optional key."""
        if key is None:
            import secrets
            key = secrets.token_hex(32)
        self.key = key.encode()[:32].ljust(32, b"\0")

    def encrypt(self, data: str) -> str:
        """Encrypt a string using XOR."""
        try:
            data_bytes = data.encode()
            encrypted = bytearray(byte ^ self.key[i % len(self.key)] for i, byte in enumerate(data_bytes))
            return base64.b64encode(encrypted).decode()
        except Exception as e:
            print(f"Encryption error: {e}")
            return data

    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt a string using XOR."""
        try:
            encrypted_bytes = base64.b64decode(encrypted_data.encode())
            decrypted = bytearray(byte ^ self.key[i % len(self.key)] for i, byte in enumerate(encrypted_bytes))
            return decrypted.decode()
        except Exception as e:
            print(f"Decryption error: {e}")
            return encrypted_data

class SimpleRateLimiter:
    """Rate limiter to prevent excessive attempts."""

    def __init__(self, max_attempts: int = 5, window_seconds: int = 300):
        """Initialize with max attempts and window."""
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self.attempts = {}

    def is_allowed(self, key: str) -> bool:
        """Check if an action is allowed for the key."""
        now = datetime.now().timestamp()
        key_attempts = [t for t in self.attempts.get(key, []) if now - t < self.window_seconds]
        if len(key_attempts) >= self.max_attempts:
            return False
        key_attempts.append(now)
        self.attempts[key] = key_attempts
        return True

    def record_failure(self, key: str):
        """Record a failure for the key."""
        now = datetime.now().timestamp()
        if key not in self.attempts:
            self.attempts[key] = []
        self.attempts[key].append(now)

def _sanitize_command(cmd: str | list[str]) -> list[str]:
    """Sanitize a command for safe execution."""
    if isinstance(cmd, str):
        parts = shlex.split(cmd)
        return [shlex.quote(part) for part in parts]
    elif isinstance(cmd, list):
        return [shlex.quote(str(part)) for part in cmd]
    else:
        raise ValueError("Invalid command type")

def log_security_event(event_type: str, details: str, severity: str = "INFO"):
    """Log a security event to file."""
    safe_details = "DETAILS_PROTECTED" if any(k in details.lower() for k in ["password", "hash", "key", "token"]) else details
    print(f"[SECURITY {severity}] {event_type}: {safe_details}")
    try:
        with open(os.path.join(os.path.dirname(os.path.dirname(__file__)), "security.log"), "a") as f:
            f.write(f"{datetime.now().isoformat()} [{severity}] {event_type}: {safe_details}\n")
    except Exception:
        pass

def get_health_status():
    """Return basic health status."""
    return {"status": "limited", "message": "Security systems not available"}

# Global instances
encryptor = SimpleEncryptor()
rate_limiter = SimpleRateLimiter()