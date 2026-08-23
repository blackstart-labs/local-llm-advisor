# ==============================================================================
# Local LLM Hardware Advisor — One-Line PowerShell Installer (Windows)
# Usage: powershell -c "irm https://raw.githubusercontent.com/blackstart-labs/local-llm-advisor/main/install.ps1 | iex"
# ==============================================================================

$ErrorActionPreference = "Stop"

Write-Host "╭──────────────────────────────────────────────────────────────╮" -ForegroundColor Cyan
Write-Host "│           Local LLM Hardware Advisor Installer               │" -ForegroundColor Cyan
Write-Host "│                   Windows Installer                          │" -ForegroundColor Cyan
Write-Host "╰──────────────────────────────────────────────────────────────╯" -ForegroundColor Cyan
Write-Host ""

# 1. Detect Python 3.10+
$pythonCmd = $null
$candidates = @("python", "py", "python3")

foreach ($cmd in $candidates) {
    if (Get-Command $cmd -ErrorAction SilentlyContinue) {
        try {
            $ver = & $cmd -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>$null
            if ($ver) {
                $parts = $ver.Split('.')
                $major = [int]$parts[0]
                $minor = [int]$parts[1]
                if ($major -eq 3 -and $minor -ge 10) {
                    $pythonCmd = $cmd
                    break
                }
            }
        } catch {}
    }
}

if (-not $pythonCmd) {
    Write-Host "Error: Python 3.10 or higher is required to run Local LLM Advisor." -ForegroundColor Red
    Write-Host "Please install Python 3.10+ from https://www.python.org or Microsoft Store and re-run this script." -ForegroundColor Yellow
    exit 1
}

$pyVersion = & $pythonCmd --version
Write-Host "✓ Found Python: $pyVersion" -ForegroundColor Green

# 2. Prepare install path
$installDir = Join-Path $env:USERPROFILE ".local-llm-advisor"
$venvDir = Join-Path $installDir "venv"
$scriptsDir = Join-Path $venvDir "Scripts"

Write-Host "Installing to: $installDir" -ForegroundColor Cyan

if (-not (Test-Path $installDir)) {
    New-Item -ItemType Directory -Path $installDir -Force | Out-Null
}

# 3. Create virtual environment
if (-not (Test-Path $venvDir)) {
    Write-Host "Creating Python virtual environment..." -ForegroundColor Yellow
    & $pythonCmd -m venv $venvDir
}

# 4. Install package
$pipCmd = Join-Path $scriptsDir "pip.exe"
Write-Host "Installing package dependencies..." -ForegroundColor Yellow

& $pipCmd install --upgrade pip --quiet
try {
    & $pipCmd install git+https://github.com/blackstart-labs/local-llm-advisor.git --quiet
} catch {
    if (Test-Path "pyproject.toml") {
        & $pipCmd install -e . --quiet
    }
}

# 5. Add Scripts directory to User PATH environment variable
$currentPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($currentPath -notlike "*$scriptsDir*") {
    Write-Host "Adding $scriptsDir to User PATH..." -ForegroundColor Yellow
    $newPath = "$currentPath;$scriptsDir"
    [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
    $env:Path = "$env:Path;$scriptsDir"
}

Write-Host ""
Write-Host "✓ Installation complete!" -ForegroundColor Green
Write-Host "Run the hardware scan using:" -ForegroundColor Green
Write-Host "  llm-advisor scan" -ForegroundColor Cyan
Write-Host ""
