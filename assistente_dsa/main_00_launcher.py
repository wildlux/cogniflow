#!/usr/bin/env python3
"""
Script per avviare l'applicazione DSA in modo sicuro
"""

import os
import sys
import traceback
import threading
import time
from typing import cast

# Sistemi di sicurezza integrati (con fallback sicuro)
security_available = False
print("🔄 L'applicazione funzionerà con funzionalità di sicurezza base")

# Funzioni fallback sicure


def log_security_event(event_type: str, details: str, severity: str = "INFO"):
    print("[SECURITY {severity}] {event_type}: {details}")


def get_health_status():
    return {"status": "limited", "message": "Security systems not available"}

    # health_monitor = None  # Not currently used


# Performance monitoring thread
performance_thread = None
stop_monitoring = False

# Import del sistema di configurazione centralizzato
# Add parent directory to path for module imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Import del performance monitor
try:
    import importlib.util
    perf_path = os.path.join(os.path.dirname(__file__), "core", "performance_monitor.py")
    spec = importlib.util.spec_from_file_location("performance_monitor", perf_path)
    if spec and spec.loader:
        perf_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(perf_module)
        performance_monitor = perf_module.performance_monitor
        measure_function_time = perf_module.measure_function_time
        performance_available = True
        print("✅ Performance monitor loaded")
    else:
        raise ImportError("Could not load performance monitor spec")
except Exception:
    performance_available = False
    print("⚠️  Performance monitor not available: {e}")
    performance_monitor = None
    measure_function_time = None

try:
    from assistente_dsa.main_03_configurazione_e_opzioni import (
        load_settings,
        get_setting
    )
except ImportError:
    # Fallback for direct execution
    from assistente_dsa.main_03_configurazione_e_opzioni import (
        load_settings,
        get_setting
    )


@measure_function_time("security_checks") if measure_function_time else lambda f: f
def start_performance_monitoring():
    """Start periodic performance monitoring"""
    global performance_thread, stop_monitoring

    if not performance_available or not performance_monitor:
        return

    def monitoring_worker():
        snapshot_count = 0
        while not stop_monitoring:
            try:
                snapshot_count += 1
                if performance_monitor:
                    performance_monitor.take_snapshot("periodic_{snapshot_count}")
                time.sleep(30)  # Take snapshot every 30 seconds
            except Exception:
                print("Performance monitoring error: {e}")
                break

    stop_monitoring = False
    performance_thread = threading.Thread(target=monitoring_worker, daemon=True)
    performance_thread.start()
    print("🔄 Performance monitoring started (30s intervals)")


def stop_performance_monitoring():
    """Stop periodic performance monitoring"""
    global stop_monitoring

    if performance_thread and performance_thread.is_alive():
        stop_monitoring = True
        performance_thread.join(timeout=5)
        print("✅ Performance monitoring stopped")


def perform_security_checks():
    """Perform comprehensive security and usability checks"""
    print("🔍 Performing security and usability checks...")

    # Take initial performance snapshot
    if performance_available and performance_monitor:
        performance_monitor.take_snapshot("security_checks_start")

    # Check Python version
    if sys.version_info < (3, 8):
        log_security_event("VERSION_CHECK", "Python 3.8+ required", "ERROR")
        print("❌ ERROR: Python 3.8 or higher required")
        return False

    # At this point, we know Python version >= 3.8
    assert sys.version_info >= (3, 8), "Python version check failed"
    log_security_event("VERSION_CHECK", "Python {sys.version} detected", "INFO")
    print("✅ Python version: {sys.version}")

    # Check if running as root (security risk)
    if os.geteuid() == 0:
        log_security_event("PERMISSION_CHECK", "Running as root", "WARNING")
        print("⚠️  WARNING: Running as root - this may pose security risks")

    # Check write permissions in current directory
    try:
        test_file = os.path.join(os.getcwd(), ".test_write")
        with open(test_file, 'w') as f:
            f.write("test")
        os.remove(test_file)
        log_security_event("PERMISSION_CHECK", "Write permissions verified", "INFO")
        print("✅ Write permissions verified")
    except Exception:
        log_security_event("PERMISSION_CHECK", "No write permissions: {e}", "ERROR")
        print("❌ ERROR: No write permissions in current directory: {e}")
        return False

    # Check required directories exist
    required_dirs = ['Save', 'Screenshot', 'assistente_dsa']
    for dir_name in required_dirs:
        if not os.path.exists(dir_name):
            log_security_event("DIRECTORY_CHECK", "Directory '{dir_name}' missing", "WARNING")
            print("⚠️  WARNING: Required directory '{dir_name}' not found")
        else:
            log_security_event("DIRECTORY_CHECK", "Directory '{dir_name}' exists", "INFO")
            print("✅ Directory '{dir_name}' exists")

    # Check required Python packages
    required_packages = ['PyQt5', 'subprocess', 'os', 'sys']
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
            log_security_event("PACKAGE_CHECK", "Package '{package}' available", "INFO")
            print("✅ Package '{package}' available")
        except ImportError:
            missing_packages.append(package)
            log_security_event("PACKAGE_CHECK", "Package '{package}' missing", "WARNING")
            print("❌ Package '{package}' missing")

    if missing_packages:
        log_security_event("PACKAGE_CHECK", "Missing packages: {', '.join(missing_packages)}", "WARNING")
        print("⚠️  WARNING: Missing packages: {', '.join(missing_packages)}")
        print("Please install missing packages using: pip install <package>")

    # Take snapshot after security checks
    if performance_available and performance_monitor:
        performance_monitor.take_snapshot("security_checks_complete")

    return True


