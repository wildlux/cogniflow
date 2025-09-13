#!/usr/bin/env python3
"""
Security Dashboard - Dashboard di sicurezza in tempo reale
Sistema di monitoraggio e alerting avanzato
"""

import threading
import time
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Callable, Optional
from dataclasses import dataclass
from enum import Enum
import logging
from collections import defaultdict, deque

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Livelli di severità per gli alert."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AlertType(Enum):
    """Tipi di alert di sicurezza."""
    BRUTE_FORCE = "BRUTE_FORCE"
    SUSPICIOUS_ACTIVITY = "SUSPICIOUS_ACTIVITY"
    UNAUTHORIZED_ACCESS = "UNAUTHORIZED_ACCESS"
    DATA_BREACH = "DATA_BREACH"
    SYSTEM_COMPROMISE = "SYSTEM_COMPROMISE"
    CONFIGURATION_ERROR = "CONFIGURATION_ERROR"
    DEPENDENCY_VULNERABILITY = "DEPENDENCY_VULNERABILITY"
    ANOMALOUS_TRAFFIC = "ANOMALOUS_TRAFFIC"


@dataclass
class SecurityAlert:
    """Classe per rappresentare un alert di sicurezza."""
    alert_id: str
    alert_type: AlertType
    severity: AlertSeverity
    title: str
    description: str
    timestamp: datetime
    source_ip: Optional[str]
    user_id: Optional[str]
    metadata: Dict[str, Any]
    acknowledged: bool = False
    resolved: bool = False
    resolution_time: Optional[datetime] = None


