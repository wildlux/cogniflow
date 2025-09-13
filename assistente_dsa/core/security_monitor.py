#!/usr/bin/env python3
"""
Security Monitor - Sistema di monitoraggio sicurezza
Monitora attività sospette e fornisce alert di sicurezza
"""

import logging
import time
import threading
import json
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
            "max_file_access_attempts": 20,
        }

        # Tracking delle attività recenti
        self.recent_activities = []
        self.last_alert_time = {}

    def log_security_event(
        self, event_type: str, details: Dict[str, Any], severity: str = "INFO"
    ):
        """Registra un evento di sicurezza."""
        with self.lock:
            event = {
                "timestamp": datetime.now(),
                "type": event_type,
                "details": details,
                "severity": severity,
                "source_ip": details.get("ip", "localhost"),
            }

            self.recent_activities.append(event)

            # Mantieni solo le ultime 1000 attività
            if len(self.recent_activities) > 1000:
                self.recent_activities = self.recent_activities[-1000:]

            # Log dell'evento
            logger.log(
                getattr(logging, severity), "Security Event: {event_type} - {details}"
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
        if (
            self.suspicious_activities[event_type]
            >= self.thresholds["max_suspicious_activities"]
        ):
            self._generate_alert(
                "HIGH_ACTIVITY",
                "Alta attività sospetta per {event_type}: {self.suspicious_activities[event_type]} eventi",
                "HIGH",
            )
            self.suspicious_activities[event_type] = 0  # Reset contatore

        if (
            self.failed_attempts[event["source_ip"]]
            >= self.thresholds["max_failed_attempts"]
        ):
            self._generate_alert(
                "BRUTE_FORCE",
                "Tentativi falliti eccessivi da {event['source_ip']}: {self.failed_attempts[event['source_ip']]}",
                "CRITICAL",
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
            "severity": severity,
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
                "last_alert": self.alerts[-1] if self.alerts else None,
            }

    def clear_old_alerts(self, days: int = 7):
        """Pulisce alert più vecchi di X giorni."""
        with self.lock:
            cutoff_date = datetime.now() - timedelta(days=days)
            self.alerts = [
                alert for alert in self.alerts if alert["timestamp"] > cutoff_date
            ]

    def is_ip_blocked(self, ip: str) -> bool:
        """Verifica se un IP è bloccato per tentativi eccessivi."""
        with self.lock:
            return (
                self.failed_attempts.get(ip, 0)
                >= self.thresholds["max_failed_attempts"] * 2
            )

    def detect_anomalous_activity(self) -> List[Dict[str, Any]]:
        """Rileva attività anomale usando analisi statistica."""
        anomalies = []
        with self.lock:
            if len(self.recent_activities) < 10:
                return anomalies  # Non abbastanza dati

            # Analizza pattern di attività
            recent_events = self.recent_activities[-100:]  # Ultimi 100 eventi

            # Conta eventi per tipo
            event_counts = defaultdict(int)
            for event in recent_events:
                event_counts[event["type"]] += 1

            # Rileva picchi anomali
            avg_events_per_type = len(recent_events) / len(event_counts)
            for event_type, count in event_counts.items():
                if count > avg_events_per_type * 3:  # 3 volte la media
                    anomalies.append({
                        "type": "ANOMALOUS_ACTIVITY_SPIKE",
                        "description": f"Picco anomalo di eventi {event_type}: {count} eventi",
                        "severity": "HIGH",
                        "data": {"event_type": event_type, "count": count}
                    })

            # Rileva attività da IP sospetti
            ip_counts = defaultdict(int)
            for event in recent_events:
                ip_counts[event.get("source_ip", "unknown")] += 1

            for ip, count in ip_counts.items():
                if count > 20:  # Più di 20 eventi da un singolo IP
                    anomalies.append({
                        "type": "SUSPICIOUS_IP_ACTIVITY",
                        "description": f"Attività elevata da IP {ip}: {count} eventi",
                        "severity": "MEDIUM",
                        "data": {"ip": ip, "count": count}
                    })

        return anomalies

    def generate_security_report(self) -> Dict[str, Any]:
        """Genera un report di sicurezza completo."""
        with self.lock:
            anomalies = self.detect_anomalous_activity()

            return {
                "timestamp": datetime.now(),
                "summary": {
                    "total_alerts": len(self.alerts),
                    "active_anomalies": len(anomalies),
                    "suspicious_activities": dict(self.suspicious_activities),
                    "failed_attempts": dict(self.failed_attempts),
                    "blocked_ips": [
                        ip for ip in self.failed_attempts.keys()
                        if self.is_ip_blocked(ip)
                    ]
                },
                "recent_alerts": self.alerts[-10:],  # Ultimi 10 alert
                "anomalies": anomalies,
                "recommendations": self._generate_security_recommendations()
            }

    def _generate_security_recommendations(self) -> List[str]:
        """Genera raccomandazioni di sicurezza basate sull'analisi."""
        recommendations = []

        # Raccomandazioni basate sugli alert attivi
        if len(self.alerts) > 5:
            recommendations.append("🔴 Alto numero di alert di sicurezza - revisione urgente del sistema")

        # Raccomandazioni basate sui tentativi falliti
        total_failed = sum(self.failed_attempts.values())
        if total_failed > 10:
            recommendations.append("🟡 Molti tentativi di accesso falliti - possibile attacco brute force")

        # Raccomandazioni basate sulle attività sospette
        for activity, count in self.suspicious_activities.items():
            if count > 5:
                recommendations.append(f"🟡 Attività sospetta elevata: {activity} ({count} occorrenze)")

        # Raccomandazioni generali
        if not recommendations:
            recommendations.append("✅ Sistema di sicurezza operativo normalmente")

        return recommendations

    def export_security_audit(self, filepath: str):
        """Esporta un audit di sicurezza completo."""
        report = self.generate_security_report()

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, default=str)
            logger.info(f"Security audit exported to {filepath}")
        except Exception as e:
            logger.error(f"Failed to export security audit: {e}")

    def get_security_score(self) -> Dict[str, Any]:
        """Calcola un punteggio di sicurezza complessivo."""
        with self.lock:
            score = 100  # Punteggio base

            # Penalità per alert attivi
            alert_penalty = len(self.alerts) * 5
            score -= min(alert_penalty, 30)

            # Penalità per tentativi falliti
            failed_penalty = sum(self.failed_attempts.values()) * 2
            score -= min(failed_penalty, 20)

            # Penalità per attività sospette
            suspicious_penalty = sum(self.suspicious_activities.values()) * 3
            score -= min(suspicious_penalty, 25)

            # Bonus per attività recenti normali
            if len(self.recent_activities) > 50:
                score += 5

            score = max(0, min(100, score))  # Limita tra 0 e 100

            return {
                "score": score,
                "level": self._get_security_level(score),
                "factors": {
                    "alerts": len(self.alerts),
                    "failed_attempts": sum(self.failed_attempts.values()),
                    "suspicious_activities": sum(self.suspicious_activities.values())
                }
            }

    def _get_security_level(self, score: int) -> str:
        """Converte il punteggio in un livello di sicurezza."""
        if score >= 90:
            return "EXCELLENT"
        elif score >= 80:
            return "GOOD"
        elif score >= 70:
            return "FAIR"
        elif score >= 60:
            return "POOR"
        else:
            return "CRITICAL"


# Istanza globale del monitor di sicurezza
security_monitor = SecurityMonitor()


def log_security_event(
    event_type: str, details: Dict[str, Any], severity: str = "INFO"
):
    """Funzione di comodo per loggare eventi di sicurezza."""
    security_monitor.log_security_event(event_type, details, severity)


def get_security_stats() -> Dict[str, Any]:
    """Funzione di comodo per ottenere statistiche di sicurezza."""
    return security_monitor.get_security_stats()
