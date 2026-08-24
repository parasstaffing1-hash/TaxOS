"""Tests verifying specifications and schemas for all 845 catalog tools."""

from __future__ import annotations

from taxos.domain.catalog.master_plan import MASTER_PLAN_TOOL_NAMES
from taxos.domain.catalog.models import ImplementationStatus
from taxos.domain.catalog.registry import get_catalog_registry
from taxos.domain.catalog.tool_specifications import get_master_spec_registry


def test_all_845_tools_have_specifications():
    """Verify that every single tool from the master plan has a valid specification."""
    spec_registry = get_master_spec_registry()
    all_specs = spec_registry.get_all_specs()

    assert len(all_specs) == len(MASTER_PLAN_TOOL_NAMES)
    assert len(all_specs) == 845

    for spec in all_specs:
        assert spec.number in MASTER_PLAN_TOOL_NAMES
        assert spec.title == MASTER_PLAN_TOOL_NAMES[spec.number]
        assert spec.tool_id
        assert spec.family
        assert spec.jurisdiction
        assert len(spec.input_fields) >= 1
        assert len(spec.official_sources) >= 1
        assert spec.handler_key in (
            "india_deductions",
            "india_house_property",
            "india_business",
            "india_tcs",
            "india_corporate",
            "global_tax",
            "generic_financial",
        )


def test_catalog_registry_tools_are_complete():
    """Verify that the central catalog registry marks all 845 tools as complete."""
    catalog = get_catalog_registry()
    tools = catalog.get_all()

    assert len(tools) == 845
    for tool in tools:
        assert tool.status == ImplementationStatus.COMPLETE
        assert tool.api_endpoint is not None
        assert tool.route is not None
