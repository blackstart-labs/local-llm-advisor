# Scoring & Compatibility Methodology

The Local LLM Hardware Advisor computes a deterministic score (0–100) for model-hardware pairings across five distinct factors:

$$\text{Total Score} = \text{HardwareFit (30)} + \text{MemoryHeadroom (20)} + \text{Speed (20)} + \text{ModelQuality (20)} + \text{ContextSupport (10)}$$

## 1. Hardware Fit (30 Points Max)
- **🟢 Excellent (30 pts):** Model fits completely in dedicated VRAM (or unified memory) with $\ge 25\%$ VRAM headroom.
- **🟢 Good (25 pts):** Model fits in VRAM with moderate headroom or in safe system RAM with $\ge 20\%$ RAM headroom.
- **🟡 Possible (18 pts):** Fits in safe system RAM with tight headroom ($0\% - 20\%$).
- **🟠 Borderline (10 pts):** Exceeds safe budget but within physical system RAM limit.
- **🔴 Not Recommended (0 pts):** Exceeds total physical RAM or disk storage space.

## 2. Memory Headroom (20 Points Max)
Calculated dynamically based on VRAM or safe RAM headroom:
$$\text{VRAM Headroom Score} = \min(20, \max(5, \text{Headroom\%} \times 0.4))$$

Safe RAM budget formula prevents OS thrashing:
$$\text{Safe RAM Budget} = \text{Available RAM} - \max(2.0 \text{ GB}, 0.15 \times \text{Total RAM})$$

## 3. Expected Speed (20 Points Max)
Evaluates latency tier based on GPU compute vs CPU core offloading and model parameter count.

## 4. Model Quality (20 Points Max)
Weighted by model benchmark intelligence tier (Frontier, High Quality, Moderate, Entry).

## 5. Context Support (10 Points Max)
Evaluates KV cache memory overhead at target context window sizes (8K, 16K, 32K, 128K).
