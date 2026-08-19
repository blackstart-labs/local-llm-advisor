"""Tests for overall hardware detector pipeline."""

from unittest.mock import MagicMock, patch

from llm_advisor.hardware.detector import SystemHardwareDetector
from llm_advisor.hardware.schema import (
    CpuInfo,
    HardwareProfile,
    MemoryInfo,
    OsInfo,
    RuntimeCapabilities,
    StorageInfo,
)


@patch("llm_advisor.hardware.detector.detect_cpu")
@patch("llm_advisor.hardware.detector.detect_memory")
@patch("llm_advisor.hardware.detector.detect_gpus")
@patch("llm_advisor.hardware.detector.detect_storage")
@patch("llm_advisor.hardware.detector.detect_os")
@patch("llm_advisor.hardware.detector.detect_runtime")
def test_system_hardware_detector(
    mock_runtime: MagicMock,
    mock_os: MagicMock,
    mock_storage: MagicMock,
    mock_gpus: MagicMock,
    mock_memory: MagicMock,
    mock_cpu: MagicMock,
) -> None:
    mock_cpu.return_value = CpuInfo(
        brand="Intel", model="Core i7", physical_cores=4, logical_cores=8
    )
    mock_memory.return_value = MemoryInfo(
        total_bytes=16 * (1024**3),
        available_bytes=12 * (1024**3),
        used_bytes=4 * (1024**3),
        utilization_percent=25.0,
        safe_budget_bytes=9 * (1024**3),
    )
    mock_gpus.return_value = []
    mock_storage.return_value = StorageInfo(free_bytes=100 * (1024**3), total_bytes=500 * (1024**3))
    mock_os.return_value = OsInfo(
        platform_name="Linux", release="6.5", version="1", architecture="x86_64"
    )
    mock_runtime.return_value = RuntimeCapabilities(has_ollama=True)

    detector = SystemHardwareDetector()
    profile = detector.detect()

    assert isinstance(profile, HardwareProfile)
    assert profile.cpu.brand == "Intel"
    assert profile.memory.total_gb == 16.0
    assert profile.runtime.has_ollama is True
