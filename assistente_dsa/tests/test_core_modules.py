#!/usr/bin/env python3
"""
Test Suite per Moduli Core - DSA Assistant
Test per cache_manager, performance_monitor, circuit_breaker, health_monitor, security_monitor
"""

import os
import pytest
import time
import json
import tempfile
from unittest.mock import patch, MagicMock


class TestCacheManager:
    """Test per il cache manager."""

    def setup_method(self):
        """Setup per ogni test."""
        from core.cache_manager import CacheManager, LRUCache, PersistentCache
        self.cache_manager = CacheManager()

    def test_lru_cache_basic_operations(self):
        """Test operazioni base LRU cache."""
        cache = self.cache_manager.get_cache("test")

        # Test put e get
        cache.put("key1", "value1")
        assert cache.get("key1") == "value1"

        # Test cache miss
        assert cache.get("nonexistent") is None

        # Test sovrascrittura
        cache.put("key1", "value2")
        assert cache.get("key1") == "value2"

    def test_lru_cache_eviction(self):
        """Test eviction LRU."""
        cache = self.cache_manager.get_cache("test_small")
        cache.max_size = 2

        # Riempi cache
        cache.put("key1", "value1")
        cache.put("key2", "value2")
        cache.put("key3", "value3")  # Dovrebbe rimuovere key1

        assert cache.get("key1") is None
        assert cache.get("key2") == "value2"
        assert cache.get("key3") == "value3"

    def test_persistent_cache(self):
        """Test cache persistente."""
        with tempfile.TemporaryDirectory() as temp_dir:
            persistent_cache = self.cache_manager.get_persistent_cache()
            # Cambia directory cache per test
            original_dir = persistent_cache.cache_dir
            persistent_cache.cache_dir = temp_dir

            try:
                # Test put e get persistente
                persistent_cache.put("persist_key", {"data": "test"})
                result = persistent_cache.get("persist_key")
                assert result == {"data": "test"}

                # Test persistenza su disco
                cache_file = os.path.join(temp_dir, "cache_file.cache")
                assert os.path.exists(cache_file)

                # Test cleanup
                persistent_cache.cleanup_expired()
                stats = persistent_cache.get_stats()
                assert "disk_files" in stats

            finally:
                persistent_cache.cache_dir = original_dir

    def test_cache_stats(self):
        """Test statistiche cache."""
        cache = self.cache_manager.get_cache("stats_test")
        cache.put("key1", "value1")
        cache.put("key2", "value2")

        stats = cache.get_stats()
        assert stats["total_entries"] == 2
        assert stats["hits"] == 0  # Nessun hit ancora
        assert stats["misses"] == 0

        # Genera hits e misses
        cache.get("key1")  # Hit
        cache.get("nonexistent")  # Miss

        stats = cache.get_stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 1


