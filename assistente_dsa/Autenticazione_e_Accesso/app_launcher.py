import os
import sys
import json
import time
import threading
import subprocess
import traceback
from typing import cast, Callable, Any

# Add current directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Import required modules
from .security_utils import _sanitize_command, perform_security_checks
from .gui_components import LoginDialog, LauncherMainWindow
from .auth_manager import AUTH_AVAILABLE, auth_manager

# Application launcher module
# Contains application startup, launch logic, and performance monitoring

# Performance monitoring variables
performance_thread = None
stop_monitoring = False
performance_monitor = None
measure_function_time = None
performance_available = False

def start_performance_monitoring():
    global performance_thread, stop_monitoring
    if not performance_available or not performance_monitor:
        return

    def monitoring_worker():
        snapshot_count = 0
        while not stop_monitoring:
            try:
                snapshot_count += 1
                if performance_monitor:
                    performance_monitor.take_snapshot(f"periodic_{snapshot_count}")
                time.sleep(30)
            except Exception as e:
                print(f"Performance monitoring error: {e}")
                break

    stop_monitoring = False
    performance_thread = threading.Thread(target=monitoring_worker, daemon=True)
    performance_thread.start()
    print("🔄 Performance monitoring started (30s intervals)")


def stop_performance_monitoring():
    global stop_monitoring
    if performance_thread and performance_thread.is_alive():
        stop_monitoring = True
        performance_thread.join(timeout=5)
        print("✅ Performance monitoring stopped")


def test_imports():
    print("Testing imports with centralized configuration...")

    if performance_available and performance_monitor:
        performance_monitor.take_snapshot("import_tests_start")

    try:
        from main_03_configurazione_e_opzioni import (
            load_settings,
            get_setting,
        )
        window_width = cast(int, get_setting("ui.window_width", 1200))
        window_height = cast(int, get_setting("ui.window_height", 800))
        print(f"Centralized settings loaded - Window size: {window_width}x {window_height}")
        print(f"Application theme: {get_setting('application.theme', 'Chiaro')}")

        try:
            import importlib.util
            aircraft_path = os.path.join(os.path.dirname(__file__), "main_01_Aircraft.py")
            spec = importlib.util.spec_from_file_location("main_01_Aircraft", aircraft_path)
            if spec is None or spec.loader is None:
                print("⚠️  Could not load main_01_Aircraft spec, but continuing...")
                return True  # Continue anyway
            main_01_Aircraft = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(main_01_Aircraft)
            print("✅ Main module (main_01_Aircraft) imported successfully")
        except Exception as e:
            print(f"⚠️  Main module import failed: {e}, but continuing...")
            return True  # Continue anyway

        if performance_available and performance_monitor:
            performance_monitor.take_snapshot("import_tests_complete")

        return True
    except Exception as e:
        print(f"Import error: {e}")
        traceback.print_exc()
        return False


def select_theme():
    print("\n🎨 Selezione Tema Automatica:")
    default_themes = [{"name": "Professionale", "icon": "💼", "description": "Per professionisti e studenti universitari"}, {"name": "Studente", "icon": "🎒", "description": "Per ragazzi che vanno a scuola"}, {"name": "Chimico", "icon": "🥽", "description": "Per chimici o subacquei"}, {"name": "Donna", "icon": "👝", "description": "Per donne che hanno tutto in borsa"}, {"name": "Artigiano", "icon": "🧰", "description": "Per artigiani, cassetta degli attrezzi"}, {"name": "Specchio", "icon": "🪞", "description": "Tema specchio"}, {"name": "Magico", "icon": "🪄", "description": "Tema magico"}, {"name": "Pensieri", "icon": "💭", "description": "Tema pensieri"}, {"name": "Nuvola", "icon": "🗯", "description": "Tema nuvola"}, {"name": "Audio", "icon": "🔊", "description": "Tema audio"}, {"name": "Chat", "icon": "💬", "description": "Tema chat"}]
    from main_03_configurazione_e_opzioni import get_setting, set_setting
    themes = get_setting("themes.available", default_themes)
    if not themes:
        print("Nessun tema disponibile")
        return
    selected_theme = cast(str, themes[0]["name"])
    set_setting("themes.selected", selected_theme)
    print(f"✅ Tema selezionato automaticamente: {selected_theme}")
    print("ℹ️  Nota: Menu di selezione temi disabilitato temporaneamente per stabilità")


