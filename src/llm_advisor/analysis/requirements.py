"""Resource overhead calculations for weights, KV cache, and runtime reserve."""

from __future__ import annotations


def calculate_kv_cache_gb(param_count_billions: float, context_length: int) -> float:
    """Estimate KV cache memory requirement in GB based on parameters and context length.

    Formula heuristic:
    KV Cache (GB) = (context_length * param_count_billions) / 500,000.0
    """
    if param_count_billions <= 0 or context_length <= 0:
        return 0.0

    kv_gb = (context_length * param_count_billions) / 500000.0
    return round(kv_gb, 3)


def calculate_total_memory_required_gb(
    file_size_gb: float,
    param_count_billions: float,
    context_length: int,
    runtime_overhead_gb: float = 0.5,
) -> float:
    """Compute total estimated memory required (Weights + KV Cache + Runtime Overhead)."""
    kv_cache_gb = calculate_kv_cache_gb(param_count_billions, context_length)
    total_gb = file_size_gb + kv_cache_gb + runtime_overhead_gb
    return round(total_gb, 2)
