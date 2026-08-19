"""Tests for memory detection and safe inference budget calculations."""

from unittest.mock import MagicMock, patch

from llm_advisor.hardware.memory import calculate_safe_budget, detect_memory


def test_calculate_safe_budget_standard_16gb() -> None:
    # Total: 16 GB, Available: 12 GB
    total = 16 * (1024**3)
    available = 12 * (1024**3)

    safe_budget = calculate_safe_budget(total, available)
    safe_gb = safe_budget / (1024**3)

    # OS headroom = max(2 GB, 15% of 16 GB = 2.4 GB) = 2.4 GB
    # Safe budget = 12 GB - 2.4 GB = 9.6 GB
    assert 9.5 <= safe_gb <= 9.7


def test_calculate_safe_budget_low_memory_8gb() -> None:
    # Total: 8 GB, Available: 4 GB
    total = 8 * (1024**3)
    available = 4 * (1024**3)

    safe_budget = calculate_safe_budget(total, available)
    safe_gb = safe_budget / (1024**3)

    # OS headroom = max(2 GB, 1.2 GB) = 2.0 GB
    # Safe budget = 4.0 GB - 2.0 GB = 2.0 GB
    assert 1.9 <= safe_gb <= 2.1


def test_calculate_safe_budget_zero_available() -> None:
    total = 16 * (1024**3)
    available = 0

    safe_budget = calculate_safe_budget(total, available)
    assert safe_budget == 0


@patch("psutil.virtual_memory")
def test_detect_memory_psutil(mock_vm: MagicMock) -> None:
    mock_vm.return_value = MagicMock(
        total=16 * (1024**3),
        available=10 * (1024**3),
        used=6 * (1024**3),
        percent=37.5,
    )

    mem_info = detect_memory()

    assert mem_info.total_gb == 16.0
    assert mem_info.available_gb == 10.0
    assert mem_info.utilization_percent == 37.5
    assert mem_info.safe_budget_gb > 0.0
