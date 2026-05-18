from __future__ import annotations

from typing import Any

from ocsfkit.models import DiffChange
from ocsfkit.transforms import SEVERITY_ID_TO_TEXT


def diff_events(before: dict[str, Any], after: dict[str, Any]) -> list[DiffChange]:
    changes: list[DiffChange] = []
    _walk("", before, after, changes)
    _add_enum_context(changes)
    return changes


def _walk(path: str, before: Any, after: Any, changes: list[DiffChange]) -> None:
    if isinstance(before, dict) and isinstance(after, dict):
        keys = sorted(set(before) | set(after))
        for key in keys:
            child_path = f"{path}.{key}" if path else key
            if key not in before:
                changes.append(DiffChange(path=child_path, after=after[key], kind="added"))
            elif key not in after:
                changes.append(DiffChange(path=child_path, before=before[key], kind="removed"))
            else:
                _walk(child_path, before[key], after[key], changes)
        return
    if isinstance(before, list) and isinstance(after, list):
        common = min(len(before), len(after))
        for index in range(common):
            _walk(f"{path}[{index}]", before[index], after[index], changes)
        for index in range(common, len(before)):
            changes.append(
                DiffChange(path=f"{path}[{index}]", before=before[index], kind="removed")
            )
        for index in range(common, len(after)):
            changes.append(DiffChange(path=f"{path}[{index}]", after=after[index], kind="added"))
        return
    if before != after:
        changes.append(DiffChange(path=path, before=before, after=after, kind="changed"))


def _add_enum_context(changes: list[DiffChange]) -> None:
    for change in changes:
        if change.path == "severity_id":
            change.before = _severity_label(change.before)
            change.after = _severity_label(change.after)


def _severity_label(value: Any) -> Any:
    if isinstance(value, int) and value in SEVERITY_ID_TO_TEXT:
        return {"id": value, "name": SEVERITY_ID_TO_TEXT[value]}
    return value