class TestPerformanceMonitor:
    """Test per il performance monitor."""

    @pytest.fixture(autouse=True)
    def setup_monitor(self):
        """Setup per ogni test."""
        import importlib.util
        import os

        perf_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "core", "performance_monitor.py")
        spec = importlib.util.spec_from_file_location("performance_monitor", perf_path)
        if spec and spec.loader:
            perf_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(perf_module)
            self.monitor = perf_module.PerformanceMonitor()
        else:
            pytest.skip("Performance monitor module not available")

    def test_measure_time_decorator(self):
        """Test decorator per misurazione tempo."""

        @self.monitor.measure_time("test_function")
        def test_func():
            time.sleep(0.01)
            return "result"

        result = test_func()
        assert result == "result"

        # Verifica che la metrica sia stata registrata
        assert len(self.monitor.metrics) > 0
        assert "test_function.execution_time" in self.monitor.metrics

    def test_system_metrics(self):
        """Test raccolta metriche di sistema."""
        metrics = self.monitor.get_system_metrics()

        # Verifica metriche essenziali
        assert "cpu_percent" in metrics
        assert "memory_percent" in metrics
        assert "num_threads" in metrics

        # Verifica che i valori siano ragionevoli
        assert isinstance(metrics["cpu_percent"], (int, float))
        assert isinstance(metrics["memory_percent"], (int, float))

    def test_snapshot_creation(self):
        """Test creazione snapshot."""
        self.monitor.record_metric("test_metric", 42.0)

        snapshot = self.monitor.take_snapshot("test_snapshot")

        assert snapshot["label"] == "test_snapshot"
        assert "system_metrics" in snapshot
        assert "custom_metrics" in snapshot
        assert "timestamp" in snapshot

    def test_performance_report(self):
        """Test generazione report prestazioni."""
        # Aggiungi alcune metriche
        self.monitor.record_metric("test.execution_time", 0.5)
        self.monitor.record_metric("test.execution_time", 1.2)
        self.monitor.record_metric("test.execution_time", 0.8)

        report = self.monitor.get_performance_report()

        assert "current_metrics" in report
        assert "custom_metrics_summary" in report
        assert "test.execution_time" in report["custom_metrics_summary"]

        summary = report["custom_metrics_summary"]["test.execution_time"]
        assert summary["count"] == 3
        assert abs(summary["avg"] - 0.833) < 0.1  # Media approssimativa

    def test_performance_issue_detection(self):
        """Test rilevamento problemi prestazioni."""
        # Simula alto uso CPU
        with patch.object(self.monitor, 'get_system_metrics', return_value={"cpu_percent": 85.0, "memory_percent": 50.0}):
            issues = self.monitor.detect_performance_issues()

            assert len(issues) > 0
            cpu_issue = next((i for i in issues if i["type"] == "high_cpu_usage"), None)
            assert cpu_issue is not None
            assert "CPU elevato" in cpu_issue["message"]

    def test_metrics_export(self):
        """Test esportazione metriche."""
        self.monitor.record_metric("export_test", 123.45)

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_file = f.name

        try:
            self.monitor.export_metrics(temp_file)

            # Verifica che il file sia stato creato e contenga dati validi
            assert os.path.exists(temp_file)

            with open(temp_file, 'r') as f:
                data = json.load(f)

            assert "metrics" in data
            assert "snapshots" in data
            assert "export_timestamp" in data

        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)


class TestCircuitBreaker:
    """Test per il circuit breaker."""

    def setup_method(self):
        """Setup per ogni test."""
        from core.circuit_breaker import CircuitBreaker, CircuitBreakerError
        self.cb = CircuitBreaker(failure_threshold=2, recovery_timeout=1)

    def test_initial_state(self):
        """Test stato iniziale."""
        assert self.cb.get_state().value == "CLOSED"
        assert self.cb.metrics["total_requests"] == 0

    def test_successful_calls(self):
        """Test chiamate riuscite."""
        result = self.cb.call(lambda: "success")
        assert result == "success"
        assert self.cb.metrics["successful_requests"] == 1

    def test_failure_handling(self):
        """Test gestione failure."""
        from core.circuit_breaker import CircuitBreakerError

        # Simula failure
        with pytest.raises(RuntimeError):
            self.cb.call(lambda: (_ for _ in ()).throw(RuntimeError("test error")))

        assert self.cb.metrics["failed_requests"] == 1

        # Dopo threshold, dovrebbe aprire
        with pytest.raises(RuntimeError):
            self.cb.call(lambda: (_ for _ in ()).throw(RuntimeError("test error")))

        # Ora dovrebbe essere aperto
        with pytest.raises(CircuitBreakerError):
            self.cb.call(lambda: "should fail")

    def test_recovery_mechanism(self):
        """Test meccanismo di recovery."""
        from core.circuit_breaker import CircuitBreakerError

        # Porta il circuit breaker in stato OPEN
        for _ in range(3):
            try:
                self.cb.call(lambda: (_ for _ in ()).throw(RuntimeError("error")))
            except RuntimeError:
                pass

        # Verifica che sia aperto
        with pytest.raises(CircuitBreakerError):
            self.cb.call(lambda: "test")

        # Aspetta recovery timeout
        import time
        time.sleep(1.1)

        # Dovrebbe provare recovery e avere successo
        result = self.cb.call(lambda: "recovery success")
        assert result == "recovery success"
        assert self.cb.get_state().value == "CLOSED"


