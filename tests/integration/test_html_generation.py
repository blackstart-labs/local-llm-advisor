"""Integration test for full end-to-end HTML report generation."""

import os
from tempfile import NamedTemporaryFile
from llm_advisor.hardware.detector import SystemHardwareDetector
from llm_advisor.analysis.recommender import RecommendationEngine
from llm_advisor.reporting.html import generate_html_report


def test_full_html_report_pipeline() -> None:
    detector = SystemHardwareDetector()
    hardware = detector.detect()

    recommender = RecommendationEngine()
    report = recommender.recommend(hardware)

    with NamedTemporaryFile(suffix=".html", mode="w+", delete=False) as tmp:
        out_path = tmp.name

    generated_file = generate_html_report(report, output_path=out_path)

    assert os.path.exists(generated_file)
    assert os.path.getsize(generated_file) > 1000

    with open(generated_file, encoding="utf-8") as f:
        content = f.read()

    assert "<!DOCTYPE html>" in content
    assert "Local LLM Hardware Advisor" in content
    assert report.overall_rating_badge in content
