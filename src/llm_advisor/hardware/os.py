"""Operating system and platform details detection."""

from __future__ import annotations

import platform

from llm_advisor.hardware.schema import OsInfo


def detect_os() -> OsInfo:
    """Detect platform operating system, release, and kernel versions."""
    system_name = platform.system() or "Unknown OS"
    release = platform.release() or "Unknown Release"
    version = platform.version() or ""
    arch = platform.machine() or "x86_64"

    kernel_version: str | None = None
    if system_name == "Linux":
        kernel_version = release
    elif system_name == "Darwin":
        kernel_version = f"Darwin {release}"
    elif system_name == "Windows":
        kernel_version = f"NT {version}"

    return OsInfo(
        platform_name=system_name,
        release=release,
        version=version,
        architecture=arch,
        kernel_version=kernel_version,
    )
