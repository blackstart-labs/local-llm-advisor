"""Local LLM runtime and driver availability detection."""

from __future__ import annotations

import shutil
import subprocess

from llm_advisor.hardware.schema import RuntimeCapabilities


def _is_executable_in_path(cmd: str) -> bool:
    """Check if binary executable exists in PATH."""
    return shutil.which(cmd) is not None


def detect_runtime() -> RuntimeCapabilities:
    """Detect local runtime installations and acceleration support."""
    has_ollama = _is_executable_in_path("ollama")
    has_llamacpp = _is_executable_in_path("llama-cli") or _is_executable_in_path("main")
    has_lmstudio = _is_executable_in_path("lmstudio") or _is_executable_in_path("lms")
    has_open_webui = _is_executable_in_path("open-webui")

    has_cuda = _is_executable_in_path("nvcc") or _is_executable_in_path("nvidia-smi")
    has_rocm = _is_executable_in_path("rocm-smi")
    has_vulkan = _is_executable_in_path("vulkaninfo")
    has_metal = False

    try:
        res = subprocess.run(
            ["sysctl", "-n", "machdep.cpu.brand_string"], capture_output=True, text=True, timeout=1
        )
        if res.returncode == 0 and (
            "Apple" in res.stdout or "M1" in res.stdout or "M2" in res.stdout or "M3" in res.stdout
        ):
            has_metal = True
    except Exception:
        pass

    return RuntimeCapabilities(
        has_ollama=has_ollama,
        has_llamacpp=has_llamacpp,
        has_lmstudio=has_lmstudio,
        has_open_webui=has_open_webui,
        has_cuda=has_cuda,
        has_rocm=has_rocm,
        has_vulkan=has_vulkan,
        has_metal=has_metal,
    )
