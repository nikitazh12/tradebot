.PHONY: install install-sdk sync lint fmt typecheck test test-unit smoke db-init migrate

install:
	uv sync

install-sdk:
	uv pip install t-tech-investments \
		--index-url https://opensource.tbank.ru/api/v4/projects/238/packages/pypi/simple

sync: install

lint:
	uv run ruff check src/ tests/

fmt:
	uv run ruff format src/ tests/

typecheck:
	uv run mypy src/

test:
	uv run pytest

test-unit:
	uv run pytest tests/unit/

smoke:
	uv run tradebot smoke

db-init:
	uv run tradebot db:init

migrate:
	uv run alembic upgrade head
