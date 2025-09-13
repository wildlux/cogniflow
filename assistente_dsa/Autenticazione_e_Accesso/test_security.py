#!/usr/bin/env python3
"""
Test suite for security implementations
"""

import sys
import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from Autenticazione_e_Accesso.security_utils import (
    SecureEncryptor,
    validate_input,
    hash_password_secure,
    verify_password_secure,
    check_file_permissions,
    secure_file_operation,
    log_security_event
)


class TestSecurity(unittest.TestCase):
    """Test cases for security implementations"""

    def setUp(self):
        """Set up test fixtures"""
        self.test_key = "test_encryption_key_12345"
        self.encryptor = SecureEncryptor(self.test_key)

    def test_encrypt_decrypt(self):
        """Test encryption and decryption"""
        test_data = "Hello, World! This is a test message."

        # Test encryption
        encrypted = self.encryptor.encrypt(test_data)
        self.assertIsInstance(encrypted, str)
        self.assertNotEqual(encrypted, test_data)

        # Test decryption
        try:
            decrypted = self.encryptor.decrypt(encrypted)
            self.assertEqual(decrypted, test_data)
        except ImportError:
            # Skip if cryptography is not available
            self.skipTest("Cryptography library not available")

    def test_password_hashing(self):
        """Test password hashing and verification"""
        password = "my_secure_password_123"

        # Hash password
        hashed = hash_password_secure(password)
        self.assertIsInstance(hashed, str)
        self.assertTrue(hashed.startswith("pbkdf2_sha256$"))

        # Verify password
        self.assertTrue(verify_password_secure(password, hashed))
        self.assertFalse(verify_password_secure("wrong_password", hashed))

    def test_input_validation(self):
        """Test input validation"""
        # Valid input
        self.assertTrue(validate_input("hello world", max_length=50))
        self.assertTrue(validate_input("test@example.com", allowed_chars="a-zA-Z0-9@."))

        # Invalid input
        self.assertFalse(validate_input("hello world" * 100, max_length=50))  # Too long
        self.assertFalse(validate_input("test<script>", allowed_chars="a-z"))  # Invalid chars
        self.assertFalse(validate_input("../../../etc/passwd"))  # Dangerous pattern

    def test_file_permissions(self):
        """Test file permission checking"""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"test content")
            temp_file = f.name

        try:
            perms = check_file_permissions(temp_file)
            self.assertIsInstance(perms, dict)
            self.assertIn("permissions", perms)
            self.assertIn("secure", perms)
        finally:
            os.unlink(temp_file)

    def test_secure_file_operation(self):
        """Test secure file operations"""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = os.path.join(temp_dir, "test.txt")
            test_content = "This is test content"

            # Test write
            success, _ = secure_file_operation(test_file, "write", test_content)
            self.assertTrue(success)
            self.assertTrue(os.path.exists(test_file))

            # Test read
            success, content = secure_file_operation(test_file, "read")
            self.assertTrue(success)
            self.assertEqual(content, test_content)

            # Test delete
            success, _ = secure_file_operation(test_file, "delete")
            self.assertTrue(success)
            self.assertFalse(os.path.exists(test_file))

    @patch('Autenticazione_e_Accesso.security_utils.print')
    def test_security_logging(self, mock_print):
        """Test security event logging"""
        # Test normal logging
        log_security_event("TEST_EVENT", "Test message", "INFO")
        mock_print.assert_called()

        # Test sensitive data protection
        log_security_event("AUTH_FAILURE", "Password: secret123", "WARNING")
        # Should not log the actual password
        call_args = mock_print.call_args[0][0]
        self.assertNotIn("secret123", call_args)


if __name__ == "__main__":
    print("🧪 Running security tests...")
    unittest.main(verbosity=2)