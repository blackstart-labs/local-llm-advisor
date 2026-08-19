"""Compatibility classification engine for hardware profiles vs LLMs."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field

from llm_advisor.analysis.requirements import calculate_total_memory_required_gb
from llm_advisor.hardware.schema import HardwareProfile
from llm_advisor.models.schema import ModelProfile, QuantizationLevel


class CompatibilityLevel(str, Enum):
    """Compatibility classification level."""

    EXCELLENT = "Excellent"
    GOOD = "Good"
    POSSIBLE = "Possible"
    BORDERLINE = "Borderline"
    NOT_RECOMMENDED = "Not Recommended"

    @property
    def badge_emoji(self) -> str:
        if self == CompatibilityLevel.EXCELLENT or self == CompatibilityLevel.GOOD:
            return "🟢"
        elif self == CompatibilityLevel.POSSIBLE:
            return "🟡"
        elif self == CompatibilityLevel.BORDERLINE:
            return "🟠"
        else:
            return "🔴"


class CompatibilityResult(BaseModel, frozen=True):
    """Result of evaluating a specific model and quantization on user hardware."""

    model_id: str
    quantization_level: QuantizationLevel
    level: CompatibilityLevel
    required_memory_gb: float
    kv_cache_gb: float
    fits_in_vram: bool
    fits_in_ram: bool
    vram_headroom_percent: float = 0.0
    ram_headroom_percent: float = 0.0
    context_length_evaluated: int
    reasons: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class CompatibilityEngine:
    """Evaluates compatibility between hardware profile and LLM quantizations."""

    def evaluate(
        self,
        hardware: HardwareProfile,
        model: ModelProfile,
        quantization_level: QuantizationLevel,
        context_length: int | None = None,
    ) -> CompatibilityResult:
        quant = model.get_quantization(quantization_level)
        if not quant:
            # Fallback to default quantization if requested precision not found
            quant = model.get_quantization(model.default_quantization)
            if not quant:
                # Emergency fallback
                file_gb = model.parameter_count_billions * 0.6
                rec_ram = file_gb * 1.4
                rec_vram = file_gb * 1.2
            else:
                file_gb = quant.file_size_gb
                rec_ram = quant.recommended_ram_gb
                rec_vram = quant.recommended_vram_gb
        else:
            file_gb = quant.file_size_gb
            rec_ram = quant.recommended_ram_gb
            rec_vram = quant.recommended_vram_gb

        eval_context = (
            context_length if context_length is not None else min(8192, model.context_length)
        )
        req_memory_gb = calculate_total_memory_required_gb(
            file_size_gb=file_gb,
            param_count_billions=model.parameter_count_billions,
            context_length=eval_context,
            runtime_overhead_gb=0.5,
        )

        vram_gb = hardware.total_vram_gb
        safe_ram_gb = hardware.memory.safe_budget_gb
        total_ram_gb = hardware.memory.total_gb

        fits_in_vram = vram_gb > 0 and (vram_gb >= req_memory_gb or vram_gb >= rec_vram)
        fits_in_ram = safe_ram_gb >= req_memory_gb or safe_ram_gb >= rec_ram

        vram_headroom = ((vram_gb - req_memory_gb) / vram_gb * 100.0) if vram_gb > 0 else 0.0
        ram_headroom = (
            ((safe_ram_gb - req_memory_gb) / safe_ram_gb * 100.0) if safe_ram_gb > 0 else 0.0
        )

        reasons: list[str] = []
        warnings: list[str] = []

        # Determine compatibility tier
        if fits_in_vram and vram_headroom >= 25.0:
            level = CompatibilityLevel.EXCELLENT
            reasons.append(
                f"Fits comfortably in GPU VRAM ({vram_gb:.1f} GB available, {vram_headroom:.0f}% headroom)"
            )
        elif fits_in_vram:
            level = CompatibilityLevel.GOOD
            reasons.append(f"Fits in GPU VRAM with moderate headroom ({vram_headroom:.0f}%)")
        elif fits_in_ram and ram_headroom >= 20.0:
            level = CompatibilityLevel.GOOD
            reasons.append(
                f"Fits comfortably in safe system RAM ({safe_ram_gb:.1f} GB safe budget)"
            )
            if vram_gb > 0:
                warnings.append(
                    "VRAM insufficient for full GPU offload; will run via CPU/RAM offloading"
                )
            else:
                reasons.append("Running on CPU + RAM")
        elif fits_in_ram:
            level = CompatibilityLevel.POSSIBLE
            reasons.append(f"Fits in system RAM with tight headroom ({ram_headroom:.0f}%)")
            warnings.append("Close to safe RAM limit; close heavy applications before running")
        elif total_ram_gb >= req_memory_gb:
            level = CompatibilityLevel.BORDERLINE
            reasons.append("Exceeds safe RAM budget but within total physical RAM")
            warnings.append("High risk of system slowdown or OS memory pressure")
        else:
            level = CompatibilityLevel.NOT_RECOMMENDED
            reasons.append(
                f"Required memory ({req_memory_gb:.1f} GB) exceeds available RAM ({total_ram_gb:.1f} GB)"
            )

        # Disk space check
        if hardware.storage.free_gb < file_gb + 2.0:
            if level != CompatibilityLevel.NOT_RECOMMENDED:
                level = CompatibilityLevel.BORDERLINE
            warnings.append(
                f"Disk space low ({hardware.storage.free_gb:.1f} GB free, model weights need {file_gb:.1f} GB)"
            )

        return CompatibilityResult(
            model_id=model.id,
            quantization_level=quantization_level,
            level=level,
            required_memory_gb=req_memory_gb,
            kv_cache_gb=round((eval_context * model.parameter_count_billions) / 500000.0, 2),
            fits_in_vram=fits_in_vram,
            fits_in_ram=fits_in_ram,
            vram_headroom_percent=round(vram_headroom, 1),
            ram_headroom_percent=round(ram_headroom, 1),
            context_length_evaluated=eval_context,
            reasons=reasons,
            warnings=warnings,
        )
