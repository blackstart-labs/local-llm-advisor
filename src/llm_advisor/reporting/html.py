"""HTML report generator rendering Jinja2 standalone dashboard."""

from __future__ import annotations

import os
from typing import Optional
from jinja2 import Environment, FileSystemLoader

from llm_advisor.analysis.recommender import RecommendationReport


def generate_html_report(
    report: RecommendationReport,
    output_path: Optional[str] = None,
) -> str:
    """Generate self-contained HTML report file."""
    target_path = output_path if output_path is not None else "report.html"
    abs_target_path = os.path.abspath(target_path)

    templates_dir = os.path.join(os.path.dirname(__file__), "templates")
    env = Environment(loader=FileSystemLoader(templates_dir), autoescape=True)
    template = env.get_template("report.html.j2")

    rendered_html = template.render(report=report)

    with open(abs_target_path, "w", encoding="utf-8") as f:
        f.write(rendered_html)

    return abs_target_path
