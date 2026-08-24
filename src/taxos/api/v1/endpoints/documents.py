"""Document generation API endpoints.

Exposes endpoints to generate, preview, and download documents
for any dynamic calculator. Also provides template CRUD for the admin panel.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel, Field, ValidationError

from taxos.api.dependencies.auth import get_current_admin
from taxos.api.v1.deps import get_salary_calculator_service
from taxos.api.v1.endpoints.dynamic_calculators import calculator_factory as _calc_factory
from taxos.application.calculators.evaluator import evaluate_calculator
from taxos.application.calculators.factory import CalculatorFactory
from taxos.application.documents.engine import DocumentEngine, ExportFormat
from taxos.application.documents.template_registry import TemplateRegistry
from taxos.application.services.salary_calculator import SalaryCalculatorService
from taxos.domain.documents.extractor import (
    DocumentExtractionEngine,
    DocumentExtractionResult,
    DocumentType,
)
from taxos.domain.documents.schema import ReportTemplateConfig
from taxos.infrastructure.database.models.iam import User

router = APIRouter(prefix="/documents", tags=["documents"])

# Singletons — initialized at module load
_doc_engine = DocumentEngine()
_template_registry = TemplateRegistry()
_extractor = DocumentExtractionEngine()


def _get_factory() -> CalculatorFactory:
    return _calc_factory


def _get_registry() -> TemplateRegistry:
    return _template_registry


# ── Document Generation ─────────────────────────────────────────


class GenerateRequest(BaseModel):
    """Parsed from the JSON body of the generate endpoint."""

    format: ExportFormat = "pdf"
    template_id: str = "default"
    inputs: dict[str, Any] = Field(default_factory=dict)


@router.post("/extract", response_model=DocumentExtractionResult)
async def extract_tax_document(
    file: UploadFile = File(...),
    document_type: DocumentType | None = Form(default=None),
) -> DocumentExtractionResult:
    """Safely extract reviewable fields from CSV, JSON, PDF, and text documents."""
    filename = file.filename or "uploaded-document"
    content_type = file.content_type or "application/octet-stream"
    payload = await file.read(DocumentExtractionEngine.MAX_BYTES + 1)
    try:
        return _extractor.extract(
            filename=filename,
            content_type=content_type,
            payload=payload,
            document_type=document_type,
        )
    except ValueError as exc:
        raise HTTPException(status_code=413, detail=str(exc)) from exc


@router.post("/{slug}/generate")
async def generate_document(
    slug: str,
    request: Request,
    factory: CalculatorFactory = Depends(_get_factory),
    salary_service: SalaryCalculatorService = Depends(get_salary_calculator_service),
) -> Response:
    """Generate a document for a calculator.

    Accepts a JSON body with:
    - ``format``: pdf | excel | csv | json | html | xml | markdown | text
    - ``template_id``: Report template ID (default: "default")
    - ``inputs``: Calculator input values (same as /calculate endpoint)
    """
    config = factory.get_config(slug)
    model_cls = factory.get_request_model(slug)
    if not config or not model_cls:
        raise HTTPException(status_code=404, detail="Calculator not found")

    try:
        body = await request.json()
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid JSON body") from exc

    try:
        req = GenerateRequest.model_validate(body)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail="Invalid document request") from exc

    # Validate inputs
    inputs_data = req.inputs
    try:
        validated = model_cls(**inputs_data)
        inputs_data = validated.model_dump()
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Input validation failed: {exc}") from exc

    # Run calculator
    try:
        results = await evaluate_calculator(config, inputs_data, salary_service)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Calculation could not be completed") from exc

    # Get template
    template = _template_registry.get(req.template_id) or _template_registry.get_default()

    # Generate document
    try:
        doc_bytes = _doc_engine.generate(
            format=req.format,
            calculator_config=config,
            results=results,
            template=template,
            inputs_data=inputs_data,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Document generation failed") from exc

    mime = _doc_engine.get_mime_type(req.format)
    ext = _doc_engine.get_file_extension(req.format)
    filename = f"{slug}-report{ext}"

    return Response(
        content=doc_bytes,
        media_type=mime,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-Report-Template": template.id,
        },
    )


# ── Template CRUD ────────────────────────────────────────────────


@router.get("/templates")
async def list_templates(
    registry: TemplateRegistry = Depends(_get_registry),
) -> list[dict[str, Any]]:
    """List all available report templates."""
    return [
        {"id": t.id, "name": t.name, "description": t.description, "style": t.template_style}
        for t in registry.list_all()
    ]


@router.get("/templates/{template_id}", response_model=ReportTemplateConfig)
async def get_template(
    template_id: str,
    registry: TemplateRegistry = Depends(_get_registry),
) -> ReportTemplateConfig:
    """Get a specific template configuration."""
    template = registry.get(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template


@router.post("/templates", response_model=ReportTemplateConfig)
async def create_template(
    template: ReportTemplateConfig,
    registry: TemplateRegistry = Depends(_get_registry),
    _: User = Depends(get_current_admin),
) -> ReportTemplateConfig:
    """Create a new report template."""
    if registry.get(template.id):
        raise HTTPException(status_code=400, detail="Template with this ID already exists")
    registry.save(template)
    return template


@router.put("/templates/{template_id}", response_model=ReportTemplateConfig)
async def update_template(
    template_id: str,
    template: ReportTemplateConfig,
    registry: TemplateRegistry = Depends(_get_registry),
    _: User = Depends(get_current_admin),
) -> ReportTemplateConfig:
    """Update an existing report template."""
    if template.id != template_id:
        raise HTTPException(status_code=400, detail="Template ID in path must match body")
    registry.save(template)
    return template


@router.delete("/templates/{template_id}", status_code=204, response_model=None)
async def delete_template(
    template_id: str,
    registry: TemplateRegistry = Depends(_get_registry),
    _: User = Depends(get_current_admin),
) -> None:
    """Delete a report template."""
    if not registry.delete(template_id):
        raise HTTPException(status_code=404, detail="Template not found or cannot be deleted")
