"""GPU hardware detection across NVIDIA, AMD, Intel, and Apple Silicon for Linux, macOS, and Windows."""

from __future__ import annotations

import json
import os
import platform
import subprocess

from llm_advisor.hardware.schema import GpuInfo, GpuVendor


def _detect_nvidia_gpus() -> list[GpuInfo]:
    """Detect NVIDIA GPUs via nvidia-smi command across Linux, macOS, and Windows."""
    gpus: list[GpuInfo] = []

    # Potential binary paths (including Windows default NVSMI install directory)
    candidates = ["nvidia-smi"]
    if platform.system() == "Windows":
        win_nvsmi = os.path.join(
            os.environ.get("PROGRAMFILES", "C:\\Program Files"),
            "NVIDIA Corporation",
            "NVSMI",
            "nvidia-smi.exe",
        )
        if os.path.exists(win_nvsmi):
            candidates.insert(0, win_nvsmi)

    for cmd in candidates:
        try:
            res = subprocess.run(
                [
                    cmd,
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
                if gpus:
                    break
        except Exception:
            pass
    return gpus


def _detect_apple_silicon_gpu() -> list[GpuInfo]:
    """Detect Apple Silicon or Intel macOS GPU with unified memory or dedicated VRAM."""
    gpus: list[GpuInfo] = []
    if platform.system() == "Darwin":
        if "arm" in platform.machine().lower():
            try:
                import psutil

                vm = psutil.virtual_memory()
                total_ram = int(vm.total)
                # Apple Silicon shares unified memory
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
        else:
            # Intel Mac GPU detection via system_profiler
            try:
                res = subprocess.run(
                    ["system_profiler", "SPDisplaysDataType"],
                    capture_output=True,
                    text=True,
                    timeout=4,
                )
                if res.returncode == 0:
                    gpu_name = "macOS Graphics"
                    vram_bytes = 0
                    vendor = GpuVendor.UNKNOWN
                    for line in res.stdout.splitlines():
                        line_str = line.strip()
                        if line_str.startswith("Chipset Model:"):
                            gpu_name = line_str.split(":", 1)[1].strip()
                            if "AMD" in gpu_name or "Radeon" in gpu_name:
                                vendor = GpuVendor.AMD
                            elif "Intel" in gpu_name:
                                vendor = GpuVendor.INTEL
                            elif "NVIDIA" in gpu_name:
                                vendor = GpuVendor.NVIDIA
                        elif line_str.startswith("VRAM (Total):") or line_str.startswith("VRAM (Dynamic):"):
                            vram_str = line_str.split(":", 1)[1].strip()
                            if "GB" in vram_str:
                                vram_gb = float(vram_str.replace("GB", "").strip())
                                vram_bytes = int(vram_gb * (1024**3))
                            elif "MB" in vram_str:
                                vram_mb = float(vram_str.replace("MB", "").strip())
                                vram_bytes = int(vram_mb * 1024 * 1024)

                    if gpu_name != "macOS Graphics":
                        gpus.append(
                            GpuInfo(
                                vendor=vendor,
                                name=gpu_name,
                                vram_bytes=vram_bytes,
                                metal_available=True,
                            )
                        )
            except Exception:
                pass

    return gpus


def _detect_windows_wmi_gpu() -> list[GpuInfo]:
    """Detect AMD/Intel/NVIDIA GPUs on Windows via PowerShell Get-CimInstance Win32_VideoController."""
    gpus: list[GpuInfo] = []
    if platform.system() == "Windows":
        try:
            res = subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-Command",
                    "Get-CimInstance Win32_VideoController | Select-Object Name, AdapterRAM, DriverVersion | ConvertTo-Json",
                ],
                capture_output=True,
                text=True,
                timeout=4,
            )
            if res.returncode == 0 and res.stdout.strip():
                try:
                    data = json.loads(res.stdout)
                    items = data if isinstance(data, list) else [data]
                    for item in items:
                        name = item.get("Name", "Windows GPU")
                        adapter_ram = item.get("AdapterRAM") or 0
                        driver = item.get("DriverVersion", "")

                        # Filter out virtual display adapters
                        if "Virtual" in name or "Basic Render" in name or "RDP" in name:
                            continue

                        vendor = GpuVendor.UNKNOWN
                        if "NVIDIA" in name:
                            vendor = GpuVendor.NVIDIA
                        elif "AMD" in name or "Radeon" in name:
                            vendor = GpuVendor.AMD
                        elif "Intel" in name:
                            vendor = GpuVendor.INTEL

                        vram_bytes = int(adapter_ram) if isinstance(adapter_ram, (int, float)) and adapter_ram > 0 else 0
                        # 4GB uint32 overflow fix in WMI AdapterRAM
                        if vram_bytes < 0:
                            vram_bytes = (vram_bytes + 2**32)

                        gpus.append(
                            GpuInfo(
                                vendor=vendor,
                                name=name,
                                vram_bytes=vram_bytes,
                                driver_version=driver,
                                cuda_available=(vendor == GpuVendor.NVIDIA),
                            )
                        )
                except Exception:
                    pass
        except Exception:
            pass
    return gpus


def _detect_amd_gpus() -> list[GpuInfo]:
    """Detect AMD GPUs via rocm-smi on Linux."""
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
    """Detect available GPUs across Linux, macOS, and Windows with fail-safe behavior."""
    gpus: list[GpuInfo] = []

    # 1. Try NVIDIA (Linux / Windows / macOS)
    gpus.extend(_detect_nvidia_gpus())

    # 2. Try macOS (Apple Silicon / Intel Mac)
    if not gpus and platform.system() == "Darwin":
        gpus.extend(_detect_apple_silicon_gpu())

    # 3. Try Windows WMI / DirectX
    if not gpus and platform.system() == "Windows":
        gpus.extend(_detect_windows_wmi_gpu())

    # 4. Try AMD ROCm on Linux
    if not gpus and platform.system() == "Linux":
        gpus.extend(_detect_amd_gpus())

    return gpus