class RealTimeAlertingSystem:
    """Sistema di alerting in tempo reale per eventi di sicurezza."""

    def __init__(self):
        self.alerts: Dict[str, SecurityAlert] = {}
        self.alert_handlers: Dict[AlertType, List[Callable]] = defaultdict(list)
        self.active_alerts: Dict[str, SecurityAlert] = {}
        self.alert_history = deque(maxlen=1000)  # Mantieni ultimi 1000 alert
        self.alert_thresholds = self._get_default_thresholds()
        self.monitoring_active = False
        self.monitoring_thread: Optional[threading.Thread] = None

        # Configurazioni
        self.alert_cooldown_minutes = 5  # Evita spam di alert simili
        self.max_active_alerts = 50
        self.auto_resolve_hours = 24  # Risolvi automaticamente dopo 24 ore

    def _get_default_thresholds(self) -> Dict[str, Any]:
        """Ottieni soglie di default per gli alert."""
        return {
            'failed_login_attempts': 5,
            'suspicious_activities': 10,
            'unusual_traffic_spike': 100,
            'configuration_changes': 3,
            'dependency_vulnerabilities': 1,
            'system_errors': 20
        }

    def register_alert_handler(self, alert_type: AlertType, handler: Callable):
        """Registra un handler per un tipo di alert specifico."""
        self.alert_handlers[alert_type].append(handler)
        logger.info(f"Handler registrato per alert type: {alert_type.value}")

    def trigger_alert(self, alert_type: AlertType, severity: AlertSeverity,
                     title: str, description: str, source_ip: Optional[str] = None,
                     user_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Triggera un nuovo alert di sicurezza."""
        if metadata is None:
            metadata = {}

        # Genera ID univoco per l'alert
        alert_id = f"alert_{int(time.time() * 1000)}_{alert_type.value}"

        # Controlla cooldown per evitare spam
        if self._is_alert_on_cooldown(alert_type, source_ip):
            logger.debug(f"Alert {alert_type.value} in cooldown, skipping")
            return alert_id

        alert = SecurityAlert(
            alert_id=alert_id,
            alert_type=alert_type,
            severity=severity,
            title=title,
            description=description,
            timestamp=datetime.now(),
            source_ip=source_ip,
            user_id=user_id,
            metadata=metadata
        )

        # Salva alert
        self.alerts[alert_id] = alert
        self.active_alerts[alert_id] = alert
        self.alert_history.append(alert)

        # Limita numero di alert attivi
        if len(self.active_alerts) > self.max_active_alerts:
            oldest_alert_id = min(self.active_alerts.keys(),
                                key=lambda x: self.active_alerts[x].timestamp.timestamp())
            self._resolve_alert(oldest_alert_id, "Auto-resolved due to limit")

        # Notifica handlers
        self._notify_handlers(alert)

        # Log alert
        logger.warning(f"🚨 SECURITY ALERT [{severity.value}]: {title} - {description}")

        return alert_id

    def _is_alert_on_cooldown(self, alert_type: AlertType, source_ip: Optional[str]) -> bool:
        """Verifica se un alert è in cooldown."""
        cutoff_time = datetime.now() - timedelta(minutes=self.alert_cooldown_minutes)

        for alert in self.alert_history:
            if (alert.alert_type == alert_type and
                alert.timestamp > cutoff_time and
                alert.source_ip == source_ip):
                return True

        return False

    def _notify_handlers(self, alert: SecurityAlert):
        """Notifica tutti i handlers registrati per questo tipo di alert."""
        for handler in self.alert_handlers[alert.alert_type]:
            try:
                handler(alert)
            except Exception as e:
                logger.error(f"Errore nell'handler dell'alert: {e}")

    def acknowledge_alert(self, alert_id: str, user_id: str):
        """Segna un alert come riconosciuto."""
        if alert_id in self.active_alerts:
            self.active_alerts[alert_id].acknowledged = True
            logger.info(f"Alert {alert_id} acknowledged by {user_id}")

    def resolve_alert(self, alert_id: str, resolution: str, user_id: str):
        """Risolvi un alert."""
        self._resolve_alert(alert_id, resolution)
        logger.info(f"Alert {alert_id} resolved by {user_id}: {resolution}")

    def _resolve_alert(self, alert_id: str, resolution: str):
        """Risolvi internamente un alert."""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.resolved = True
            alert.resolution_time = datetime.now()
            alert.metadata['resolution'] = resolution

            del self.active_alerts[alert_id]

    def get_active_alerts(self) -> List[SecurityAlert]:
        """Ottieni tutti gli alert attivi."""
        return list(self.active_alerts.values())

    def get_alerts_by_severity(self, severity: AlertSeverity) -> List[SecurityAlert]:
        """Ottieni alert per severità."""
        return [alert for alert in self.active_alerts.values() if alert.severity == severity]

    def get_alert_statistics(self) -> Dict[str, Any]:
        """Ottieni statistiche sugli alert."""
        total_alerts = len(self.alert_history)
        active_alerts = len(self.active_alerts)

        severity_counts = defaultdict(int)
        type_counts = defaultdict(int)

        for alert in self.alert_history:
            severity_counts[alert.severity.value] += 1
            type_counts[alert.alert_type.value] += 1

        return {
            'total_alerts': total_alerts,
            'active_alerts': active_alerts,
            'severity_distribution': dict(severity_counts),
            'type_distribution': dict(type_counts),
            'most_recent_alert': self.alert_history[-1] if self.alert_history else None
        }

    def start_monitoring(self):
        """Avvia il monitoraggio in tempo reale."""
        if self.monitoring_active:
            return

        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        logger.info("Real-time security monitoring started")

    def stop_monitoring(self):
        """Ferma il monitoraggio."""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        logger.info("Real-time security monitoring stopped")

    def _monitoring_loop(self):
        """Loop principale del monitoraggio."""
        while self.monitoring_active:
            try:
                self._perform_security_checks()
                self._cleanup_old_alerts()
                time.sleep(30)  # Controlla ogni 30 secondi
            except Exception as e:
                logger.error(f"Errore nel monitoring loop: {e}")
                time.sleep(60)  # Aspetta più tempo in caso di errore

    def _perform_security_checks(self):
        """Esegue controlli di sicurezza periodici."""
        # Qui si potrebbero aggiungere controlli specifici come:
        # - Monitoraggio uso CPU/memoria anomalo
        # - Controllo file di configurazione modificati
        # - Verifica integrità database
        # - Controllo connessioni di rete sospette

        # Esempio: controllo configurazione modificata
        self._check_configuration_integrity()

    def _check_configuration_integrity(self):
        """Verifica integrità della configurazione."""
        # Implementazione semplificata - in produzione si userebbe hashing
        config_files = [
            'assistente_dsa/main_03_configurazione_e_opzioni.py',
            'requirements.txt',
            'assistente_dsa/core/security_monitor.py'
        ]

        for config_file in config_files:
            if os.path.exists(config_file):
                # Simula controllo di integrità
                file_modified = os.path.getmtime(config_file)
                hours_since_modified = (time.time() - file_modified) / 3600

                if hours_since_modified < 1:  # Modificato nell'ultima ora
                    self.trigger_alert(
                        AlertType.CONFIGURATION_ERROR,
                        AlertSeverity.MEDIUM,
                        "File di configurazione modificato",
                        f"Il file {config_file} è stato modificato recentemente",
                        metadata={'file': config_file, 'hours_ago': hours_since_modified}
                    )

    def _cleanup_old_alerts(self):
        """Pulisce alert vecchi automaticamente."""
        cutoff_time = datetime.now() - timedelta(hours=self.auto_resolve_hours)

        alerts_to_resolve = []
        for alert_id, alert in self.active_alerts.items():
            if alert.timestamp < cutoff_time and not alert.acknowledged:
                alerts_to_resolve.append(alert_id)

        for alert_id in alerts_to_resolve:
            self._resolve_alert(alert_id, "Auto-resolved after timeout")


class SecurityDashboard:
    """Dashboard di sicurezza per monitoraggio e gestione."""

    def __init__(self, alerting_system: RealTimeAlertingSystem):
        self.alerting_system = alerting_system
        self.dashboard_data = {}
        self.update_interval = 60  # Aggiorna ogni minuto
        self.last_update = datetime.now()

    def get_dashboard_data(self) -> Dict[str, Any]:
        """Ottieni dati completi per la dashboard."""
        if (datetime.now() - self.last_update).seconds > self.update_interval:
            self._update_dashboard_data()

        return self.dashboard_data

    def _update_dashboard_data(self):
        """Aggiorna i dati della dashboard."""
        self.dashboard_data = {
            'timestamp': datetime.now(),
            'alerts': {
                'active': len(self.alerting_system.active_alerts),
                'total_today': self._count_today_alerts(),
                'by_severity': self._get_alerts_by_severity(),
                'recent': self._get_recent_alerts(10)
            },
            'system_status': self._get_system_status(),
            'security_score': self._calculate_security_score(),
            'recommendations': self._generate_recommendations()
        }
        self.last_update = datetime.now()

    def _count_today_alerts(self) -> int:
        """Conta alert di oggi."""
        today = datetime.now().date()
        return sum(1 for alert in self.alerting_system.alert_history
                  if alert.timestamp.date() == today)

    def _get_alerts_by_severity(self) -> Dict[str, int]:
        """Ottieni conteggio alert per severità."""
        severity_counts = defaultdict(int)
        for alert in self.alerting_system.active_alerts.values():
            severity_counts[alert.severity.value] += 1
        return dict(severity_counts)

    def _get_recent_alerts(self, limit: int) -> List[Dict[str, Any]]:
        """Ottieni alert recenti."""
        recent_alerts = list(self.alerting_system.alert_history)[-limit:]
        return [{
            'id': alert.alert_id,
            'type': alert.alert_type.value,
            'severity': alert.severity.value,
            'title': alert.title,
            'timestamp': alert.timestamp.isoformat(),
            'acknowledged': alert.acknowledged
        } for alert in recent_alerts]

    def _get_system_status(self) -> Dict[str, Any]:
        """Ottieni stato del sistema."""
        return {
            'monitoring_active': self.alerting_system.monitoring_active,
            'active_handlers': sum(len(handlers) for handlers in self.alerting_system.alert_handlers.values()),
            'alert_thresholds': self.alerting_system.alert_thresholds,
            'uptime': "Sistema operativo"  # Placeholder
        }

    def _calculate_security_score(self) -> Dict[str, Any]:
        """Calcola punteggio di sicurezza."""
        active_alerts = len(self.alerting_system.active_alerts)
        total_alerts = len(self.alerting_system.alert_history)

        # Formula semplice per il punteggio
        base_score = 100
        alert_penalty = active_alerts * 5
        history_penalty = min(total_alerts * 0.5, 20)

        score = max(0, int(base_score - alert_penalty - history_penalty))

        return {
            'score': score,
            'level': self._get_security_level(score),
            'factors': {
                'active_alerts': active_alerts,
                'total_alerts': total_alerts
            }
        }

    def _get_security_level(self, score: int) -> str:
        """Converte punteggio in livello di sicurezza."""
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

    def _generate_recommendations(self) -> List[str]:
        """Genera raccomandazioni di sicurezza."""
        recommendations = []

        active_alerts = len(self.alerting_system.active_alerts)
        if active_alerts > 5:
            recommendations.append("🔴 Alto numero di alert attivi - revisione urgente richiesta")

        if not self.alerting_system.monitoring_active:
            recommendations.append("🟡 Monitoraggio sicurezza non attivo - riavviare il sistema")

        return recommendations


# Handlers di esempio per alert
def email_alert_handler(alert: SecurityAlert):
    """Handler per invio email di alert."""
    print(f"📧 EMAIL ALERT: {alert.title} - {alert.description}")


def log_alert_handler(alert: SecurityAlert):
    """Handler per logging avanzato di alert."""
    logger.critical(f"🚨 CRITICAL ALERT: {alert.alert_type.value} - {alert.title}")


def notification_alert_handler(alert: SecurityAlert):
    """Handler per notifiche desktop."""
    print(f"🔔 NOTIFICATION: {alert.severity.value} - {alert.title}")


# Istanze globali
alerting_system = RealTimeAlertingSystem()
security_dashboard = SecurityDashboard(alerting_system)

# Registra handlers di default
alerting_system.register_alert_handler(AlertType.SYSTEM_COMPROMISE, email_alert_handler)
alerting_system.register_alert_handler(AlertType.SYSTEM_COMPROMISE, log_alert_handler)
alerting_system.register_alert_handler(AlertType.UNAUTHORIZED_ACCESS, notification_alert_handler)


def trigger_security_alert(alert_type: AlertType, severity: AlertSeverity,
                          title: str, description: str, **kwargs) -> str:
    """Funzione di comodo per triggerare alert."""
    return alerting_system.trigger_alert(alert_type, severity, title, description, **kwargs)


def get_security_dashboard() -> Dict[str, Any]:
    """Funzione di comodo per ottenere dati dashboard."""
    return security_dashboard.get_dashboard_data()


def start_security_monitoring():
    """Avvia il monitoraggio sicurezza."""
    alerting_system.start_monitoring()


def stop_security_monitoring():
    """Ferma il monitoraggio sicurezza."""
    alerting_system.stop_monitoring()