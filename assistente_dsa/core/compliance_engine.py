#!/usr/bin/env python3
"""
Compliance Engine - Motore di compliance e audit automatizzato
Genera report di compliance e mantiene audit trails completi
"""

import json
import os
import csv
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
import logging
import threading
import time

logger = logging.getLogger(__name__)


@dataclass
class AuditEvent:
    """Evento di audit per compliance."""
    event_id: str
    timestamp: datetime
    user_id: Optional[str]
    action: str
    resource: str
    result: str
    compliance_category: str
    risk_level: str
    details: Dict[str, Any]
    hash_value: str = ""


@dataclass
class ComplianceReport:
    """Report di compliance."""
    report_id: str
    generated_at: datetime
    period_start: datetime
    period_end: datetime
    compliance_framework: str
    overall_score: float
    sections: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)
    audit_trail_hash: str = ""


class ComplianceEngine:
    """Motore per automazione compliance e audit trails."""

    def __init__(self, audit_log_path: Optional[str] = None, reports_path: Optional[str] = None):
        if audit_log_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            audit_log_path = os.path.join(base_dir, "Save", "AUDIT", "audit.log")

        if reports_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            reports_path = os.path.join(base_dir, "Save", "COMPLIANCE", "reports")

        self.audit_log_path = audit_log_path
        self.reports_path = reports_path
        self.audit_events: List[AuditEvent] = []
        self.compliance_frameworks = self._initialize_frameworks()

        # Assicura directory esistano
        os.makedirs(os.path.dirname(audit_log_path), exist_ok=True)
        os.makedirs(reports_path, exist_ok=True)

        # Carica audit events esistenti
        self._load_audit_events()

    def _initialize_frameworks(self) -> Dict[str, Dict[str, Any]]:
        """Inizializza framework di compliance supportati."""
        return {
            'GDPR': {
                'name': 'General Data Protection Regulation',
                'categories': ['data_protection', 'privacy', 'consent', 'breach_notification'],
                'requirements': {
                    'data_encryption': 'Data must be encrypted at rest and in transit',
                    'access_logging': 'All data access must be logged',
                    'consent_management': 'User consent must be properly managed',
                    'breach_reporting': 'Data breaches must be reported within 72 hours'
                }
            },
            'ISO27001': {
                'name': 'ISO 27001 Information Security Management',
                'categories': ['access_control', 'cryptography', 'physical_security', 'operations'],
                'requirements': {
                    'risk_assessment': 'Regular risk assessments must be performed',
                    'access_control': 'Access must be controlled and monitored',
                    'cryptography': 'Cryptographic controls must be implemented',
                    'incident_management': 'Security incidents must be managed'
                }
            },
            'NIST': {
                'name': 'NIST Cybersecurity Framework',
                'categories': ['identify', 'protect', 'detect', 'respond', 'recover'],
                'requirements': {
                    'asset_management': 'Assets must be identified and managed',
                    'access_control': 'Access to assets must be controlled',
                    'awareness_training': 'Security awareness training required',
                    'incident_response': 'Incident response plans must exist'
                }
            },
            'PCI_DSS': {
                'name': 'Payment Card Industry Data Security Standard',
                'categories': ['cardholder_data', 'transmission', 'vulnerability_management'],
                'requirements': {
                    'data_protection': 'Cardholder data must be protected',
                    'secure_transmission': 'Data must be transmitted securely',
                    'vulnerability_scanning': 'Regular vulnerability scans required'
                }
            }
        }

    def _load_audit_events(self):
        """Carica eventi di audit dal file."""
        if not os.path.exists(self.audit_log_path):
            return

        try:
            with open(self.audit_log_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        event_data = json.loads(line)
                        event = AuditEvent(**event_data)
                        self.audit_events.append(event)
        except Exception as e:
            logger.error(f"Errore caricamento audit events: {e}")

    def log_audit_event(self, user_id: Optional[str], action: str, resource: str,
                       result: str, compliance_category: str, risk_level: str,
                       details: Optional[Dict[str, Any]] = None):
        """Registra un evento di audit."""
        if details is None:
            details = {}

        event_id = f"audit_{int(time.time() * 1000000)}"

        # Crea hash dell'evento per integrità
        event_content = f"{event_id}{user_id or ''}{action}{resource}{result}{compliance_category}{risk_level}{json.dumps(details, sort_keys=True)}"
        hash_value = hashlib.sha256(event_content.encode()).hexdigest()
        """Registra un evento di audit."""
        if details is None:
            details = {}

        event_id = f"audit_{int(time.time() * 1000000)}"

        # Crea hash dell'evento per integrità
        event_content = f"{event_id}{user_id}{action}{resource}{result}{compliance_category}{risk_level}{json.dumps(details, sort_keys=True)}"
        hash_value = hashlib.sha256(event_content.encode()).hexdigest()

        event = AuditEvent(
            event_id=event_id,
            timestamp=datetime.now(),
            user_id=user_id,
            action=action,
            resource=resource,
            result=result,
            compliance_category=compliance_category,
            risk_level=risk_level,
            details=details,
            hash_value=hash_value
        )

        # Converti None a stringa vuota per serializzazione JSON
        event_dict = {
            'event_id': event.event_id,
            'timestamp': event.timestamp.isoformat(),
            'user_id': event.user_id or '',
            'action': event.action,
            'resource': event.resource,
            'result': event.result,
            'compliance_category': event.compliance_category,
            'risk_level': event.risk_level,
            'details': event.details,
            'hash_value': event.hash_value
        }

        self.audit_events.append(event)

        # Scrivi su file
        self._write_audit_event(event)

        logger.info(f"Audit event logged: {action} on {resource} by {user_id}")

    def _write_audit_event(self, event: AuditEvent):
        """Scrive evento di audit su file."""
        try:
            event_dict = {
                'event_id': event.event_id,
                'timestamp': event.timestamp.isoformat(),
                'user_id': event.user_id,
                'action': event.action,
                'resource': event.resource,
                'result': event.result,
                'compliance_category': event.compliance_category,
                'risk_level': event.risk_level,
                'details': event.details,
                'hash_value': event.hash_value
            }

            with open(self.audit_log_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(event_dict) + '\n')

        except Exception as e:
            logger.error(f"Errore scrittura audit event: {e}")

    def generate_compliance_report(self, framework: str, days: int = 30) -> ComplianceReport:
        """Genera un report di compliance per un framework specifico."""
        if framework not in self.compliance_frameworks:
            raise ValueError(f"Framework non supportato: {framework}")

        period_end = datetime.now()
        period_start = period_end - timedelta(days=days)

        # Filtra eventi per periodo
        relevant_events = [
            event for event in self.audit_events
            if period_start <= event.timestamp <= period_end
        ]

        # Calcola punteggio compliance
        overall_score = self._calculate_compliance_score(framework, relevant_events)

        # Genera sezioni del report
        sections = self._generate_report_sections(framework, relevant_events)

        # Genera raccomandazioni
        recommendations = self._generate_recommendations(framework, overall_score, relevant_events)

        # Crea hash dell'audit trail
        audit_trail_content = ''.join(event.hash_value for event in relevant_events)
        audit_trail_hash = hashlib.sha256(audit_trail_content.encode()).hexdigest()

        report = ComplianceReport(
            report_id=f"report_{framework}_{int(time.time())}",
            generated_at=period_end,
            period_start=period_start,
            period_end=period_end,
            compliance_framework=framework,
            overall_score=overall_score,
            sections=sections,
            recommendations=recommendations,
            audit_trail_hash=audit_trail_hash
        )

        # Salva report
        self._save_compliance_report(report)

        return report

    def _calculate_compliance_score(self, framework: str, events: List[AuditEvent]) -> float:
        """Calcola punteggio di compliance."""
        if not events:
            return 0.0

        framework_config = self.compliance_frameworks[framework]
        categories = framework_config['categories']

        category_scores = {}

        for category in categories:
            category_events = [e for e in events if e.compliance_category == category]
            if category_events:
                # Calcola score basato sui risultati degli eventi
                success_count = sum(1 for e in category_events if e.result == 'success')
                total_count = len(category_events)
                category_scores[category] = (success_count / total_count) * 100
            else:
                category_scores[category] = 0.0

        # Punteggio complessivo pesato
        if category_scores:
            return sum(category_scores.values()) / len(category_scores)
        return 0.0

    def _generate_report_sections(self, framework: str, events: List[AuditEvent]) -> Dict[str, Any]:
        """Genera sezioni del report di compliance."""
        sections = {}

        framework_config = self.compliance_frameworks[framework]

        for category in framework_config['categories']:
            category_events = [e for e in events if e.compliance_category == category]

            sections[category] = {
                'events_count': len(category_events),
                'success_rate': self._calculate_success_rate(category_events),
                'risk_distribution': self._calculate_risk_distribution(category_events),
                'top_actions': self._get_top_actions(category_events),
                'recent_events': self._get_recent_events(category_events, limit=5)
            }

        return sections

    def _calculate_success_rate(self, events: List[AuditEvent]) -> float:
        """Calcola tasso di successo per eventi."""
        if not events:
            return 0.0

        success_count = sum(1 for e in events if e.result == 'success')
        return (success_count / len(events)) * 100

    def _calculate_risk_distribution(self, events: List[AuditEvent]) -> Dict[str, int]:
        """Calcola distribuzione del rischio."""
        distribution = {'low': 0, 'medium': 0, 'high': 0, 'critical': 0}

        for event in events:
            distribution[event.risk_level] += 1

        return distribution

    def _get_top_actions(self, events: List[AuditEvent]) -> List[Tuple[str, int]]:
        """Ottieni azioni più frequenti."""
        from collections import Counter

        actions = [event.action for event in events]
        return Counter(actions).most_common(5)

    def _get_recent_events(self, events: List[AuditEvent], limit: int) -> List[Dict[str, Any]]:
        """Ottieni eventi recenti."""
        sorted_events = sorted(events, key=lambda e: e.timestamp, reverse=True)
        recent = sorted_events[:limit]

        return [{
            'timestamp': event.timestamp.isoformat(),
            'action': event.action,
            'result': event.result,
            'risk_level': event.risk_level,
            'details': event.details
        } for event in recent]

    def _generate_recommendations(self, framework: str, score: float,
                                events: List[AuditEvent]) -> List[str]:
        """Genera raccomandazioni basate sui risultati."""
        recommendations = []

        if score < 70:
            recommendations.append("🔴 Punteggio compliance critico - Revisione immediata richiesta")

        if score < 85:
            recommendations.append("🟡 Migliorare controlli di sicurezza e monitoraggio")

        # Raccomandazioni specifiche per framework
        if framework == 'GDPR':
            if not any(e.action == 'data_encryption' for e in events):
                recommendations.append("Crittografia dati non implementata - Rischio violazione GDPR")

            if not any(e.action == 'consent_management' for e in events):
                recommendations.append("Gestione consenso utenti mancante")

        elif framework == 'ISO27001':
            if not any(e.compliance_category == 'risk_assessment' for e in events):
                recommendations.append("Valutazione rischi non regolare - Richiesta ISO27001")

        elif framework == 'NIST':
            if not any(e.action == 'incident_response' for e in events):
                recommendations.append("Piano risposta incidenti mancante")

        # Raccomandazioni basate su eventi ad alto rischio
        high_risk_events = [e for e in events if e.risk_level in ['high', 'critical']]
        if len(high_risk_events) > 10:
            recommendations.append("Elevato numero di eventi ad alto rischio - Investigazione richiesta")

        return recommendations

    def _save_compliance_report(self, report: ComplianceReport):
        """Salva report di compliance su file."""
        try:
            report_file = os.path.join(
                self.reports_path,
                f"compliance_report_{report.compliance_framework}_{report.generated_at.strftime('%Y%m%d_%H%M%S')}.json"
            )

            report_dict = {
                'report_id': report.report_id,
                'generated_at': report.generated_at.isoformat(),
                'period_start': report.period_start.isoformat(),
                'period_end': report.period_end.isoformat(),
                'compliance_framework': report.compliance_framework,
                'overall_score': report.overall_score,
                'sections': report.sections,
                'recommendations': report.recommendations,
                'audit_trail_hash': report.audit_trail_hash
            }

            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report_dict, f, indent=2, ensure_ascii=False)

            logger.info(f"Compliance report saved: {report_file}")

        except Exception as e:
            logger.error(f"Errore salvataggio compliance report: {e}")

    def export_audit_trail_csv(self, filepath: str, days: int = 30):
        """Esporta audit trail in formato CSV."""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            relevant_events = [e for e in self.audit_events if e.timestamp >= cutoff_date]

            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['event_id', 'timestamp', 'user_id', 'action', 'resource',
                            'result', 'compliance_category', 'risk_level', 'details']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                writer.writeheader()
                for event in relevant_events:
                    writer.writerow({
                        'event_id': event.event_id,
                        'timestamp': event.timestamp.isoformat(),
                        'user_id': event.user_id or '',
                        'action': event.action,
                        'resource': event.resource,
                        'result': event.result,
                        'compliance_category': event.compliance_category,
                        'risk_level': event.risk_level,
                        'details': json.dumps(event.details)
                    })

            logger.info(f"Audit trail exported to CSV: {filepath}")

        except Exception as e:
            logger.error(f"Errore esportazione audit trail CSV: {e}")

    def verify_audit_integrity(self) -> Tuple[bool, List[str]]:
        """Verifica integrità dell'audit trail."""
        issues = []

        # Verifica hash degli eventi
        for event in self.audit_events:
            expected_hash = hashlib.sha256(
                f"{event.event_id}{event.user_id}{event.action}{event.resource}{event.result}{event.compliance_category}{event.risk_level}{json.dumps(event.details, sort_keys=True)}".encode()
            ).hexdigest()

            if event.hash_value != expected_hash:
                issues.append(f"Hash mismatch for event {event.event_id}")

        # Verifica sequenza temporale
        sorted_events = sorted(self.audit_events, key=lambda e: e.timestamp)
        for i in range(1, len(sorted_events)):
            if sorted_events[i].timestamp < sorted_events[i-1].timestamp:
                issues.append(f"Time sequence violation between events {sorted_events[i-1].event_id} and {sorted_events[i].event_id}")

        return len(issues) == 0, issues

    def get_compliance_status(self) -> Dict[str, Any]:
        """Ottieni stato generale della compliance."""
        return {
            'total_audit_events': len(self.audit_events),
            'frameworks_supported': list(self.compliance_frameworks.keys()),
            'last_audit_event': self.audit_events[-1].timestamp if self.audit_events else None,
            'audit_integrity': self.verify_audit_integrity()[0],
            'recent_reports': self._get_recent_reports()
        }

    def _get_recent_reports(self) -> List[Dict[str, Any]]:
        """Ottieni report di compliance recenti."""
        if not os.path.exists(self.reports_path):
            return []

        try:
            report_files = [f for f in os.listdir(self.reports_path) if f.endswith('.json')]
            report_files.sort(reverse=True)

            recent_reports = []
            for filename in report_files[:5]:  # Ultimi 5 report
                filepath = os.path.join(self.reports_path, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    report_data = json.load(f)
                    recent_reports.append({
                        'filename': filename,
                        'framework': report_data.get('compliance_framework'),
                        'score': report_data.get('overall_score'),
                        'generated_at': report_data.get('generated_at')
                    })

            return recent_reports

        except Exception as e:
            logger.error(f"Errore lettura report recenti: {e}")
            return []


# Istanza globale del motore di compliance
compliance_engine = ComplianceEngine()


def log_compliance_event(user_id: Optional[str], action: str, resource: str,
                        result: str, compliance_category: str, risk_level: str,
                        details: Optional[Dict[str, Any]] = None):
    """Funzione di comodo per loggare eventi di compliance."""
    compliance_engine.log_audit_event(
        user_id, action, resource, result, compliance_category, risk_level, details
    )


def generate_compliance_report(framework: str, days: int = 30) -> ComplianceReport:
    """Funzione di comodo per generare report di compliance."""
    return compliance_engine.generate_compliance_report(framework, days)


def get_compliance_status() -> Dict[str, Any]:
    """Funzione di comodo per ottenere stato compliance."""
    return compliance_engine.get_compliance_status()


def export_audit_trail_csv(filepath: str, days: int = 30):
    """Funzione di comodo per esportare audit trail."""
    compliance_engine.export_audit_trail_csv(filepath, days)