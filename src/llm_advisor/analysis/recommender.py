"""Recommendation engine producing purpose-focused rankings and recommendations."""

from __future__ import annotations

from pydantic import BaseModel, Field

from llm_advisor.analysis.compatibility import (
    CompatibilityEngine,
    CompatibilityLevel,
    CompatibilityResult,
)
from llm_advisor.analysis.scoring import ConfidenceLevel, ScoreResult, ScoringEngine
from llm_advisor.hardware.schema import HardwareProfile
from llm_advisor.models.registry import DefaultModelRegistry, ModelRegistry
from llm_advisor.models.schema import ModelProfile, QuantizationLevel


class Recommendation(BaseModel, frozen=True):
    """Detailed recommendation record for a specific model."""

    rank: int
    model: ModelProfile
    recommended_quantization: QuantizationLevel
    compatibility: CompatibilityResult
    score: int
    score_result: ScoreResult
    best_for: list[str]
    why_recommended: list[str]
    pros: list[str]
    cons: list[str]
    suggested_runtime: str
    suggested_context_range: str
    alternative_model_id: str | None = None


class RecommendationReport(BaseModel, frozen=True):
    """Full recommendation report containing overall and category rankings."""

    hardware: HardwareProfile
    overall_rating_badge: str
    overall_rating_text: str
    primary_bottleneck: str
    recommended_model_size_class: str
    top_recommendations: list[Recommendation] = Field(default_factory=list)
    by_purpose: dict[str, list[Recommendation]] = Field(default_factory=dict)
    confidence: ConfidenceLevel = ConfidenceLevel.HIGH


