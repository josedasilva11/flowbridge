"""Field mapping and transform engine driven by the YAML config.

Incoming payloads are first remapped to canonical field names, then each
field has an ordered list of transforms applied to it.
"""

from __future__ import annotations

from typing import Any


def _apply_single(value: str, transform: Any) -> str:
    """Apply one transform step to a string value.

    Args:
        value: The current string value (may be empty).
        transform: Either a string name (strip, lower, upper, title) or a
            single-key dict like {"default": "web"}.

    Returns:
        The transformed string value.
    """
    if isinstance(transform, dict):
        if "default" in transform and not value.strip():
            return str(transform["default"])
        return value
    if transform == "strip":
        return value.strip()
    if transform == "lower":
        return value.lower()
    if transform == "upper":
        return value.upper()
    if transform == "title":
        return value.title()
    raise ValueError(f"Unknown transform: {transform!r}")


def apply_mapping(raw: dict[str, Any], mapping: dict[str, str]) -> dict[str, str]:
    """Remap raw incoming keys to canonical keys.

    Args:
        raw: The raw incoming payload as a dict.
        mapping: A dict of incoming_key to canonical_key.

    Returns:
        A dict keyed by canonical field names with string values.
    """
    result: dict[str, str] = {}
    for incoming_key, canonical_key in mapping.items():
        value = raw.get(incoming_key)
        result[canonical_key] = "" if value is None else str(value)
    return result


def apply_transforms(
    fields: dict[str, str], transforms: dict[str, list[Any]]
) -> dict[str, str]:
    """Apply the configured ordered transforms to each canonical field.

    Args:
        fields: Canonical fields after mapping.
        transforms: A dict of field name to an ordered list of transform steps.

    Returns:
        A new dict with transforms applied. Fields without a transform list
        are passed through unchanged.
    """
    result = dict(fields)
    for field, steps in transforms.items():
        value = result.get(field, "")
        for step in steps:
            value = _apply_single(value, step)
        result[field] = value
    return result
