"""Tests for ModelRegistry and catalog querying."""

from llm_advisor.models.registry import ModelRegistry, DefaultModelRegistry
from llm_advisor.models.schema import QuantizationLevel


def test_default_model_registry_contains_models() -> None:
    registry: ModelRegistry = DefaultModelRegistry()
    all_models = registry.list_all()

    assert len(all_models) >= 10
    ids = [m.id for m in all_models]
    assert "qwen2.5-7b-instruct" in ids
    assert "llama-3.1-8b-instruct" in ids
    assert "phi-4" in ids


def test_get_model_by_id() -> None:
    registry = DefaultModelRegistry()
    model = registry.get_by_id("qwen2.5-7b-instruct")

    assert model is not None
    assert model.name == "Qwen 2.5 7B Instruct"
    assert model.parameter_count_billions >= 7.0

    quant_q4 = model.get_quantization(QuantizationLevel.Q4_K_M)
    assert quant_q4 is not None
    assert quant_q4.recommended_ram_gb > 0


def test_filter_by_use_case() -> None:
    registry = DefaultModelRegistry()
    coding_models = registry.filter_by_use_case("coding")

    assert len(coding_models) > 0
    for m in coding_models:
        assert "coding" in [u.lower() for u in m.use_cases]


def test_filter_by_max_params() -> None:
    registry = DefaultModelRegistry()
    small_models = registry.filter_by_max_parameters(4.0)

    assert len(small_models) > 0
    for m in small_models:
        assert m.parameter_count_billions <= 4.0
