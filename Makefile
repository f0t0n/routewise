.PHONY: check test lint typecheck fmt

check: lint typecheck test

test:
	uv run pytest

lint:
	uv tool run ruff check .
	uv tool run ruff format --check .
	shellcheck install bin/miss-log

typecheck:
	uv tool run pyright --warnings

fmt:
	uv tool run ruff format .
	uv tool run ruff check --fix .
