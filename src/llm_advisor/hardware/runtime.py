"""Local LLM runtime and driver availability detection across Linux, macOS, and Windows."""

from __future__ import annotations

import os
import platform
import shutil
import subprocess

from llm_advisor.hardware.schema import RuntimeCapabilities


def _is_executable_in_path(cmd: str) -> bool:
    """Check if binary executable exists in PATH or standard platform paths."""
    if shutil.which(cmd) is not None:
        return True

    system = platform.system()
    if system == "Windows":
        # Check standard Windows app installation directories
        local_app_data = os.environ.get("LOCALAPPDATA", "")
        program_files = os.environ.get("PROGRAMFILES", "C:\\Program Files")

        known_paths = [
            os.path.join(local_app_data, "Programs", "Ollama", "ollama.exe"),
            os.path.join(program_files, "Ollama", "ollama.exe"),
            os.path.join(local_app_data, "Programs", "LM Studio", "LM Studio.exe"),
            os.path.join(local_app_data, "Programs", "LM Studio", "resources", "app", "bin", "lms.exe"),
        ]
        for p in known_paths:
            if os.path.exists(p) and cmd in p.lower():
                return True

    elif system == "Darwin":
        known_mac_paths = [
            "/Applications/Ollama.app",
            "/Applications/LM Studio.app",
            "/usr/local/bin/ollama",
            "/opt/homebrew/bin/ollama",
            "/usr/local/bin/llama-cli",
            "/opt/homebrew/bin/llama-cli",
        ]
        for p in known_mac_paths:
            if os.path.exists(p) and cmd in p.lower():
                return True

    return False


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

    if platform.system() == "Darwin":
        try:
            res = subprocess.run(
                ["sysctl", "-n", "machdep.cpu.brand_string"], capture_output=True, text=True, timeout=1
            )
            if res.returncode == 0 and (
                "Apple" in res.stdout or "M1" in res.stdout or "M2" in res.stdout or "M3" in res.stdout or "M4" in res.stdout
            ) or "arm" in platform.machine().lower():
                has_metal = True
        except Exception:
            if "arm" in platform.machine().lower():
                has_metal = True

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
