#!/usr/bin/env bash
# ==============================================================================
# Local LLM Hardware Advisor — One-Line Installer (Linux & macOS)
# Usage: curl -fsSL https://raw.githubusercontent.com/blackstart-labs/local-llm-advisor/main/install.sh | bash
# ==============================================================================

set -euo pipefail

COLOR_CYAN='\033[0;36m'
COLOR_GREEN='\033[0;32m'
COLOR_YELLOW='\033[1;33m'
COLOR_RED='\033[0;31m'
COLOR_RESET='\033[0m'

echo -e "${COLOR_CYAN}"
echo "╭──────────────────────────────────────────────────────────────╮"
echo "│           Local LLM Hardware Advisor Installer               │"
echo "│                 Linux & macOS Installer                      │"
echo "╰──────────────────────────────────────────────────────────────╯"
echo -e "${COLOR_RESET}"

# 1. Detect Python 3.10+
PYTHON_BIN=""
for cmd in python3.12 python3.11 python3.10 python3 python; do
    if command -v "$cmd" &>/dev/null; then
        VER=$("$cmd" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
        MAJOR=$(echo "$VER" | cut -d. -f1)
        MINOR=$(echo "$VER" | cut -d. -f2)
        if [ "$MAJOR" -eq 3 ] && [ "$MINOR" -ge 10 ]; then
            PYTHON_BIN="$cmd"
            break
        fi
    fi
done

if [ -z "$PYTHON_BIN" ]; then
    echo -e "${COLOR_RED}Error: Python 3.10 or higher is required to run Local LLM Advisor.${COLOR_RESET}"
    echo "Please install Python 3.10+ and re-run this script."
    exit 1
fi

echo -e "✓ Found Python: ${COLOR_GREEN}$("$PYTHON_BIN" --version)${COLOR_RESET}"

# 2. Prepare installation directory
INSTALL_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/local-llm-advisor"
BIN_DIR="$HOME/.local/bin"

echo -e "Installing to: ${COLOR_CYAN}${INSTALL_DIR}${COLOR_RESET}"
mkdir -p "${INSTALL_DIR}" "${BIN_DIR}"

# 3. Create virtual environment
VENV_DIR="${INSTALL_DIR}/venv"
if [ ! -d "${VENV_DIR}" ]; then
    echo "Creating Python virtual environment..."
    "$PYTHON_BIN" -m venv "${VENV_DIR}"
fi

# 4. Install local-llm-advisor
echo "Installing package and dependencies..."
"${VENV_DIR}/bin/pip" install --upgrade pip --quiet
"${VENV_DIR}/bin/pip" install git+https://github.com/blackstart-labs/local-llm-advisor.git --quiet || \
"${VENV_DIR}/bin/pip" install local-llm-advisor --quiet || \
( [ -f "pyproject.toml" ] && "${VENV_DIR}/bin/pip" install -e . --quiet )

# 5. Create symlink in ~/.local/bin
SYMLINK_PATH="${BIN_DIR}/llm-advisor"
rm -f "${SYMLINK_PATH}"
ln -s "${VENV_DIR}/bin/llm-advisor" "${SYMLINK_PATH}"
chmod +x "${SYMLINK_PATH}"

echo -e "✓ Executable linked: ${COLOR_GREEN}${SYMLINK_PATH}${COLOR_RESET}"

# 6. Check PATH
case ":$PATH:" in
    *":${BIN_DIR}:"*) ;;
    *)
        echo -e "${COLOR_YELLOW}Notice: ${BIN_DIR} is not in your PATH.${COLOR_RESET}"
        echo "Add it to your shell configuration (~/.bashrc, ~/.zshrc, or ~/.profile):"
        echo -e "${COLOR_CYAN}  export PATH=\"\$HOME/.local/bin:\$PATH\"${COLOR_RESET}"
        ;;
esac

echo -e "\n${COLOR_GREEN}✓ Installation complete! Run the hardware scan with:${COLOR_RESET}"
echo -e "${COLOR_CYAN}  llm-advisor scan${COLOR_RESET}\n"
