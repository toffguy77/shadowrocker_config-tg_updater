UV=uv
PY=python
UV_PY=3.13

# Dockerized runtime
IMAGE_NAME?=shadowrocket-bot
CONTAINER_NAME?=shadowrocket-bot
PORT?=9123

.PHONY: help deps lock run dev clean env docker-build docker-run docker-logs docker-stop docker-restart docker-status

help:
	@echo "Targets: deps, deps-test, lock, run, dev, docker-build, docker-run, docker-logs, docker-stop, docker-restart, docker-status, test, test-unit, test-integration, test-e2e, test-all, coverage, env, clean"
# Create .venv and install deps from pyproject.toml
deps:
	$(UV) sync --python $(UV_PY)

# Install test/dev dependencies as well
deps-test:
	$(UV) sync --python $(UV_PY) --extra test

# Update lock (uv resolves versions)
lock:
	$(UV) lock --python $(UV_PY)

# Build Docker image
docker-build:
	docker build -t $(IMAGE_NAME) .

# Local run (uv-managed venv)
run:
	$(UV) run --python $(UV_PY) $(PY) -m bot.main

# Dockerized run (background with restart)
docker-run: docker-build
	@docker stop $(CONTAINER_NAME) 2>/dev/null || true
	@docker rm $(CONTAINER_NAME) 2>/dev/null || true
	docker run -d \
		--name $(CONTAINER_NAME) \
		--env-file .env \
		-p $(PORT):$(PORT) \
		--restart always \
		$(IMAGE_NAME)

# Dev run with verbose logs (local venv)
dev:
	LOG_LEVEL=DEBUG $(UV) run --python $(UV_PY) $(PY) -m bot.main

# Logs from container
docker-logs:
	docker logs -f $(CONTAINER_NAME)

# Stop and remove container
docker-stop:
	@docker stop $(CONTAINER_NAME) 2>/dev/null || true
	@docker rm $(CONTAINER_NAME) 2>/dev/null || true

# Restart container
docker-restart: docker-stop docker-run

# Show container status
docker-status:
	docker ps -f name=$(CONTAINER_NAME)

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
