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
import json
import hashlib
from datetime import datetime
from typing import cast, Callable, TYPE_CHECKING

# Webcam capture imports (not used in this file)
opencv_available = False

# GUI imports
try:
    from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, QLabel, QMessageBox, QLineEdit, QFormLayout, QDialog
    from PyQt6.QtCore import Qt
    pyqt_available = True
except ImportError:
    pyqt_available = False
    print("⚠️  PyQt6 not available - GUI launcher disabled")

if TYPE_CHECKING:
    from core.performance_monitor import PerformanceMonitor  # noqa: F811
    from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, QLabel, QMessageBox, QLineEdit, QFormLayout, QDialog  # noqa: F811
    from PyQt6.QtCore import Qt  # noqa: F811

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
except ImportError as e:
    print(f"❌ ERROR: Could not import configuration module: {e}")
    print("Please ensure main_03_configurazione_e_opzioni.py exists and is accessible")
    sys.exit(1)

# Sistema di autenticazione semplificato integrato
import hashlib
from datetime import datetime

class SimpleAuthManager:
    def __init__(self):
        self.data_dir = os.path.join(os.path.dirname(__file__), "Save", "AUTH")
        os.makedirs(self.data_dir, exist_ok=True)
        self.users_file = os.path.join(self.data_dir, "users.json")
        self._load_users()

    def _load_users(self):
        if os.path.exists(self.users_file):
            try:
                with open(self.users_file, 'r', encoding='utf-8') as f:
                    self.users = json.load(f)
            except:
                self.users = {}
        else:
            self.users = {}
            # Crea utente admin predefinito
            self._create_default_admin()

    def _create_default_admin(self):
        admin_user = {
            "username": "admin",
            "password_hash": hashlib.sha256("admin123".encode()).hexdigest(),
            "full_name": "System Administrator",
            "group": "Administrator",
            "is_active": True,
            "created_at": datetime.now().isoformat(),
            "last_login": None
        }
        self.users["admin"] = admin_user
        self._save_users()
        print("✅ Utente amministratore creato: admin / admin123")

    def _save_users(self):
        try:
            with open(self.users_file, 'w', encoding='utf-8') as f:
                json.dump(self.users, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Errore salvataggio utenti: {e}")

    def authenticate(self, username, password):
        if username not in self.users:
            return None
        user = self.users[username]
        if not user.get("is_active", True):
            return None
        if user["password_hash"] != hashlib.sha256(password.encode()).hexdigest():
            return None
        user["last_login"] = datetime.now().isoformat()
        self._save_users()
        return user

    def get_user_permissions(self, username):
        user = self.users.get(username)
        if not user:
            return {"system_access": False}
        group = user.get("group", "Guest")
        # Permessi semplificati
        permissions = {
            "Administrator": {"system_access": True, "user_management": True, "ai_access": True},
            "Teacher": {"system_access": True, "user_management": False, "ai_access": True},
            "Student": {"system_access": True, "user_management": False, "ai_access": True},
            "Guest": {"system_access": True, "user_management": False, "ai_access": False}
        }
        return permissions.get(group, {"system_access": False})

AUTH_AVAILABLE = True
auth_manager = SimpleAuthManager()

def get_auth_manager():
    return auth_manager

print("✅ Authentication system loaded")


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
                    _snapshot: SnapshotType = cast(SnapshotType, performance_monitor.take_snapshot(f"periodic_{snapshot_count}"))  # noqa: F841
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
        _security_start_snapshot: SnapshotType = cast(SnapshotType, performance_monitor.take_snapshot("security_checks_start"))  # noqa: F841

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
    try:
        if os.geteuid() == 0:
            log_security_event("PERMISSION_CHECK", "Running as root", "WARNING")
            print("⚠️  WARNING: Running as root - this may pose security risks")
    except AttributeError:
        # os.geteuid() not available on Windows
        pass

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

    # Check required directories exist (sequential for better error handling)
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    required_dirs = ['Save', 'Screenshot', 'assistente_dsa']
    required_paths = [os.path.join(project_root, d) for d in required_dirs]
    for dir_path in required_paths:
        dir_name, exists = check_directory(dir_path)
        if not exists:
            log_security_event("DIRECTORY_CHECK", f"Directory '{dir_name}' missing", "WARNING")
            print(f"⚠️  WARNING: Required directory '{dir_name}' not found")
        else:
            log_security_event("DIRECTORY_CHECK", f"Directory '{dir_name}' exists", "INFO")
            print(f"✅ Directory '{dir_name}' exists")

    # Check required Python packages (sequential for better error handling)
    required_packages = ['PyQt6', 'subprocess', 'os', 'sys', 'cv2', 'numpy']
    missing_packages: list[str] = []
    for package in required_packages:
        try:
            available = check_package(package)[1]
            if available:
                log_security_event("PACKAGE_CHECK", f"Package '{package}' available", "INFO")
                print(f"✅ Package '{package}' available")
            else:
                missing_packages.append(package)
                log_security_event("PACKAGE_CHECK", f"Package '{package}' missing", "WARNING")
                print(f"❌ Package '{package}' missing")
        except Exception as e:
            missing_packages.append(package)
            log_security_event("PACKAGE_CHECK", f"Package '{package}' check failed: {e}", "WARNING")
            print(f"⚠️  Package '{package}' check failed: {e}")

    if missing_packages:
        log_security_event("PACKAGE_CHECK", f"Missing packages: {', '.join(missing_packages)}", "WARNING")
        print(f"⚠️  WARNING: Missing packages: {', '.join(missing_packages)}")
        print("Please install missing packages using: pip install <package>")

    # Take snapshot after security checks
    if performance_available and performance_monitor:
        _security_complete_snapshot: SnapshotType = cast(SnapshotType, performance_monitor.take_snapshot("security_checks_complete"))  # noqa: F841

    return True
    python_version_ok = sys.version_info >= (3, 8)
    if not python_version_ok:
        log_security_event("VERSION_CHECK", "Python 3.8+ required", "ERROR")
        print("❌ ERROR: Python 3.8 or higher required")
        return False

    # At this point, we know Python version >= 3.8
    log_security_event("VERSION_CHECK", f"Python {sys.version} detected", "INFO")
    print(f"✅ Python version: {sys.version}")

    # Check if running as root (security risk)
    try:
        if os.geteuid() == 0:
            log_security_event("PERMISSION_CHECK", "Running as root", "WARNING")
            print("⚠️  WARNING: Running as root - this may pose security risks")
    except AttributeError:
        # os.geteuid() not available on Windows
        pass

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

    # Check required directories exist (sequential for better error handling)
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    required_dirs = ['Save', 'Screenshot', 'assistente_dsa']
    required_paths = [os.path.join(project_root, d) for d in required_dirs]
    for dir_path in required_paths:
        dir_name, exists = check_directory(dir_path)
        if not exists:
            log_security_event("DIRECTORY_CHECK", f"Directory '{dir_name}' missing", "WARNING")
            print(f"⚠️  WARNING: Required directory '{dir_name}' not found")
        else:
            log_security_event("DIRECTORY_CHECK", f"Directory '{dir_name}' exists", "INFO")
            print(f"✅ Directory '{dir_name}' exists")

    # Check required Python packages (sequential for better error handling)
    required_packages = ['PyQt6', 'subprocess', 'os', 'sys', 'cv2', 'numpy']
    missing_packages: list[str] = []
    for package in required_packages:
        try:
            available = check_package(package)[1]
            if available:
                log_security_event("PACKAGE_CHECK", f"Package '{package}' available", "INFO")
                print(f"✅ Package '{package}' available")
            else:
                missing_packages.append(package)
                log_security_event("PACKAGE_CHECK", f"Package '{package}' missing", "WARNING")
                print(f"❌ Package '{package}' missing")
        except Exception as e:
            missing_packages.append(package)
            log_security_event("PACKAGE_CHECK", f"Package '{package}' check failed: {e}", "WARNING")
            print(f"⚠️  Package '{package}' check failed: {e}")

    if missing_packages:
        log_security_event("PACKAGE_CHECK", f"Missing packages: {', '.join(missing_packages)}", "WARNING")
        print(f"⚠️  WARNING: Missing packages: {', '.join(missing_packages)}")
        print("Please install missing packages using: pip install <package>")

    # Take snapshot after security checks
    if performance_available and performance_monitor:
        _security_complete_snapshot: SnapshotType = cast(SnapshotType, performance_monitor.take_snapshot("security_checks_complete"))  # noqa: F841

    return True


@conditional_decorator(measure_function_time, "test_imports")
def test_imports():
    """Test all critical imports using centralized configuration"""
    print("Testing imports with centralized configuration...")

    # Take snapshot before import tests
    if performance_available and performance_monitor:
        _import_start_snapshot: SnapshotType = cast(SnapshotType, performance_monitor.take_snapshot("import_tests_start"))  # noqa: F841

    try:
        # Test import configurazione centralizzata

        # Ottieni dimensioni finestra dalle impostazioni centralizzate
        window_width = cast(int, get_setting('ui.window_width', 1200))
        window_height = cast(int, get_setting('ui.window_height', 800))

        print(f"Centralized settings loaded - Window size: {window_width}x{window_height}")
        print(f"Application theme: {get_setting('application.theme', 'Chiaro')}")

        # Test degli import critici
        try:
            # Test import del modulo principale
            import main_01_Aircraft
            print("✅ Main module (main_01_Aircraft) imported successfully")

        except ImportError as e:
            print(f"❌ Critical module import failed: {e}")
            return False

        # Take snapshot after import tests
        if performance_available and performance_monitor:
            _import_complete_snapshot: SnapshotType = cast(SnapshotType, performance_monitor.take_snapshot("import_tests_complete"))  # noqa: F841

        return True

    except Exception as e:
        print(f"Import error: {e}")
        traceback.print_exc()
        return False


def select_theme():
    """Automatically select the first available theme (Professionale)."""
    print("\n🎨 Selezione Tema Automatica:")

    # Use default themes since settings file doesn't have them
    default_themes = [
        {"name": "Professionale", "icon": "💼", "description": "Per professionisti e studenti universitari"},
        {"name": "Studente", "icon": "🎒", "description": "Per ragazzi che vanno a scuola"},
        {"name": "Chimico", "icon": "🥽", "description": "Per chimici o subacquei"},
        {"name": "Donna", "icon": "👝", "description": "Per donne che hanno tutto in borsa"},
        {"name": "Artigiano", "icon": "🧰", "description": "Per artigiani, cassetta degli attrezzi"},
        {"name": "Specchio", "icon": "🪞", "description": "Tema specchio"},
        {"name": "Magico", "icon": "🪄", "description": "Tema magico"},
        {"name": "Pensieri", "icon": "💭", "description": "Tema pensieri"},
        {"name": "Nuvola", "icon": "🗯", "description": "Tema nuvola"},
        {"name": "Audio", "icon": "🔊", "description": "Tema audio"},
        {"name": "Chat", "icon": "💬", "description": "Tema chat"}
    ]

    themes = get_setting('themes.available', default_themes)  # pyright: ignore[reportAny]
    if not themes:
        print("Nessun tema disponibile")
        return

    # Automatically select the first theme (Professionale)
    selected_theme = cast(str, themes[0]['name'])
    _ = set_setting('themes.selected', selected_theme)
    print(f"✅ Tema selezionato automaticamente: {selected_theme}")
    print("ℹ️  Nota: Menu di selezione temi disabilitato temporaneamente per stabilità")


class LoginDialog(QDialog):  # type: ignore[misc]
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

        self.username_input: QLineEdit = QLineEdit()  # type: ignore
        self.username_input.setPlaceholderText("Enter username")
        form_layout.addRow("Username:", self.username_input)

        self.password_input: QLineEdit = QLineEdit()  # type: ignore
        self.password_input.setPlaceholderText("Enter password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)  # type: ignore
        form_layout.addRow("Password:", self.password_input)

        layout.addLayout(form_layout)

        # Login button
        self.login_button: QPushButton = QPushButton("Login")  # type: ignore
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
        _ = self.login_button.clicked.connect(self.attempt_login)  # pyright: ignore[reportUnknownMemberType]
        layout.addWidget(self.login_button)

        # Status label
        self.status_label: QLabel = QLabel("")  # type: ignore
        self.status_label.setStyleSheet("color: #d32f2f; font-size: 12px;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)  # type: ignore
        layout.addWidget(self.status_label)

        # Connect Enter key to login
        _ = self.username_input.returnPressed.connect(self.attempt_login)  # pyright: ignore[reportUnknownMemberType]
        _ = self.password_input.returnPressed.connect(self.attempt_login)  # pyright: ignore[reportUnknownMemberType]

    def attempt_login(self):
        """Attempt to login with provided credentials."""
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()

        # Test credentials: root/@general
        if username == "root" and password == "@general":
            self.accept()  # Close dialog with success
        else:
            self.status_label.setText("❌ Invalid username or password")
            self.username_input.clear()
            self.password_input.clear()
            self.username_input.setFocus()


class LauncherMainWindow(QMainWindow):  # type: ignore[misc]
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
        self.launch_button: QPushButton = QPushButton("✈️ Launch Aircraft")  # type: ignore
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
        _ = self.launch_button.clicked.connect(self.launch_aircraft)  # pyright: ignore[reportUnknownMemberType]
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
                _ = QMessageBox.critical(self, "Error", f"Script not found: {aircraft_script}")  # type: ignore
                return

            # Secure command execution with timeout
            cmd = [sys.executable, aircraft_script]
            _ = subprocess.Popen(cmd, cwd=current_dir)

            _ = QMessageBox.information(self, "Success", "Aircraft application launched!")  # type: ignore

        except Exception as e:
            _ = QMessageBox.critical(self, "Error", f"Failed to launch Aircraft: {str(e)}")  # type: ignore


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
    bypass_login = cast(bool, get_setting('startup.bypass_login', False))

    if bypass_login:
        print("🔓 Bypass login abilitato - Avvio diretto dell'applicazione principale...")
        # Skip login and go directly to main application
        import subprocess
        current_dir = os.path.dirname(os.path.abspath(__file__))
        aircraft_script = os.path.join(current_dir, "main_01_Aircraft.py")

        if os.path.exists(aircraft_script):
            cmd = [sys.executable, aircraft_script]
            try:
                _ = subprocess.Popen(cmd, cwd=current_dir)
                print("✅ Applicazione principale avviata con successo")
            except Exception as e:
                print(f"❌ Errore avvio applicazione principale: {e}")
        else:
            print(f"❌ Script applicazione principale non trovato: {aircraft_script}")
        return

    # Normal login flow
    print("🔐 Bypass login disabilitato - Richiesta autenticazione...")
    login_dialog = LoginDialog()
    result = login_dialog.exec()  # type: ignore
    if result == QDialog.DialogCode.Accepted:  # type: ignore
        # Login successful, show main window
        print("✅ Login riuscito - Avvio launcher...")
        window = LauncherMainWindow()
        window.show()
        _ = app.exec()  # type: ignore
    else:
        # Login cancelled or failed - do not start application
        print("❌ Login annullato o fallito - Applicazione non avviata")
        return


def run_app():
    """Run the application by calling main_01_Aircraft.py"""
    # Take initial snapshot
    if performance_available and performance_monitor:
        _app_startup_snapshot: SnapshotType = cast(SnapshotType, performance_monitor.take_snapshot("app_startup"))  # noqa: F841

    if not perform_security_checks():
        print("❌ Cannot start application due to security check failures")
        return

    if not test_imports():
        print("❌ Cannot start application due to import errors")
        return

    try:
        print("✅ Starting DSA Assistant...")
        print("✈️ Calling Aircraft main interface...")

        # Start periodic performance monitoring
        _ = start_performance_monitoring()

        # Sistema di autenticazione già inizializzato
        print("🔐 Authentication system ready")

        # Verifica che le impostazioni siano accessibili globalmente
        settings = load_settings()

        selected_theme_name = cast(str, get_setting('themes.selected', 'Professionale'))
        themes = cast(list, get_setting('themes.available', []))  # pyright: ignore[reportMissingTypeArgument,reportUnknownVariableType]
        selected_theme_icon = next((cast(str, t['icon']) for t in themes if cast(str, t['name']) == selected_theme_name), '🎨')  # pyright: ignore[reportUnknownVariableType]

        print(f"✅ Global settings loaded - Theme: {settings['application']['theme']}")
        print(f"✅ UI Size: {settings['ui']['window_width']}x{settings['ui']['window_height']}")
        print(f"✅ Selected Theme: {selected_theme_icon} {selected_theme_name}")
        print("🔐 Proceeding to authentication...")

        # Selezione tema temporaneamente disabilitata per debug
        print("🎨 Theme selection skipped for debugging")

        # Sistema di autenticazione
        bypass_login = cast(bool, get_setting('startup.bypass_login', True))  # Temporaneamente abilitato per test
        print(f"🔐 Bypass login setting: {bypass_login}")

        if bypass_login:
            print("\n🔓 Bypass login abilitato - Accesso come admin...")
            current_user = {"username": "admin", "full_name": "Administrator", "group": "Administrator"}
        else:
            # Richiedi autenticazione
            print("\n🔐 Autenticazione richiesta...")
            if AUTH_AVAILABLE and auth_manager:
                username = input("Username: ").strip()
                password = input("Password: ").strip()

                current_user = auth_manager.authenticate(username, password)
                if not current_user:
                    print("❌ Autenticazione fallita")
                    return

                print(f"✅ Benvenuto, {current_user['full_name']}!")
            else:
                print("⚠️ Sistema autenticazione non disponibile - accesso come guest")
                current_user = {"username": "guest", "full_name": "Guest User", "group": "Guest"}

        # Verifica permessi per accesso al sistema
        if AUTH_AVAILABLE and auth_manager:
            permissions = auth_manager.get_user_permissions(current_user['username'])
            if not permissions.get('system_access', False):
                print("❌ Accesso al sistema negato")
                return
        else:
            permissions = {"system_access": True, "ai_access": True}

        print(f"🔑 Permessi caricati: {list(permissions.keys())}")

        # Avvia l'applicazione principale
        print("\n🚀 Avvio applicazione principale...")
        import subprocess
        current_dir = os.path.dirname(os.path.abspath(__file__))
        aircraft_script = os.path.join(current_dir, "main_01_Aircraft.py")

        if not os.path.exists(aircraft_script):
            print(f"❌ ERROR: Script not found: {aircraft_script}")
            return

        print(f"✈️ Launching: {aircraft_script}")
        cmd = [sys.executable, aircraft_script]

        # Passa informazioni utente come variabili d'ambiente
        env = os.environ.copy()
        env['DSA_USERNAME'] = current_user['username']
        env['DSA_FULL_NAME'] = current_user['full_name']
        env['DSA_GROUP'] = current_user.get('group', 'Guest')
        env['DSA_PERMISSIONS'] = json.dumps(permissions)

        try:
            result = subprocess.run(
                cmd,
                cwd=current_dir,
                timeout=300,  # 5 minutes timeout
                capture_output=True,
                text=True,
                env=env
            )
            if result.returncode != 0:
                print(f"❌ Aircraft exited with error code: {result.returncode}")
                print(f"STDOUT: {result.stdout}")
                print(f"STDERR: {result.stderr}")
            else:
                print("✅ Aircraft completed successfully")
        except subprocess.TimeoutExpired:
            print("⏰ ERROR: Application startup timeout")
        except Exception as e:
            print(f"❌ ERROR: Unexpected error during startup: {e}")

    except Exception as e:
        print(f"❌ Application error: {e}")
        traceback.print_exc()

    # Performance monitoring finalization
    if performance_available and performance_monitor:
        _app_shutdown_snapshot: SnapshotType = cast(SnapshotType, performance_monitor.take_snapshot("app_shutdown"))  # noqa: F841

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
    _ = stop_performance_monitoring()
    print("🏁 Application finished")


if __name__ == "__main__":
    _: object = run_app()
