"""Singleton Pattern — Thread-safe performance metrics collector."""

import threading
import time
import os
import psutil


class PerformanceMonitor:
    """
    Thread-safe Singleton that tracks application performance metrics.

    Design Pattern: Singleton with double-checked locking.
    Tracks: uptime, peak memory, active threads, request count, avg response time.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    instance = super().__new__(cls)
                    instance._start_time = time.time()
                    instance._request_count = 0
                    instance._total_time = 0.0
                    instance._peak_memory = 0.0
                    cls._instance = instance
        return cls._instance

    def record_request(self, duration: float):
        """Record a completed request's duration."""
        with self._lock:
            self._request_count += 1
            self._total_time += duration
            process = psutil.Process(os.getpid())
            mem = process.memory_info().rss / 1024 / 1024
            if mem > self._peak_memory:
                self._peak_memory = mem

    def get_metrics(self) -> dict:
        """Return current performance metrics."""
        process = psutil.Process(os.getpid())
        mem = process.memory_info().rss / 1024 / 1024
        threads = process.num_threads()
        elapsed = time.time() - self._start_time
        hours, rem = divmod(int(elapsed), 3600)
        minutes, seconds = divmod(rem, 60)
        ms = int((elapsed - int(elapsed)) * 1000)
        return {
            "time": f"{hours:02}:{minutes:02}:{seconds:02}.{ms:03}",
            "memory": f"{mem:.2f} MB",
            "threads": threads,
        }

    def get_detailed_metrics(self) -> dict:
        """Return extended metrics for debugging."""
        base = self.get_metrics()
        avg_time = (
            self._total_time / self._request_count if self._request_count > 0 else 0
        )
        base.update(
            {
                "totalRequests": self._request_count,
                "avgResponseTime": f"{avg_time:.4f}s",
                "peakMemory": f"{self._peak_memory:.2f} MB",
            }
        )
        return base
