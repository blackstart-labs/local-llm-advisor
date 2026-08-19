"""Tests for recommendation engine ranking and purpose-specific categories."""

from llm_advisor.analysis.recommender import RecommendationEngine
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
from llm_advisor.models.registry import DefaultModelRegistry


def test_recommendation_engine_ranks_models() -> None:
    hw = HardwareProfile(
        cpu=CpuInfo(brand="Intel", model="Core i7", physical_cores=8, logical_cores=16),
        memory=MemoryInfo(
            total_bytes=16 * (1024**3),
            available_bytes=12 * (1024**3),
            used_bytes=4 * (1024**3),
            utilization_percent=25.0,
            safe_budget_bytes=9 * (1024**3),
        ),
        gpus=[
            GpuInfo(
                vendor=GpuVendor.NVIDIA,
                name="NVIDIA RTX 3060",
                vram_bytes=12 * (1024**3),
                cuda_available=True,
            )
        ],
        storage=StorageInfo(free_bytes=100 * (1024**3), total_bytes=500 * (1024**3)),
        os_info=OsInfo(platform_name="Linux", release="6.5", version="1", architecture="x86_64"),
        runtime=RuntimeCapabilities(has_ollama=True),
    )

    registry = DefaultModelRegistry()
    recommender = RecommendationEngine(registry=registry)

    report = recommender.recommend(hw)

    assert len(report.top_recommendations) > 0
    # Top recommendation should fit nicely on 12GB VRAM
    top = report.top_recommendations[0]
    assert top.score >= 50
    assert top.recommended_quantization is not None


def test_recommendation_engine_purpose_coding() -> None:
    hw = HardwareProfile(
        cpu=CpuInfo(brand="Intel", model="Core i5", physical_cores=4, logical_cores=8),
        memory=MemoryInfo(
            total_bytes=16 * (1024**3),
            available_bytes=10 * (1024**3),
            used_bytes=6 * (1024**3),
            utilization_percent=37.5,
            safe_budget_bytes=7 * (1024**3),
        ),
        gpus=[],
        storage=StorageInfo(free_bytes=50 * (1024**3), total_bytes=500 * (1024**3)),
        os_info=OsInfo(platform_name="Linux", release="6.5", version="1", architecture="x86_64"),
        runtime=RuntimeCapabilities(has_ollama=True),
    )

    registry = DefaultModelRegistry()
    recommender = RecommendationEngine(registry=registry)

    report = recommender.recommend(hw, purpose="coding")

    assert len(report.top_recommendations) > 0
    for rec in report.top_recommendations:
        assert rec.model.coding_strength >= 5.0
