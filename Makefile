.PHONY: check test lint typecheck secrets fmt hooks

check: lint typecheck secrets test

test:
	uv run pytest

lint:
	uv tool run ruff check .
	uv tool run ruff format --check .
	shellcheck install bin/miss-log .githooks/pre-commit

# Runs pyright inside the project environment so it resolves pytest.
typecheck:
	uv run --with pyright pyright --warnings

# History, then what is staged for the next commit.
secrets:
	gitleaks git --no-banner --redact .
	gitleaks git --no-banner --redact --pre-commit --staged .

fmt:
	uv tool run ruff format .
	uv tool run ruff check --fix .

# Uses the tracked hooks in .githooks/ (pre-commit runs `make check`).
hooks:
	git config core.hooksPath .githooks
