"""Performance metrics endpoint."""

from fastapi import APIRouter
from core.performance_monitor import PerformanceMonitor

router = APIRouter(tags=["Performance"])


@router.get("/performance")
async def get_performance():
    """
    Performance Report — System execution metrics.

    Returns time (uptime), memory usage, and thread count.
    """
    monitor = PerformanceMonitor()
    return monitor.get_metrics()