class RecommendationEngine:
    """Engine executing compatibility analysis, scoring, and recommendation ranking."""

    def __init__(
        self,
        registry: ModelRegistry | None = None,
        compatibility_engine: CompatibilityEngine | None = None,
        scoring_engine: ScoringEngine | None = None,
    ) -> None:
        self.registry = registry if registry is not None else DefaultModelRegistry()
        self.compat_engine = (
            compatibility_engine if compatibility_engine is not None else CompatibilityEngine()
        )
        self.scoring_engine = scoring_engine if scoring_engine is not None else ScoringEngine()

    def recommend(
        self,
        hardware: HardwareProfile,
        purpose: str | None = None,
        max_ram_gb: float | None = None,
    ) -> RecommendationReport:
        all_models = self.registry.list_all()
        recommendations: list[Recommendation] = []

        for model in all_models:
            # Skip if user requested lower max RAM limit than default model req
            if max_ram_gb and model.parameter_count_billions > max_ram_gb * 1.5:
                continue

            best_rec: Recommendation | None = None
            best_score = -1

            for quant in model.supported_quantizations:
                compat_res = self.compat_engine.evaluate(hardware, model, quant.level)
                score_res = self.scoring_engine.score(hardware, model, compat_res)

                if score_res.total_score > best_score:
                    best_score = score_res.total_score

                    # Suggest optimal runtime
                    runtime_str = "Ollama / llama.cpp"
                    if (
                        hardware.os_info.platform_name == "Darwin"
                        and "arm" in hardware.os_info.architecture.lower()
                    ):
                        runtime_str = "Ollama / LM Studio (Apple Metal)"
                    elif len(hardware.gpus) > 0 and hardware.gpus[0].cuda_available:
                        runtime_str = "Ollama / llama.cpp (CUDA acceleration)"

                    context_range = f"8K – {compat_res.context_length_evaluated // 1024}K tokens"

                    best_rec = Recommendation(
                        rank=0,
                        model=model,
                        recommended_quantization=quant.level,
                        compatibility=compat_res,
                        score=score_res.total_score,
                        score_result=score_res,
                        best_for=model.use_cases[:3],
                        why_recommended=score_res.why_recommended
                        or [f"Good fit for {model.family} model family"],
                        pros=model.pros,
                        cons=model.cons,
                        suggested_runtime=runtime_str,
                        suggested_context_range=context_range,
                    )

            if best_rec and best_rec.compatibility.level != CompatibilityLevel.NOT_RECOMMENDED:
                recommendations.append(best_rec)

        # Sort recommendations descending by score
        recommendations.sort(key=lambda r: r.score, reverse=True)

        # Assign ranks
        ranked_recs: list[Recommendation] = []
        for idx, rec in enumerate(recommendations, 1):
            alt_id = recommendations[idx].model.id if idx < len(recommendations) else None
            updated_rec = Recommendation(
                rank=idx,
                model=rec.model,
                recommended_quantization=rec.recommended_quantization,
                compatibility=rec.compatibility,
                score=rec.score,
                score_result=rec.score_result,
                best_for=rec.best_for,
                why_recommended=rec.why_recommended,
                pros=rec.pros,
                cons=rec.cons,
                suggested_runtime=rec.suggested_runtime,
                suggested_context_range=rec.suggested_context_range,
                alternative_model_id=alt_id,
            )
            ranked_recs.append(updated_rec)

        # Filter by specific purpose if requested
        top_list = ranked_recs
        if purpose:
            target_p = purpose.lower().strip()
            top_list = [
                r for r in ranked_recs if target_p in [u.lower() for u in r.model.use_cases]
            ] or ranked_recs

        # Categorize by purpose
        by_purpose: dict[str, list[Recommendation]] = {
            "General Assistant": [
                r for r in ranked_recs if "general_chat" in [u.lower() for u in r.model.use_cases]
            ][:3],
            "Coding & Development": [
                r for r in ranked_recs if "coding" in [u.lower() for u in r.model.use_cases]
            ][:3],
            "Reasoning & Logic": [
                r for r in ranked_recs if "reasoning" in [u.lower() for u in r.model.use_cases]
            ][:3],
            "Local RAG": [
                r for r in ranked_recs if "rag" in [u.lower() for u in r.model.use_cases]
            ][:3],
            "Lightweight / Fast": [
                r for r in ranked_recs if "lightweight" in [u.lower() for u in r.model.use_cases]
            ][:3],
        }

        # Overall machine capability rating
        safe_ram = hardware.memory.safe_budget_gb
        vram = hardware.total_vram_gb

        if vram >= 16.0 or safe_ram >= 32.0:
            badge = "🟢 High-Performance Local Workstation"
            rating_text = "Capable of running 14B–32B Q4/Q8 models smoothly."
            size_class = "14B – 32B quantized models"
            bottleneck = "Storage speed / VRAM capacity for 70B models"
        elif vram >= 8.0 or safe_ram >= 12.0:
            badge = "🟢 Good Mid-Range Local Inference"
            rating_text = "Comfortably runs 7B–9B Q4 models at fast speeds."
            size_class = "7B – 9B quantized models"
            bottleneck = "VRAM capacity (8GB limits 14B+ models)"
        elif safe_ram >= 6.0:
            badge = "🟡 Entry-Level Local Inference"
            rating_text = "Best suited for 1B–4B models or heavily quantized 7B."
            size_class = "1B – 4B quantized models"
            bottleneck = "System RAM safe budget / No dedicated GPU"
        else:
            badge = "🟠 Ultra-Lightweight Inference"
            rating_text = "Limited to tiny 1B–2B models under high memory pressure."
            size_class = "1B – 2B micro models"
            bottleneck = "Low system RAM (< 6GB available)"

        confidence = ConfidenceLevel.HIGH if len(hardware.gpus) > 0 else ConfidenceLevel.MEDIUM

        return RecommendationReport(
            hardware=hardware,
            overall_rating_badge=badge,
            overall_rating_text=rating_text,
            primary_bottleneck=bottleneck,
            recommended_model_size_class=size_class,
            top_recommendations=top_list[:5],
            by_purpose=by_purpose,
            confidence=confidence,
        )
