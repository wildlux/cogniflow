#!/usr/bin/env python3
"""
DSA Assistant Launcher - Main Entry Point
This is the simplified main launcher that imports from modular components.
"""

# Import modular components
import sys
import os

# Add current directory to path for absolute imports
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Import modules (using explicit imports for better code clarity)
# Note: These may show linting warnings but work correctly at runtime
# The modules are added to sys.path above, so imports work at runtime
from Autenticazione_e_Accesso.security_utils import (  # type: ignore
    SecureEncryptor, SimpleEncryptor, SimpleRateLimiter,
    log_security_event, get_health_status, conditional_decorator,
    _sanitize_command, check_package, validate_input,
    generate_secure_token, hash_password_secure, verify_password_secure,
    check_file_permissions, secure_file_operation,
    check_dependency_vulnerabilities, check_security_headers,
    check_directory, perform_security_checks,
    encryptor, rate_limiter
)
from Autenticazione_e_Accesso.auth_manager import SimpleAuthManager, get_auth_manager  # type: ignore
from Autenticazione_e_Accesso.gui_components import AdminSetupDialog, LauncherMainWindow  # type: ignore
from Autenticazione_e_Accesso.app_launcher import run_app  # type: ignore
from core.security_dashboard import start_security_monitoring  # type: ignore

# Main entry point
if __name__ == "__main__":
    # Start security monitoring
    start_security_monitoring()
    print("🔒 Security monitoring started")

    run_app()