"""Tool & Calculator Catalog API Endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body, HTTPException, Query

from taxos.application.tools.executor import get_universal_tool_executor
from taxos.domain.catalog.models import (
    ImplementationStatus,
    TaxTool,
    ToolFamily,
    ToolPersona,
    ToolType,
)
from taxos.domain.catalog.registry import get_catalog_registry
from taxos.domain.catalog.tool_specifications import get_master_spec_registry

router = APIRouter(prefix="/catalog", tags=["Tool Catalog"])


@router.get("", response_model=list[TaxTool])
async def list_catalog_tools(  # noqa: PLR0917
    family: ToolFamily | None = Query(default=None, description="Filter by tool family"),
    jurisdiction: str | None = Query(default=None, description="Country code e.g. IN, US, GB"),
    persona: ToolPersona | None = Query(default=None, description="Filter by user persona"),
    query: str | None = Query(default=None, description="Search keyword in title/tags"),
    limit: int = Query(default=50, ge=1, le=850),
    offset: int = Query(default=0, ge=0),
) -> list[TaxTool]:
    """Search and browse all 845+ TaxOS tools, calculators, validators, and analyzers."""
    registry = get_catalog_registry()
    return registry.filter_by(
        family=family,
        jurisdiction=jurisdiction,
        persona=persona,
        query=query,
        limit=limit,
        offset=offset,
    )


@router.get("/stats")
async def get_catalog_stats() -> dict[str, int | float]:
    """Get total counts and coverage statistics."""
    registry = get_catalog_registry()
    all_tools = registry.get_all()
    complete = sum(1 for t in all_tools if t.status == ImplementationStatus.COMPLETE)
    partial = sum(1 for t in all_tools if t.status == ImplementationStatus.PARTIAL)
    not_started = sum(1 for t in all_tools if t.status == ImplementationStatus.NOT_STARTED)
    return {
        "total_tools": len(all_tools),
        "catalog_target": 845,
        "catalog_coverage_percent": round(len(all_tools) / 845 * 100, 2),
        "complete_tools": complete,
        "partial_tools": partial,
        "not_started_tools": not_started,
        "india_tools_count": sum(1 for t in all_tools if t.jurisdiction == "IN"),
        "global_tools_count": sum(1 for t in all_tools if t.jurisdiction != "IN"),
        "calculators_count": sum(1 for t in all_tools if t.tool_type == ToolType.CALCULATOR),
        "validators_count": sum(
            1 for t in all_tools if t.tool_type in (ToolType.VALIDATOR, ToolType.CHECKER)
        ),
    }


@router.get("/families")
async def list_catalog_families() -> list[dict[str, str | int]]:
    """Return family counts for hub pages and navigation."""
    tools = get_catalog_registry().get_all()
    counts: dict[str, int] = {}
    for tool in tools:
        counts[tool.family.value] = counts.get(tool.family.value, 0) + 1
    return [{"family": family, "count": count} for family, count in sorted(counts.items())]


@router.get("/{tool_id}", response_model=TaxTool)
async def get_tool_by_id(tool_id: str) -> TaxTool:
    """Retrieve metadata and schema for a specific catalog tool."""
    registry = get_catalog_registry()
    tool = registry.get_by_id(tool_id)
    if not tool:
        raise HTTPException(
            status_code=404, detail=f"Tool with id '{tool_id}' not found in catalog."
        )
    return tool


@router.get("/{tool_id}/schema")
async def get_tool_schema(tool_id: str) -> dict[str, Any]:
    """Retrieve the interactive UI input schema and legal source references for a tool."""
    spec = get_master_spec_registry().get_spec(tool_id)
    if not spec:
        raise HTTPException(
            status_code=404, detail=f"Tool specification for '{tool_id}' not found."
        )
    return spec.model_dump()


@router.post("/{tool_id}/calculate")
async def calculate_catalog_tool(
    tool_id: str,
    payload: dict[str, Any] = Body(default_factory=dict),
    tax_year: str = Query(default="2024-25"),
) -> dict[str, Any]:
    """Execute authoritative tax calculation for any of the 845 catalog tools."""
    try:
        executor = get_universal_tool_executor()
        result = executor.execute_tool(tool_id=tool_id, payload=payload, tax_year=tax_year)
        return result.model_dump()
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=422, detail=f"Calculation error for tool '{tool_id}': {exc}"
        ) from exc