def open_launcher_gui():
    try:
        from PyQt6.QtWidgets import QApplication
        pyqt_available = True
    except ImportError:
        pyqt_available = False

    if not pyqt_available:
        print("❌ PyQt6 not available. Cannot open GUI window.")
        return

    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    from main_03_configurazione_e_opzioni import get_setting
    from gui_components import LoginDialog, LauncherMainWindow
    from .security_utils import _sanitize_command

    bypass_login = cast(bool, get_setting("startup.bypass_login", False))

    if bypass_login:
        print("🔓 Bypass login abilitato - Avvio diretto dell'applicazione principale...")
        current_dir = os.path.dirname(os.path.abspath(__file__))
        aircraft_script = os.path.join(current_dir, "main_01_Aircraft.py")

        if os.path.exists(aircraft_script):
            cmd = [sys.executable, aircraft_script]
            sanitized_cmd = _sanitize_command(cmd)
            try:
                subprocess.Popen(sanitized_cmd, cwd=current_dir)
                print("✅ Applicazione principale avviata con successo")
            except Exception as e:
                print("❌ Errore avvio applicazione principale: Controlla i log per dettagli")
                try:
                    with open(os.path.join(os.path.dirname(__file__), "error.log"), "a") as f:
                        f.write(f"{time.time()}: Errore avvio app - {type(e).__name__}\n")
                except Exception:
                    pass
        else:
            print(f"❌ Script applicazione principale non trovato: {aircraft_script}")
        return

    print("🔐 Bypass login disabilitato - Richiesta autenticazione...")
    login_dialog = LoginDialog()
    result = login_dialog.exec()
    if result == LoginDialog.DialogCode.Accepted:
        print("✅ Login riuscito - Avvio launcher...")
        window = LauncherMainWindow(login_dialog.authenticated_user)
        window.show()
        app.exec()
    else:
        print("❌ Login annullato o fallito - Applicazione non avviata")
        return


def run_app():
    if performance_available and performance_monitor:
        performance_monitor.take_snapshot("app_startup")

    from security_utils import perform_security_checks

    if not perform_security_checks():
        print("❌ Cannot start application due to security check failures")
        return

    if not test_imports():
        print("❌ Cannot start application due to import errors")
        return

    try:
        print("✅ Starting DSA Assistant...")
        print("✈️ Calling Aircraft main interface...")
        start_performance_monitoring()
        print("🔐 Authentication system ready")

        from main_03_configurazione_e_opzioni import load_settings, get_setting
        settings = load_settings()
        selected_theme_name = cast(str, get_setting("themes.selected", "Professionale"))
        themes = cast(list[dict[str, str]], get_setting("themes.available", []))
        selected_theme_icon = next((cast(str, t["icon"]) for t in themes if cast(str, t["name"]) == selected_theme_name), "🎨")

        print(f"✅ Global settings loaded - Theme: {settings['application']['theme']}")
        print(f"✅ UI Size: {settings['ui']['window_width']}x{settings['ui']['window_height']}")
        print(f"✅ Selected Theme: {selected_theme_icon} {selected_theme_name}")
        print("🔐 Proceeding to authentication...")

        print("🎨 Theme selection skipped for debugging")
        bypass_login = cast(bool, get_setting("startup.bypass_login", True))
        print(f"🔐 Bypass login setting: {bypass_login}")

        if bypass_login:
            print("\n🔓 Bypass login abilitato - Accesso come admin...")
            current_user = {"username": "admin", "full_name": "Administrator", "group": "Administrator"}
        else:
            print("\n🔐 Aprire finestra di autenticazione...")
            open_launcher_gui()
            return

        from Autenticazione_e_Accesso.auth_manager import AUTH_AVAILABLE, auth_manager
        if AUTH_AVAILABLE and auth_manager:
            permissions = auth_manager.get_user_permissions(current_user["username"])
            if not permissions.get("system_access", False):
                print("❌ Accesso al sistema negato")
                return
        else:
            permissions = {"system_access": True, "ai_access": True}

        print(f"🔑 Permessi caricati: {list(permissions.keys())}")
        print("\n🚀 Avvio applicazione principale...")

        current_dir = os.path.dirname(os.path.abspath(__file__))
        aircraft_script = os.path.join(current_dir, "main_01_Aircraft.py")

        if not os.path.exists(aircraft_script):
            print(f"❌ ERROR: Script not found: {aircraft_script}")
            return

        print(f"✈️ Launching: {aircraft_script}")
        cmd = [sys.executable, aircraft_script]
        env = os.environ.copy()
        env["DSA_USERNAME"] = current_user["username"]
        env["DSA_FULL_NAME"] = current_user["full_name"]
        env["DSA_GROUP"] = current_user.get("group", "Guest")
        env["DSA_PERMISSIONS"] = json.dumps(permissions)

        try:
            result = subprocess.run(cmd, cwd=current_dir, timeout=300, capture_output=True, text=True, env=env)
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

    if performance_available and performance_monitor:
        performance_monitor.take_snapshot("app_shutdown")
        report = performance_monitor.get_performance_report()
        print("\n📊 Performance Report:")
        try:
            from core.performance_monitor import SystemMetricsType
            current_metrics = cast(SystemMetricsType, report["current_metrics"])
            print(f"   CPU Usage: {cast(float, current_metrics.get('cpu_percent', 'N/A'))}%")
            print(f"   Memory Usage: {cast(float, current_metrics.get('memory_percent', 'N/A'))}%")
            print(f"   Threads: {cast(int, current_metrics.get('num_threads', 'N/A'))}")

            issues = performance_monitor.detect_performance_issues()
            if issues:
                print("\n⚠️  Performance Issues Detected:")
                for issue in issues:
                    print(f"   {issue['type']}: {issue['message']}")
                    print(f"   Suggestion: {issue['suggestion']}")

            try:
                metrics_file = os.path.join(os.getcwd(), "performance_metrics.json")
                performance_monitor.export_metrics(metrics_file)
                print(f"\n📄 Performance metrics exported to: {metrics_file}")
            except Exception as e:
                print(f"⚠️  Could not export performance metrics: {e}")
        except ImportError:
            print("   Performance metrics not available")

    stop_performance_monitoring()
    print("🏁 Application finished")