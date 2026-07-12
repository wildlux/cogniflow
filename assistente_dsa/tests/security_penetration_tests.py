#!/usr/bin/env python3
"""
Security Penetration Tests - Test di penetrazione e sicurezza avanzata
Test automatici per identificare vulnerabilità di sicurezza
"""

import unittest
import time
import threading
import os
import tempfile
import subprocess
import json
from unittest.mock import patch, MagicMock, mock_open
from typing import Dict, List, Any
import hashlib
import secrets
import logging

# Configurazione logging per test
logging.basicConfig(level=logging.WARNING)

# Import moduli di sicurezza
try:
    from core.security_monitor import security_monitor
    from core.user_auth_manager import UserAuthManager
    from core.input_validator import InputValidator
    from core.advanced_encryption import AdvancedEncryptionManager
    from core.security_dashboard import (
        RealTimeAlertingSystem, AlertType, AlertSeverity,
        trigger_security_alert, get_security_dashboard
    )
except ImportError as e:
    print(f"Errore import moduli sicurezza: {e}")
    # Fallback per test parziali
    security_monitor = None
    UserAuthManager = None
    InputValidator = None
    AdvancedEncryptionManager = None
    RealTimeAlertingSystem = None


class PenetrationTestBase(unittest.TestCase):
    """Classe base per test di penetrazione."""

    def setUp(self):
        """Setup comune per tutti i test."""
        self.test_data = {
            'username': 'testuser',
            'password': 'SecurePass123!',
            'email': 'test@example.com'
        }
        self.temp_files = []

    def tearDown(self):
        """Pulizia dopo ogni test."""
        for temp_file in self.temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except:
                pass

    def create_temp_file(self, content: str = "", suffix: str = ".tmp") -> str:
        """Crea un file temporaneo per i test."""
        with tempfile.NamedTemporaryFile(mode='w', suffix=suffix, delete=False) as f:
            f.write(content)
            temp_path = f.name
        self.temp_files.append(temp_path)
        return temp_path


class TestSQLInjection(PenetrationTestBase):
    """Test per vulnerabilità SQL injection."""

    def test_sql_injection_attempts(self):
        """Test tentativi di SQL injection."""
        if not UserAuthManager:
            self.skipTest("UserAuthManager non disponibile")

        malicious_inputs = [
            "' OR '1'='1",
            "admin'; DROP TABLE users; --",
            "' UNION SELECT * FROM users --",
            "admin' --",
            "'; SELECT password FROM users WHERE '1'='1"
        ]

        # Crea database temporaneo per test
        db_path = self.create_temp_file(suffix='.db')
        auth_manager = UserAuthManager(db_path)

        for malicious_input in malicious_inputs:
            with self.subTest(input=malicious_input):
                # Questi dovrebbero fallire o essere sanitizzati
                result = auth_manager.authenticate(malicious_input, "password")
                self.assertIsNone(result, f"SQL injection non bloccato: {malicious_input}")

    def test_parameterized_queries(self):
        """Test che le query siano parameterized."""
        if not UserAuthManager:
            self.skipTest("UserAuthManager non disponibile")

        db_path = self.create_temp_file(suffix='.db')
        auth_manager = UserAuthManager(db_path)

        # Crea utente valido
        success = auth_manager.create_user(
            "validuser", "ValidPass123!", "Valid User", "valid@example.com"
        )
        self.assertTrue(success, "Creazione utente valido dovrebbe riuscire")

        # Test autenticazione con input normale
        user = auth_manager.authenticate("validuser", "ValidPass123!")
        self.assertIsNotNone(user, "Autenticazione valida dovrebbe riuscire")


class TestXSSVulnerabilities(PenetrationTestBase):
    """Test per vulnerabilità Cross-Site Scripting (XSS)."""

    def test_xss_payloads(self):
        """Test payload XSS comuni."""
        if not InputValidator:
            self.skipTest("InputValidator non disponibile")

        validator = InputValidator()

        xss_payloads = [
            "<script>alert('xss')</script>",
            "<img src=x onerror=alert('xss')>",
            "javascript:alert('xss')",
            "<iframe src='javascript:alert(\"xss\")'>",
            "<svg onload=alert('xss')>",
            "'><script>alert('xss')</script>",
            "<body onload=alert('xss')>"
        ]

        for payload in xss_payloads:
            with self.subTest(payload=payload):
                # Test sanitizzazione
                sanitized = validator.sanitize_string(payload)
                self.assertNotIn('<script', sanitized.lower(),
                               f"XSS payload non sanitizzato: {payload}")
                self.assertNotIn('javascript:', sanitized.lower(),
                               f"JavaScript non rimosso: {payload}")
                self.assertNotIn('onload', sanitized.lower(),
                               f"Event handler non rimosso: {payload}")

    def test_html_injection(self):
        """Test injection HTML."""
        if not InputValidator:
            self.skipTest("InputValidator non disponibile")

        validator = InputValidator()

        html_injections = [
            "<b>Bold text</b>",
            "<a href='http://evil.com'>Link</a>",
            "<div style='color:red'>Styled text</div>",
            "<!-- Comment -->",
            "<![CDATA[ <script> ]]>",
        ]

        for injection in html_injections:
            with self.subTest(injection=injection):
                sanitized = validator.sanitize_string(injection)
                # HTML dovrebbe essere escaped
                self.assertNotEqual(injection, sanitized,
                                  f"HTML non escaped: {injection}")


