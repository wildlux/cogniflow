#!/usr/bin/env python3
"""
Health Monitor - Sistema di monitoraggio salute applicazione
Controlla regolarmente lo stato di salute dei componenti critici
"""

import logging
import time
import threading
import psutil
from typing import Dict, List, Callable, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class HealthCheck:
    """Rappresenta un singolo health check."""

    def __init__(self, name: str, check_func: Callable, interval: int = 60, timeout: int = 10):
        """
        Inizializza un health check.

        Args:
            name: Nome del check
            check_func: Funzione che esegue il check
            interval: Intervallo in secondi tra controlli
            timeout: Timeout in secondi per il check
        """
        self.name = name
        self.check_func = check_func
        self.interval = interval
        self.timeout = timeout
        self.last_check = 0
        self.last_result = None
        self.last_error = None
        self.consecutive_failures = 0

    def should_run(self) -> bool:
        """Verifica se il check dovrebbe essere eseguito."""
        return time.time() - self.last_check >= self.interval

    def run(self) -> Dict[str, Any]:
        """Esegue il health check."""
        start_time = time.time()
        self.last_check = start_time

        try:
            result = self._run_with_timeout()
            self.last_result = result
            self.last_error = None
            self.consecutive_failures = 0

            return {
                "name": self.name,
                "status": "healthy",
                "result": result,
                "response_time": time.time() - start_time,
                "timestamp": datetime.now()
            }

        except Exception as e:
            self.consecutive_failures += 1
            self.last_error = str(e)

            return {
                "name": self.name,
                "status": "unhealthy",
                "error": str(e),
                "consecutive_failures": self.consecutive_failures,
                "response_time": time.time() - start_time,
                "timestamp": datetime.now()
            }

    def _run_with_timeout(self) -> Any:
        """Esegue il check con timeout."""
        import signal

        def timeout_handler(signum, frame):
            raise TimeoutError("Health check '{self.name}' timed out")

        # Imposta timeout (solo su sistemi Unix-like)
        try:
            old_handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(self.timeout)

            try:
                return self.check_func()
            finally:
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)

        except (ImportError, AttributeError):
            # Su Windows o se signal non disponibile, esegui senza timeout
            return self.check_func()


