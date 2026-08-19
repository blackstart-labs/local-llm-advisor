"""Integration test verifying end-to-end recommendation pipeline on deterministic fixtures."""

import json
import os
from llm_advisor.hardware.schema import HardwareProfile
from llm_advisor.analysis.recommender import RecommendationEngine


def _load_fixture(filename: str) -> HardwareProfile:
    dir_path = os.path.dirname(os.path.dirname(__file__))
    fixture_path = os.path.join(dir_path, "fixtures", filename)
    with open(fixture_path, encoding="utf-8") as f:
        data = json.load(f)
    return HardwareProfile.model_validate(data)


def test_low_end_machine_recommendations() -> None:
    hw = _load_fixture("low_end_machine.json")
    recommender = RecommendationEngine()
    report = recommender.recommend(hw)

    assert len(report.top_recommendations) > 0
    # Top recommendation for low end machine should be lightweight
    top = report.top_recommendations[0]
    assert top.model.parameter_count_billions <= 4.0


def test_high_end_machine_recommendations() -> None:
    hw = _load_fixture("high_end_machine.json")
    recommender = RecommendationEngine()
    report = recommender.recommend(hw)

    assert len(report.top_recommendations) > 0
    top = report.top_recommendations[0]
    assert top.score >= 80
