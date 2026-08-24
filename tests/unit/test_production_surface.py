"""Production API surface regression tests."""

from __future__ import annotations

from taxos.core.config import Settings


def _route_paths(routes):
    for route in routes:
        path = getattr(route, "path", None)
        if isinstance(path, str):
            yield path
        nested_routes = getattr(route, "routes", None)
        if nested_routes:
            yield from _route_paths(nested_routes)


def test_production_hides_docs_and_internal_operational_routes(monkeypatch) -> None:
    import taxos.main as main

    settings = Settings(
        ENVIRONMENT="production",
        DATABASE_URL="sqlite+aiosqlite:///",
        SECRET_KEY="a-production-secret-key-that-is-longer-than-32-characters",
        FIELD_ENCRYPTION_KEY="a-production-field-key-that-is-longer-than-32-chars",
        ALLOWED_ORIGINS=["https://taxos.example"],
        ENABLE_INTERNAL_TOOLS=False,
    )
    monkeypatch.setattr(main, "get_settings", lambda: settings)

    app = main.create_app()
    route_paths = set(_route_paths(app.routes))

    assert app.docs_url is None
    assert app.redoc_url is None
    assert app.openapi_url is None
    assert not any(path.startswith("/api/v1/analytics") for path in route_paths)
    assert not any(path.startswith("/api/v1/updater") for path in route_paths)
    assert not any(path.startswith("/api/v1/verification") for path in route_paths)
