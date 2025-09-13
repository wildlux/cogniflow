#!/usr/bin/env python3
"""
Threat Detection Engine - Motore di rilevamento minacce avanzato
Correlazione eventi e analisi comportamentale per sicurezza proattiva
"""

import time
import threading
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Set
from collections import defaultdict, deque
import logging
import re
import hashlib
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ThreatPattern:
    """Pattern di minaccia identificato."""
    pattern_id: str
    name: str
    description: str
    severity: str
    indicators: List[str]
    confidence: float
    first_seen: datetime
    last_seen: datetime
    occurrences: int = 0
    correlated_events: List[str] = field(default_factory=list)


@dataclass
class SecurityEvent:
    """Evento di sicurezza per analisi."""
    event_id: str
    timestamp: datetime
    event_type: str
    source_ip: Optional[str]
    user_id: Optional[str]
    resource: str
    action: str
    result: str
    metadata: Dict[str, Any]
    risk_score: float = 0.0


class ThreatDetectionEngine:
    """Motore avanzato per rilevamento minacce."""

    def __init__(self):
        self.known_threats: Dict[str, ThreatPattern] = {}
        self.event_buffer: deque = deque(maxlen=10000)  # Buffer circolare per eventi
        self.correlation_rules: Dict[str, Dict[str, Any]] = {}
        self.risk_thresholds = {
            'low': 0.3,
            'medium': 0.6,
            'high': 0.8,
            'critical': 0.95
        }
        self.monitoring_active = False
        self.analysis_thread: Optional[threading.Thread] = None

        # Inizializza pattern di minaccia conosciuti
        self._initialize_threat_patterns()
        self._initialize_correlation_rules()

    def _initialize_threat_patterns(self):
        """Inizializza pattern di minaccia conosciuti."""
        self.known_threats = {
            'brute_force_attack': ThreatPattern(
                pattern_id='brute_force_attack',
                name='Brute Force Attack',
                description='Multiple failed authentication attempts',
                severity='HIGH',
                indicators=['failed_login', 'rate_limit_exceeded'],
                confidence=0.8,
                first_seen=datetime.now(),
                last_seen=datetime.now()
            ),
            'privilege_escalation': ThreatPattern(
                pattern_id='privilege_escalation',
                name='Privilege Escalation Attempt',
                description='Attempt to gain higher privileges',
                severity='CRITICAL',
                indicators=['unauthorized_access', 'admin_function_access'],
                confidence=0.9,
                first_seen=datetime.now(),
                last_seen=datetime.now()
            ),
            'data_exfiltration': ThreatPattern(
                pattern_id='data_exfiltration',
                name='Data Exfiltration',
                description='Large data transfers or unusual file access',
                severity='HIGH',
                indicators=['large_file_download', 'unusual_file_access'],
                confidence=0.7,
                first_seen=datetime.now(),
                last_seen=datetime.now()
            ),
            'sql_injection_attempt': ThreatPattern(
                pattern_id='sql_injection_attempt',
                name='SQL Injection Attempt',
                description='Potential SQL injection attack',
                severity='CRITICAL',
                indicators=['suspicious_sql_pattern', 'database_error'],
                confidence=0.95,
                first_seen=datetime.now(),
                last_seen=datetime.now()
            ),
            'xss_attack': ThreatPattern(
                pattern_id='xss_attack',
                name='Cross-Site Scripting Attack',
                description='Potential XSS attack detected',
                severity='HIGH',
                indicators=['script_injection', 'html_injection'],
                confidence=0.85,
                first_seen=datetime.now(),
                last_seen=datetime.now()
            ),
            'anomalous_behavior': ThreatPattern(
                pattern_id='anomalous_behavior',
                name='Anomalous User Behavior',
                description='Unusual user activity patterns',
                severity='MEDIUM',
                indicators=['unusual_time_access', 'unusual_location'],
                confidence=0.6,
                first_seen=datetime.now(),
                last_seen=datetime.now()
            )
        }

    def _initialize_correlation_rules(self):
        """Inizializza regole di correlazione eventi."""
        self.correlation_rules = {
            'multi_stage_attack': {
                'description': 'Multi-stage attack pattern',
                'events': ['reconnaissance', 'initial_compromise', 'privilege_escalation'],
                'time_window': 3600,  # 1 ora
                'severity': 'CRITICAL'
            },
            'lateral_movement': {
                'description': 'Lateral movement within network',
                'events': ['successful_login', 'file_access', 'network_scan'],
                'time_window': 1800,  # 30 minuti
                'severity': 'HIGH'
            },
            'data_theft_campaign': {
                'description': 'Coordinated data theft attempt',
                'events': ['large_download', 'encryption_attempt', 'data_access'],
                'time_window': 7200,  # 2 ore
                'severity': 'CRITICAL'
            }
        }

    def add_security_event(self, event: SecurityEvent):
        """Aggiunge un evento di sicurezza per analisi."""
        self.event_buffer.append(event)

        # Analizza evento immediatamente per minacce note
        self._analyze_single_event(event)

        logger.debug(f"Security event added: {event.event_type} from {event.source_ip}")

    def _analyze_single_event(self, event: SecurityEvent) -> List[ThreatPattern]:
        """Analizza un singolo evento per pattern di minaccia."""
        detected_threats = []

        for threat_id, threat in self.known_threats.items():
            match_score = self._calculate_pattern_match(event, threat)
            if match_score >= threat.confidence:
                threat.occurrences += 1
                threat.last_seen = datetime.now()
                threat.correlated_events.append(event.event_id)
                detected_threats.append(threat)

                logger.warning(f"Threat detected: {threat.name} (confidence: {match_score:.2f})")

        return detected_threats

    def _calculate_pattern_match(self, event: SecurityEvent, threat: ThreatPattern) -> float:
        """Calcola quanto un evento corrisponde a un pattern di minaccia."""
        match_score = 0.0
        total_indicators = len(threat.indicators)

        if total_indicators == 0:
            return 0.0

        for indicator in threat.indicators:
            if self._event_matches_indicator(event, indicator):
                match_score += 1.0

        # Bonus per metadata rilevanti
        if event.metadata:
            metadata_bonus = self._calculate_metadata_bonus(event, threat)
            match_score += metadata_bonus

        return min(match_score / total_indicators, 1.0)

    def _event_matches_indicator(self, event: SecurityEvent, indicator: str) -> bool:
        """Verifica se un evento corrisponde a un indicatore."""
        # Mapping indicatori a controlli
        indicator_checks = {
            'failed_login': lambda e: e.event_type == 'authentication' and e.result == 'failed',
            'successful_login': lambda e: e.event_type == 'authentication' and e.result == 'success',
            'unauthorized_access': lambda e: e.event_type == 'access' and e.result == 'denied',
            'admin_function_access': lambda e: e.action in ['admin_panel', 'user_management'] and e.result == 'success',
            'large_file_download': lambda e: e.event_type == 'file_access' and e.metadata.get('file_size', 0) > 1000000,
            'unusual_file_access': lambda e: e.event_type == 'file_access' and self._is_unusual_file_access(e),
            'suspicious_sql_pattern': lambda e: self._contains_sql_injection_patterns(e),
            'database_error': lambda e: e.event_type == 'database' and e.result == 'error',
            'script_injection': lambda e: self._contains_script_injection(e),
            'html_injection': lambda e: self._contains_html_injection(e),
            'unusual_time_access': lambda e: self._is_unusual_time_access(e),
            'rate_limit_exceeded': lambda e: e.event_type == 'rate_limit' and e.result == 'exceeded'
        }

        check_func = indicator_checks.get(indicator)
        return check_func(event) if check_func else False

    def _calculate_metadata_bonus(self, event: SecurityEvent, threat: ThreatPattern) -> float:
        """Calcola bonus basato sui metadata dell'evento."""
        bonus = 0.0

        if threat.pattern_id == 'brute_force_attack':
            if event.metadata.get('attempt_count', 0) > 5:
                bonus += 0.3

        elif threat.pattern_id == 'data_exfiltration':
            if event.metadata.get('transfer_rate', 0) > 1000000:  # 1MB/s
                bonus += 0.4

        elif threat.pattern_id == 'sql_injection_attempt':
            if len(event.metadata.get('query_length', 0)) > 1000:
                bonus += 0.2

        return bonus

    def _is_unusual_file_access(self, event: SecurityEvent) -> bool:
        """Verifica se l'accesso file è insolito."""
        # Logica semplificata - in produzione userebbe ML
        unusual_patterns = [
            r'\.exe$', r'\.bat$', r'\.cmd$', r'\.scr$', r'\.pif$',
            r'\\windows\\', r'\\system32\\', r'/etc/', r'/bin/'
        ]

        resource = event.resource.lower()
        return any(re.search(pattern, resource) for pattern in unusual_patterns)

    def _contains_sql_injection_patterns(self, event: SecurityEvent) -> bool:
        """Verifica presenza pattern SQL injection."""
        sql_patterns = [
            r';\s*DROP', r';\s*DELETE', r';\s*UPDATE', r';\s*INSERT',
            r'UNION\s+SELECT', r'OR\s+\d+=\d+', r'--', r'/\*.*\*/',
            r';\s*EXEC', r';\s*EXECUTE'
        ]

        query = str(event.metadata.get('query', '')).upper()
        return any(re.search(pattern, query) for pattern in sql_patterns)

    def _contains_script_injection(self, event: SecurityEvent) -> bool:
        """Verifica presenza script injection."""
        script_patterns = [
            r'<script[^>]*>.*?</script>',
            r'javascript:',
            r'vbscript:',
            r'on\w+\s*=',
            r'eval\s*\(',
            r'document\.cookie',
            r'window\.location'
        ]

        data = str(event.metadata.get('input_data', ''))
        return any(re.search(pattern, data, re.IGNORECASE) for pattern in script_patterns)

    def _contains_html_injection(self, event: SecurityEvent) -> bool:
        """Verifica presenza HTML injection."""
        html_patterns = [
            r'<[^>]+>',  # Tag HTML
            r'&lt;[^&]+&gt;',  # HTML entities
            r'<iframe[^>]*>',
            r'<object[^>]*>',
            r'<embed[^>]*>'
        ]

        data = str(event.metadata.get('input_data', ''))
        return any(re.search(pattern, data, re.IGNORECASE) for pattern in html_patterns)

    def _is_unusual_time_access(self, event: SecurityEvent) -> bool:
        """Verifica se l'accesso è in orario insolito."""
        # Logica semplificata - in produzione userebbe analisi storica
        hour = event.timestamp.hour

        # Considera insoliti gli accessi tra le 2:00 e le 5:00
        return 2 <= hour <= 5

    def analyze_event_correlation(self) -> List[Dict[str, Any]]:
        """Analizza correlazione eventi per minacce complesse."""
        correlations = []

        for rule_name, rule in self.correlation_rules.items():
            correlated_events = self._find_correlated_events(rule)
            if correlated_events:
                correlation = {
                    'rule_name': rule_name,
                    'description': rule['description'],
                    'severity': rule['severity'],
                    'events': correlated_events,
                    'confidence': len(correlated_events) / len(rule['events']),
                    'timestamp': datetime.now()
                }
                correlations.append(correlation)

                logger.warning(f"Event correlation detected: {rule_name}")

        return correlations

    def _find_correlated_events(self, rule: Dict[str, Any]) -> List[SecurityEvent]:
        """Trova eventi correlati secondo una regola."""
        time_window = rule['time_window']
        required_events = set(rule['events'])
        cutoff_time = datetime.now() - timedelta(seconds=time_window)

        # Trova eventi recenti che corrispondono
        matching_events = []
        found_event_types = set()

        for event in reversed(list(self.event_buffer)):
            if event.timestamp < cutoff_time:
                break

            if event.event_type in required_events:
                matching_events.append(event)
                found_event_types.add(event.event_type)

        # Verifica se abbiamo tutti i tipi di evento richiesti
        if found_event_types >= required_events:
            return matching_events

        return []

    def calculate_risk_score(self, event: SecurityEvent) -> float:
        """Calcola punteggio di rischio per un evento."""
        base_score = 0.0

        # Score basato sul tipo di evento
        event_risks = {
            'authentication': 0.3,
            'file_access': 0.4,
            'network': 0.5,
            'database': 0.6,
            'admin_action': 0.8,
            'system': 0.7
        }

        base_score += event_risks.get(event.event_type, 0.1)

        # Score basato sul risultato
        if event.result == 'failed':
            base_score += 0.3
        elif event.result == 'denied':
            base_score += 0.4
        elif event.result == 'error':
            base_score += 0.2

        # Score basato sui metadata
        if event.metadata:
            metadata_score = self._calculate_metadata_risk(event.metadata)
            base_score += metadata_score

        # Score basato sulla correlazione con minacce note
        threat_score = self._calculate_threat_correlation_score(event)
        base_score += threat_score

        return min(base_score, 1.0)

    def _calculate_metadata_risk(self, metadata: Dict[str, Any]) -> float:
        """Calcola rischio basato sui metadata."""
        risk_score = 0.0

        # Rischio basato sulla dimensione dei dati
        if 'file_size' in metadata:
            size_mb = metadata['file_size'] / (1024 * 1024)
            if size_mb > 100:
                risk_score += 0.3
            elif size_mb > 10:
                risk_score += 0.1

        # Rischio basato sul numero di tentativi
        if 'attempt_count' in metadata:
            attempts = metadata['attempt_count']
            if attempts > 10:
                risk_score += 0.4
            elif attempts > 5:
                risk_score += 0.2

        # Rischio basato sulla velocità di trasferimento
        if 'transfer_rate' in metadata:
            rate_mbps = metadata['transfer_rate'] / (1024 * 1024)
            if rate_mbps > 50:
                risk_score += 0.3

        return risk_score

    def _calculate_threat_correlation_score(self, event: SecurityEvent) -> float:
        """Calcola score basato sulla correlazione con minacce note."""
        max_correlation = 0.0

        for threat in self.known_threats.values():
            correlation = self._calculate_pattern_match(event, threat)
            max_correlation = max(max_correlation, correlation)

        return max_correlation * 0.5  # Peso 50%

    def get_threat_intelligence(self) -> Dict[str, Any]:
        """Ottieni intelligence sulle minacce rilevate."""
        return {
            'active_threats': len([t for t in self.known_threats.values() if t.occurrences > 0]),
            'total_occurrences': sum(t.occurrences for t in self.known_threats.values()),
            'most_active_threat': max(self.known_threats.values(), key=lambda t: t.occurrences),
            'recent_correlations': self.analyze_event_correlation(),
            'risk_distribution': self._calculate_risk_distribution()
        }

    def _calculate_risk_distribution(self) -> Dict[str, int]:
        """Calcola distribuzione del rischio degli eventi recenti."""
        risk_levels = {'low': 0, 'medium': 0, 'high': 0, 'critical': 0}

        for event in list(self.event_buffer)[-100:]:  # Ultimi 100 eventi
            risk = event.risk_score
            if risk >= self.risk_thresholds['critical']:
                risk_levels['critical'] += 1
            elif risk >= self.risk_thresholds['high']:
                risk_levels['high'] += 1
            elif risk >= self.risk_thresholds['medium']:
                risk_levels['medium'] += 1
            else:
                risk_levels['low'] += 1

        return risk_levels

    def start_monitoring(self):
        """Avvia monitoraggio minacce."""
        if self.monitoring_active:
            return

        self.monitoring_active = True
        self.analysis_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.analysis_thread.start()
        logger.info("Threat detection monitoring started")

    def stop_monitoring(self):
        """Ferma monitoraggio minacce."""
        self.monitoring_active = False
        if self.analysis_thread:
            self.analysis_thread.join(timeout=5)
        logger.info("Threat detection monitoring stopped")

    def _monitoring_loop(self):
        """Loop principale di monitoraggio."""
        while self.monitoring_active:
            try:
                # Analizza correlazioni eventi
                correlations = self.analyze_event_correlation()
                if correlations:
                    for correlation in correlations:
                        logger.warning(f"Advanced threat correlation: {correlation['rule_name']}")

                # Aggiorna punteggi di rischio per eventi recenti
                for event in list(self.event_buffer)[-50:]:  # Ultimi 50 eventi
                    if event.risk_score == 0.0:  # Non ancora calcolato
                        event.risk_score = self.calculate_risk_score(event)

                time.sleep(60)  # Analizza ogni minuto

            except Exception as e:
                logger.error(f"Error in threat detection monitoring: {e}")
                time.sleep(120)  # Aspetta più tempo in caso di errore


