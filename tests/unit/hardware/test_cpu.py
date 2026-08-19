"""Tests for CPU hardware detection."""

from unittest.mock import MagicMock, patch

from llm_advisor.hardware.cpu import detect_cpu


@patch("psutil.cpu_count")
@patch("platform.processor")
@patch("platform.machine")
def test_detect_cpu_basic(
    mock_machine: MagicMock,
    mock_processor: MagicMock,
    mock_cpu_count: MagicMock,
) -> None:
    mock_machine.return_value = "x86_64"
    mock_processor.return_value = "x86_64"
    mock_cpu_count.side_effect = lambda logical=True: 8 if logical else 4

    cpu_info = detect_cpu()

    assert cpu_info.physical_cores == 4
    assert cpu_info.logical_cores == 8
    assert cpu_info.is_64bit is True
    assert "x86_64" in cpu_info.architecture or "x86" in cpu_info.architecture
