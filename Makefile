.PHONY: install format lint security test check run

install:
	uv sync --dev

format:
	uv run ruff check --select I --fix app/ tests/
	uv run ruff format app/ tests/

lint:
	uv run ruff check app/ tests/

security:
	uv run bandit -c pyproject.toml -r app/

test:
	uv run pytest tests/ --cov=app --cov-report=term-missing --cov-report=html

check: format lint security test

build:
	docker build -t dailymotion-user-registration-api .

run:
	uv run uvicorn app.main:app --reload
