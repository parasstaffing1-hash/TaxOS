# TaxOS Architecture

## Overview

TaxOS follows **Clean Architecture** (Ports & Adapters) to ensure the domain logic remains independent of frameworks, databases, and external services. This enables:

- **Testability** — Domain logic can be tested without infrastructure
- **Flexibility** — Swap databases, frameworks, or APIs without touching business rules
- **Scalability** — Add new tax calculators without modifying the core

## Dependency Flow

```
    ┌─────────────────────────────────────────────┐
    │              API / Presentation              │
    │     FastAPI routers, middleware, schemas      │
    │                                               │
    │         Depends on: Application               │
    └──────────────────┬──────────────────────────┘
                       │
                       ▼
    ┌─────────────────────────────────────────────┐
    │              Application Layer               │
    │     Services, Use Cases, Interface Ports      │
    │                                               │
    │         Depends on: Domain                    │
    └──────────────────┬──────────────────────────┘
                       │
                       ▼
    ┌─────────────────────────────────────────────┐
    │               Domain Layer                   │
    │     Entities, Value Objects, Types            │
    │                                               │
    │         Depends on: Nothing (pure Python)     │
    └─────────────────────────────────────────────┘
                       ▲
                       │
    ┌──────────────────┴──────────────────────────┐
    │            Infrastructure Layer              │
    │     SQLAlchemy, structlog, external APIs      │
    │                                               │
    │     Implements: Application interfaces        │
    └─────────────────────────────────────────────┘
```

> **Key Principle**: Infrastructure depends on Application (via interfaces), not the other way around. This is the Dependency Inversion Principle in action.

## Layer Details

### Domain Layer (`src/taxos/domain/`)

The innermost layer containing:

- **Entities**: Core business objects with identity (`BaseEntity` with UUID + timestamps)
- **Value Objects**: Immutable domain concepts
- **Domain Types**: Shared type aliases (`EntityId`, etc.)

**Rules**: Zero external dependencies. Only Python stdlib and Pydantic for validation.

### Application Layer (`src/taxos/application/`)

Orchestrates domain logic through:

- **Services**: Business use cases (e.g., `HealthService`)
- **Interface Ports**: Abstract contracts (`AbstractRepository`) that infrastructure must implement

**Rules**: Depends only on Domain. No framework imports.

### Infrastructure Layer (`src/taxos/infrastructure/`)

Implements application ports using concrete technologies:

- **Database**: SQLAlchemy async engine, session management, generic repository
- **Logging**: structlog ↔ stdlib bridge
- **Future**: Email, cache, external API clients

**Rules**: Implements Application interfaces. Can import anything.

### API Layer (`src/taxos/api/`)

Presentation concerns:

- **Endpoints**: FastAPI route handlers
- **Schemas**: Pydantic request/response models
- **Middleware**: Request ID injection, error handling
- **Dependencies**: FastAPI `Depends()` providers

**Rules**: Depends on Application services. Never accesses Infrastructure directly.

## Repository Pattern

```
AbstractRepository[T]          (Application — interface port)
        ▲
        │  implements
        │
SQLAlchemyRepository[T]       (Infrastructure — concrete adapter)
```

All data access goes through the abstract interface. Tests can substitute in-memory implementations without touching a database.

## Dependency Injection

FastAPI's `Depends()` mechanism provides constructor injection:

```python
# deps.py — centralized providers
SettingsDep = Annotated[Settings, Depends(get_app_settings)]
DbSessionDep = Annotated[AsyncSession, Depends(get_db_session)]
HealthServiceDep = Annotated[HealthService, Depends(get_health_service)]

# endpoint — clean signatures
async def liveness(service: HealthServiceDep) -> HealthResponse:
    ...
```

## Error Handling Strategy

```
TaxOSError (base)
├── NotFoundError        → 404
├── ConflictError        → 409
├── DomainValidationError → 422
├── AuthorizationError   → 403
└── InfrastructureError  → 503
```

Domain exceptions are raised in services and automatically mapped to HTTP status codes by global exception handlers in middleware.

## Configuration Management

- **Pydantic Settings** loads from `.env` files and environment variables
- Validated at startup — fail fast on misconfiguration
- Singleton via `@lru_cache` for zero overhead
- Environment-specific behavior via `ENVIRONMENT` field

## Logging Architecture

- **structlog** provides structured, context-rich logging
- JSON output in production, colored console in development
- Request ID is bound to every log entry via contextvars
- Third-party loggers (uvicorn, sqlalchemy) are quieted

## API Versioning

Routes are prefixed with `/api/v1/`. When v2 is needed:

1. Create `src/taxos/api/v2/` with its own router and endpoints
2. Mount at `/api/v2` in `main.py`
3. v1 continues unchanged — no breaking changes

## Adding a New Tax Calculator

1. **Domain**: Create entity in `domain/entities/`
2. **Application**: Define service in `application/services/`, repository interface in `application/interfaces/`
3. **Infrastructure**: Implement ORM model in `infrastructure/database/models/`, repository in `infrastructure/database/`
4. **API**: Add schemas in `api/schemas/`, endpoints in `api/v1/endpoints/`, wire into `v1/router.py`
5. **Tests**: Unit tests for service, integration tests for endpoints
