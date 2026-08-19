# Architecture Documentation

## High-Level Pipeline

```
CLI (commands.py)
   │
   ▼
SystemHardwareDetector ──► HardwareProfile
   │                           │
   ▼                           ▼
ModelRegistry ─────────► CompatibilityEngine ──► CompatibilityResult
                               │
                               ▼
                        ScoringEngine ─────────► ScoreResult
                               │
                               ▼
                     RecommendationEngine ──────► RecommendationReport
                                                     │
                             ┌───────────────────────┴───────────────────────┐
                             ▼                                               ▼
                     TerminalRenderer                                   HtmlRenderer
                             │                                               │
                             ▼                                               ▼
                      stdout (Rich UI)                               report.html (Dashboard)
```

## Architectural Principles

1. **Clean Separation of Concerns**: Hardware detection, model metadata, compatibility rules, scoring, and UI rendering live in completely decoupled packages.
2. **Immutable Domain Models**: All core profiles (`HardwareProfile`, `ModelProfile`, `CompatibilityResult`, `ScoreResult`) use frozen Pydantic v2 schemas.
3. **Injectable Dependencies**: Hardware detectors and model registries follow abstract interfaces (`HardwareDetector`, `ModelRegistry`) for zero-hardware unit testing.
4. **Data-Driven Catalog Extensibility**: Adding a new open-weight LLM requires adding a record in `src/llm_advisor/models/catalog.py` without modifying scoring or recommendation logic.
5. **Zero Cloud API Requirement**: Analysis runs 100% locally and offline without external API calls or telemetry.
