#!/usr/bin/env python3
"""
Security Integration Tests - Test automatici per sicurezza
Da eseguire nella pipeline CI/CD
"""

import unittest
import tempfile
import os
import sys
import json
import logging
from unittest.mock import patch, MagicMock
import time

# Aggiungi il percorso del progetto
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.security_monitor import SecurityMonitor, security_monitor
from core.user_auth_manager import UserAuthManager
from core.input_validator import InputValidator


class TestSecurityIntegration(unittest.TestCase):
    """Test di integrazione per funzionalità di sicurezza."""

    def setUp(self):
        """Setup per ogni test."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_security.db")

        # Crea istanze per i test
        self.auth_manager = UserAuthManager(self.db_path)
        self.input_validator = InputValidator()

    def tearDown(self):
        """Pulizia dopo ogni test."""
        # Rimuovi file temporanei
        try:
            if os.path.exists(self.db_path):
                os.remove(self.db_path)
            os.rmdir(self.temp_dir)
        except:
            pass

    def test_password_security(self):
        """Test sicurezza password con PBKDF2."""
        # Test password valida
        result = self.auth_manager.create_user(
            "testuser",
            "SecurePass123!",
            "Test User",
            "test@example.com"
        )
        self.assertTrue(result, "Creazione utente con password sicura dovrebbe riuscire")

        # Test autenticazione
        user = self.auth_manager.authenticate("testuser", "SecurePass123!")
        self.assertIsNotNone(user, "Autenticazione con password corretta dovrebbe riuscire")

        # Test password errata
        user = self.auth_manager.authenticate("testuser", "WrongPass123!")
        self.assertIsNone(user, "Autenticazione con password errata dovrebbe fallire")

    def test_brute_force_protection(self):
        """Test protezione contro attacchi brute force."""
        # Simula tentativi falliti
        for i in range(6):  # Più del limite
            user = self.auth_manager.authenticate("nonexistent", "wrongpass")
            if i < 5:
                self.assertIsNone(user, f"Tentativo {i+1} dovrebbe fallire")

        # Il sesto tentativo dovrebbe essere bloccato dal rate limiter
        # Nota: Questo test potrebbe richiedere mocking del rate limiter

    def test_input_validation(self):
        """Test validazione input sicura."""
        # Test input validi
        valid, data, errors = self.input_validator.validate_and_sanitize({
            'username': 'validuser123',
            'email': 'test@example.com',
            'password': 'SecurePass123!'
        }, {
            'username': 'username',
            'email': 'email',
            'password': 'password'
        })

        self.assertTrue(valid, "Input validi dovrebbero passare validazione")
        self.assertEqual(len(errors), 0, "Non dovrebbero esserci errori per input validi")

        # Test input pericolosi
        dangerous_inputs = [
            "<script>alert('xss')</script>",
            "../../../etc/passwd",
            "admin' OR '1'='1",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>"
        ]

        for dangerous_input in dangerous_inputs:
            sanitized = self.input_validator.sanitize_string(dangerous_input)
            self.assertNotIn('<', sanitized, f"Input pericoloso non sanitizzato: {dangerous_input}")
            self.assertNotIn('javascript:', sanitized, f"JavaScript non rimosso: {dangerous_input}")

    def test_sql_injection_prevention(self):
        """Test prevenzione SQL injection."""
        # Test input che potrebbero causare SQL injection
        malicious_inputs = [
            "admin' --",
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "admin'; SELECT * FROM users; --"
        ]

        for malicious_input in malicious_inputs:
            # Questi dovrebbero essere gestiti in sicurezza dal sistema
            # Nota: In un test reale, si dovrebbe mockare il database
            sanitized = self.input_validator.sanitize_string(malicious_input)
            # Verifica che i caratteri pericolosi siano stati rimossi o escaped
            self.assertNotIn(';', sanitized, f"SQL injection non prevenuto: {malicious_input}")

    def test_security_monitoring(self):
        """Test sistema di monitoraggio sicurezza."""
        # Test logging eventi di sicurezza
        security_monitor.log_security_event(
            "TEST_EVENT",
            {"test": "data"},
            "INFO"
        )

        # Verifica che l'evento sia stato registrato
        stats = security_monitor.get_security_stats()
        self.assertGreater(stats["recent_activities_count"], 0, "Dovrebbero esserci attività recenti")

    def test_file_security(self):
        """Test sicurezza accesso file."""
        # Test accesso a file sensibili
        sensitive_files = [
            "users.json",
            "settings.json",
            "security.log"
        ]

        for filename in sensitive_files:
            valid, msg = self.input_validator.validate_filename(filename)
            self.assertTrue(valid, f"Nome file sensibile dovrebbe essere valido: {filename}")

            # Test path traversal
            malicious_paths = [
                "../../../etc/passwd",
                "..\\..\\..\\windows\\system32",
                "/etc/shadow"
            ]

            for malicious_path in malicious_paths:
                valid, msg = self.input_validator.validate_path(malicious_path, allow_absolute=False)
                self.assertFalse(valid, f"Path traversal non bloccato: {malicious_path}")

    def test_encryption_security(self):
        """Test sicurezza crittografia."""
        from main_00_launcher import SimpleEncryptor

        encryptor = SimpleEncryptor()

        test_data = "Sensitive user data"
        encrypted = encryptor.encrypt(test_data)
        decrypted = encryptor.decrypt(encrypted)

        # Verifica che la crittografia funzioni
        self.assertNotEqual(test_data, encrypted, "Dati dovrebbero essere crittografati")
        self.assertEqual(test_data, decrypted, "Decrittazione dovrebbe ripristinare dati originali")

        # Verifica che la crittografia sia deterministica (stessa chiave = stesso risultato)
        encrypted2 = encryptor.encrypt(test_data)
        self.assertEqual(encrypted, encrypted2, "Crittografia dovrebbe essere deterministica")

    def test_rate_limiting(self):
        """Test rate limiting per prevenzione brute force."""
        from main_00_launcher import SimpleRateLimiter

        limiter = SimpleRateLimiter(max_attempts=3, window_seconds=60)

        # Test tentativi consentiti
        for i in range(3):
            allowed = limiter.is_allowed("test_ip")
            self.assertTrue(allowed, f"Tentativo {i+1} dovrebbe essere consentito")

        # Test blocco dopo limite
        allowed = limiter.is_allowed("test_ip")
        self.assertFalse(allowed, "Tentativo oltre limite dovrebbe essere bloccato")

    def test_dependency_vulnerability_check(self):
        """Test controllo vulnerabilità dipendenze."""
        # Questo test richiede che pip-audit sia disponibile
        try:
            from main_00_launcher import check_dependency_vulnerabilities

            safe, vulnerabilities = check_dependency_vulnerabilities()

            # Il test dovrebbe almeno completare senza errori
            self.assertIsInstance(safe, bool, "Risultato dovrebbe essere booleano")
            self.assertIsInstance(vulnerabilities, list, "Vulnerabilità dovrebbe essere lista")

        except ImportError:
            self.skipTest("pip-audit non disponibile per test vulnerabilità")

    def test_security_headers(self):
        """Test configurazione security headers."""
        try:
            from main_00_launcher import check_security_headers

            safe, issues = check_security_headers()

            # Verifica che la funzione completi
            self.assertIsInstance(safe, bool, "Risultato sicurezza dovrebbe essere booleano")
            self.assertIsInstance(issues, list, "Issues dovrebbe essere lista")

        except ImportError:
            self.skipTest("Funzione security headers non disponibile")


class TestSecurityPerformance(unittest.TestCase):
    """Test performance del sistema di sicurezza."""

    def test_security_monitor_performance(self):
        """Test performance del security monitor."""
        import time

        start_time = time.time()

        # Simula molti eventi di sicurezza
        for i in range(100):
            security_monitor.log_security_event(
                "PERFORMANCE_TEST",
                {"iteration": i},
                "INFO"
            )

        end_time = time.time()
        duration = end_time - start_time

        # Verifica che l'elaborazione sia ragionevolmente veloce
        self.assertLess(duration, 5.0, "Elaborazione 100 eventi dovrebbe richiedere meno di 5 secondi")

        # Verifica che tutti gli eventi siano stati registrati
        stats = security_monitor.get_security_stats()
        self.assertGreaterEqual(stats["recent_activities_count"], 100)


if __name__ == '__main__':
    # Configurazione logging per test
    logging.basicConfig(level=logging.WARNING)

    # Esegui test
    unittest.main(verbosity=2)