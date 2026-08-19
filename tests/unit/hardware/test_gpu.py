"""Tests for GPU detection and fallbacks."""

from unittest.mock import MagicMock, patch
from llm_advisor.hardware.gpu import detect_gpus
from llm_advisor.hardware.schema import GpuVendor


@patch("subprocess.run")
def test_detect_gpus_nvidia_success(mock_run: MagicMock) -> None:
    # Mock nvidia-smi CSV output
    mock_run.return_value = MagicMock(
        returncode=0,
        stdout="NVIDIA GeForce RTX 4090, 24576, 535.129.03\n",
    )

    gpus = detect_gpus()

    assert len(gpus) == 1
    assert gpus[0].vendor == GpuVendor.NVIDIA
    assert "RTX 4090" in gpus[0].name
    assert gpus[0].vram_gb >= 24.0
    assert gpus[0].cuda_available is True


@patch("subprocess.run")
def test_detect_gpus_unavailable_no_crash(mock_run: MagicMock) -> None:
    # Subprocess fails or nvidia-smi not found
    mock_run.side_effect = FileNotFoundError()

    gpus = detect_gpus()

    # Should not crash, returns empty list or unknown fallback
    assert isinstance(gpus, list)
