from __future__ import annotations

import importlib.util
from datetime import datetime, timezone
from importlib.metadata import entry_points
from pathlib import Path
from typing import Any

from ocsfkit.errors import MappingError
from ocsfkit.transform_packs import TRANSFORM_PACKS

SEVERITY_TEXT_TO_ID = {
    "unknown": 0,
    "informational": 1,
    "info": 1,
    "low": 2,
    "medium": 3,
    "high": 4,
    "critical": 5,
    "fatal": 6,
}

SEVERITY_ID_TO_TEXT = {
    0: "Unknown",
    1: "Informational",
    2: "Low",
    3: "Medium",
    4: "High",
    5: "Critical",
    6: "Fatal",
}


def parse_timestamp(value: Any) -> int:
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if not isinstance(value, str) or not value.strip():
        raise MappingError(f"Cannot parse timestamp from {value!r}")
    raw = value.strip()
    if raw.isdigit():
        return int(raw)
    normalized = raw.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise MappingError(f"Cannot parse timestamp from {value!r}") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return int(parsed.timestamp() * 1000)


def severity_text_to_id(value: Any) -> int:
    if isinstance(value, int):
        return value
    key = str(value).strip().lower()
    if key not in SEVERITY_TEXT_TO_ID:
        raise MappingError(f"Unknown severity text: {value!r}")
    return SEVERITY_TEXT_TO_ID[key]


def severity_id_to_text(value: Any) -> str:
    try:
        return SEVERITY_ID_TO_TEXT[int(value)]
    except (ValueError, KeyError) as exc:
        raise MappingError(f"Unknown severity id: {value!r}") from exc


def to_string(value: Any) -> str:
    return str(value)


def to_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise MappingError(f"Cannot convert {value!r} to int") from exc


def lower(value: Any) -> str:
    return str(value).lower()


def upper(value: Any) -> str:
    return str(value).upper()


def title_case(value: Any) -> str:
    return str(value).title()


def epoch_seconds_to_ms(value: Any) -> int:
    return to_int(value) * 1000


TRANSFORMS = {
    "parse_timestamp": parse_timestamp,
    "severity_text_to_id": severity_text_to_id,
    "severity_id_to_text": severity_id_to_text,
    "to_string": to_string,
    "to_int": to_int,
    "lower": lower,
    "upper": upper,
    "title_case": title_case,
    "epoch_seconds_to_ms": epoch_seconds_to_ms,
}


def apply_transform(name: str, value: Any, transforms: dict[str, Any] | None = None) -> Any:
    registry = TRANSFORMS | TRANSFORM_PACKS | load_entry_point_transforms() | (transforms or {})
    if name not in registry:
        raise MappingError(f"Unknown transform: {name}")
    return registry[name](value)


def load_entry_point_transforms() -> dict[str, Any]:
    loaded: dict[str, Any] = {}
    for entry_point in entry_points(group="ocsfkit.transforms"):
        func = entry_point.load()
        if not callable(func):
            raise MappingError(f"Transform entry point is not callable: {entry_point.name}")
        loaded[entry_point.name] = func
    return loaded


def load_custom_transforms(paths: list[str], base_dir: Path | None = None) -> dict[str, Any]:
    loaded: dict[str, Any] = {}
    for raw_path in paths:
        path = Path(raw_path)
        if not path.is_absolute() and base_dir is not None:
            path = base_dir / path
        if not path.exists():
            raise MappingError(f"Custom transform file does not exist: {path}")
        module_name = f"ocsfkit_custom_transforms_{abs(hash(path))}"
        spec = importlib.util.spec_from_file_location(module_name, path)
        if spec is None or spec.loader is None:
            raise MappingError(f"Could not load custom transform file: {path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module_transforms = getattr(module, "TRANSFORMS", None)
        if not isinstance(module_transforms, dict):
            raise MappingError(f"{path} must define a TRANSFORMS dictionary")
        for name, func in module_transforms.items():
            if not isinstance(name, str) or not callable(func):
                raise MappingError(f"Invalid custom transform entry in {path}: {name!r}")
            loaded[name] = func
    return loaded