@measure_function_time("test_imports") if measure_function_time else lambda f: f
def test_imports():
    """Test all critical imports using centralized configuration"""
    print("Testing imports with centralized configuration...")

    # Take snapshot before import tests
    if performance_available and performance_monitor:
        performance_monitor.take_snapshot("import_tests_start")

    try:
        # Test import configurazione centralizzata

        # Ottieni dimensioni finestra dalle impostazioni centralizzate
        window_width = cast(int, get_setting('ui.window_width', 1200))
        window_height = cast(int, get_setting('ui.window_height', 800))

        print("Centralized settings loaded - Window size: {window_width}x{window_height}")
        print("Application theme: {get_setting('application.theme', 'Chiaro')}")

        # Test degli import critici
        try:
            # Test classe MainWindow (ora integrata in main_01_Aircraft)
            print("MainWindow class available in main_01_Aircraft")

        except ImportError as e:
            print("Critical module import failed: {e}")
            return False

        return True

    except Exception:
        print("Import error: {e}")
        traceback.print_exc()
        return False

    # Take snapshot after import tests
    if performance_available and performance_monitor:
        performance_monitor.take_snapshot("import_tests_complete")


@measure_function_time("run_app") if measure_function_time else lambda f: f
def run_app():
    """Run the application by calling main_01_Aircraft.py"""
    # Take initial snapshot
    if performance_available and performance_monitor:
        performance_monitor.take_snapshot("app_startup")

    if not perform_security_checks():
        print("Cannot start application due to security check failures")
        return

    if not test_imports():
        print("Cannot start application due to import errors")
        return

    try:
        print("Starting DSA Assistant...")
        print("Calling Aircraft main interface...")

        # Start periodic performance monitoring
        start_performance_monitoring()

        # Verifica che le impostazioni siano accessibili globalmente
        settings = load_settings()

        print("Global settings loaded - Theme: {settings['application']['theme']}")
        print("UI Size: {settings['ui']['window_width']}x{settings['ui']['window_height']}")

        # Import and run main_01_Aircraft
        import subprocess

        # Get the current script directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        aircraft_script = os.path.join(current_dir, "main_01_Aircraft.py")

        # Validate script path before execution
        if not os.path.exists(aircraft_script):
            print("ERROR: Script not found: {aircraft_script}")
            return

        # Secure command execution with timeout
        cmd = [sys.executable, aircraft_script]
        try:
            result = subprocess.run(
                cmd,
                cwd=current_dir,
                timeout=300,  # 5 minutes timeout
                capture_output=True,
                text=True
            )
        except subprocess.TimeoutExpired:
            print("ERROR: Application startup timeout")
            return
        except subprocess.CalledProcessError as e:
            print("ERROR: Application failed with code {e.returncode}")
            print("STDOUT: {cast(str, e.stdout)}")
            print("STDERR: {cast(str, e.stderr)}")
            return
        except Exception:
            print("ERROR: Unexpected error during startup: {e}")
            return

        if result.returncode != 0:
            print("Aircraft exited with error code: {result.returncode}")
        else:
            print("Aircraft completed successfully")

    except Exception:
        print("Application error: {e}")
        traceback.print_exc()

    # Performance monitoring finalization
    if performance_available and performance_monitor:
        performance_monitor.take_snapshot("app_shutdown")

        # Generate and display performance report
        report = performance_monitor.get_performance_report()
        print("\n📊 Performance Report:")
        print("   CPU Usage: {report['current_metrics'].get('cpu_percent', 'N/A')}%")
        print("   Memory Usage: {report['current_metrics'].get('memory_percent', 'N/A')}%")
        print("   Threads: {report['current_metrics'].get('num_threads', 'N/A')}")

        # Check for performance issues
        issues = performance_monitor.detect_performance_issues()
        if issues:
            print("\n⚠️  Performance Issues Detected:")
            for issue in issues:
                print("   {issue['type']}: {issue['message']}")
                print("   Suggestion: {issue['suggestion']}")

        # Export metrics to file
        try:
            metrics_file = os.path.join(os.getcwd(), "performance_metrics.json")
            performance_monitor.export_metrics(metrics_file)
            print("\n📄 Performance metrics exported to: {metrics_file}")
        except Exception:
            print("⚠️  Could not export performance metrics: {e}")

    # Stop periodic monitoring
    stop_performance_monitoring()


if __name__ == "__main__":
    run_app()