class TestHealthMonitor:
    """Test per il health monitor."""

    def setup_method(self):
        """Setup per ogni test."""
        from core.health_monitor import HealthMonitor
        self.monitor = HealthMonitor()

    def test_add_check(self):
        """Test aggiunta check."""
        def test_check():
            return {"status": "healthy", "message": "OK"}

        self.monitor.add_check("test_check", test_check)

        # Verifica che il check sia stato aggiunto
        assert "test_check" in self.monitor.checks

    def test_run_single_check(self):
        """Test esecuzione singolo check."""
        def healthy_check():
            return {"status": "healthy", "message": "All good"}

        self.monitor.add_check("healthy", healthy_check)

        results = self.monitor.run_all_checks()

        assert "healthy" in results
        assert results["healthy"]["status"] == "healthy"
        assert results["healthy"]["message"] == "All good"

    def test_unhealthy_check(self):
        """Test check non healthy."""
        def unhealthy_check():
            return {"status": "unhealthy", "message": "Something wrong"}

        self.monitor.add_check("unhealthy", unhealthy_check)

        results = self.monitor.run_all_checks()

        assert "unhealthy" in results
        assert results["unhealthy"]["status"] == "unhealthy"

    def test_check_with_exception(self):
        """Test check che solleva eccezione."""
        def failing_check():
            raise Exception("Check failed")

        self.monitor.add_check("failing", failing_check)

        results = self.monitor.run_all_checks()

        assert "failing" in results
        assert results["failing"]["status"] == "unhealthy"
        assert "Check failed" in results["failing"]["message"]

    def test_multiple_checks(self):
        """Test esecuzione multipli check."""
        def check1():
            return {"status": "healthy", "message": "Check 1 OK"}

        def check2():
            return {"status": "healthy", "message": "Check 2 OK"}

        self.monitor.add_check("check1", check1)
        self.monitor.add_check("check2", check2)

        results = self.monitor.run_all_checks()

        assert len(results) == 2
        assert all(r["status"] == "healthy" for r in results.values())


class TestSecurityMonitor:
    """Test per il security monitor."""

    def setup_method(self):
        """Setup per ogni test."""
        from core.security_monitor import SecurityMonitor
        self.monitor = SecurityMonitor()

    def test_log_security_event(self):
        """Test logging eventi sicurezza."""
        self.monitor.log_security_event("TEST_EVENT", {"message": "Test message", "user": "test"}, "INFO")

        # Verifica che l'evento sia stato registrato
        stats = self.monitor.get_security_stats()
        assert stats["recent_activities_count"] >= 1

    def test_event_filtering(self):
        """Test filtraggio eventi."""
        self.monitor.log_security_event("INFO_EVENT", {"message": "Info message"}, "INFO")
        self.monitor.log_security_event("WARN_EVENT", {"message": "Warn message"}, "WARNING")
        self.monitor.log_security_event("ERROR_EVENT", {"message": "Error message"}, "ERROR")

        # Verifica che gli eventi siano stati registrati
        stats = self.monitor.get_security_stats()
        assert stats["recent_activities_count"] >= 3

    def test_recent_activities(self):
        """Test attività recenti."""
        self.monitor.log_security_event("ACTIVITY1", {"message": "Activity 1"}, "INFO")
        self.monitor.log_security_event("ACTIVITY2", {"message": "Activity 2"}, "INFO")

        stats = self.monitor.get_security_stats()
        assert stats["recent_activities_count"] >= 2

    def test_security_incident_detection(self):
        """Test rilevamento incidenti sicurezza."""
        # Log multipli eventi di sicurezza
        for i in range(5):
            self.monitor.log_security_event("SUSPICIOUS_{i}", {"message": "Suspicious activity {i}"}, "WARNING")

        # Verifica che gli eventi siano stati registrati
        stats = self.monitor.get_security_stats()
        assert stats["recent_activities_count"] >= 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
