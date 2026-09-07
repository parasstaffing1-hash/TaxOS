# TaxOS

**Enterprise Tax Calculation Platform**

A production-ready, async Python platform foundation built with Clean Architecture principles, designed to support hundreds of tax calculators.

---

## Architecture

```
┌──────────────────────────────────────────────┐
│                  API Layer                    │
│          (FastAPI, Middleware, DI)            │
├──────────────────────────────────────────────┤
│              Application Layer               │
│          (Services, Use Cases)               │
├──────────────────────────────────────────────┤
│               Domain Layer                   │
│       (Entities, Value Objects, Types)       │
├──────────────────────────────────────────────┤
│            Infrastructure Layer              │
│     (Database, Logging, External APIs)       │
└──────────────────────────────────────────────┘
```

Dependencies flow **inward** — outer layers depend on inner layers, never the reverse.

## Tech Stack

| Category        | Technology                         |
|----------------|------------------------------------|
| Runtime        | Python 3.13                        |
| Framework      | FastAPI + Uvicorn                  |
| Validation     | Pydantic v2                        |
| ORM            | SQLAlchemy 2.x (async)             |
| Migrations     | Alembic                            |
| Database       | PostgreSQL 16                      |
| Logging        | structlog                          |
| Dependencies   | uv                                 |
| Linting        | Ruff + Black                       |
| Type Checking  | MyPy (strict)                      |
| Testing        | Pytest + pytest-asyncio            |
| Containers     | Docker + Docker Compose            |
| CI/CD          | GitHub Actions                     |

## Quick Start

### Prerequisites

- [Python 3.13](https://www.python.org/downloads/)
- [uv](https://docs.astral.sh/uv/)
- [Docker](https://www.docker.com/) (optional, for full stack)

### Local Development

```bash
# Clone the repository
git clone <repository-url>
cd Tax

# Install dependencies
uv sync --all-extras

# Copy environment config
cp .env.example .env

# Start PostgreSQL (via Docker)
docker compose up db -d

# Run the application
uv run uvicorn taxos.main:app --reload

# Open API docs
# http://localhost:8000/docs
```

### Docker (Full Stack)

```bash
cp .env.example .env
# Use the production file explicitly so the development override is not loaded.
docker compose -f docker-compose.yml up --build -d
```

The full stack serves the Next.js frontend at `http://localhost:3000` and the
FastAPI API at `http://localhost:8000`. Before deployment, replace every local
secret in `.env`—especially `SECRET_KEY`, `FIELD_ENCRYPTION_KEY`, and
`POSTGRES_PASSWORD`—with values from your secret manager. Set
`ENVIRONMENT=production`, keep `DEBUG=false`, and set `ALLOWED_ORIGINS` to the
exact HTTPS origin(s) serving the frontend. Production settings fail closed
when required secrets are missing or a wildcard CORS origin is configured.

The API container runs Alembic migrations before Uvicorn starts. Its Docker
healthcheck uses `/api/v1/health/ready`, so the frontend waits for a live API
and database. For multi-replica deployments, run `alembic upgrade head` as a
separate release job before scaling replicas and then start the API services.

The catalog exposes all registered tools, but only tools marked `complete` or
`partial` are executable. Treat the catalog's `release_coverage_percent` as a
release metric; do not advertise `not_started` or `blocked` tools as live
calculators.

## Development Commands

```bash
# ── Linting & Formatting ──────────────────────────
uv run ruff check src/ tests/          # Lint
uv run ruff check --fix src/ tests/    # Lint + auto-fix
uv run black src/ tests/               # Format

# ── Type Checking ─────────────────────────────────
uv run mypy src/

# ── Testing ───────────────────────────────────────
uv run pytest                          # Run all tests
uv run pytest tests/unit/              # Unit tests only
uv run pytest tests/integration/       # Integration tests only
uv run pytest --cov=taxos              # With coverage

# ── Database Migrations ───────────────────────────
uv run alembic revision --autogenerate -m "description"
uv run alembic upgrade head
uv run alembic downgrade -1
```

## Project Structure

```
Tax/
├── src/taxos/
│   ├── main.py                        # FastAPI app factory
│   ├── core/                          # Configuration, logging, exceptions
│   │   ├── config.py                  # Pydantic Settings
│   │   ├── exceptions.py             # Domain exception hierarchy
│   │   ├── logging.py                # structlog configuration
│   │   └── types.py                  # Shared type aliases
│   ├── domain/                        # Domain models
│   │   └── entities/
│   │       └── base.py               # Base entity (UUID + timestamps)
│   ├── application/                   # Service layer
│   │   ├── interfaces/
│   │   │   └── repositories.py       # Abstract repository protocol
│   │   └── services/
│   │       └── health.py             # Health check service
│   ├── infrastructure/                # Framework adapters
│   │   ├── database/
│   │   │   ├── base.py               # SQLAlchemy base + mixins
│   │   │   ├── session.py            # Async engine + sessions
│   │   │   ├── repository.py         # Generic SQLAlchemy repository
│   │   │   └── migrations/           # Alembic migrations
│   │   └── logging/
│   │       └── setup.py              # Logging bridge
│   └── api/                           # Presentation layer
│       ├── deps.py                    # Dependency injection
│       ├── middleware.py              # Request ID + error handling
│       ├── schemas/                   # Pydantic response models
│       │   ├── common.py             # Generic envelopes
│       │   └── health.py             # Health schemas
│       └── v1/                        # API version 1
│           ├── router.py             # Aggregate router
│           └── endpoints/
│               └── health.py         # Health endpoints
├── tests/
│   ├── conftest.py                    # Shared fixtures
│   ├── unit/                          # Unit tests
│   └── integration/                   # Integration tests
├── docs/
│   └── architecture.md               # Architecture documentation
├── pyproject.toml                     # Project config (uv + tools)
├── alembic.ini                        # Alembic config
├── Dockerfile                         # Multi-stage Docker build
├── docker-compose.yml                 # Full stack definition
└── docker-compose.override.yml        # Dev overrides
```

## API Endpoints

| Method | Path                    | Description           |
|--------|-------------------------|-----------------------|
| GET    | `/api/v1/health`        | Liveness probe        |
| GET    | `/api/v1/health/ready`  | Readiness probe       |
| GET    | `/docs`                 | OpenAPI (Swagger) UI  |
| GET    | `/redoc`                | ReDoc documentation   |

## License

MIT
