"""Integration tests verifying hardware detection pipeline execution."""

from llm_advisor.hardware.detector import SystemHardwareDetector
from llm_advisor.hardware.schema import HardwareProfile


def test_live_hardware_detector_execution() -> None:
    detector = SystemHardwareDetector()
    profile = detector.detect()

    assert isinstance(profile, HardwareProfile)
    assert profile.cpu.physical_cores >= 1
    assert profile.memory.total_gb > 0
    assert profile.storage.free_gb >= 0
    assert profile.os_info.platform_name in ("Linux", "Darwin", "Windows")
