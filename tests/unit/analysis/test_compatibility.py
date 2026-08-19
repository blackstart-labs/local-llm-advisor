"""Tests for compatibility classification engine."""

from llm_advisor.analysis.compatibility import (
    CompatibilityEngine,
    CompatibilityLevel,
)
from llm_advisor.hardware.schema import (
    CpuInfo,
    GpuInfo,
    GpuVendor,
    HardwareProfile,
    MemoryInfo,
    OsInfo,
    RuntimeCapabilities,
    StorageInfo,
)
from llm_advisor.models.schema import (
    ModelProfile,
    QuantizationLevel,
    QuantizationProfile,
)


def _make_hardware_profile(ram_gb: float, vram_gb: float = 0.0) -> HardwareProfile:
    total_bytes = int(ram_gb * (1024**3))
    available_bytes = int((ram_gb - 2.0) * (1024**3))
    safe_budget_bytes = int((ram_gb - 4.0) * (1024**3))

    gpus = []
    if vram_gb > 0:
        gpus.append(
            GpuInfo(
                vendor=GpuVendor.NVIDIA,
                name="NVIDIA GPU",
                vram_bytes=int(vram_gb * (1024**3)),
                cuda_available=True,
            )
        )

    return HardwareProfile(
        cpu=CpuInfo(brand="Intel", model="Core i7", physical_cores=8, logical_cores=16),
        memory=MemoryInfo(
            total_bytes=total_bytes,
            available_bytes=available_bytes,
            used_bytes=total_bytes - available_bytes,
            utilization_percent=20.0,
            safe_budget_bytes=safe_budget_bytes,
        ),
        gpus=gpus,
        storage=StorageInfo(free_bytes=100 * (1024**3), total_bytes=500 * (1024**3)),
        os_info=OsInfo(platform_name="Linux", release="6.5", version="1", architecture="x86_64"),
        runtime=RuntimeCapabilities(has_ollama=True),
    )


def test_compatibility_excellent_on_gpu() -> None:
    # 64 GB RAM, 24 GB VRAM GPU vs 4.7 GB Q4 model
    hw = _make_hardware_profile(ram_gb=64.0, vram_gb=24.0)
    engine = CompatibilityEngine()

    model = ModelProfile(
        id="qwen2.5-7b-instruct",
        name="Qwen 2.5 7B",
        family="Qwen",
        parameter_count_billions=7.6,
        context_length=8192,
        supported_quantizations=[
            QuantizationProfile(
                level=QuantizationLevel.Q4_K_M,
                bits_per_weight=4.5,
                file_size_gb=4.7,
                recommended_ram_gb=7.0,
                recommended_vram_gb=5.8,
            )
        ],
    )

    res = engine.evaluate(hw, model, QuantizationLevel.Q4_K_M, context_length=8192)
    assert res.level == CompatibilityLevel.EXCELLENT
    assert res.fits_in_vram is True


test_compatibility_excellent_on_gpu()


def test_compatibility_not_recommended_insufficient_ram() -> None:
    # 8 GB RAM, no GPU vs 42 GB 70B model
    hw = _make_hardware_profile(ram_gb=8.0, vram_gb=0.0)
    engine = CompatibilityEngine()

    model = ModelProfile(
        id="llama-3.1-70b-instruct",
        name="Llama 70B",
        family="Llama",
        parameter_count_billions=70.0,
        context_length=8192,
        supported_quantizations=[
            QuantizationProfile(
                level=QuantizationLevel.Q4_K_M,
                bits_per_weight=4.5,
                file_size_gb=42.5,
                recommended_ram_gb=50.0,
                recommended_vram_gb=46.0,
            )
        ],
    )

    res = engine.evaluate(hw, model, QuantizationLevel.Q4_K_M, context_length=8192)
    assert res.level == CompatibilityLevel.NOT_RECOMMENDED
