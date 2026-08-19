"""Tests for resource requirement and KV cache memory calculation."""

from llm_advisor.analysis.requirements import (
    calculate_kv_cache_gb,
    calculate_total_memory_required_gb,
)


def test_calculate_kv_cache_small_context() -> None:
    # 7B model at 8K context
    kv_gb = calculate_kv_cache_gb(param_count_billions=7.0, context_length=8192)
    assert 0.05 <= kv_gb <= 0.25


def test_calculate_kv_cache_large_context() -> None:
    # 70B model at 128K context
    kv_gb = calculate_kv_cache_gb(param_count_billions=70.0, context_length=128000)
    assert 15.0 <= kv_gb <= 22.0


def test_calculate_total_memory_required() -> None:
    # Base weight: 4.5 GB, 7B params, 8K context
    total_req = calculate_total_memory_required_gb(
        file_size_gb=4.5, param_count_billions=7.0, context_length=8192, runtime_overhead_gb=0.5
    )
    assert 5.0 <= total_req <= 5.5
