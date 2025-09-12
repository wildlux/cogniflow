"""
Configurazione per MediaPipe in macchina virtuale
Questo file gestisce l'esecuzione di MediaPipe in un ambiente virtuale separato
"""

import os
import json
import subprocess
import logging
from typing import Optional, Dict, Any


class MediaPipeVMConfig:
    """Gestisce la configurazione e l'esecuzione di MediaPipe in VM."""

    def __init__(self, config_file: str = "mediapipe_vm_config.json"):
        self.config_file = config_file
        self.config = self._load_config()
        self.vm_process: Optional[subprocess.Popen] = None

    def _load_config(self) -> Dict[str, Any]:
        """Carica la configurazione dalla VM."""
        default_config = {
            "vm_enabled": False,
            "vm_path": "/path/to/mediapipe/vm",
            "python_executable": "python3.9",
            "mediapipe_service_port": 8001,
            "vm_startup_timeout": 30,
            "auto_start_vm": False,
            "vm_environment": {
                "PYTHONPATH": "/path/to/mediapipe/vm",
                "MEDIAPIPE_SERVICE_URL": "http://localhost:8001",
            },
        }

        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    loaded_config = json.load(f)
                    default_config.update(loaded_config)
            except Exception as e:
                logging.error(f"Errore caricamento config VM: {e}")

        return default_config

    def save_config(self):
        """Salva la configurazione su file."""
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            logging.info(f"Configurazione VM salvata: {self.config_file}")
        except Exception as e:
            logging.error(f"Errore salvataggio config VM: {e}")

    def is_vm_available(self) -> bool:
        """Verifica se la VM è disponibile e configurata."""
        if not self.config.get("vm_enabled", False):
            return False

        vm_path = self.config.get("vm_path", "")
        if not os.path.exists(vm_path):
            logging.warning(f"Percorso VM non trovato: {vm_path}")
            return False

        python_exe = os.path.join(
            vm_path, self.config.get("python_executable", "python3.9")
        )
        if not os.path.exists(python_exe):
            logging.warning(f"Python VM non trovato: {python_exe}")
            return False

        return True

    def start_vm_service(self) -> bool:
        """Avvia il servizio MediaPipe nella VM."""
        if not self.is_vm_available():
            logging.error("VM MediaPipe non disponibile")
            return False

        try:
            vm_path = self.config["vm_path"]
            python_exe = self.config["python_executable"]
            service_script = os.path.join(vm_path, "mediapipe_service.py")

            if not os.path.exists(service_script):
                logging.error(f"Script servizio VM non trovato: {service_script}")
                return False

            # Imposta le variabili d'ambiente
            env = os.environ.copy()
            env.update(self.config.get("vm_environment", {}))

            # Avvia il processo nella VM
            self.vm_process = subprocess.Popen(
                [python_exe, service_script],
                cwd=vm_path,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            logging.info(f"Servizio MediaPipe VM avviato (PID: {self.vm_process.pid})")
            return True

        except Exception as e:
            logging.error(f"Errore avvio servizio VM: {e}")
            return False

    def stop_vm_service(self):
        """Ferma il servizio MediaPipe nella VM."""
        if self.vm_process:
            try:
                self.vm_process.terminate()
                self.vm_process.wait(timeout=10)
                logging.info("Servizio MediaPipe VM fermato")
            except subprocess.TimeoutExpired:
                self.vm_process.kill()
                logging.warning("Servizio MediaPipe VM forzatamente terminato")
            except Exception as e:
                logging.error(f"Errore arresto servizio VM: {e}")
            finally:
                self.vm_process = None

    def get_service_url(self) -> str:
        """Restituisce l'URL del servizio MediaPipe."""
        port = self.config.get("mediapipe_service_port", 8001)
        return f"http://localhost:{port}"

    def update_config(self, key: str, value: Any):
        """Aggiorna una configurazione specifica."""
        self.config[key] = value
        self.save_config()


# Istanza globale per l'applicazione
mediapipe_vm = MediaPipeVMConfig()
