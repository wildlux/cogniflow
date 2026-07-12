#!/usr/bin/env python3
"""
Ultra-light main launcher for DSA Assistant
Coordinates all modules for secure application startup
"""

# Import core modules
from core.system_checks_module import perform_security_checks, test_imports
from core.performance_module import initialize_performance_monitor, start_performance_monitoring, stop_performance_monitoring
from core.theme_selector import select_theme
from core.auth_flow import handle_authentication, check_permissions
from core.app_launcher import launch_main_application

def run_app():
    """Ultra-light main application runner"""
    print("🚀 DSA Assistant Ultra-Light Launcher")
    print("=" * 50)

    # Initialize performance monitoring
    performance_available = initialize_performance_monitor()
    if performance_available:
        start_performance_monitoring()

    # Security checks
    if not perform_security_checks():
        print("❌ Security check failed")
        return

    # Import tests
    if not test_imports():
        print("❌ Import test failed")
        return

    try:
        print("✅ Starting DSA Assistant...")

        # Theme selection
        select_theme()

        # Authentication
        user = handle_authentication()
        if user is None:
            return  # GUI handles the flow

        # Permission check
        permissions = check_permissions(user)
        if permissions is None:
            return

        print(f"🔑 Permissions: {list(permissions.keys())}")

        # Launch main application
        success = launch_main_application(user, permissions)
        if not success:
            print("❌ Application launch failed")

    except Exception as e:
        print(f"❌ Application error: {e}")
        import traceback
        traceback.print_exc()

    # Cleanup
    if performance_available:
        stop_performance_monitoring()
    print("🏁 Finished")

if __name__ == "__main__":
    run_app()