# Istanza globale del motore di rilevamento minacce
threat_detection_engine = ThreatDetectionEngine()


def analyze_security_event(event_type: str, source_ip: Optional[str] = None,
                          user_id: Optional[str] = None, resource: str = "",
                          action: str = "", result: str = "",
                          metadata: Optional[Dict[str, Any]] = None) -> List[ThreatPattern]:
    """Funzione di comodo per analizzare un evento di sicurezza."""
    if metadata is None:
        metadata = {}

    event = SecurityEvent(
        event_id=f"evt_{int(time.time() * 1000)}_{hashlib.md5(str(metadata).encode()).hexdigest()[:8]}",
        timestamp=datetime.now(),
        event_type=event_type,
        source_ip=source_ip,
        user_id=user_id,
        resource=resource,
        action=action,
        result=result,
        metadata=metadata
    )

    threat_detection_engine.add_security_event(event)
    return threat_detection_engine._analyze_single_event(event)


def get_threat_intelligence() -> Dict[str, Any]:
    """Funzione di comodo per ottenere intelligence sulle minacce."""
    return threat_detection_engine.get_threat_intelligence()


def start_threat_monitoring():
    """Avvia monitoraggio minacce."""
    threat_detection_engine.start_monitoring()


def stop_threat_monitoring():
    """Ferma monitoraggio minacce."""
    threat_detection_engine.stop_monitoring()