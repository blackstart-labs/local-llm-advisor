"""Tests for Windows and macOS specific hardware detection routines."""

from unittest.mock import MagicMock, patch

from llm_advisor.hardware.cpu import _detect_instruction_sets, _get_cpu_brand_model
from llm_advisor.hardware.gpu import _detect_apple_silicon_gpu, _detect_windows_wmi_gpu
from llm_advisor.hardware.runtime import detect_runtime
from llm_advisor.hardware.schema import GpuVendor


@patch("platform.system")
@patch("subprocess.run")
def test_windows_cpu_detection(mock_run: MagicMock, mock_system: MagicMock) -> None:
    mock_system.return_value = "Windows"
    mock_run.return_value = MagicMock(
        returncode=0,
        stdout="AMD Ryzen 7 5800X 8-Core Processor\n",
    )

    brand, model = _get_cpu_brand_model()
    assert brand == "AMD"
    assert "Ryzen 7 5800X" in model


@patch("platform.system")
@patch("subprocess.run")
def test_windows_gpu_wmi_detection(mock_run: MagicMock, mock_system: MagicMock) -> None:
    mock_system.return_value = "Windows"
    mock_run.return_value = MagicMock(
        returncode=0,
        stdout='{"Name": "NVIDIA GeForce RTX 4070", "AdapterRAM": 12884901888, "DriverVersion": "551.23"}\n',
    )

    gpus = _detect_windows_wmi_gpu()
    assert len(gpus) == 1
    assert gpus[0].vendor == GpuVendor.NVIDIA
    assert "RTX 4070" in gpus[0].name
    assert gpus[0].vram_gb >= 12.0


@patch("platform.system")
@patch("platform.machine")
@patch("psutil.virtual_memory")
def test_macos_apple_silicon_gpu(
    mock_vm: MagicMock, mock_machine: MagicMock, mock_system: MagicMock
) -> None:
    mock_system.return_value = "Darwin"
    mock_machine.return_value = "arm64"
    mock_vm.return_value = MagicMock(total=36 * (1024**3))

    gpus = _detect_apple_silicon_gpu()
    assert len(gpus) == 1
    assert gpus[0].vendor == GpuVendor.APPLE
    assert gpus[0].is_unified_memory is True
    assert gpus[0].metal_available is True
    assert gpus[0].vram_gb >= 36.0


@patch("platform.system")
@patch("subprocess.run")
def test_macos_instruction_sets(mock_run: MagicMock, mock_system: MagicMock) -> None:
    mock_system.return_value = "Darwin"
    mock_run.return_value = MagicMock(
        returncode=0,
        stdout="hw.optional.avx2: 1\nhw.optional.neon: 1\n",
    )

    instructions = _detect_instruction_sets()
    assert "AVX2" in instructions
    assert "NEON" in instructions


@patch("platform.system")
@patch("shutil.which")
def test_runtime_windows_paths(mock_which: MagicMock, mock_system: MagicMock) -> None:
    mock_system.return_value = "Windows"
    mock_which.return_value = None

    capabilities = detect_runtime()
    assert isinstance(capabilities.has_ollama, bool)
    assert isinstance(capabilities.has_cuda, bool)
