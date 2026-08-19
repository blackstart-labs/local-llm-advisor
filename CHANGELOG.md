# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-08-20

### Added
- Initial production release of Local LLM Hardware Advisor.
- Cross-platform hardware detection layer (CPU, RAM, GPU/VRAM, Storage, OS, local runtimes).
- Safe memory budget calculation formula avoiding OS thrashing.
- Model catalog covering Qwen 2.5, Llama 3.1/3.2, Gemma 2, DeepSeek R1 distillations, Phi-4, Mistral.
- Compatibility & Memory Overhead Engine factoring weights, KV cache context overhead, and runtime reserve.
- Multi-factor explainable scoring engine (0–100 scale) with explicit breakdowns and confidence levels.
- Rich terminal UI renderer with panels, tables, trees, and semantic color palette.
- Self-contained Jinja2 HTML report generator with dark glassmorphism dashboard UI design system.
- Typer CLI commands (`scan`, `recommend`, `models`, `model`, `report`).
- Full unit and integration test suite with high coverage and GitHub Actions CI.