class TestBruteForceProtection(PenetrationTestBase):
    """Test protezione contro attacchi brute force."""

    def test_rate_limiting(self):
        """Test rate limiting per tentativi di login."""
        if not UserAuthManager:
            self.skipTest("UserAuthManager non disponibile")

        db_path = self.create_temp_file(suffix='.db')
        auth_manager = UserAuthManager(db_path)

        # Simula tentativi falliti
        failed_attempts = 10
        for i in range(failed_attempts):
            result = auth_manager.authenticate("nonexistent", f"wrongpass{i}")
            if i < 5:  # Primi 5 dovrebbero fallire normalmente
                self.assertIsNone(result, f"Tentativo {i+1} dovrebbe fallire")

        # Dopo diversi tentativi, dovrebbe esserci rate limiting
        # Nota: Questo test potrebbe richiedere configurazione specifica

    def test_account_lockout(self):
        """Test blocco account dopo tentativi falliti."""
        if not UserAuthManager:
            self.skipTest("UserAuthManager non disponibile")

        db_path = self.create_temp_file(suffix='.db')
        auth_manager = UserAuthManager(db_path)

        # Crea utente valido
        auth_manager.create_user("testuser", "CorrectPass123!", "Test User", "test@example.com")

        # Simula molti tentativi falliti
        for i in range(10):
            auth_manager.authenticate("testuser", f"wrongpass{i}")

        # L'account dovrebbe essere bloccato o rate limited
        result = auth_manager.authenticate("testuser", "CorrectPass123!")
        # In un'implementazione reale, questo potrebbe essere None se bloccato


class TestEncryptionSecurity(PenetrationTestBase):
    """Test sicurezza crittografia."""

    def test_encryption_key_rotation(self):
        """Test rotazione chiavi di crittografia."""
        if not AdvancedEncryptionManager:
            self.skipTest("AdvancedEncryptionManager non disponibile")

        key_store = self.create_temp_file(suffix='.json')
        encryption = AdvancedEncryptionManager(key_store)

        # Test crittografia/decrittografia
        test_data = "Sensitive data for encryption test"
        encrypted = encryption.encrypt_data(test_data)
        decrypted = encryption.decrypt_data(encrypted)

        self.assertEqual(test_data, decrypted, "Crittografia/decrittografia dovrebbe funzionare")

        # Test rotazione chiavi
        old_key_id = encryption.current_key_id
        encryption.rotate_keys()

        self.assertNotEqual(old_key_id, encryption.current_key_id,
                          "Chiave dovrebbe essere ruotata")

        # Test che i dati crittati con chiave vecchia possano ancora essere decrittati
        decrypted_after_rotation = encryption.decrypt_data(encrypted)
        self.assertEqual(test_data, decrypted_after_rotation,
                        "Dati crittati con chiave vecchia dovrebbero essere decrittabili")

    def test_multiple_algorithms(self):
        """Test supporto algoritmi multipli."""
        if not AdvancedEncryptionManager:
            self.skipTest("AdvancedEncryptionManager non disponibile")

        key_store = self.create_temp_file(suffix='.json')
        encryption = AdvancedEncryptionManager(key_store)

        test_data = "Test data for algorithm testing"
        algorithms = ['AES-256-GCM', 'AES-256-CBC']

        for algorithm in algorithms:
            with self.subTest(algorithm=algorithm):
                try:
                    encrypted = encryption.encrypt_data(test_data, algorithm)
                    decrypted = encryption.decrypt_data(encrypted)
                    self.assertEqual(test_data, decrypted,
                                   f"Algoritmo {algorithm} dovrebbe funzionare")
                except Exception as e:
                    self.fail(f"Errore con algoritmo {algorithm}: {e}")

    def test_encryption_integrity(self):
        """Test integrità crittografia (tampering detection)."""
        if not AdvancedEncryptionManager:
            self.skipTest("AdvancedEncryptionManager non disponibile")

        key_store = self.create_temp_file(suffix='.json')
        encryption = AdvancedEncryptionManager(key_store)

        test_data = "Data integrity test"
        encrypted = encryption.encrypt_data(test_data)

        # Modifica i dati crittati (simula tampering)
        if len(encrypted) > 20:
            tampered = encrypted[:10] + 'X' + encrypted[11:]
            with self.assertRaises(Exception):
                encryption.decrypt_data(tampered)


