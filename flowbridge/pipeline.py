"""The core pipeline: load config, validate, transform, and dispatch.

This module ties the models, transform engine, and actions together. Both
the FastAPI app and the demo script call process_lead.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from .actions import dispatch
from .models import IncomingLead, ProcessedLead
from .transforms import apply_mapping, apply_transforms

CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.yaml"


@lru_cache(maxsize=1)
def load_config(path: str | None = None) -> dict[str, Any]:
    """Load and cache the YAML config.

    Args:
        path: Optional override path to the config file.

    Returns:
        The parsed config as a dict.
    """
    config_file = Path(path) if path else CONFIG_PATH
    with config_file.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def process_lead(raw: dict[str, Any]) -> dict[str, Any]:
    """Run one raw lead payload through the full pipeline.

    Args:
        raw: The raw incoming payload as a dict.

    Returns:
        A dict with the processed lead and the per-action results.
    """
    config = load_config()
    # Validate the raw payload against the incoming schema.
    validated = IncomingLead(**raw)
    # Map raw keys to canonical keys, then apply transforms.
    mapped = apply_mapping(validated.model_dump(), config["mapping"])
    transformed = apply_transforms(mapped, config.get("transforms", {}))
    # Coerce into the processed schema to guarantee the canonical shape.
    processed = ProcessedLead(**transformed).model_dump()
    results = dispatch(processed, config.get("actions", []))
    return {"lead": processed, "results": results}
