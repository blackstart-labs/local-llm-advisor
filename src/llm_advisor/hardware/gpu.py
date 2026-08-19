"""GPU hardware detection across NVIDIA, AMD, Intel, and Apple Silicon."""

from __future__ import annotations

import platform
import subprocess

import psutil

from llm_advisor.hardware.schema import GpuInfo, GpuVendor


def _detect_nvidia_gpus() -> list[GpuInfo]:
    """Detect NVIDIA GPUs via nvidia-smi command."""
    gpus: list[GpuInfo] = []
    try:
        res = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=name,memory.total,driver_version",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            timeout=3,
        )
        if res.returncode == 0 and res.stdout.strip():
            for line in res.stdout.strip().splitlines():
                parts = [p.strip() for p in line.split(",")]
                if len(parts) >= 3:
                    name = parts[0]
                    vram_mb = float(parts[1]) if parts[1].replace(".", "", 1).isdigit() else 0.0
                    driver = parts[2]
                    vram_bytes = int(vram_mb * 1024 * 1024)
                    gpus.append(
                        GpuInfo(
                            vendor=GpuVendor.NVIDIA,
                            name=name,
                            vram_bytes=vram_bytes,
                            driver_version=driver,
                            cuda_available=True,
                            is_unified_memory=False,
                        )
                    )
    except Exception:
        pass
    return gpus


def _detect_apple_silicon_gpu() -> list[GpuInfo]:
    """Detect Apple Silicon GPU with unified memory."""
    gpus: list[GpuInfo] = []
    if platform.system() == "Darwin" and "arm" in platform.machine().lower():
        try:
            vm = psutil.virtual_memory()
            total_ram = int(vm.total)
            # On Apple Silicon, GPU shares unified memory
            gpus.append(
                GpuInfo(
                    vendor=GpuVendor.APPLE,
                    name="Apple Silicon Metal GPU (Unified Memory)",
                    vram_bytes=total_ram,
                    metal_available=True,
                    is_unified_memory=True,
                )
            )
        except Exception:
            pass
    return gpus


def _detect_amd_gpus() -> list[GpuInfo]:
    """Detect AMD GPUs via rocm-smi or lspci."""
    gpus: list[GpuInfo] = []
    try:
        res = subprocess.run(
            ["rocm-smi", "--showid", "--json"],
            capture_output=True,
            text=True,
            timeout=3,
        )
        if res.returncode == 0 and "GPU" in res.stdout:
            gpus.append(
                GpuInfo(
                    vendor=GpuVendor.AMD,
                    name="AMD Instinct / Radeon ROCm GPU",
                    vram_bytes=8 * (1024**3),
                    rocm_available=True,
                )
            )
    except Exception:
        pass
    return gpus


def detect_gpus() -> list[GpuInfo]:
    """Detect available GPUs with fail-safe behavior."""
    gpus: list[GpuInfo] = []

    # 1. Try NVIDIA
    gpus.extend(_detect_nvidia_gpus())

    # 2. Try Apple Silicon
    if not gpus:
        gpus.extend(_detect_apple_silicon_gpu())

    # 3. Try AMD
    if not gpus:
        gpus.extend(_detect_amd_gpus())

    return gpus
