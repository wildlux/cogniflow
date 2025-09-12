#!/usr/bin/env python3
"""
Performance Monitor - Sistema di monitoraggio prestazioni
Analizza e ottimizza le performance dell'applicazione
"""

import time
import psutil
import threading
from typing import Dict, List, Any, Optional, Callable
from functools import wraps
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """Monitor di prestazioni per l'applicazione."""

    def __init__(self):
        self.metrics = {}
        self.snapshots = []
        self.lock = threading.Lock()
        self.process = psutil.Process()

    def measure_time(self, func_name: str):
        """Decorator per misurare il tempo di esecuzione di una funzione."""

        def decorator(func: Callable):
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    execution_time = time.time() - start_time
                    self.record_metric(f"{func_name}.execution_time", execution_time)
                    return result
                except Exception as e:
                    execution_time = time.time() - start_time
                    self.record_metric(f"{func_name}.execution_time", execution_time)
                    self.record_metric(f"{func_name}.error_count", 1)
                    raise e

            return wrapper

        return decorator

    def record_metric(
        self, name: str, value: float, tags: Optional[Dict[str, Any]] = None
    ):
        """Registra una metrica."""
        with self.lock:
            if name not in self.metrics:
                self.metrics[name] = []

            metric_data = {
                "timestamp": datetime.now(),
                "value": value,
                "tags": tags or {},
            }

            self.metrics[name].append(metric_data)

            # Mantieni solo le ultime 1000 metriche per metrica
            if len(self.metrics[name]) > 1000:
                self.metrics[name] = self.metrics[name][-1000:]

    def get_system_metrics(self) -> Dict[str, Any]:
        """Ottiene metriche di sistema."""
        try:
            cpu_percent = self.process.cpu_percent()
            memory_info = self.process.memory_info()
            memory_percent = self.process.memory_percent()

            return {
                "cpu_percent": cpu_percent,
                "memory_rss": memory_info.rss,
                "memory_vms": memory_info.vms,
                "memory_percent": memory_percent,
                "num_threads": self.process.num_threads(),
                "num_fds": (
                    self.process.num_fds() if hasattr(self.process, "num_fds") else None
                ),
            }
        except Exception:
            logger.error("Error getting system metrics: {e}")
            return {}

    def take_snapshot(self, label: str = ""):
        """Crea uno snapshot delle metriche correnti."""
        snapshot = {
            "timestamp": datetime.now(),
            "label": label,
            "system_metrics": self.get_system_metrics(),
            "custom_metrics": dict(self.metrics),
        }

        with self.lock:
            self.snapshots.append(snapshot)

            # Mantieni solo gli ultimi 100 snapshot
            if len(self.snapshots) > 100:
                self.snapshots = self.snapshots[-100:]

        return snapshot

    def get_performance_report(self) -> Dict[str, Any]:
        """Genera un report delle prestazioni."""
        with self.lock:
            report = {
                "timestamp": datetime.now(),
                "system_info": {
                    "cpu_count": psutil.cpu_count(),
                    "memory_total": psutil.virtual_memory().total,
                },
                "current_metrics": self.get_system_metrics(),
                "custom_metrics_summary": {},
            }

            # Riassunto metriche custom
            for name, values in self.metrics.items():
                if values:
                    metric_values = [v["value"] for v in values]
                    report["custom_metrics_summary"][name] = {
                        "count": len(metric_values),
                        "avg": sum(metric_values) / len(metric_values),
                        "min": min(metric_values),
                        "max": max(metric_values),
                        "latest": metric_values[-1],
                    }

            return report

    def detect_performance_issues(self) -> List[Dict[str, Any]]:
        """Rileva potenziali problemi di prestazioni."""
        issues = []
        report = self.get_performance_report()

        # Controlla uso CPU elevato
        cpu_percent = report["current_metrics"].get("cpu_percent", 0)
        if cpu_percent > 80:
            issues.append(
                {
                    "type": "high_cpu_usage",
                    "severity": "warning",
                    "message": "Uso CPU elevato: {cpu_percent:.1f}%",
                    "suggestion": "Ottimizza operazioni CPU-intensive o considera multiprocessing",
                }
            )

        # Controlla uso memoria elevato
        memory_percent = report["current_metrics"].get("memory_percent", 0)
        if memory_percent > 80:
            issues.append(
                {
                    "type": "high_memory_usage",
                    "severity": "warning",
                    "message": "Uso memoria elevato: {memory_percent:.1f}%",
                    "suggestion": "Verifica memory leaks o ottimizza strutture dati",
                }
            )

        # Controlla funzioni lente
        for name, summary in report["custom_metrics_summary"].items():
            if name.endswith(".execution_time") and summary["avg"] > 1.0:
                issues.append(
                    {
                        "type": "slow_function",
                        "severity": "info",
                        "message": "Funzione {name} lenta: {summary['avg']:.2f}s media",
                        "suggestion": "Ottimizza algoritmo o considera caching",
                    }
                )

        return issues

    def export_metrics(self, filepath: str):
        """Esporta metriche in file JSON."""
        import json

        with self.lock:
            data = {
                "export_timestamp": datetime.now().isoformat(),
                "metrics": self.metrics,
                "snapshots": [
                    {
                        "timestamp": s["timestamp"].isoformat(),
                        "label": s["label"],
                        "system_metrics": s["system_metrics"],
                    }
                    for s in self.snapshots
                ],
            }

        with open(filepath, "w") as f:
            json.dump(data, f, indent=2, default=str)

        logger.info(f"Performance metrics exported to {filepath}")


# Istanza globale del monitor prestazioni
performance_monitor = PerformanceMonitor()


def get_performance_report() -> Dict[str, Any]:
    """Funzione di comodo per ottenere report prestazioni."""
    return performance_monitor.get_performance_report()


def measure_function_time(func_name: str):
    """Decorator di comodo per misurare tempo funzioni."""
    return performance_monitor.measure_time(func_name)
