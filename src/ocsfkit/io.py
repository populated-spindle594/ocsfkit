from __future__ import annotations

import json
import sys
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import yaml

from ocsfkit.errors import InputLoadError


def _read_text(input_path: str) -> tuple[str, str]:
    if input_path == "-":
        return sys.stdin.read(), "stdin"
    path = Path(input_path)
    try:
        return path.read_text(), path.suffix.lower()
    except OSError as exc:
        raise InputLoadError(f"Could not read {input_path}: {exc}") from exc


def load_events(input_path: str) -> list[dict[str, Any]]:
    return list(iter_events(input_path))


def iter_events(input_path: str) -> Iterator[dict[str, Any]]:
    if input_path != "-" and Path(input_path).suffix.lower() == ".ndjson":
        yield from _iter_ndjson_file(Path(input_path))
        return
    text, suffix = _read_text(input_path)
    if not text.strip():
        raise InputLoadError("Input is empty")
    try:
        if suffix in {".yaml", ".yml"}:
            loaded = yaml.safe_load(text)
            yield from _coerce_events(loaded)
            return
        if suffix == ".ndjson":
            yield from _load_ndjson(text)
            return
        try:
            loaded = json.loads(text)
            yield from _coerce_events(loaded)
            return
        except json.JSONDecodeError:
            yield from _load_ndjson(text)
            return
    except (yaml.YAMLError, json.JSONDecodeError) as exc:
        raise InputLoadError(f"Could not parse input: {exc}") from exc


def _iter_ndjson_file(path: Path) -> Iterator[dict[str, Any]]:
    found = False
    try:
        with path.open() as handle:
            for line_number, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                found = True
                try:
                    value = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise InputLoadError(f"Invalid NDJSON on line {line_number}: {exc}") from exc
                if not isinstance(value, dict):
                    raise InputLoadError(f"NDJSON line {line_number} is not a JSON object")
                yield value
    except OSError as exc:
        raise InputLoadError(f"Could not read {path}: {exc}") from exc
    if not found:
        raise InputLoadError("No events found in NDJSON input")


def _load_ndjson(text: str) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise InputLoadError(f"Invalid NDJSON on line {line_number}: {exc}") from exc
        if not isinstance(value, dict):
            raise InputLoadError(f"NDJSON line {line_number} is not a JSON object")
        events.append(value)
    if not events:
        raise InputLoadError("No events found in NDJSON input")
    return events


def _coerce_events(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, dict):
        return [value]
    if isinstance(value, list) and all(isinstance(item, dict) for item in value):
        return value
    raise InputLoadError("Input must be a JSON/YAML object, array of objects, or NDJSON objects")


def load_mapping_file(mapping_path: str) -> dict[str, Any]:
    path = Path(mapping_path)
    try:
        value = yaml.safe_load(path.read_text())
    except OSError as exc:
        raise InputLoadError(f"Could not read mapping {mapping_path}: {exc}") from exc
    except yaml.YAMLError as exc:
        raise InputLoadError(f"Could not parse mapping {mapping_path}: {exc}") from exc
    if not isinstance(value, dict):
        raise InputLoadError("Mapping file must contain a YAML object")
    return value
