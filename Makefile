.PHONY: install dev-install test coverage lint format typecheck clean run

VENV = .venv
PYTHON = $(VENV)/bin/python
PIP = $(VENV)/bin/pip
pytest = $(VENV)/bin/pytest
ruff = $(VENV)/bin/ruff
mypy = $(VENV)/bin/mypy

install:
	$(PIP) install -e .

dev-install:
	$(PIP) install -e ".[dev]"

test:
	$(pytest) tests/

coverage:
	$(pytest) --cov=src/llm_advisor --cov-report=term-missing tests/

lint:
	$(ruff) check src tests

format:
	$(ruff) format src tests

typecheck:
	$(mypy) src

clean:
	rm -rf build dist *.egg-info .pytest_cache .coverage htmlcov .mypy_cache .ruff_cache report.html

run:
	$(PYTHON) -m llm_advisor scan
