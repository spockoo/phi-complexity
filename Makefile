.PHONY: setup lint format-check typecheck test ci-local

setup:
	pip install -e .
	pip install pytest pytest-cov ruff black==25.11.0 mypy

lint:
	ruff check .

format-check:
	black --check .

typecheck:
	python -m mypy phi_complexity --ignore-missing-imports

test:
	python -m pytest tests/ --cov=phi_complexity --cov-report=term-missing

ci-local: lint format-check typecheck test
