# syntax=docker/dockerfile:1

# ====== Builder ======
FROM python:3.13-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# System deps for SSL and certificates (usually present, but ensure)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# Install uv to resolve and install deps from pyproject/uv.lock
RUN pip install --no-cache-dir uv

# Only dependency files first for better layer caching
COPY pyproject.toml uv.lock ./

# Create project venv and install runtime deps (no dev)
RUN uv sync --frozen --no-dev --python 3.13

# Copy application source
COPY bot ./bot

# ====== Runtime ======
FROM python:3.13-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Copy virtualenv and app sources from builder
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/bot /app/bot

# Optionally expose metrics port
EXPOSE 9123

# Healthcheck (lightweight ping via python import)
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD /app/.venv/bin/python -c "import sys; import socket; sys.exit(0)"

# Run
CMD ["/app/.venv/bin/python", "-m", "bot.main"]
