"""Hardware detector abstraction layer and platform implementation."""

from __future__ import annotations

from abc import ABC, abstractmethod

from llm_advisor.hardware.cpu import detect_cpu
from llm_advisor.hardware.gpu import detect_gpus
from llm_advisor.hardware.memory import detect_memory
from llm_advisor.hardware.os import detect_os
from llm_advisor.hardware.runtime import detect_runtime
from llm_advisor.hardware.schema import HardwareProfile
from llm_advisor.hardware.storage import detect_storage


class HardwareDetector(ABC):
    """Abstract interface for system hardware detection."""

    @abstractmethod
    def detect(self) -> HardwareProfile:
        """Collect and return normalized hardware profile."""
        pass


class SystemHardwareDetector(HardwareDetector):
    """Concrete detector inspecting local operating system and hardware."""

    def detect(self) -> HardwareProfile:
        cpu = detect_cpu()
        memory = detect_memory()
        gpus = detect_gpus()
        storage = detect_storage()
        os_info = detect_os()
        runtime = detect_runtime()

        return HardwareProfile(
            cpu=cpu,
            memory=memory,
            gpus=gpus,
            storage=storage,
            os_info=os_info,
            runtime=runtime,
        )
