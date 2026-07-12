#!/usr/bin/env python3
"""
Circuit Breaker - Pattern per gestire failure di servizi esterni
Implementa il pattern Circuit Breaker per l'AI e altri servizi
"""

import time
import logging
import threading
from enum import Enum
from typing import Callable, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class CircuitBreakerState(Enum):
    """Stati del Circuit Breaker"""

    CLOSED = "CLOSED"  # Stato normale, richieste passano attraverso
    OPEN = "OPEN"  # Circuito aperto, richieste bloccate
    HALF_OPEN = "HALF_OPEN"  # Test di recovery, permette alcune richieste


class CircuitBreakerError(Exception):
    """Eccezione lanciata quando il circuit breaker è aperto."""

    pass


class CircuitBreaker:
    """
    Implementazione del pattern Circuit Breaker.

    Stati:
    - CLOSED: Richieste normali, tutto funziona
    - OPEN: Servizio non disponibile, blocca richieste
    - HALF_OPEN: Test di recovery, permette poche richieste
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception=Exception,
        success_threshold: int = 3,
        timeout: float = 10.0,
    ):
        """
        Inizializza il Circuit Breaker.

        Args:
            failure_threshold: Numero di failure prima di aprire il circuito
            recovery_timeout: Secondi prima di provare recovery
            expected_exception: Tipo di eccezione che conta come failure
            success_threshold: Successi richiesti per chiudere il circuito
            timeout: Timeout per le operazioni
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.success_threshold = success_threshold
        self.timeout = timeout

        # Stato corrente
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None

        # Lock per thread safety
        self.lock = threading.Lock()

        # Metriche
        self.metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "rejected_requests": 0,
            "state_changes": [],
        }

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Esegue una funzione attraverso il circuit breaker.

        Args:
            func: Funzione da eseguire
            *args: Argomenti posizionali
            **kwargs: Argomenti keyword

        Returns:
            Risultato della funzione

        Raises:
            CircuitBreakerError: Se il circuito è aperto
        """
        with self.lock:
            self.metrics["total_requests"] += 1

            if self.state == CircuitBreakerState.OPEN:
                if self._should_attempt_reset():
                    self._change_state(CircuitBreakerState.HALF_OPEN)
                else:
                    self.metrics["rejected_requests"] += 1
                    raise CircuitBreakerError("Circuit breaker is OPEN")

            if self.state == CircuitBreakerState.HALF_OPEN:
                # In half-open, permetti solo alcune richieste
                if self.success_count >= self.success_threshold:
                    self._change_state(CircuitBreakerState.CLOSED)

        try:
            # Esegui la funzione con timeout
            result = self._call_with_timeout(func, *args, **kwargs)
            self._on_success()
            return result

        except self.expected_exception as e:
            self._on_failure()
            raise e

    def _call_with_timeout(self, func: Callable, *args, **kwargs) -> Any:
        """Esegue una funzione con timeout."""
        try:
            import signal

            def timeout_handler(signum, frame):
                raise TimeoutError("Operation timed out")

            # Imposta il signal handler per il timeout (solo su Unix-like systems)
            old_handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(int(self.timeout))

            try:
                result = func(*args, **kwargs)
                return result
            finally:
                # Ripristina il signal handler
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)

        except ImportError:
            # Su Windows, signal non è disponibile, usa un approccio alternativo
            import threading

            result: Optional[Any] = None
            exception: Optional[Exception] = None
            completed = False

            def target():
                nonlocal result, exception, completed
                try:
                    result = func(*args, **kwargs)
                except Exception as e:
                    exception = e
                finally:
                    completed = True

            thread = threading.Thread(target=target)
            thread.start()
            thread.join(self.timeout)

            if not completed:
                # Timeout occurred
                raise TimeoutError("Operation timed out")
            elif exception:
                raise exception
            else:
                return result

    def _on_success(self):
        """Gestisce un successo."""
        with self.lock:
            self.metrics["successful_requests"] += 1

            if self.state == CircuitBreakerState.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= self.success_threshold:
                    self._change_state(CircuitBreakerState.CLOSED)
            elif self.state == CircuitBreakerState.CLOSED:
                # Reset failure count su successo
                self.failure_count = 0

    def _on_failure(self):
        """Gestisce un failure."""
        with self.lock:
            self.metrics["failed_requests"] += 1
            self.failure_count += 1
            self.last_failure_time = time.time()

            if self.failure_count >= self.failure_threshold:
                self._change_state(CircuitBreakerState.OPEN)

    def _should_attempt_reset(self) -> bool:
        """Verifica se è tempo di provare il reset."""
        if self.last_failure_time is None:
            return False

        elapsed = time.time() - self.last_failure_time
        return elapsed >= self.recovery_timeout

    def _change_state(self, new_state: CircuitBreakerState):
        """Cambia lo stato del circuit breaker."""
        old_state = self.state
        self.state = new_state

        # Reset contatori quando appropriato
        if new_state == CircuitBreakerState.CLOSED:
            self.failure_count = 0
            self.success_count = 0
        elif new_state == CircuitBreakerState.HALF_OPEN:
            self.success_count = 0

        # Log del cambio di stato
        self.metrics["state_changes"].append(
            {
                "timestamp": datetime.now(),
                "from_state": old_state.value,
                "to_state": new_state.value,
            }
        )

        logger.info(
            "Circuit Breaker state changed: {old_state.value} -> {new_state.value}"
        )

    def get_state(self) -> CircuitBreakerState:
        """Restituisce lo stato corrente."""
        return self.state

    def get_metrics(self) -> dict:
        """Restituisce le metriche del circuit breaker."""
        with self.lock:
            return self.metrics.copy()

    def reset(self):
        """Reset manuale del circuit breaker."""
        with self.lock:
            self._change_state(CircuitBreakerState.CLOSED)
            self.failure_count = 0
            self.success_count = 0
            self.last_failure_time = None

    def is_available(self) -> bool:
        """Verifica se il servizio è disponibile attraverso il circuit breaker."""
        return self.state in [CircuitBreakerState.CLOSED, CircuitBreakerState.HALF_OPEN]


# Circuit Breaker specifici per i servizi
ai_circuit_breaker = CircuitBreaker(
    failure_threshold=3,  # Apri dopo 3 failure
    recovery_timeout=30,  # Prova recovery dopo 30 secondi
    timeout=15.0,  # Timeout di 15 secondi per le richieste AI
    success_threshold=2,  # Richiedi 2 successi per chiudere
)

tts_circuit_breaker = CircuitBreaker(
    failure_threshold=5,  # Più tollerante per TTS
    recovery_timeout=60,  # Recovery più lento
    timeout=10.0,
    success_threshold=3,
)

network_circuit_breaker = CircuitBreaker(
    failure_threshold=10,  # Molto tollerante per rete
    recovery_timeout=120,  # Recovery lento
    timeout=5.0,
    success_threshold=5,
)


def get_ai_circuit_breaker() -> CircuitBreaker:
    """Restituisce il circuit breaker per l'AI."""
    return ai_circuit_breaker


def get_tts_circuit_breaker() -> CircuitBreaker:
    """Restituisce il circuit breaker per TTS."""
    return tts_circuit_breaker


def get_network_circuit_breaker() -> CircuitBreaker:
    """Restituisce il circuit breaker per la rete."""
    return network_circuit_breaker
