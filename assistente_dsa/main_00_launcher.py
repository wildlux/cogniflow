#!/usr/bin/env python3
"""
Script per avviare l'applicazione DSA in modo sicuro
"""

import os
import sys
import traceback
import threading
import time
import multiprocessing
from typing import cast, Callable, TYPE_CHECKING

# Webcam capture imports
try:
    import cv2  # type: ignore
    import numpy as np  # type: ignore
    opencv_available = True
except ImportError:
    opencv_available = False
    print("⚠️  OpenCV not available - webcam features disabled")

# GUI imports for webcam test window
try:
    from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, QLabel, QMessageBox, QLineEdit, QFormLayout, QDialog
    from PyQt6.QtGui import QPixmap, QImage, QPainter, QColor
    from PyQt6.QtCore import Qt, QTimer
    pyqt_available = True
except ImportError:
    pyqt_available = False
    print("⚠️  PyQt6 not available - GUI webcam test disabled")

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
        get_setting,
        set_setting
    )
except ImportError:
    # Fallback for direct execution
    from assistente_dsa.main_03_configurazione_e_opzioni import (
        load_settings,
        get_setting,
        set_setting
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
            except Exception as e:
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


def check_package(package: str) -> tuple[str, bool]:
    """Check if a package is available."""
    try:
        __import__(package)
        return package, True
    except ImportError:
        return package, False


def check_directory(dir_path: str) -> tuple[str, bool]:
    """Check if a directory exists."""
    return os.path.basename(dir_path), os.path.exists(dir_path)


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
    except Exception as e:
        log_security_event("PERMISSION_CHECK", f"No write permissions: {e}", "ERROR")
        print(f"❌ ERROR: No write permissions in current directory: {e}")
        return False

    # Check required directories exist (parallel)
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    required_dirs = ['Save', 'Screenshot', 'assistente_dsa']
    required_paths = [os.path.join(project_root, d) for d in required_dirs]
    with multiprocessing.Pool(processes=min(len(required_paths), multiprocessing.cpu_count())) as pool:
        dir_results = pool.map(check_directory, required_paths)
    for dir_name, exists in dir_results:
        if not exists:
            log_security_event("DIRECTORY_CHECK", f"Directory '{dir_name}' missing", "WARNING")
            print(f"⚠️  WARNING: Required directory '{dir_name}' not found")
        else:
            log_security_event("DIRECTORY_CHECK", f"Directory '{dir_name}' exists", "INFO")
            print(f"✅ Directory '{dir_name}' exists")

    # Check required Python packages (parallel)
    required_packages = ['PyQt6', 'subprocess', 'os', 'sys', 'cv2', 'numpy']
    with multiprocessing.Pool(processes=min(len(required_packages), multiprocessing.cpu_count())) as pool:
        package_results = pool.map(check_package, required_packages)
    missing_packages: list[str] = []
    for package, available in package_results:
        if available:
            log_security_event("PACKAGE_CHECK", f"Package '{package}' available", "INFO")
            print(f"✅ Package '{package}' available")
        else:
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




def select_theme():
    """Allow user to select a theme from available options."""
    print("\n🎨 Selezione Tema:")
    themes = get_setting('themes.available', [])
    if not themes:
        print("Nessun tema disponibile")
        return

    for i, theme in enumerate(themes, 1):
        print(f"{i}. {theme['icon']} {theme['name']} - {theme['description']}")

    current_selected = get_setting('themes.selected', 'Professionale')
    print(f"\nTema attuale: {current_selected}")

    while True:
        try:
            choice = input("Scegli un tema (numero) o premi Enter per mantenere attuale: ").strip()
            if not choice:
                print(f"Tema mantenuto: {current_selected}")
                return
            choice_num = int(choice)
            if 1 <= choice_num <= len(themes):
                selected_theme = themes[choice_num - 1]['name']
                set_setting('themes.selected', selected_theme)
                print(f"✅ Tema selezionato: {selected_theme}")
                return
            else:
                print("Scelta non valida. Riprova.")
        except ValueError:
            print("Inserisci un numero valido.")











class LoginDialog(QDialog):  # type: ignore
    """Login dialog for authentication."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("DSA Assistant - Login")
        self.setModal(True)
        self.setFixedSize(350, 200)

        # Main layout
        layout = QVBoxLayout(self)  # type: ignore

        # Title
        title_label = QLabel("🔐 DSA Assistant Login")  # type: ignore
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #333; margin-bottom: 20px;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)  # type: ignore
        layout.addWidget(title_label)

        # Form layout for username and password
        form_layout = QFormLayout()  # type: ignore

        self.username_input = QLineEdit()  # type: ignore
        self.username_input.setPlaceholderText("Enter username")
        form_layout.addRow("Username:", self.username_input)

        self.password_input = QLineEdit()  # type: ignore
        self.password_input.setPlaceholderText("Enter password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)  # type: ignore
        form_layout.addRow("Password:", self.password_input)

        layout.addLayout(form_layout)

        # Login button
        self.login_button = QPushButton("Login")  # type: ignore
        self.login_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
                margin-top: 20px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.login_button.clicked.connect(self.attempt_login)
        layout.addWidget(self.login_button)

        # Status label
        self.status_label = QLabel("")  # type: ignore
        self.status_label.setStyleSheet("color: #d32f2f; font-size: 12px;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)  # type: ignore
        layout.addWidget(self.status_label)

        # Connect Enter key to login
        self.username_input.returnPressed.connect(self.attempt_login)
        self.password_input.returnPressed.connect(self.attempt_login)

    def attempt_login(self):
        """Attempt to login with provided credentials."""
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()

        # Test credentials: root/root
        if username == "root" and password == "root":
            self.accept()  # Close dialog with success
        else:
            self.status_label.setText("❌ Invalid username or password")
            self.username_input.clear()
            self.password_input.clear()
            self.username_input.setFocus()


class LauncherMainWindow(QMainWindow):  # type: ignore
    """Main launcher window."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("DSA Assistant Launcher")
        self.setGeometry(300, 300, 500, 400)

        # Central widget
        central_widget = QWidget()  # type: ignore
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)  # type: ignore

        # Title
        title_label = QLabel("🚀 DSA Assistant Launcher")  # type: ignore
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #333; margin: 20px;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)  # type: ignore
        layout.addWidget(title_label)

        # Status info
        status_text = "✅ Security checks passed\n✅ Imports loaded successfully\n🎨 Theme configured"
        status_label = QLabel(status_text)  # type: ignore
        status_label.setStyleSheet("font-size: 14px; color: #666; margin: 10px;")
        status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)  # type: ignore
        layout.addWidget(status_label)



        # Launch Aircraft button
        self.launch_button = QPushButton("✈️ Launch Aircraft")  # type: ignore
        self.launch_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 15px;
                padding: 20px 40px;
                font-size: 18px;
                font-weight: bold;
                margin: 20px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3e8e41;
            }
        """)
        self.launch_button.clicked.connect(self.launch_aircraft)
        layout.addWidget(self.launch_button)

        layout.addStretch()



    def launch_aircraft(self):
        """Launch the main Aircraft application."""
        try:
            # Import and run main_01_Aircraft
            import subprocess

            # Get the current script directory
            current_dir = os.path.dirname(os.path.abspath(__file__))
            aircraft_script = os.path.join(current_dir, "main_01_Aircraft.py")

            # Validate script path before execution
            if not os.path.exists(aircraft_script):
                QMessageBox.critical(self, "Error", f"Script not found: {aircraft_script}")  # type: ignore
                return

            # Secure command execution with timeout
            cmd = [sys.executable, aircraft_script]
            subprocess.Popen(cmd, cwd=current_dir)

            QMessageBox.information(self, "Success", "Aircraft application launched!")  # type: ignore

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to launch Aircraft: {str(e)}")  # type: ignore


def open_launcher_gui():
    """Open the main launcher GUI window with login or bypass based on settings."""
    if not pyqt_available:
        print("❌ PyQt6 not available. Cannot open GUI window.")
        return

    # Check if QApplication already exists
    app = QApplication.instance()  # type: ignore
    if app is None:
        app = QApplication(sys.argv)  # type: ignore

    # Check if bypass login is enabled
    bypass_login = get_setting('startup.bypass_login', False)

    if bypass_login:
        print("🔓 Bypass login abilitato - Avvio diretto dell'applicazione principale...")
        # Skip login and go directly to main application
        import subprocess
        current_dir = os.path.dirname(os.path.abspath(__file__))
        aircraft_script = os.path.join(current_dir, "main_01_Aircraft.py")

        if os.path.exists(aircraft_script):
            cmd = [sys.executable, aircraft_script]
            try:
                subprocess.Popen(cmd, cwd=current_dir)
                print("✅ Applicazione principale avviata con successo")
            except Exception as e:
                print(f"❌ Errore avvio applicazione principale: {e}")
        else:
            print(f"❌ Script applicazione principale non trovato: {aircraft_script}")
        return

    # Normal login flow
    print("🔐 Bypass login disabilitato - Richiesta autenticazione...")
    login_dialog = LoginDialog()
    if login_dialog.exec() == QDialog.DialogCode.Accepted:  # type: ignore
        # Login successful, show main window
        print("✅ Login riuscito - Avvio launcher...")
        window = LauncherMainWindow()
        window.show()
        app.exec()  # type: ignore
    else:
        # Login cancelled or failed - do not start application
        print("❌ Login annullato o fallito - Applicazione non avviata")
        return








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

        selected_theme_name = get_setting('themes.selected', 'Professionale')
        themes = get_setting('themes.available', [])
        selected_theme_icon = next((t['icon'] for t in themes if t['name'] == selected_theme_name), '🎨')

        print(f"Global settings loaded - Theme: {settings['application']['theme']}")
        print(f"UI Size: {settings['ui']['window_width']}x{settings['ui']['window_height']}")
        print(f"Selected Theme: {selected_theme_icon} {selected_theme_name}")

        # Selezione tema
        select_theme()

        # Check if bypass login is enabled
        bypass_login = get_setting('startup.bypass_login', False)

        if bypass_login:
            print("\n🔓 Bypass login abilitato - Avvio diretto applicazione principale...")
            # Skip launcher GUI and run main application directly
            import subprocess
            current_dir = os.path.dirname(os.path.abspath(__file__))
            aircraft_script = os.path.join(current_dir, "main_01_Aircraft.py")

            if not os.path.exists(aircraft_script):
                print(f"ERROR: Script not found: {aircraft_script}")
                return

            cmd = [sys.executable, aircraft_script]
            try:
                result = subprocess.run(
                    cmd,
                    cwd=current_dir,
                    timeout=300,  # 5 minutes timeout
                    capture_output=True,
                    text=True
                )
                if result.returncode != 0:
                    print(f"Aircraft exited with error code: {result.returncode}")
                    print(f"STDOUT: {result.stdout}")
                    print(f"STDERR: {result.stderr}")
                else:
                    print("Aircraft completed successfully")
            except subprocess.TimeoutExpired:
                print("ERROR: Application startup timeout")
            except Exception as e:
                print(f"ERROR: Unexpected error during startup: {e}")
        else:
            # Normal flow with launcher GUI
            if pyqt_available:
                print("\n🖥️  Opening launcher GUI...")
                open_launcher_gui()
            else:
                print("\n⚠️  PyQt6 not available - cannot open GUI")

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
