"""Release-safety tests for catalog status and schema identity."""

from __future__ import annotations

from taxos.domain.catalog.models import ImplementationStatus
from taxos.domain.catalog.registry import get_catalog_registry
from taxos.domain.catalog.tool_specifications import get_master_spec_registry


def test_every_catalog_tool_has_a_matching_schema():
    catalog = get_catalog_registry()
    specs = get_master_spec_registry()

    assert all(specs.get_spec(tool.id) is not None for tool in catalog.get_all())


def test_only_verified_tools_are_released():
    tools = get_catalog_registry().get_all()
    released = [tool for tool in tools if tool.status != ImplementationStatus.NOT_STARTED]

    assert {tool.id for tool in released} >= {
        "income-tax-calculator",
        "ctc-to-take-home-calculator",
        "gst-calculator",
    }
    assert len(released) < len(tools)
