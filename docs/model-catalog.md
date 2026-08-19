# Model Catalog & Extensibility

## Overview

The model catalog (`src/llm_advisor/models/catalog.py`) defines open-weight LLM profiles and quantization requirements.

## Adding a New Model

To add a new model family or size to the system:

1. Open `src/llm_advisor/models/catalog.py`.
2. Append a new `ModelProfile` instance to `get_default_catalog()`:

```python
ModelProfile(
    id="my-custom-model-7b",
    name="My Custom Model 7B",
    family="CustomFamily",
    parameter_count_billions=7.2,
    context_length=32768,
    supported_quantizations=[
        QuantizationProfile(
            level=QuantizationLevel.Q4_K_M,
            bits_per_weight=4.5,
            file_size_gb=4.5,
            recommended_ram_gb=7.0,
            recommended_vram_gb=5.8,
        )
    ],
    use_cases=["coding", "general_chat"],
    pros=["Fast inference", "Low VRAM requirement"],
    cons=["Smaller knowledge base"],
)
```

No changes to scoring rules, compatibility algorithms, or CLI renderers are needed!
