UV=uv
PY=python
UV_PY=3.13

.PHONY: help deps lock run dev clean env

help:
	@echo "Targets: deps, deps-test, lock, test, test-unit, test-integration, test-e2e, test-all, coverage, run, dev, env, clean"

# Create .venv and install deps from pyproject.toml
deps:
	$(UV) sync --python $(UV_PY)

# Install test/dev dependencies as well
deps-test:
	$(UV) sync --python $(UV_PY) --extra test

# Update lock (uv resolves versions)
lock:
	$(UV) lock --python $(UV_PY)

# Run bot (uses .env)
run:
	$(UV) run --python $(UV_PY) $(PY) -m bot.main

# Dev run with verbose logs
dev:
	LOG_LEVEL=DEBUG $(UV) run --python $(UV_PY) $(PY) -m bot.main

# Pytest targets
test:
	$(UV) run --python $(UV_PY) pytest -m "not integration and not e2e"

test-unit:
	$(UV) run --python $(UV_PY) pytest tests/unit -m "not integration and not e2e"

test-integration:
	$(UV) run --python $(UV_PY) pytest -m integration

test-e2e:
	$(UV) run --python $(UV_PY) pytest -m e2e

# Run all tests (unit + integration + e2e)
test-all:
	$(MAKE) test
	$(MAKE) test-integration
	$(MAKE) test-e2e

coverage:
	$(UV) run --python $(UV_PY) pytest --cov=bot --cov-report=term-missing

# Create .env from template (no overwrite)
env:
	@test -f .env || cp .env.example .env
	@echo ".env ready"

clean:
	rm -rf .venv __pycache__ */__pycache__
