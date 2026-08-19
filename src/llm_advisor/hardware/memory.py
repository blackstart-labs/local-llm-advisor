"""Memory detection and safe LLM budget calculation."""

from __future__ import annotations

import psutil
from llm_advisor.hardware.schema import MemoryInfo


def calculate_safe_budget(total_bytes: int, available_bytes: int) -> int:
    """Calculate safe RAM allocation budget for local LLMs without causing OS thrashing.

    Formula:
    OS_HEADROOM = max(2.0 GB, 15% of total RAM)
    safe_budget_bytes = max(0, available_bytes - OS_HEADROOM)
    """
    if available_bytes <= 0:
        return 0

    two_gb = 2 * (1024**3)
    fifteen_percent = int(total_bytes * 0.15)
    os_headroom = max(two_gb, fifteen_percent)

    safe_budget = max(0, available_bytes - os_headroom)
    return safe_budget


def detect_memory() -> MemoryInfo:
    """Detect system physical memory and compute safe LLM inference budget."""
    try:
        vm = psutil.virtual_memory()
        total = int(vm.total)
        available = int(vm.available)
        used = int(vm.used)
        utilization = float(vm.percent)
    except Exception:
        # Fail-safe default fallback
        total = 8 * (1024**3)
        available = 4 * (1024**3)
        used = 4 * (1024**3)
        utilization = 50.0

    safe_budget = calculate_safe_budget(total, available)

    return MemoryInfo(
        total_bytes=total,
        available_bytes=available,
        used_bytes=used,
        utilization_percent=utilization,
        safe_budget_bytes=safe_budget,
    )