class HealthMonitor:
    """Monitor di salute per l'applicazione."""

    def __init__(self):
        self.checks: Dict[str, HealthCheck] = {}
        self.results: List[Dict] = []
        self.alerts: List[Dict] = []
        self.lock = threading.Lock()
        self.monitoring_active = False
        self.monitor_thread = None

        # Soglie di alert
        self.thresholds = {
            "max_consecutive_failures": 3,
            "alert_cooldown_minutes": 5
        }

        # Inizializza i check di default
        self._setup_default_checks()

    def _setup_default_checks(self):
        """Imposta i controlli di salute di default."""
        # Check di sistema
        self.add_check("cpu_usage", self._check_cpu_usage, interval=30)
        self.add_check("memory_usage", self._check_memory_usage, interval=30)
        self.add_check("disk_space", self._check_disk_space, interval=300)

        # Check specifici dell'applicazione
        self.add_check("ollama_connection", self._check_ollama_connection, interval=60)
        self.add_check("settings_access", self._check_settings_access, interval=120)
        self.add_check("log_writing", self._check_log_writing, interval=60)

    def add_check(self, name: str, check_func: Callable, interval: int = 60, timeout: int = 10):
        """Aggiunge un nuovo health check."""
        with self.lock:
            self.checks[name] = HealthCheck(name, check_func, interval, timeout)
            logger.info("Added health check: {name}")

    def remove_check(self, name: str):
        """Rimuove un health check."""
        with self.lock:
            if name in self.checks:
                del self.checks[name]
                logger.info("Removed health check: {name}")

    def run_all_checks(self) -> Dict[str, Dict]:
        """Esegue tutti i controlli di salute."""
        results = {}

        with self.lock:
            for name, check in self.checks.items():
                if check.should_run():
                    result = check.run()
                    results[name] = result
                    self.results.append(result)

                    # Mantieni solo gli ultimi 1000 risultati
                    if len(self.results) > 1000:
                        self.results = self.results[-1000:]

                    # Verifica se generare alert
                    self._check_alert_conditions(result)

        return results

    def _check_alert_conditions(self, result: Dict):
        """Verifica se il risultato richiede un alert."""
        if result["status"] == "unhealthy":
            check_name = result["name"]
            consecutive_failures = result.get("consecutive_failures", 0)

            if consecutive_failures >= self.thresholds["max_consecutive_failures"]:
                self._generate_alert(
                    "HEALTH_CHECK_FAILED",
                    "Health check '{check_name}' failed {consecutive_failures} times consecutively",
                    "WARNING",
                    result
                )

    def _generate_alert(self, alert_type: str, message: str, severity: str, details: Optional[Dict] = None) -> None:
        """Genera un alert di salute."""
        # Controlla cooldown
        now = datetime.now()
        recent_alerts = [a for a in self.alerts
                         if a.get("type") == alert_type
                         and (now - a["timestamp"]).total_seconds() < self.thresholds["alert_cooldown_minutes"] * 60]

        if recent_alerts:
            return  # Alert ancora in cooldown

        alert = {
            "timestamp": now,
            "type": alert_type,
            "message": message,
            "severity": severity,
            "details": details or {}
        }

        self.alerts.append(alert)

        # Mantieni solo gli ultimi 100 alert
        if len(self.alerts) > 100:
            self.alerts = self.alerts[-100:]

        logger.warning("🏥 HEALTH ALERT: {message}")

    def start_monitoring(self, interval: int = 60):
        """Avvia il monitoraggio periodico."""
        if self.monitoring_active:
            return

        self.monitoring_active = True
        self.monitor_thread = threading.Thread(target=self._monitoring_loop, args=(interval,))
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        logger.info("Health monitoring started with {interval}s interval")

    def stop_monitoring(self):
        """Ferma il monitoraggio."""
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("Health monitoring stopped")

    def _monitoring_loop(self, interval: int):
        """Loop principale del monitoraggio."""
        while self.monitoring_active:
            try:
                self.run_all_checks()
            except Exception:
                logger.error("Error in health monitoring loop: {e}")

            time.sleep(interval)

    def get_health_status(self) -> Dict[str, Any]:
        """Restituisce lo stato generale di salute."""
        with self.lock:
            total_checks = len(self.checks)
            healthy_checks = sum(1 for r in self.results[-total_checks:]
                                 if r.get("status") == "healthy")

            return {
                "overall_status": "healthy" if healthy_checks == total_checks else "degraded",
                "total_checks": total_checks,
                "healthy_checks": healthy_checks,
                "unhealthy_checks": total_checks - healthy_checks,
                "last_check": self.results[-1] if self.results else None,
                "active_alerts": len([a for a in self.alerts
                                      if (datetime.now() - a["timestamp"]).total_seconds() < 3600])  # Ultima ora
            }

    # Metodi di check specifici

    def _check_cpu_usage(self) -> Dict[str, Any]:
        """Controlla l'utilizzo della CPU."""
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_freq = psutil.cpu_freq()
        return {
            "cpu_percent": cpu_percent,
            "cpu_count": psutil.cpu_count(),
            "cpu_freq": cpu_freq.current if cpu_freq else None
        }

    def _check_memory_usage(self) -> Dict[str, float]:
        """Controlla l'utilizzo della memoria."""
        memory = psutil.virtual_memory()
        return {
            "memory_percent": memory.percent,
            "memory_used_gb": memory.used / (1024**3),
            "memory_total_gb": memory.total / (1024**3),
            "memory_available_gb": memory.available / (1024**3)
        }

    def _check_disk_space(self) -> Dict[str, Any]:
        """Controlla lo spazio su disco."""
        disk = psutil.disk_usage('/')
        return {
            "disk_percent": disk.percent,
            "disk_used_gb": disk.used / (1024**3),
            "disk_total_gb": disk.total / (1024**3),
            "disk_free_gb": disk.free / (1024**3)
        }

    def _check_ollama_connection(self) -> Dict[str, Any]:
        """Controlla la connessione a Ollama."""
        try:
            # Import qui per evitare dipendenze circolari
            from Artificial_Intelligence.Ollama.ollama_manager import OllamaManager
            manager = OllamaManager()
            is_running = manager.check_ollama_running()

            return {
                "ollama_running": is_running,
                "connection_status": "connected" if is_running else "disconnected"
            }
        except Exception as e:
            return {
                "ollama_running": False,
                "connection_status": "error",
                "error": str(e)
            }

    def _check_settings_access(self) -> Dict[str, Any]:
        """Controlla l'accesso alle impostazioni."""
        try:
            from main_03_configurazione_e_opzioni import load_settings
            settings = load_settings()

            return {
                "settings_accessible": True,
                "settings_keys": len(settings) if isinstance(settings, dict) else 0
            }
        except Exception as e:
            return {
                "settings_accessible": False,
                "error": str(e)
            }

    def _check_log_writing(self) -> Dict[str, Any]:
        """Controlla la scrittura dei log."""
        try:
            import tempfile
            import os

            # Prova a scrivere un log temporaneo
            with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
                test_message = "Health check test at {datetime.now()}"
                f.write(test_message)
                temp_file = f.name

            # Verifica che il file sia stato scritto
            with open(temp_file, 'r') as f:
                _ = f.read()

            # Pulisci
            os.unlink(temp_file)

            return {
                "log_writing": True,
                "test_message": test_message[:50] + "...",
                "file_created": True
            }
        except Exception as e:
            return {
                "log_writing": False,
                "error": str(e)
            }


# Istanza globale del monitor di salute
health_monitor = HealthMonitor()


def get_health_status() -> Dict[str, Any]:
    """Funzione di comodo per ottenere lo stato di salute."""
    return health_monitor.get_health_status()


def run_health_checks() -> Dict[str, Dict]:
    """Funzione di comodo per eseguire tutti i controlli."""
    return health_monitor.run_all_checks()
