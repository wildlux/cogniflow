"""
Performance monitoring module for tracking system performance.
"""

import os, time, threading
from typing import cast, Optional, Callable, Any

performance_thread = None
stop_monitoring = False
performance_monitor = None
measure_function_time = None

def conditional_decorator(decorator_func, name: str):
    """Apply decorator conditionally."""
    def decorator(func):
        return decorator_func(name)(func) if decorator_func else func
    return decorator

@conditional_decorator(measure_function_time, "security_checks")
def start_performance_monitoring():
    """Start performance monitoring thread."""
    global performance_thread, stop_monitoring
    if not performance_monitor:
        return

    def monitoring_worker():
        snapshot_count = 0
        while not stop_monitoring:
            try:
                snapshot_count += 1
                if performance_monitor:
                    performance_monitor.take_snapshot(f"periodic_{snapshot_count}")
                time.sleep(30)
            except Exception as e:
                print(f"Performance monitoring error: {e}")
                break

    stop_monitoring = False
    performance_thread = threading.Thread(target=monitoring_worker, daemon=True)
    performance_thread.start()
    print("🔄 Performance monitoring started (30s intervals)")

def stop_performance_monitoring():
    """Stop performance monitoring thread."""
    global stop_monitoring
    if performance_thread and performance_thread.is_alive():
        stop_monitoring = True
        performance_thread.join(timeout=5)
        print("✅ Performance monitoring stopped")

def initialize_performance_monitor():
    """Initialize performance monitor if available"""
    global performance_monitor, measure_function_time

    try:
        import importlib.util
        perf_path = os.path.join(os.path.dirname(__file__), "performance_monitor.py")
        spec = importlib.util.spec_from_file_location("performance_monitor", perf_path)
        if spec and spec.loader:
            perf_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(perf_module)
            performance_monitor = perf_module.performance_monitor
            measure_function_time = perf_module.measure_function_time
            print("✅ Performance monitor loaded")
            return True
    except Exception as e:
        print(f"⚠️  Performance monitor not available: {e}")

    return False