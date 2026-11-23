.PHONY: setup dev run test lint typecheck web-dev web-build e2e validate hooks

setup:
	uv sync --locked
	pnpm --dir web install --frozen-lockfile

dev:
	uv run --locked agent-hub run --reload

# Static serving is added in Phase 8; currently serves the API shell.
run: web-build
	uv run --locked agent-hub run

test:
	uv run --locked pytest
	pnpm --dir web test

lint:
	uv run --locked ruff check .
	uv run --locked ruff format --check .
	pnpm --dir web lint
	pnpm --dir web format:check

typecheck:
	uv run --locked mypy
	pnpm --dir web typecheck

web-dev:
	pnpm --dir web dev

web-build:
	pnpm --dir web build

e2e:
	pnpm --dir web e2e

validate:
	uv run --locked agent-hub validate

hooks:
	uv run --locked pre-commit install
