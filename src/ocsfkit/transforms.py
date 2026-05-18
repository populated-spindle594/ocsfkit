from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from ocsfkit.errors import MappingError

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


TRANSFORMS = {
    "parse_timestamp": parse_timestamp,
    "severity_text_to_id": severity_text_to_id,
    "severity_id_to_text": severity_id_to_text,
}


def apply_transform(name: str, value: Any) -> Any:
    if name not in TRANSFORMS:
        raise MappingError(f"Unknown transform: {name}")
    return TRANSFORMS[name](value)

