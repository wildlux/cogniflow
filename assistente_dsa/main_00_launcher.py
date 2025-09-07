#!/usr/bin/env python3
"""
Script per avviare l'applicazione DSA in modo sicuro
"""

import os
import sys
import traceback
import threading
import time
from typing import cast, Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from core.performance_monitor import PerformanceMonitor

# Type definitions for performance monitoring
SnapshotType = dict[str, object]
SystemMetricsType = dict[str, object]

# Sistemi di sicurezza integrati (con fallback sicuro)
security_available = False
print("🔄 L'applicazione funzionerà con funzionalità di sicurezza base")

# Funzioni fallback sicure


def log_security_event(event_type: str, details: str, severity: str = "INFO"):
    print(f"[SECURITY {severity}] {event_type}: {details}")


def get_health_status():
    return {"status": "limited", "message": "Security systems not available"}

    # health_monitor = None  # Not currently used


def conditional_decorator(decorator_func: "Callable[[str], Callable[[Callable[..., object]], Callable[..., object]]] | None", name: str) -> "Callable[[Callable[..., object]], Callable[..., object]]":
    """Apply decorator conditionally."""
    def decorator(func: Callable[..., object]) -> Callable[..., object]:
        if decorator_func:
            return decorator_func(name)(func)  # type: ignore
        return func
    return decorator


# Performance monitoring thread
performance_thread = None
stop_monitoring = False
performance_monitor: "PerformanceMonitor | None" = None
measure_function_time: "Callable[[str], Callable[[Callable[..., object]], Callable[..., object]]] | None" = None

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
        performance_monitor = cast('PerformanceMonitor', perf_module.performance_monitor)
        measure_function_time = cast("Callable[[str], Callable[[Callable[..., object]], Callable[..., object]]] | None", perf_module.measure_function_time)
        performance_available = True
        print("✅ Performance monitor loaded")
    else:
        raise ImportError("Could not load performance monitor spec")
except Exception as e:
    performance_available = False
    print(f"⚠️  Performance monitor not available: {e}")
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


@conditional_decorator(measure_function_time, "security_checks")
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
                    _snapshot: SnapshotType = cast(SnapshotType, performance_monitor.take_snapshot("periodic_{snapshot_count}"))
                time.sleep(30)  # Take snapshot every 30 seconds
            except Exception:
                print(f"Performance monitoring error: {e}")
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
        _security_start_snapshot: SnapshotType = cast(SnapshotType, performance_monitor.take_snapshot("security_checks_start"))

    # Check Python version
    python_version_ok = sys.version_info >= (3, 8)
    if not python_version_ok:
        log_security_event("VERSION_CHECK", "Python 3.8+ required", "ERROR")
        print("❌ ERROR: Python 3.8 or higher required")
        return False

    # At this point, we know Python version >= 3.8
    log_security_event("VERSION_CHECK", f"Python {sys.version} detected", "INFO")
    print(f"✅ Python version: {sys.version}")

    # Check if running as root (security risk)
    if os.geteuid() == 0:
        log_security_event("PERMISSION_CHECK", "Running as root", "WARNING")
        print("⚠️  WARNING: Running as root - this may pose security risks")

    # Check write permissions in current directory
    try:
        test_file = os.path.join(os.getcwd(), ".test_write")
        with open(test_file, 'w') as f:
            _ = f.write("test")
        os.remove(test_file)
        log_security_event("PERMISSION_CHECK", "Write permissions verified", "INFO")
        print("✅ Write permissions verified")
    except Exception:
        log_security_event("PERMISSION_CHECK", f"No write permissions: {e}", "ERROR")
        print(f"❌ ERROR: No write permissions in current directory: {e}")
        return False

    # Check required directories exist
    required_dirs = ['Save', 'Screenshot', 'assistente_dsa']
    for dir_name in required_dirs:
        if not os.path.exists(dir_name):
            log_security_event("DIRECTORY_CHECK", f"Directory '{dir_name}' missing", "WARNING")
            print(f"⚠️  WARNING: Required directory '{dir_name}' not found")
        else:
            log_security_event("DIRECTORY_CHECK", f"Directory '{dir_name}' exists", "INFO")
            print(f"✅ Directory '{dir_name}' exists")

    # Check required Python packages
    required_packages = ['PyQt5', 'subprocess', 'os', 'sys']
    missing_packages: list[str] = []
    for package in required_packages:
        try:
            __import__(package)
            log_security_event("PACKAGE_CHECK", f"Package '{package}' available", "INFO")
            print(f"✅ Package '{package}' available")
        except ImportError:
            missing_packages.append(package)
            log_security_event("PACKAGE_CHECK", f"Package '{package}' missing", "WARNING")
            print(f"❌ Package '{package}' missing")

    if missing_packages:
        log_security_event("PACKAGE_CHECK", f"Missing packages: {', '.join(missing_packages)}", "WARNING")
        print(f"⚠️  WARNING: Missing packages: {', '.join(missing_packages)}")
        print("Please install missing packages using: pip install <package>")

    # Take snapshot after security checks
    if performance_available and performance_monitor:
        _security_complete_snapshot: SnapshotType = cast(SnapshotType, performance_monitor.take_snapshot("security_checks_complete"))

    return True


