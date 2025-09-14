"""
Modulo per l'avvio dell'applicazione principale
"""

import os
import sys
import json
import subprocess
from typing import Dict, Any

def launch_main_application(user: Dict[str, Any], permissions: Dict[str, bool]) -> bool:
    """
    Avvia l'applicazione principale con le credenziali utente
    """
    print("✈️ Avvio applicazione principale...")

    current_dir = os.path.dirname(os.path.dirname(__file__))
    aircraft_script = os.path.join(current_dir, "main_01_Aircraft.py")

    if not os.path.exists(aircraft_script):
        print(f"❌ Script non trovato: {aircraft_script}")
        return False

    # Prepara comando e variabili d'ambiente
    cmd = [sys.executable, aircraft_script]
    env = os.environ.copy()
    env["DSA_USERNAME"] = user["username"]
    env["DSA_FULL_NAME"] = user["full_name"]
    env["DSA_GROUP"] = user.get("group", "Guest")
    env["DSA_PERMISSIONS"] = json.dumps(permissions)

    try:
        result = subprocess.run(
            cmd,
            cwd=current_dir,
            timeout=300,
            capture_output=True,
            text=True,
            env=env
        )

        if result.returncode != 0:
            print(f"❌ Codice uscita: {result.returncode}")
            print(f"STDOUT: {result.stdout}")
            print(f"STDERR: {result.stderr}")
            return False
        else:
            print("✅ Applicazione completata con successo")
            return True

    except subprocess.TimeoutExpired:
        print("⏰ Timeout applicazione")
        return False
    except Exception as e:
        print(f"❌ Errore: {e}")
        return False

def prepare_application_environment(user: Dict[str, Any], permissions: Dict[str, bool]) -> Dict[str, str]:
    """Prepare environment variables for the application."""
    env = os.environ.copy()
    env["DSA_USERNAME"] = user["username"]
    env["DSA_FULL_NAME"] = user["full_name"]
    env["DSA_GROUP"] = user.get("group", "Guest")
    env["DSA_PERMISSIONS"] = json.dumps(permissions)
    return env

def get_application_path() -> str:
    """Get the path to the main application script."""
    current_dir = os.path.dirname(os.path.dirname(__file__))
    return os.path.join(current_dir, "main_01_Aircraft.py")