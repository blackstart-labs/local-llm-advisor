"""Tests for Rich terminal renderer."""

from io import StringIO

from rich.console import Console

from llm_advisor.analysis.recommender import RecommendationEngine, RecommendationReport
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
from llm_advisor.reporting.terminal import render_terminal_report


def test_render_terminal_report_output() -> None:
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

    recommender = RecommendationEngine()
    report: RecommendationReport = recommender.recommend(hw)

    buffer = StringIO()
    console = Console(file=buffer, force_terminal=True, width=100)

    render_terminal_report(report, console=console)
    output = buffer.getvalue()

    assert "Local LLM Hardware Advisor" in output
    assert "Hardware Assessment" in output
    assert "Top Recommendations" in output
