from __future__ import annotations

from typing import Any

from ocsfkit.models import DiffChange


def diff_mappings(before: dict[str, Any], after: dict[str, Any]) -> list[DiffChange]:
    before_semantic = _semantic_mapping(before)
    after_semantic = _semantic_mapping(after)
    changes: list[DiffChange] = []
    _walk("", before_semantic, after_semantic, changes)
    return changes


def _semantic_mapping(mapping: dict[str, Any]) -> dict[str, Any]:
    fields = mapping.get("fields") or {}
    return {
        "schema_version": mapping.get("schema_version"),
        "ocsf_version": mapping.get("ocsf_version"),
        "requires_ocsfkit": mapping.get("requires_ocsfkit"),
        "target_class": mapping.get("target_class") or {},
        "fields": {
            str(target): _semantic_field(spec)
            for target, spec in sorted(fields.items())
            if isinstance(spec, dict)
        },
        "drop": sorted(mapping.get("drop") or []),
        "custom_transforms": sorted(mapping.get("custom_transforms") or []),
    }


def _semantic_field(spec: dict[str, Any]) -> dict[str, Any]:
    if "foreach" in spec:
        return {"foreach": spec["foreach"]}
    return {
        key: spec.get(key)
        for key in ("from", "transform", "default", "guess", "required")
        if key in spec
    }


def _walk(path: str, before: Any, after: Any, changes: list[DiffChange]) -> None:
    if isinstance(before, dict) and isinstance(after, dict):
        for key in sorted(set(before) | set(after)):
            child_path = f"{path}.{key}" if path else key
            if key not in before:
                changes.append(DiffChange(path=child_path, after=after[key], kind="added"))
            elif key not in after:
                changes.append(DiffChange(path=child_path, before=before[key], kind="removed"))
            else:
                _walk(child_path, before[key], after[key], changes)
        return
    if isinstance(before, list) and isinstance(after, list):
        if before != after:
            changes.append(DiffChange(path=path, before=before, after=after, kind="changed"))
        return
    if before != after:
        changes.append(DiffChange(path=path, before=before, after=after, kind="changed"))
