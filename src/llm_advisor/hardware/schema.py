"""Hardware domain models and immutability definitions."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class GpuVendor(str, Enum):
    """Supported GPU vendor categories."""

    NVIDIA = "NVIDIA"
    AMD = "AMD"
    INTEL = "Intel"
    APPLE = "Apple"
    UNKNOWN = "Unknown"


class StorageType(str, Enum):
    """Storage drive technology classification."""

    NVME = "NVMe"
    SSD = "SSD"
    HDD = "HDD"
    UNKNOWN = "Unknown"


class CpuInfo(BaseModel, frozen=True):
    """CPU specifications and instruction set capabilities."""

    brand: str = "Unknown CPU"
    model: str = "Unknown Model"
    architecture: str = "x86_64"
    physical_cores: int = 1
    logical_cores: int = 1
    frequency_ghz: float | None = None
    instruction_sets: list[str] = Field(default_factory=list)
    is_64bit: bool = True

    @property
    def summary_string(self) -> str:
        """User-friendly summary string of the CPU."""
        cores_str = f"{self.physical_cores}c/{self.logical_cores}t"
        freq_str = f" @ {self.frequency_ghz:.2f}GHz" if self.frequency_ghz else ""
        return f"{self.brand} {self.model} ({cores_str}){freq_str}"


class MemoryInfo(BaseModel, frozen=True):
    """System RAM metrics and conservative inference budget."""

    total_bytes: int
    available_bytes: int
    used_bytes: int
    utilization_percent: float
    safe_budget_bytes: int

    @property
    def total_gb(self) -> float:
        return self.total_bytes / (1024**3)

    @property
    def available_gb(self) -> float:
        return self.available_bytes / (1024**3)

    @property
    def safe_budget_gb(self) -> float:
        return self.safe_budget_bytes / (1024**3)


class GpuInfo(BaseModel, frozen=True):
    """GPU hardware, VRAM, and driver acceleration attributes."""

    vendor: GpuVendor = GpuVendor.UNKNOWN
    name: str = "Unknown GPU"
    vram_bytes: int = 0
    driver_version: str | None = None
    cuda_available: bool = False
    rocm_available: bool = False
    metal_available: bool = False
    is_unified_memory: bool = False

    @property
    def vram_gb(self) -> float:
        return self.vram_bytes / (1024**3)


class StorageInfo(BaseModel, frozen=True):
    """Storage space and filesystem specifications."""

    free_bytes: int
    total_bytes: int
    filesystem: str = "Unknown"
    storage_type: StorageType = StorageType.UNKNOWN

    @property
    def free_gb(self) -> float:
        return self.free_bytes / (1024**3)

    @property
    def total_gb(self) -> float:
        return self.total_bytes / (1024**3)


class OsInfo(BaseModel, frozen=True):
    """Operating system and platform attributes."""

    platform_name: str  # e.g., Linux, Darwin, Windows
    release: str
    version: str
    architecture: str
    kernel_version: str | None = None

    @property
    def summary_string(self) -> str:
        return f"{self.platform_name} {self.release} ({self.architecture})"


class RuntimeCapabilities(BaseModel, frozen=True):
    """Installed local LLM runtimes and hardware acceleration stacks."""

    has_ollama: bool = False
    has_llamacpp: bool = False
    has_lmstudio: bool = False
    has_open_webui: bool = False
    has_cuda: bool = False
    has_rocm: bool = False
    has_vulkan: bool = False
    has_metal: bool = False


class HardwareProfile(BaseModel, frozen=True):
    """Normalized snapshot of the machine's hardware environment."""

    cpu: CpuInfo
    memory: MemoryInfo
    gpus: list[GpuInfo] = Field(default_factory=list)
    storage: StorageInfo
    os_info: OsInfo
    runtime: RuntimeCapabilities

    @property
    def primary_gpu(self) -> GpuInfo | None:
        """Return primary GPU with highest VRAM if available."""
        if not self.gpus:
            return None
        return max(self.gpus, key=lambda g: g.vram_bytes)

    @property
    def total_vram_bytes(self) -> int:
        """Total dedicated or unified VRAM across detected GPUs."""
        return sum(g.vram_bytes for g in self.gpus)

    @property
    def total_vram_gb(self) -> float:
        return self.total_vram_bytes / (1024**3)
