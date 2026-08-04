"""Dynamic Calculators Endpoints."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request

from taxos.api.dependencies.auth import get_current_admin
from taxos.api.v1.deps import get_salary_calculator_service
from taxos.application.calculators.evaluator import evaluate_calculator
from taxos.application.calculators.factory import CalculatorFactory
from taxos.application.services.salary_calculator import SalaryCalculatorService
from taxos.domain.calculators.schema import CalculatorConfig
from taxos.infrastructure.database.models.iam import User

router = APIRouter(tags=["dynamic-calculators"])

# Global factory instance loaded at startup
calculator_factory = CalculatorFactory()


def get_factory() -> CalculatorFactory:
    """Dependency to inject the factory."""
    return calculator_factory


@router.get("/", response_model=list[CalculatorConfig])
async def list_calculators(
    factory: CalculatorFactory = Depends(get_factory),
) -> list[CalculatorConfig]:
    """Returns a list of all dynamic calculators."""
    return list(factory.calculators.values())


@router.post("/", response_model=CalculatorConfig)
async def create_calculator(
    config: CalculatorConfig,
    factory: CalculatorFactory = Depends(get_factory),
    _: User = Depends(get_current_admin),
) -> CalculatorConfig:
    """Creates a new calculator configuration."""
    if factory.get_config(config.slug):
        raise HTTPException(status_code=400, detail="Calculator with this slug already exists.")
    factory.save_config(config)
    return config


@router.put("/{slug}", response_model=CalculatorConfig)
async def update_calculator(
    slug: str,
    config: CalculatorConfig,
    factory: CalculatorFactory = Depends(get_factory),
    _: User = Depends(get_current_admin),
) -> CalculatorConfig:
    """Updates an existing calculator configuration."""
    if config.slug != slug:
        raise HTTPException(status_code=400, detail="Slug in path must match slug in body.")
    if not factory.get_config(slug):
        raise HTTPException(status_code=404, detail="Calculator not found.")
    factory.save_config(config)
    return config


@router.delete("/{slug}", status_code=204)
async def delete_calculator(
    slug: str,
    factory: CalculatorFactory = Depends(get_factory),
    _: User = Depends(get_current_admin),
) -> None:
    """Deletes a calculator configuration."""
    if not factory.delete_config(slug):
        raise HTTPException(status_code=404, detail="Calculator not found.")


@router.get("/{slug}/config", response_model=CalculatorConfig)
async def get_calculator_config(
    slug: str, factory: CalculatorFactory = Depends(get_factory)
) -> CalculatorConfig:
    """Returns the UI schema configuration for a specific calculator."""
    config = factory.get_config(slug)
    if not config:
        raise HTTPException(status_code=404, detail="Calculator not found")
    return config


@router.post("/{slug}/calculate")
async def calculate(
    slug: str,
    request: Request,
    factory: CalculatorFactory = Depends(get_factory),
    salary_service: SalaryCalculatorService = Depends(get_salary_calculator_service),
) -> dict[str, Any]:
    """Dynamically validates and calculates based on the config."""
    config = factory.get_config(slug)
    model_cls = factory.get_request_model(slug)

    if not config or not model_cls:
        raise HTTPException(status_code=404, detail="Calculator not found")

    # Dynamically parse and validate body using the generated Pydantic model
    try:
        body = await request.json()
    except Exception:
        body = {}

    try:
        validated_data = model_cls(**body)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    # Evaluate formulas
    try:
        results = await evaluate_calculator(config, validated_data.model_dump(), salary_service)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Calculation could not be completed") from exc

    return {"results": results}
