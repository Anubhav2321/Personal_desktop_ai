"""
ARIS System Monitor API
Real-time system stats endpoint for the live HUD dashboard.
"""

from fastapi import APIRouter

router = APIRouter()

# Import from our system_control module
from .system_control import get_system_stats, get_running_processes, PSUTIL_AVAILABLE


@router.get("/system/stats")
async def system_stats():
    """Return real-time system statistics for the frontend dashboard."""
    stats = get_system_stats()
    return {"status": "ok", "stats": stats, "psutil_available": PSUTIL_AVAILABLE}


@router.get("/system/processes")
async def system_processes():
    """Return top processes by memory usage."""
    procs = get_running_processes(limit=10)
    return {"status": "ok", "processes": procs}