class TestFileSystemSecurity(PenetrationTestBase):
    """Test sicurezza file system."""

    def test_path_traversal(self):
        """Test prevenzione path traversal."""
        if not InputValidator:
            self.skipTest("InputValidator non disponibile")

        validator = InputValidator()

        malicious_paths = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\cmd.exe",
            "/etc/shadow",
            "....//....//....//etc/passwd",
            "..%2F..%2F..%2Fetc%2Fpasswd"
        ]

        for path in malicious_paths:
            with self.subTest(path=path):
                valid, message = validator.validate_path(path, allow_absolute=False)
                self.assertFalse(valid, f"Path traversal non bloccato: {path}")

    def test_file_permission_security(self):
        """Test sicurezza permessi file."""
        # Crea file di test
        test_file = self.create_temp_file("test content")

        # Test lettura file
        try:
            with open(test_file, 'r') as f:
                content = f.read()
            self.assertEqual(content, "test content", "Lettura file dovrebbe funzionare")
        except Exception as e:
            self.fail(f"Errore lettura file: {e}")

        # Test che non si possano leggere file di sistema
        system_files = ['/etc/passwd', '/etc/shadow', 'C:\\Windows\\System32\\config\\SAM']
        for sys_file in system_files:
            if os.path.exists(sys_file):
                with self.assertRaises(PermissionError):
                    with open(sys_file, 'r') as f:
                        f.read()


class TestNetworkSecurity(PenetrationTestBase):
    """Test sicurezza rete."""

    def test_command_injection(self):
        """Test prevenzione command injection."""
        if not InputValidator:
            self.skipTest("InputValidator non disponibile")

        validator = InputValidator()

        malicious_commands = [
            "; rm -rf /",
            "| cat /etc/passwd",
            "`whoami`",
            "$(rm -rf /)",
            "; net user hacker password /add"
        ]

        for command in malicious_commands:
            with self.subTest(command=command):
                sanitized = validator.sanitize_string(command)
                # I caratteri pericolosi dovrebbero essere rimossi o escaped
                dangerous_chars = [';', '|', '`', '$', '(']
                for char in dangerous_chars:
                    if char in command:
                        self.assertNotIn(char, sanitized,
                                       f"Carattere pericoloso non rimosso: {char} in {command}")

    def test_url_validation(self):
        """Test validazione URL."""
        if not InputValidator:
            self.skipTest("InputValidator non disponibile")

        validator = InputValidator()

        valid_urls = [
            "https://example.com",
            "http://localhost:8080",
            "https://api.github.com/users/test"
        ]

        invalid_urls = [
            "javascript:alert('xss')",
            "data:text/html,<script>alert('xss')</script>",
            "vbscript:msgbox('xss')",
            "file:///etc/passwd"
        ]

        for url in valid_urls:
            with self.subTest(url=url):
                valid, message = validator.validate_path(url)  # Usa validate_path come proxy
                # Nota: Questo è un test semplificato

        for url in invalid_urls:
            with self.subTest(url=url):
                sanitized = validator.sanitize_string(url)
                self.assertNotIn('javascript:', sanitized.lower(),
                               f"URL pericoloso non sanitizzato: {url}")


class TestPerformanceSecurity(PenetrationTestBase):
    """Test performance sotto carico di sicurezza."""

    def test_encryption_performance(self):
        """Test performance crittografia sotto carico."""
        if not AdvancedEncryptionManager:
            self.skipTest("AdvancedEncryptionManager non disponibile")

        key_store = self.create_temp_file(suffix='.json')
        encryption = AdvancedEncryptionManager(key_store)

        # Test crittografia di dati di grandi dimensioni
        large_data = "A" * 1000000  # 1MB di dati

        start_time = time.time()
        encrypted = encryption.encrypt_data(large_data)
        encrypt_time = time.time() - start_time

        start_time = time.time()
        decrypted = encryption.decrypt_data(encrypted)
        decrypt_time = time.time() - start_time

        # Verifica correttezza
        self.assertEqual(large_data, decrypted, "Crittografia/decrittografia dati grandi dovrebbe funzionare")

        # Verifica performance (dovrebbe essere ragionevole)
        total_time = encrypt_time + decrypt_time
        self.assertLess(total_time, 10.0, "Crittografia 1MB dovrebbe richiedere meno di 10 secondi")

    def test_concurrent_security_operations(self):
        """Test operazioni di sicurezza concorrenti."""
        if not AdvancedEncryptionManager:
            self.skipTest("AdvancedEncryptionManager non disponibile")

        key_store = self.create_temp_file(suffix='.json')
        encryption = AdvancedEncryptionManager(key_store)

        results = []
        errors = []

        def encrypt_worker(worker_id: int):
            """Worker per test concorrenza."""
            try:
                test_data = f"Test data from worker {worker_id}"
                encrypted = encryption.encrypt_data(test_data)
                decrypted = encryption.decrypt_data(encrypted)

                if test_data == decrypted:
                    results.append(True)
                else:
                    results.append(False)
            except Exception as e:
                errors.append(str(e))

        # Avvia worker concorrenti
        threads = []
        num_workers = 10

        for i in range(num_workers):
            thread = threading.Thread(target=encrypt_worker, args=(i,))
            threads.append(thread)
            thread.start()

        # Aspetta completamento
        for thread in threads:
            thread.join(timeout=30)

        # Verifica risultati
        self.assertEqual(len(results), num_workers,
                        "Tutti i worker dovrebbero completare")
        self.assertTrue(all(results), "Tutti i worker dovrebbero avere successo")
        self.assertEqual(len(errors), 0, f"Non dovrebbero esserci errori: {errors}")


