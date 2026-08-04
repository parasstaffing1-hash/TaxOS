"""Dynamic Calculator API Factory."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, create_model

from taxos.core.exceptions import InfrastructureError
from taxos.domain.calculators.schema import CalculatorConfig


class CalculatorFactory:
    """Loads calculator configurations and generates Pydantic models dynamically."""

    def __init__(self, config_dir: str | Path = "rules/calculators") -> None:
        self.config_dir = Path(config_dir)
        self.calculators: dict[str, CalculatorConfig] = {}
        self.request_models: dict[str, type[BaseModel]] = {}
        self._load_configs()

    def _load_configs(self) -> None:
        if not self.config_dir.exists():
            self.config_dir.mkdir(parents=True, exist_ok=True)
            return

        for file_path in self.config_dir.glob("*.json"):
            try:
                data = json.loads(file_path.read_text(encoding="utf-8"))
                config = CalculatorConfig(**data)
                self.calculators[config.slug] = config
                self.request_models[config.slug] = self._create_request_model(config)
            except Exception as exc:
                raise InfrastructureError(
                    f"Invalid calculator configuration: {file_path.name}"
                ) from exc

    def _create_request_model(self, config: CalculatorConfig) -> type[BaseModel]:
        """Dynamically create a Pydantic model for request validation."""
        fields: dict[str, tuple[type, Any]] = {}

        for inp in config.inputs:
            field_type = float if inp.type in ("currency", "number", "percentage") else str
            if inp.type == "boolean":
                field_type = bool

            # Create Pydantic Field
            kwargs: dict[str, Any] = {}
            if inp.default is not None:
                kwargs["default"] = inp.default
            elif not inp.required:
                kwargs["default"] = None
                field_type = field_type | None  # type: ignore

            if inp.min_value is not None:
                kwargs["ge"] = inp.min_value
            if inp.max_value is not None:
                kwargs["le"] = inp.max_value

            # Note: create_model expects (type, Field(...))
            if kwargs and "default" not in kwargs:
                fields[inp.id] = (field_type, Field(..., **kwargs))
            else:
                fields[inp.id] = (field_type, Field(**kwargs))

        model_name = f"{config.slug.replace('-', ' ').title().replace(' ', '')}Request"
        return create_model(model_name, **fields)  # type: ignore

    def get_config(self, slug: str) -> CalculatorConfig | None:
        return self.calculators.get(slug)

    def get_request_model(self, slug: str) -> type[BaseModel] | None:
        return self.request_models.get(slug)

    def reload(self) -> None:
        """Reload all configurations from disk."""
        self.calculators.clear()
        self.request_models.clear()
        self._load_configs()

    def save_config(self, config: CalculatorConfig) -> None:
        """Save a new or updated calculator configuration to disk and reload memory."""
        if not self.config_dir.exists():
            self.config_dir.mkdir(parents=True, exist_ok=True)

        file_path = self.config_dir / f"{config.slug}.json"

        # Serialize omitting defaults to keep it clean, if desired, but model_dump_json gives a full schema
        data = config.model_dump_json(indent=2)
        file_path.write_text(data, encoding="utf-8")

        # Reload memory
        self.calculators[config.slug] = config
        self.request_models[config.slug] = self._create_request_model(config)

    def delete_config(self, slug: str) -> bool:
        """Delete a calculator configuration from disk."""
        file_path = self.config_dir / f"{slug}.json"
        if file_path.exists():
            file_path.unlink()
            if slug in self.calculators:
                del self.calculators[slug]
            if slug in self.request_models:
                del self.request_models[slug]
            return True
        return False
