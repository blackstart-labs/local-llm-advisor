"""Model domain schemas, quantization types, and model metadata definitions."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class QuantizationLevel(str, Enum):
    """Standard LLM quantization precision levels."""

    FP16 = "FP16"
    BF16 = "BF16"
    INT8 = "INT8"
    Q8_0 = "Q8_0"
    Q6_K = "Q6_K"
    Q5_K_M = "Q5_K_M"
    Q4_K_M = "Q4_K_M"
    Q3_K_M = "Q3_K_M"
    Q2_K = "Q2_K"


class SpeedClass(str, Enum):
    """Performance tier classification."""

    BLAZING = "Blazing Fast"
    FAST = "Fast"
    MODERATE = "Moderate"
    SLOW = "Slow"
    VERY_SLOW = "Very Slow"


class QualityClass(str, Enum):
    """Model quality tier classification."""

    FRONTIER = "Frontier / State-of-the-Art"
    HIGH = "High Quality"
    MODERATE = "Moderate Quality"
    ENTRY = "Entry Level"


class QuantizationProfile(BaseModel, frozen=True):
    """Metadata and resource requirements for a specific quantization level."""

    level: QuantizationLevel
    bits_per_weight: float
    file_size_gb: float
    recommended_ram_gb: float
    recommended_vram_gb: float
    quality_retention_percent: float = 95.0


class ModelProfile(BaseModel, frozen=True):
    """Domain model capturing LLM metadata, capabilities, and resource profiles."""

    id: str
    name: str
    family: str
    parameter_count_billions: float
    architecture: str = "Dense Transformer"
    context_length: int = 8192
    supported_quantizations: list[QuantizationProfile] = Field(default_factory=list)
    default_quantization: QuantizationLevel = QuantizationLevel.Q4_K_M

    # Capability Strengths (0.0 to 10.0 scale)
    reasoning_strength: float = 5.0
    coding_strength: float = 5.0
    general_chat_strength: float = 5.0
    multilingual_strength: float = 5.0
    instruction_following: float = 5.0

    speed_class: SpeedClass = SpeedClass.MODERATE
    quality_class: QualityClass = QualityClass.HIGH
    use_cases: list[str] = Field(default_factory=list)
    pros: list[str] = Field(default_factory=list)
    cons: list[str] = Field(default_factory=list)
    runtime_support: list[str] = Field(default_factory=lambda: ["ollama", "llamacpp", "lmstudio"])
    license: str = "Apache-2.0"
    notes: str | None = None

    def get_quantization(self, level: QuantizationLevel) -> QuantizationProfile | None:
        """Find quantization profile for a given precision level."""
        for q in self.supported_quantizations:
            if q.level == level:
                return q
        return None
