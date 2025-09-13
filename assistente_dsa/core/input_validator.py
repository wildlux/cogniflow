#!/usr/bin/env python3
"""
Input Validation and Sanitization Utilities
Sicurezza avanzata per la validazione degli input utente
"""

import re
import html
from typing import Any, Dict, List, Optional, Union
import logging

logger = logging.getLogger(__name__)


class InputValidator:
    """Validatore avanzato per input utente con sanitizzazione."""

    # Pattern di validazione
    PATTERNS = {
        'username': re.compile(r'^[a-zA-Z0-9_-]{3,30}$'),
        'email': re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'),
        'password': re.compile(r'^.{8,128}$'),  # Lunghezza minima 8, massima 128
        'filename': re.compile(r'^[a-zA-Z0-9._\-\s]{1,255}$'),
        'path': re.compile(r'^[a-zA-Z0-9._\-/\s]{1,4096}$'),
        'url': re.compile(r'^https?://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(?:/.*)?$'),
        'alphanumeric': re.compile(r'^[a-zA-Z0-9\s]{1,1000}$'),
        'text': re.compile(r'^[a-zA-Z0-9\s.,!?-]{1,10000}$'),
    }

    # Caratteri pericolosi da filtrare
    DANGEROUS_CHARS = ['<', '>', '"', "'", ';', '--', '/*', '*/', 'xp_', 'sp_']

    @staticmethod
    def sanitize_string(input_str: str, max_length: int = 1000) -> str:
        """Sanitizza una stringa rimuovendo caratteri pericolosi."""
        if not isinstance(input_str, str):
            return ""

        # Rimuovi caratteri null e di controllo
        sanitized = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', input_str)

        # Escape HTML
        sanitized = html.escape(sanitized)

        # Rimuovi caratteri pericolosi
        for char in InputValidator.DANGEROUS_CHARS:
            sanitized = sanitized.replace(char, '')

        # Limita lunghezza
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length]

        return sanitized.strip()

    @staticmethod
    def validate_username(username: str) -> tuple[bool, str]:
        """Valida un username."""
        if not username or not isinstance(username, str):
            return False, "Username richiesto"

        username = username.strip()

        if len(username) < 3:
            return False, "Username deve essere di almeno 3 caratteri"

        if len(username) > 30:
            return False, "Username deve essere di massimo 30 caratteri"

        if not InputValidator.PATTERNS['username'].match(username):
            return False, "Username contiene caratteri non validi"

        return True, "Username valido"

    @staticmethod
    def validate_email(email: str) -> tuple[bool, str]:
        """Valida un indirizzo email."""
        if not email or not isinstance(email, str):
            return False, "Email richiesta"

        email = email.strip().lower()

        if len(email) > 254:  # RFC 5321
            return False, "Email troppo lunga"

        if not InputValidator.PATTERNS['email'].match(email):
            return False, "Formato email non valido"

        return True, "Email valida"

    @staticmethod
    def validate_password(password: str) -> tuple[bool, str]:
        """Valida una password con controlli di complessità."""
        if not password or not isinstance(password, str):
            return False, "Password richiesta"

        if len(password) < 8:
            return False, "Password deve essere di almeno 8 caratteri"

        if len(password) > 128:
            return False, "Password deve essere di massimo 128 caratteri"

        # Controlla complessità
        has_upper = bool(re.search(r'[A-Z]', password))
        has_lower = bool(re.search(r'[a-z]', password))
        has_digit = bool(re.search(r'[0-9]', password))
        has_special = bool(re.search(r'[^A-Za-z0-9]', password))

        if not (has_upper and has_lower and has_digit):
            return False, "Password deve contenere maiuscole, minuscole e numeri"

        # Controlla sequenze comuni
        common_patterns = [
            r'123456', r'password', r'qwerty', r'admin', r'root',
            r'(.)\1{2,}',  # Caratteri ripetuti
        ]

        for pattern in common_patterns:
            if re.search(pattern, password.lower()):
                return False, "Password troppo debole o prevedibile"

        return True, "Password valida"

    @staticmethod
    def validate_filename(filename: str) -> tuple[bool, str]:
        """Valida un nome file."""
        if not filename or not isinstance(filename, str):
            return False, "Nome file richiesto"

        filename = filename.strip()

        if len(filename) > 255:
            return False, "Nome file troppo lungo"

        if not InputValidator.PATTERNS['filename'].match(filename):
            return False, "Nome file contiene caratteri non validi"

        # Controlla estensioni pericolose
        dangerous_extensions = ['.exe', '.bat', '.cmd', '.scr', '.pif', '.com']
        if any(filename.lower().endswith(ext) for ext in dangerous_extensions):
            return False, "Estensione file non consentita"

        return True, "Nome file valido"

    @staticmethod
    def validate_path(path: str, allow_absolute: bool = True) -> tuple[bool, str]:
        """Valida un percorso file."""
        if not path or not isinstance(path, str):
            return False, "Percorso richiesto"

        path = path.strip()

        if len(path) > 4096:
            return False, "Percorso troppo lungo"

        # Controlla path traversal
        if '..' in path:
            return False, "Path traversal non consentito"

        if not allow_absolute and path.startswith('/'):
            return False, "Percorso assoluto non consentito"

        # Rimuovi caratteri pericolosi
        if any(char in path for char in ['<', '>', '"', "'", ';']):
            return False, "Caratteri non validi nel percorso"

        return True, "Percorso valido"

    @staticmethod
    def validate_text_input(text: str, max_length: int = 10000) -> tuple[bool, str]:
        """Valida input di testo generico."""
        if not isinstance(text, str):
            return False, "Input deve essere una stringa"

        if len(text) > max_length:
            return False, f"Testo troppo lungo (max {max_length} caratteri)"

        # Controlla per script injection
        script_patterns = [
            r'<script[^>]*>.*?</script>',
            r'javascript:',
            r'vbscript:',
            r'on\w+\s*=',
        ]

        for pattern in script_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return False, "Contenuto script non consentito"

        return True, "Testo valido"

    @staticmethod
    def sanitize_sql_input(value: Any) -> Any:
        """Sanitizza input per uso in query SQL (da usare con parameterized queries)."""
        if isinstance(value, str):
            # Rimuovi caratteri di escape SQL
            return value.replace("'", "''").replace('\\', '\\\\')
        return value

    @staticmethod
    def validate_and_sanitize(input_data: Dict[str, Any],
                            validation_rules: Dict[str, str]) -> tuple[bool, Dict[str, Any], List[str]]:
        """
        Valida e sanitizza un dizionario di input secondo regole specificate.

        Args:
            input_data: Dati da validare
            validation_rules: Regole di validazione per chiave

        Returns:
            (success, sanitized_data, errors)
        """
        errors = []
        sanitized_data = {}

        for key, rule in validation_rules.items():
            if key not in input_data:
                if rule.endswith('?'):  # Campo opzionale
                    continue
                errors.append(f"Campo richiesto: {key}")
                continue

            value = input_data[key]

            if rule == 'username':
                valid, msg = InputValidator.validate_username(str(value))
            elif rule == 'email':
                valid, msg = InputValidator.validate_email(str(value))
            elif rule == 'password':
                valid, msg = InputValidator.validate_password(str(value))
            elif rule == 'filename':
                valid, msg = InputValidator.validate_filename(str(value))
            elif rule == 'path':
                valid, msg = InputValidator.validate_path(str(value))
            elif rule.startswith('text'):
                max_len = int(rule.split(':')[1]) if ':' in rule else 10000
                valid, msg = InputValidator.validate_text_input(str(value), max_len)
            else:
                valid, msg = True, "Regola non riconosciuta"

            if not valid:
                errors.append(f"{key}: {msg}")
            else:
                sanitized_data[key] = InputValidator.sanitize_string(str(value))

        return len(errors) == 0, sanitized_data, errors


# Istanza globale del validatore
input_validator = InputValidator()


def validate_user_input(data: Dict[str, Any]) -> tuple[bool, Dict[str, Any], List[str]]:
    """Funzione di comodo per validare input utente."""
    rules = {
        'username': 'username',
        'email': 'email',
        'password': 'password',
        'full_name': 'text:100',
        'filename': 'filename?',
        'path': 'path?',
    }
    return input_validator.validate_and_sanitize(data, rules)


def sanitize_user_input(text: str) -> str:
    """Funzione di comodo per sanitizzare input utente."""
    return input_validator.sanitize_string(text)