# Contributing to Local LLM Hardware Advisor

Thank you for contributing!

## Development Setup

```bash
# Clone repository
git clone https://github.com/blackstart-labs/local-llm-advisor.git
cd local-llm-advisor

# Create virtual environment and install dev dependencies
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Running Quality Checks

```bash
# Run tests
pytest

# Test coverage
pytest --cov=src/llm_advisor --cov-report=term-missing

# Lint & Format
ruff check src tests
ruff format src tests

# Static Typing
mypy src
```