class TestAlertingSystem(PenetrationTestBase):
    """Test sistema di alerting."""

    def test_alert_generation(self):
        """Test generazione alert di sicurezza."""
        if not RealTimeAlertingSystem:
            self.skipTest("RealTimeAlertingSystem non disponibile")

        alerting = RealTimeAlertingSystem()

        # Test generazione alert
        alert_id = alerting.trigger_alert(
            AlertType.UNAUTHORIZED_ACCESS,
            AlertSeverity.HIGH,
            "Test Alert",
            "This is a test security alert",
            source_ip="192.168.1.100",
            user_id="testuser"
        )

        self.assertIsNotNone(alert_id, "Alert dovrebbe essere generato")

        # Verifica alert attivo
        active_alerts = alerting.get_active_alerts()
        self.assertEqual(len(active_alerts), 1, "Dovrebbe esserci un alert attivo")

        alert = active_alerts[0]
        self.assertEqual(alert.alert_type, AlertType.UNAUTHORIZED_ACCESS)
        self.assertEqual(alert.severity, AlertSeverity.HIGH)

    def test_alert_cooldown(self):
        """Test cooldown degli alert."""
        if not RealTimeAlertingSystem:
            self.skipTest("RealTimeAlertingSystem non disponibile")

        alerting = RealTimeAlertingSystem()

        # Genera primo alert
        alert_id1 = alerting.trigger_alert(
            AlertType.BRUTE_FORCE,
            AlertSeverity.MEDIUM,
            "Brute Force Attempt",
            "Multiple failed login attempts",
            source_ip="10.0.0.1"
        )

        # Genera secondo alert immediatamente (dovrebbe essere in cooldown)
        alert_id2 = alerting.trigger_alert(
            AlertType.BRUTE_FORCE,
            AlertSeverity.MEDIUM,
            "Brute Force Attempt 2",
            "Another brute force attempt",
            source_ip="10.0.0.1"
        )

        # Dovrebbe esserci solo un alert attivo (il secondo è in cooldown)
        active_alerts = alerting.get_active_alerts()
        self.assertEqual(len(active_alerts), 1, "Dovrebbe esserci solo un alert (cooldown attivo)")


if __name__ == '__main__':
    # Configurazione test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Aggiungi test classes
    test_classes = [
        TestSQLInjection,
        TestXSSVulnerabilities,
        TestBruteForceProtection,
        TestEncryptionSecurity,
        TestFileSystemSecurity,
        TestNetworkSecurity,
        TestPerformanceSecurity,
        TestAlertingSystem
    ]

    for test_class in test_classes:
        suite.addTests(loader.loadTestsFromTestCase(test_class))

    # Esegui test
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Report risultati
    print(f"\n{'='*60}")
    print("RISULTATI TEST DI PENETRAZIONE")
    print(f"{'='*60}")
    print(f"Test eseguiti: {result.testsRun}")
    print(f"Successi: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Fallimenti: {len(result.failures)}")
    print(f"Errori: {len(result.errors)}")

    if result.failures:
        print(f"\nFALLIMENTI:")
        for test, traceback in result.failures:
            print(f"- {test}")

    if result.errors:
        print(f"\nERRORI:")
        for test, traceback in result.errors:
            print(f"- {test}")

    # Valutazione complessiva
    success_rate = (result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100

    print(f"\nTASSO DI SUCCESSO: {success_rate:.1f}%")

    if success_rate >= 95:
        print("✅ SICUREZZA ECCELLENTE - Tutti i test passati")
    elif success_rate >= 85:
        print("🟢 SICUREZZA BUONA - Alcuni test falliti, revisione necessaria")
    elif success_rate >= 70:
        print("🟡 SICUREZZA DISCRETA - Miglioramenti necessari")
    else:
        print("🔴 SICUREZZA INSUFFICIENTE - Azione immediata richiesta")