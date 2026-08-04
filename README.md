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
docker compose up --build
```

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