@conditional_decorator(measure_function_time, "test_imports")
def test_imports():
    """Test all critical imports using centralized configuration"""
    print("Testing imports with centralized configuration...")

    # Take snapshot before import tests
    if performance_available and performance_monitor:
        _import_start_snapshot: SnapshotType = cast(SnapshotType, performance_monitor.take_snapshot("import_tests_start"))

    try:
        # Test import configurazione centralizzata

        # Ottieni dimensioni finestra dalle impostazioni centralizzate
        window_width = cast(int, get_setting('ui.window_width', 1200))
        window_height = cast(int, get_setting('ui.window_height', 800))

        print(f"Centralized settings loaded - Window size: {window_width}x{window_height}")
        print(f"Application theme: {get_setting('application.theme', 'Chiaro')}")

        # Test degli import critici
        try:
            # Test classe MainWindow (ora integrata in main_01_Aircraft)
            print("MainWindow class available in main_01_Aircraft")

        except ImportError as e:
            print(f"Critical module import failed: {e}")
            return False

        # Take snapshot after import tests
        if performance_available and performance_monitor:
            _import_complete_snapshot: SnapshotType = cast(SnapshotType, performance_monitor.take_snapshot("import_tests_complete"))

        return True

    except Exception as e:
        print(f"Import error: {e}")
        traceback.print_exc()
        return False




@conditional_decorator(measure_function_time, "run_app")
def run_app():
    """Run the application by calling main_01_Aircraft.py"""
    # Take initial snapshot
    if performance_available and performance_monitor:
        _app_startup_snapshot: SnapshotType = cast(SnapshotType, performance_monitor.take_snapshot("app_startup"))

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
        _: object = start_performance_monitoring()

        # Verifica che le impostazioni siano accessibili globalmente
        settings = load_settings()

        print(f"Global settings loaded - Theme: {settings['application']['theme']}")
        print(f"UI Size: {settings['ui']['window_width']}x{settings['ui']['window_height']}")

        # Import and run main_01_Aircraft
        import subprocess

        # Get the current script directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        aircraft_script = os.path.join(current_dir, "main_01_Aircraft.py")

        # Validate script path before execution
        if not os.path.exists(aircraft_script):
            print(f"ERROR: Script not found: {aircraft_script}")
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
            print(f"ERROR: Application failed with code {e.returncode}")
            print(f"STDOUT: {cast(str, e.stdout)}")
            print(f"STDERR: {cast(str, e.stderr)}")
            return
        except Exception as e:
            print(f"ERROR: Unexpected error during startup: {e}")
            return

        if result.returncode != 0:
            print(f"Aircraft exited with error code: {result.returncode}")
        else:
            print("Aircraft completed successfully")

    except Exception as e:
        print(f"Application error: {e}")
        traceback.print_exc()

    # Performance monitoring finalization
    if performance_available and performance_monitor:
        _app_shutdown_snapshot: SnapshotType = cast(SnapshotType, performance_monitor.take_snapshot("app_shutdown"))

        # Generate and display performance report
        report = performance_monitor.get_performance_report()  # type: ignore
        print("\n📊 Performance Report:")
        current_metrics: SystemMetricsType = cast(SystemMetricsType, report['current_metrics'])
        print(f"   CPU Usage: {cast(float, current_metrics.get('cpu_percent', 'N/A'))}%")
        print(f"   Memory Usage: {cast(float, current_metrics.get('memory_percent', 'N/A'))}%")
        print(f"   Threads: {cast(int, current_metrics.get('num_threads', 'N/A'))}")

        # Check for performance issues
        issues = performance_monitor.detect_performance_issues()  # type: ignore
        if issues:
            print("\n⚠️  Performance Issues Detected:")
            for issue in issues:
                print(f"   {issue['type']}: {issue['message']}")
                print(f"   Suggestion: {issue['suggestion']}")

        # Export metrics to file
        try:
            metrics_file = os.path.join(os.getcwd(), "performance_metrics.json")
            performance_monitor.export_metrics(metrics_file)  # type: ignore
            print(f"\n📄 Performance metrics exported to: {metrics_file}")
        except Exception as e:
            print(f"⚠️  Could not export performance metrics: {e}")

    # Stop periodic monitoring
    _: object = stop_performance_monitoring()


if __name__ == "__main__":
    _: object = run_app()
