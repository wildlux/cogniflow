#!/usr/bin/env python3
"""
DSA Assistant Launcher - Main Entry Point
Author: Paolo Lo Bello
This is the simplified main launcher that imports from modular components.
"""

# Import modular components
from .Autenticazione_e_Accesso.app_launcher import run_app
from .core.security_dashboard import start_security_monitoring

# Main entry point
if __name__ == "__main__":
    # Start security monitoring
    start_security_monitoring()
    print("🔒 Security monitoring started")

    run_app()