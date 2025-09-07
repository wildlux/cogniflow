#!/usr/bin/env python3
"""
Security Monitor - Sistema di monitoraggio sicurezza
Monitora attività sospette e fornisce alert di sicurezza
"""

import logging
import time
import threading
from typing import Dict, List, Any
from datetime import datetime, timedelta
from collections import defaultdict

logger = logging.getLogger(__name__)


class SecurityMonitor:
    """Monitor di sicurezza per l'applicazione DSA."""

    def __init__(self):
        self.alerts = []
        self.suspicious_activities = defaultdict(int)
        self.failed_attempts = defaultdict(int)
        self.lock = threading.Lock()

        # Soglie di sicurezza
        self.thresholds = {
            "max_failed_attempts": 5,
            "max_suspicious_activities": 10,
            "alert_cooldown_minutes": 15,
            "max_file_access_attempts": 20
        }

        # Tracking delle attività recenti
        self.recent_activities = []
        self.last_alert_time = {}

    def log_security_event(self, event_type: str, details: Dict[str, Any], severity: str = "INFO"):
        """Registra un evento di sicurezza."""
        with self.lock:
            event = {
                "timestamp": datetime.now(),
                "type": event_type,
                "details": details,
                "severity": severity,
                "source_ip": details.get("ip", "localhost")
            }

            self.recent_activities.append(event)

            # Mantieni solo le ultime 1000 attività
            if len(self.recent_activities) > 1000:
                self.recent_activities = self.recent_activities[-1000:]

            # Log dell'evento
            logger.log(
                getattr(logging, severity),
                "Security Event: {event_type} - {details}"
            )

            # Verifica se generare un alert
            self._check_alert_conditions(event)

    def _check_alert_conditions(self, event):
        """Verifica se l'evento richiede un alert."""
        event_type = event["type"]
        severity = event["severity"]

        # Incrementa contatori
        if severity in ["WARNING", "ERROR"]:
            self.suspicious_activities[event_type] += 1
            self.failed_attempts[event["source_ip"]] += 1

        # Controlla soglie
        if self.suspicious_activities[event_type] >= self.thresholds["max_suspicious_activities"]:
            self._generate_alert(
                "HIGH_ACTIVITY",
                "Alta attività sospetta per {event_type}: {self.suspicious_activities[event_type]} eventi",
                "HIGH"
            )
            self.suspicious_activities[event_type] = 0  # Reset contatore

        if self.failed_attempts[event["source_ip"]] >= self.thresholds["max_failed_attempts"]:
            self._generate_alert(
                "BRUTE_FORCE",
                "Tentativi falliti eccessivi da {event['source_ip']}: {self.failed_attempts[event['source_ip']]}",
                "CRITICAL"
            )
            self.failed_attempts[event["source_ip"]] = 0  # Reset contatore

    def _generate_alert(self, alert_type: str, message: str, severity: str):
        """Genera un alert di sicurezza."""
        # Controlla cooldown per evitare spam
        now = datetime.now()
        if alert_type in self.last_alert_time:
            time_diff = now - self.last_alert_time[alert_type]
            if time_diff < timedelta(minutes=self.thresholds["alert_cooldown_minutes"]):
                return  # Alert ancora in cooldown

        alert = {
            "timestamp": now,
            "type": alert_type,
            "message": message,
            "severity": severity
        }

        self.alerts.append(alert)
        self.last_alert_time[alert_type] = now

        # Mantieni solo gli ultimi 100 alert
        if len(self.alerts) > 100:
            self.alerts = self.alerts[-100:]

        # Log dell'alert
        logger.critical("🚨 SECURITY ALERT: {alert_type} - {message}")

    def get_active_alerts(self) -> List[Dict]:
        """Restituisce gli alert attivi."""
        with self.lock:
            return self.alerts.copy()

    def get_security_stats(self) -> Dict[str, Any]:
        """Restituisce statistiche di sicurezza."""
        with self.lock:
            return {
                "total_alerts": len(self.alerts),
                "suspicious_activities": dict(self.suspicious_activities),
                "failed_attempts": dict(self.failed_attempts),
                "recent_activities_count": len(self.recent_activities),
                "last_alert": self.alerts[-1] if self.alerts else None
            }

    def clear_old_alerts(self, days: int = 7):
        """Pulisce alert più vecchi di X giorni."""
        with self.lock:
            cutoff_date = datetime.now() - timedelta(days=days)
            self.alerts = [
                alert for alert in self.alerts
                if alert["timestamp"] > cutoff_date
            ]

    def is_ip_blocked(self, ip: str) -> bool:
        """Verifica se un IP è bloccato per tentativi eccessivi."""
        with self.lock:
            return self.failed_attempts.get(ip, 0) >= self.thresholds["max_failed_attempts"] * 2


# Istanza globale del monitor di sicurezza
security_monitor = SecurityMonitor()


def log_security_event(event_type: str, details: Dict[str, Any], severity: str = "INFO"):
    """Funzione di comodo per loggare eventi di sicurezza."""
    security_monitor.log_security_event(event_type, details, severity)


def get_security_stats() -> Dict[str, Any]:
    """Funzione di comodo per ottenere statistiche di sicurezza."""
    return security_monitor.get_security_stats()
