#!/usr/bin/env python3
"""
Advanced Encryption System - Sistema di crittografia avanzato
Supporta rotazione chiavi, algoritmi multipli, e crittografia database
"""

import os
import json
import base64
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple, List
from dataclasses import dataclass
import logging
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import sqlite3

logger = logging.getLogger(__name__)


@dataclass
class EncryptionKey:
    """Classe per rappresentare una chiave di crittografia."""
    key_id: str
    key_data: bytes
    algorithm: str
    created_at: datetime
    expires_at: Optional[datetime]
    is_active: bool
    rotation_count: int


class AdvancedEncryptionManager:
    """Gestore avanzato della crittografia con supporto multi-algoritmo e rotazione chiavi."""

    def __init__(self, key_store_path: Optional[str] = None):
        if key_store_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            key_store_path = os.path.join(base_dir, "Save", "SECURITY", "key_store.json")

        self.key_store_path = key_store_path
        self._ensure_key_store_directory()
        self.keys: Dict[str, EncryptionKey] = {}
        self.current_key_id: Optional[str] = None
        self.key_rotation_days = 30  # Rotazione chiavi ogni 30 giorni
        self.supported_algorithms = ['AES-256-GCM', 'AES-256-CBC', 'ChaCha20-Poly1305']

        self._load_key_store()
        self._initialize_default_keys()

    def _ensure_key_store_directory(self):
        """Assicura che la directory del key store esista."""
        key_dir = os.path.dirname(self.key_store_path)
        os.makedirs(key_dir, exist_ok=True)

    def _load_key_store(self):
        """Carica il key store dal file."""
        if os.path.exists(self.key_store_path):
            try:
                with open(self.key_store_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                for key_data in data.get('keys', []):
                    key = EncryptionKey(
                        key_id=key_data['key_id'],
                        key_data=base64.b64decode(key_data['key_data']),
                        algorithm=key_data['algorithm'],
                        created_at=datetime.fromisoformat(key_data['created_at']),
                        expires_at=datetime.fromisoformat(key_data['expires_at']) if key_data.get('expires_at') else None,
                        is_active=key_data['is_active'],
                        rotation_count=key_data['rotation_count']
                    )
                    self.keys[key.key_id] = key

                self.current_key_id = data.get('current_key_id')

            except Exception as e:
                logger.error(f"Errore caricamento key store: {e}")
                self._initialize_default_keys()

    def _save_key_store(self):
        """Salva il key store su file."""
        try:
            data = {
                'keys': [],
                'current_key_id': self.current_key_id,
                'last_updated': datetime.now().isoformat()
            }

            for key in self.keys.values():
                key_data = {
                    'key_id': key.key_id,
                    'key_data': base64.b64encode(key.key_data).decode(),
                    'algorithm': key.algorithm,
                    'created_at': key.created_at.isoformat(),
                    'expires_at': key.expires_at.isoformat() if key.expires_at else None,
                    'is_active': key.is_active,
                    'rotation_count': key.rotation_count
                }
                data['keys'].append(key_data)

            with open(self.key_store_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            logger.error(f"Errore salvataggio key store: {e}")

    def _initialize_default_keys(self):
        """Inizializza chiavi di default se non esistono."""
        if not self.keys:
            self._generate_new_key('AES-256-GCM')
            logger.info("Chiavi di crittografia inizializzate")

    def _generate_new_key(self, algorithm: str = 'AES-256-GCM') -> str:
        """Genera una nuova chiave di crittografia."""
        key_id = f"key_{secrets.token_hex(8)}"
        key_size = 32  # 256 bit

        if algorithm == 'ChaCha20-Poly1305':
            key_size = 32
        elif algorithm.startswith('AES'):
            key_size = 32

        key_data = secrets.token_bytes(key_size)

        expires_at = datetime.now() + timedelta(days=self.key_rotation_days)

        key = EncryptionKey(
            key_id=key_id,
            key_data=key_data,
            algorithm=algorithm,
            created_at=datetime.now(),
            expires_at=expires_at,
            is_active=True,
            rotation_count=0
        )

        self.keys[key_id] = key
        if self.current_key_id is None:
            self.current_key_id = key_id
        self._save_key_store()

        logger.info(f"Nuova chiave generata: {key_id} ({algorithm})")
        return key_id

    def _get_current_key(self) -> EncryptionKey:
        """Ottiene la chiave corrente attiva."""
        if not self.current_key_id or self.current_key_id not in self.keys:
            self._generate_new_key()
            return self._get_current_key()

        key = self.keys[self.current_key_id]

        # Controlla se la chiave è scaduta
        if key.expires_at and datetime.now() > key.expires_at:
            logger.warning(f"Chiave scaduta: {key.key_id}, generando nuova chiave")
            self.rotate_keys()

        return key

    def rotate_keys(self):
        """Ruota le chiavi di crittografia."""
        old_key_id = self.current_key_id

        # Genera nuova chiave
        new_key_id = self._generate_new_key()

        # Disattiva chiave vecchia ma mantieni per decrittazione
        if old_key_id and old_key_id in self.keys:
            old_key = self.keys[old_key_id]
            old_key.is_active = False
            old_key.rotation_count += 1

        # Imposta nuova chiave come corrente
        self.current_key_id = new_key_id

        self._save_key_store()
        logger.info(f"Rotazione chiavi completata: {old_key_id} -> {new_key_id}")

    def encrypt_data(self, data: str, algorithm: Optional[str] = None) -> str:
        """Critta dati usando l'algoritmo specificato."""
        if algorithm is None:
            key = self._get_current_key()
            algorithm = key.algorithm
        else:
            # Usa algoritmo specifico se richiesto
            key = self._get_current_key()

        try:
            if algorithm == 'AES-256-GCM':
                return self._encrypt_aes_gcm(data, key.key_data)
            elif algorithm == 'AES-256-CBC':
                return self._encrypt_aes_cbc(data, key.key_data)
            elif algorithm == 'ChaCha20-Poly1305':
                return self._encrypt_chacha20(data, key.key_data)
            else:
                raise ValueError(f"Algoritmo non supportato: {algorithm}")
        except Exception as e:
            logger.error(f"Errore crittografia: {e}")
            raise

    def decrypt_data(self, encrypted_data: str) -> str:
        """Decritta dati identificando automaticamente l'algoritmo e la chiave."""
        try:
            # Il formato è: algorithm:key_id:encrypted_data
            parts = encrypted_data.split(':', 2)
            if len(parts) != 3:
                # Formato legacy, usa chiave corrente
                return self._decrypt_with_key(encrypted_data, self._get_current_key())

            algorithm, key_id, data = parts

            if key_id not in self.keys:
                raise ValueError(f"Chiave non trovata: {key_id}")

            key = self.keys[key_id]
            return self._decrypt_with_key(data, key)

        except Exception as e:
            logger.error(f"Errore decrittografia: {e}")
            raise

    def _encrypt_aes_gcm(self, data: str, key: bytes) -> str:
        """Crittografia AES-256-GCM."""
        backend = default_backend()
        iv = os.urandom(12)  # 96 bit IV per GCM

        cipher = Cipher(algorithms.AES(key), modes.GCM(iv), backend=backend)
        encryptor = cipher.encryptor()

        plaintext = data.encode('utf-8')
        ciphertext = encryptor.update(plaintext) + encryptor.finalize()

        # Combina IV, tag di autenticazione e ciphertext
        result = base64.b64encode(iv + encryptor.tag + ciphertext).decode()
        return f"AES-256-GCM:{self.current_key_id}:{result}"

    def _decrypt_aes_gcm(self, encrypted_data: str, key: bytes) -> str:
        """Decrittografia AES-256-GCM."""
        backend = default_backend()

        # Decode e separa componenti
        decoded = base64.b64decode(encrypted_data)
        iv = decoded[:12]
        tag = decoded[12:28]
        ciphertext = decoded[28:]

        cipher = Cipher(algorithms.AES(key), modes.GCM(iv, tag), backend=backend)
        decryptor = cipher.decryptor()
        plaintext = decryptor.update(ciphertext) + decryptor.finalize()

        return plaintext.decode('utf-8')

    def _encrypt_aes_cbc(self, data: str, key: bytes) -> str:
        """Crittografia AES-256-CBC."""
        backend = default_backend()
        iv = os.urandom(16)

        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=backend)
        encryptor = cipher.encryptor()

        plaintext = data.encode('utf-8')
        # Padding PKCS7
        block_size = 16
        padding_length = block_size - (len(plaintext) % block_size)
        plaintext += bytes([padding_length]) * padding_length

        ciphertext = encryptor.update(plaintext) + encryptor.finalize()

        result = base64.b64encode(iv + ciphertext).decode()
        return f"AES-256-CBC:{self.current_key_id}:{result}"

    def _decrypt_aes_cbc(self, encrypted_data: str, key: bytes) -> str:
        """Decrittografia AES-256-CBC."""
        backend = default_backend()

        decoded = base64.b64decode(encrypted_data)
        iv = decoded[:16]
        ciphertext = decoded[16:]

        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=backend)
        decryptor = cipher.decryptor()
        padded_plaintext = decryptor.update(ciphertext) + decryptor.finalize()

        # Rimuovi padding PKCS7
        padding_length = padded_plaintext[-1]
        plaintext = padded_plaintext[:-padding_length]

        return plaintext.decode('utf-8')

    def _encrypt_chacha20(self, data: str, key: bytes) -> str:
        """Crittografia ChaCha20-Poly1305."""
        from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305

        nonce = os.urandom(12)
        aad = b"authenticated_data"

        chacha = ChaCha20Poly1305(key)
        plaintext = data.encode('utf-8')
        ciphertext = chacha.encrypt(nonce, plaintext, aad)

        result = base64.b64encode(nonce + ciphertext).decode()
        return f"ChaCha20-Poly1305:{self.current_key_id}:{result}"

    def _decrypt_chacha20(self, encrypted_data: str, key: bytes) -> str:
        """Decrittografia ChaCha20-Poly1305."""
        from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305

        decoded = base64.b64decode(encrypted_data)
        nonce = decoded[:12]
        ciphertext = decoded[12:]
        aad = b"authenticated_data"

        chacha = ChaCha20Poly1305(key)
        plaintext = chacha.decrypt(nonce, ciphertext, aad)

        return plaintext.decode('utf-8')

    def _decrypt_with_key(self, encrypted_data: str, key: EncryptionKey) -> str:
        """Decritta usando una chiave specifica."""
        if key.algorithm == 'AES-256-GCM':
            return self._decrypt_aes_gcm(encrypted_data, key.key_data)
        elif key.algorithm == 'AES-256-CBC':
            return self._decrypt_aes_cbc(encrypted_data, key.key_data)
        elif key.algorithm == 'ChaCha20-Poly1305':
            return self._decrypt_chacha20(encrypted_data, key.key_data)
        else:
            raise ValueError(f"Algoritmo non supportato: {key.algorithm}")

    def encrypt_database_field(self, db_path: str, table: str, column: str, row_id: int):
        """Critta un campo specifico del database."""
        try:
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()

                # Leggi il valore attuale
                cursor.execute(f"SELECT {column} FROM {table} WHERE id = ?", (row_id,))
                row = cursor.fetchone()

                if row and row[0]:
                    plaintext = str(row[0])
                    encrypted = self.encrypt_data(plaintext)

                    # Aggiorna con valore crittato
                    cursor.execute(f"UPDATE {table} SET {column} = ? WHERE id = ?", (encrypted, row_id))
                    conn.commit()

                    logger.info(f"Campo {column} crittato per record {row_id}")

        except Exception as e:
            logger.error(f"Errore crittografia database: {e}")

    def decrypt_database_field(self, db_path: str, table: str, column: str, row_id: int) -> Optional[str]:
        """Decritta un campo specifico del database."""
        try:
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()

                cursor.execute(f"SELECT {column} FROM {table} WHERE id = ?", (row_id,))
                row = cursor.fetchone()

                if row and row[0]:
                    return self.decrypt_data(str(row[0]))

        except Exception as e:
            logger.error(f"Errore decrittografia database: {e}")

        return None

    def get_encryption_status(self) -> Dict[str, Any]:
        """Restituisce lo stato del sistema di crittografia."""
        current_key = self._get_current_key() if self.current_key_id else None

        return {
            'current_key_id': self.current_key_id,
            'total_keys': len(self.keys),
            'active_keys': len([k for k in self.keys.values() if k.is_active]),
            'supported_algorithms': self.supported_algorithms,
            'key_rotation_days': self.key_rotation_days,
            'current_algorithm': current_key.algorithm if current_key else None,
            'keys_expiring_soon': len([k for k in self.keys.values()
                                     if k.expires_at and
                                     (k.expires_at - datetime.now()).days <= 7])
        }

    def cleanup_expired_keys(self, max_age_days: int = 365):
        """Pulisce chiavi scadute da troppo tempo."""
        cutoff_date = datetime.now() - timedelta(days=max_age_days)
        expired_keys = []

        for key_id, key in self.keys.items():
            if not key.is_active and key.created_at < cutoff_date:
                expired_keys.append(key_id)

        for key_id in expired_keys:
            del self.keys[key_id]

        if expired_keys:
            self._save_key_store()
            logger.info(f"Pulite {len(expired_keys)} chiavi scadute")


# Istanza globale del gestore crittografia avanzata
advanced_encryption = AdvancedEncryptionManager()


def encrypt_sensitive_data(data: str) -> str:
    """Funzione di comodo per crittare dati sensibili."""
    return advanced_encryption.encrypt_data(data)


def decrypt_sensitive_data(encrypted_data: str) -> str:
    """Funzione di comodo per decrittare dati sensibili."""
    return advanced_encryption.decrypt_data(encrypted_data)


def rotate_encryption_keys():
    """Funzione di comodo per ruotare le chiavi."""
    advanced_encryption.rotate_keys()


def get_encryption_status() -> Dict[str, Any]:
    """Funzione di comodo per ottenere lo stato della crittografia."""
    return advanced_encryption.get_encryption_status()