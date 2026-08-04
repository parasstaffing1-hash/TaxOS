# ── Build stage ──────────────────────────────────────────────────
FROM python:3.13-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy dependency files first for layer caching
COPY pyproject.toml uv.lock* ./

# Install dependencies
RUN uv sync --frozen --no-dev --no-install-project

# Copy source code
COPY src/ src/
COPY rules/ rules/
COPY alembic.ini ./

# Install the project itself
RUN uv sync --frozen --no-dev

# ── Runtime stage ────────────────────────────────────────────────
FROM python:3.13-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

# Create non-root user
RUN groupadd --gid 1001 taxos && \
    useradd --uid 1001 --gid taxos --shell /bin/bash --create-home taxos

# Copy virtual environment and source from builder
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/src /app/src
COPY --from=builder /app/rules /app/rules
COPY --from=builder /app/alembic.ini /app/alembic.ini
COPY docker-entrypoint.sh /app/docker-entrypoint.sh
RUN chmod 755 /app/docker-entrypoint.sh

USER taxos

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD ["python", "-c", "import httpx; r = httpx.get('http://localhost:8000/api/v1/health'); r.raise_for_status()"]

ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["uvicorn", "taxos.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
