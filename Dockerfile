# ── Build stage ───────────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Install dependencies first, source-independent layer for cache efficiency.
COPY pyproject.toml uv.lock ./
RUN uv sync --no-dev --frozen --no-install-project

# Copy source and install the project itself.
COPY . .
RUN uv sync --no-dev --frozen


# ── Runtime stage ─────────────────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

WORKDIR /app

# Non-root user: never run application code as root.
RUN addgroup --system app && adduser --system --ingroup app app

# Copy only what is needed at runtime (no uv, no build tools).
COPY --from=builder --chown=app:app /app/.venv       ./.venv
COPY --from=builder --chown=app:app /app/app         ./app
COPY --from=builder --chown=app:app /app/migrations  ./migrations
COPY --from=builder --chown=app:app /app/scripts     ./scripts

# Activate the venv by prepending it to PATH.
ENV VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

USER app

# entrypoint.sh runs migrations then execs uvicorn as PID 1.
ENTRYPOINT ["sh", "scripts/entrypoint.sh"]
