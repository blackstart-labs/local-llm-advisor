"""Tests for scoring engine and explainable score breakdowns."""

from llm_advisor.analysis.compatibility import CompatibilityEngine
from llm_advisor.analysis.scoring import ConfidenceLevel, ScoringEngine
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
from llm_advisor.models.schema import ModelProfile, QuantizationLevel, QuantizationProfile


def _make_gpu_hardware() -> HardwareProfile:
    return HardwareProfile(
        cpu=CpuInfo(brand="AMD", model="Ryzen 9", physical_cores=12, logical_cores=24),
        memory=MemoryInfo(
            total_bytes=32 * (1024**3),
            available_bytes=24 * (1024**3),
            used_bytes=8 * (1024**3),
            utilization_percent=25.0,
            safe_budget_bytes=20 * (1024**3),
        ),
        gpus=[
            GpuInfo(
                vendor=GpuVendor.NVIDIA,
                name="NVIDIA RTX 4080",
                vram_bytes=16 * (1024**3),
                cuda_available=True,
            )
        ],
        storage=StorageInfo(free_bytes=200 * (1024**3), total_bytes=1000 * (1024**3)),
        os_info=OsInfo(platform_name="Linux", release="6.5", version="1", architecture="x86_64"),
        runtime=RuntimeCapabilities(has_ollama=True, has_cuda=True),
    )


def test_scoring_engine_breakdown() -> None:
    hw = _make_gpu_hardware()
    compat_engine = CompatibilityEngine()
    scoring_engine = ScoringEngine()

    model = ModelProfile(
        id="qwen2.5-7b-instruct",
        name="Qwen 2.5 7B",
        family="Qwen",
        parameter_count_billions=7.6,
        context_length=32768,
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

    compat_result = compat_engine.evaluate(hw, model, QuantizationLevel.Q4_K_M)
    score_result = scoring_engine.score(hw, model, compat_result)

    assert 0 <= score_result.total_score <= 100
    assert score_result.confidence == ConfidenceLevel.HIGH
    assert score_result.breakdown.hardware_fit_score > 0
    assert score_result.breakdown.memory_headroom_score > 0
    assert len(score_result.why_recommended) > 0
