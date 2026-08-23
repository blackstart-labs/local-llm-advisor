"""CPU hardware detection across Linux, macOS, and Windows."""

from __future__ import annotations

import os
import platform
import subprocess

from llm_advisor.hardware.schema import CpuInfo


def _detect_instruction_sets() -> list[str]:
    """Detect available SIMD / tensor instruction capabilities."""
    instructions: list[str] = []
    system = platform.system()

    if system == "Linux":
        try:
            with open("/proc/cpuinfo", encoding="utf-8") as f:
                flags = ""
                for line in f:
                    if line.startswith("flags") or line.startswith("Features"):
                        flags = line.split(":", 1)[1].strip()
                        break
                flag_set = set(flags.split())
                for flag in ["avx", "avx2", "avx512f", "avx512bw", "amx_bf16", "neon"]:
                    if flag in flag_set:
                        instructions.append(flag.upper())
        except Exception:
            pass
    elif system == "Darwin":
        try:
            res = subprocess.run(["sysctl", "-a"], capture_output=True, text=True, timeout=2)
            out = res.stdout.lower()
            if "hw.optional.avx2: 1" in out:
                instructions.append("AVX2")
            if "hw.optional.avx512f: 1" in out:
                instructions.append("AVX512F")
            if "hw.optional.neon: 1" in out or "arm" in platform.machine().lower():
                instructions.append("NEON")
        except Exception:
            pass
    elif system == "Windows":
        try:
            res = subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-Command",
                    "(Get-CimInstance Win32_Processor).Caption + ' ' + (Get-CimInstance Win32_Processor).Name",
                ],
                capture_output=True,
                text=True,
                timeout=3,
            )
            out = res.stdout.upper()
            if "AVX2" in out or "AVX" in out:
                instructions.append("AVX2")
            if "AVX512" in out:
                instructions.append("AVX512F")
        except Exception:
            pass

    return instructions


def _get_cpu_brand_model() -> tuple[str, str]:
    """Determine CPU brand and model strings across Linux, macOS, and Windows."""
    brand = "Unknown"
    model = "CPU"
    system = platform.system()

    try:
        proc_str = platform.processor()
        if proc_str:
            model = proc_str
    except Exception:
        pass

    if system == "Linux":
        try:
            with open("/proc/cpuinfo", encoding="utf-8") as f:
                for line in f:
                    if "model name" in line:
                        full_name = line.split(":", 1)[1].strip()
                        if "Intel" in full_name:
                            brand = "Intel"
                        elif "AMD" in full_name:
                            brand = "AMD"
                        elif "Apple" in full_name or "ARM" in full_name:
                            brand = "ARM"
                        model = full_name
                        break
        except Exception:
            pass
    elif system == "Darwin":
        try:
            res = subprocess.run(
                ["sysctl", "-n", "machdep.cpu.brand_string"],
                capture_output=True,
                text=True,
                timeout=2,
            )
            if res.returncode == 0 and res.stdout.strip():
                full_name = res.stdout.strip()
                if "Intel" in full_name:
                    brand = "Intel"
                elif "Apple" in full_name:
                    brand = "Apple"
                model = full_name
            elif "arm" in platform.machine().lower():
                brand = "Apple"
                model = "Apple Silicon"
        except Exception:
            pass
    elif system == "Windows":
        try:
            # Query WMI Win32_Processor for clean CPU name
            res = subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-Command",
                    "(Get-CimInstance Win32_Processor).Name",
                ],
                capture_output=True,
                text=True,
                timeout=3,
            )
            if res.returncode == 0 and res.stdout.strip():
                full_name = res.stdout.strip().splitlines()[0]
                model = full_name
                if "Intel" in full_name:
                    brand = "Intel"
                elif "AMD" in full_name:
                    brand = "AMD"
                elif "ARM" in full_name or "Snapdragon" in full_name:
                    brand = "ARM"
            else:
                proc_env = os.environ.get("PROCESSOR_IDENTIFIER", "")
                if "Intel" in proc_env:
                    brand = "Intel"
                elif "AMD" in proc_env:
                    brand = "AMD"
                if proc_env:
                    model = proc_env
        except Exception:
            proc_env = os.environ.get("PROCESSOR_IDENTIFIER", "")
            if "Intel" in proc_env:
                brand = "Intel"
            elif "AMD" in proc_env:
                brand = "AMD"
            model = proc_env or model

    return brand, model


def detect_cpu() -> CpuInfo:
    """Detect comprehensive CPU specifications."""
    brand, model = _get_cpu_brand_model()
    arch = platform.machine() or "x86_64"
    is_64bit = "64" in arch or platform.architecture()[0] == "64bit"

    try:
        import psutil

        logical = psutil.cpu_count(logical=True) or 1
        physical = psutil.cpu_count(logical=False) or logical
    except Exception:
        logical = 1
        physical = 1

    freq_ghz: float | None = None
    try:
        import psutil

        freq = psutil.cpu_freq()
        if freq and freq.max > 0:
            freq_ghz = round(freq.max / 1000.0, 2)
        elif freq and freq.current > 0:
            freq_ghz = round(freq.current / 1000.0, 2)
    except Exception:
        freq_ghz = None

    instructions = _detect_instruction_sets()

    return CpuInfo(
        brand=brand,
        model=model,
        architecture=arch,
        physical_cores=physical,
        logical_cores=logical,
        frequency_ghz=freq_ghz,
        instruction_sets=instructions,
        is_64bit=is_64bit,
    )
