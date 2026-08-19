"""Scoring engine providing multi-factor deterministic scoring and confidence level."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field

from llm_advisor.analysis.compatibility import CompatibilityLevel, CompatibilityResult
from llm_advisor.hardware.schema import HardwareProfile
from llm_advisor.models.schema import ModelProfile, QualityClass, SpeedClass


class ConfidenceLevel(str, Enum):
    """Confidence level of analysis based on hardware detection completeness."""

    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class ScoreBreakdown(BaseModel, frozen=True):
    """Detailed score component breakdown (out of 100 points)."""

    hardware_fit_score: float = 0.0  # Max 30
    memory_headroom_score: float = 0.0  # Max 20
    expected_speed_score: float = 0.0  # Max 20
    model_quality_score: float = 0.0  # Max 20
    context_support_score: float = 0.0  # Max 10

    @property
    def total_score(self) -> int:
        return int(
            round(
                self.hardware_fit_score
                + self.memory_headroom_score
                + self.expected_speed_score
                + self.model_quality_score
                + self.context_support_score
            )
        )


class ScoreResult(BaseModel, frozen=True):
    """Overall score result with breakdown, confidence, and explainability text."""

    total_score: int
    breakdown: ScoreBreakdown
    confidence: ConfidenceLevel
    why_recommended: list[str] = Field(default_factory=list)
    why_not_recommended: list[str] = Field(default_factory=list)
    bottlenecks: list[str] = Field(default_factory=list)
    upgrade_suggestions: list[str] = Field(default_factory=list)


class ScoringEngine:
    """Computes explainable scores for model-hardware pairings."""

    def score(
        self,
        hardware: HardwareProfile,
        model: ModelProfile,
        compatibility: CompatibilityResult,
    ) -> ScoreResult:
        # 1. Hardware Fit Score (Max 30)
        hw_fit = 0.0
        if compatibility.level == CompatibilityLevel.EXCELLENT:
            hw_fit = 30.0
        elif compatibility.level == CompatibilityLevel.GOOD:
            hw_fit = 25.0
        elif compatibility.level == CompatibilityLevel.POSSIBLE:
            hw_fit = 18.0
        elif compatibility.level == CompatibilityLevel.BORDERLINE:
            hw_fit = 10.0
        else:
            hw_fit = 0.0

        # 2. Memory Headroom Score (Max 20)
        mem_headroom = 0.0
        if compatibility.fits_in_vram:
            mem_headroom = min(20.0, max(5.0, compatibility.vram_headroom_percent * 0.4))
        else:
            mem_headroom = min(20.0, max(0.0, compatibility.ram_headroom_percent * 0.35))

        # 3. Expected Speed Score (Max 20)
        speed = 0.0
        if compatibility.fits_in_vram:
            if model.speed_class == SpeedClass.BLAZING:
                speed = 20.0
            elif model.speed_class == SpeedClass.FAST:
                speed = 18.0
            elif model.speed_class == SpeedClass.MODERATE:
                speed = 15.0
            elif model.speed_class == SpeedClass.SLOW:
                speed = 10.0
            else:
                speed = 5.0
        else:
            # CPU inference penalty
            if model.parameter_count_billions <= 3.5:
                speed = 14.0
            elif model.parameter_count_billions <= 9.0:
                speed = 9.0
            else:
                speed = 4.0

        # 4. Model Quality Score (Max 20)
        quality = 0.0
        if model.quality_class == QualityClass.FRONTIER:
            quality = 20.0
        elif model.quality_class == QualityClass.HIGH:
            quality = 17.0
        elif model.quality_class == QualityClass.MODERATE:
            quality = 13.0
        else:
            quality = 9.0

        # 5. Context Support Score (Max 10)
        context = 0.0
        if compatibility.context_length_evaluated >= 32768:
            context = 10.0
        elif compatibility.context_length_evaluated >= 16384:
            context = 8.0
        elif compatibility.context_length_evaluated >= 8192:
            context = 6.0
        else:
            context = 4.0

        breakdown = ScoreBreakdown(
            hardware_fit_score=round(hw_fit, 1),
            memory_headroom_score=round(mem_headroom, 1),
            expected_speed_score=round(speed, 1),
            model_quality_score=round(quality, 1),
            context_support_score=round(context, 1),
        )

        total_score = breakdown.total_score

        # Determine confidence level
        has_gpu = len(hardware.gpus) > 0
        if hardware.memory.total_bytes > 0 and hardware.cpu.physical_cores > 0 and has_gpu:
            confidence = ConfidenceLevel.HIGH
        elif hardware.memory.total_bytes > 0 and hardware.cpu.physical_cores > 0:
            confidence = ConfidenceLevel.MEDIUM
        else:
            confidence = ConfidenceLevel.LOW

        # Explainability text generation
        why_rec: list[str] = []
        why_not_rec: list[str] = []
        bottlenecks: list[str] = []
        upgrades: list[str] = []

        if compatibility.level in (CompatibilityLevel.EXCELLENT, CompatibilityLevel.GOOD):
            why_rec.append(
                f"Comfortably fits within available memory ({compatibility.required_memory_gb:.1f} GB required)"
            )
            if compatibility.fits_in_vram:
                why_rec.append("Full GPU acceleration supported with high token output speed")
            else:
                why_rec.append("Practical CPU/RAM inference supported without OS thrashing")
            if model.coding_strength >= 8.0:
                why_rec.append("Strong coding capabilities for technical tasks")
            if model.reasoning_strength >= 8.0:
                why_rec.append("High logic and step-by-step reasoning quality")
        else:
            why_not_rec.append(
                f"Heavy resource requirements ({compatibility.required_memory_gb:.1f} GB required)"
            )

        if not has_gpu:
            bottlenecks.append(
                "No dedicated GPU acceleration detected; inference will run entirely on CPU"
            )
            upgrades.append(
                "Adding a dedicated NVIDIA/Apple/AMD GPU with 8GB+ VRAM will boost speeds 5x–10x"
            )
        elif not compatibility.fits_in_vram and hardware.total_vram_gb > 0:
            bottlenecks.append(
                f"VRAM ({hardware.total_vram_gb:.1f} GB) is smaller than model requirements"
            )
            upgrades.append(
                f"Upgrading to a GPU with at least {compatibility.required_memory_gb:.0f}GB VRAM would allow full GPU offloading"
            )

        if hardware.memory.safe_budget_gb < 8.0:
            bottlenecks.append("Available system RAM is limited (< 8GB safe budget)")
            upgrades.append("Upgrading system RAM to 16GB or 32GB unlocks larger 7B–14B LLMs")

        return ScoreResult(
            total_score=total_score,
            breakdown=breakdown,
            confidence=confidence,
            why_recommended=why_rec,
            why_not_recommended=why_not_rec,
            bottlenecks=bottlenecks,
            upgrade_suggestions=upgrades,
        )
