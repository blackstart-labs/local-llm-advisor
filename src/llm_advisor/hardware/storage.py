"""Storage disk space and filesystem detection."""

from __future__ import annotations

import os
import psutil
from llm_advisor.hardware.schema import StorageInfo, StorageType


def detect_storage(path: str = ".") -> StorageInfo:
    """Detect available storage disk space and filesystem."""
    try:
        usage = psutil.disk_usage(os.path.abspath(path))
        free = int(usage.free)
        total = int(usage.total)
    except Exception:
        free = 50 * (1024**3)
        total = 500 * (1024**3)

    filesystem = "Unknown"
    storage_type = StorageType.UNKNOWN

    try:
        partitions = psutil.disk_partitions(all=False)
        target_path = os.path.abspath(path)
        for part in partitions:
            if target_path.startswith(part.mountpoint):
                filesystem = part.fstype or "Unknown"
                if "nvme" in part.device.lower():
                    storage_type = StorageType.NVME
                elif "ssd" in part.device.lower():
                    storage_type = StorageType.SSD
                break
    except Exception:
        pass

    return StorageInfo(
        free_bytes=free,
        total_bytes=total,
        filesystem=filesystem,
        storage_type=storage_type,
    )
