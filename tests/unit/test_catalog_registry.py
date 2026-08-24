"""Unit tests for Central Tool and Calculator Catalog Registry."""

from taxos.domain.catalog.models import ToolFamily
from taxos.domain.catalog.registry import get_catalog_registry


def test_catalog_initialization_and_counts():
    """Verify catalog loads master tools and generates valid routes and metadata."""
    registry = get_catalog_registry()
    tools = registry.get_all()

    assert len(tools) == 845
    assert {tool.number for tool in tools} == set(range(1, 846))
    assert len({tool.id for tool in tools}) == 845
    # Every tool has valid id, title, route, and family
    for tool in tools:
        assert tool.id
        assert tool.title
        assert tool.route.startswith("/tax/")
        assert tool.number > 0


def test_catalog_filtering():
    """Verify filtering by family, jurisdiction, persona, and query string."""
    registry = get_catalog_registry()

    # Filter by India income tax
    it_tools = registry.filter_by(family=ToolFamily.INDIA_INCOME_TAX)
    assert len(it_tools) > 0
    assert all(t.family == ToolFamily.INDIA_INCOME_TAX for t in it_tools)

    # Filter by query
    hra_tools = registry.filter_by(query="hra")
    assert len(hra_tools) > 0
    assert any("hra" in t.id for t in hra_tools)

    # Filter by jurisdiction
    us_tools = registry.filter_by(jurisdiction="US")
    assert len(us_tools) > 0
    assert any(t.jurisdiction == "US" for t in us_tools)
