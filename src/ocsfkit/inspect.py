from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from typing import Any

from pydantic import BaseModel, Field


class PathProfile(BaseModel):
    path: str
    count: int
    types: dict[str, int] = Field(default_factory=dict)
    examples: list[Any] = Field(default_factory=list)


def inspect_events(events: Iterable[dict[str, Any]], *, max_examples: int = 3) -> list[PathProfile]:
    counters: dict[str, Counter[str]] = {}
    counts: Counter[str] = Counter()
    examples: dict[str, list[Any]] = {}
    for event in events:
        for path, value in _walk_leaves(event):
            counts[path] += 1
            counters.setdefault(path, Counter())[_type_name(value)] += 1
            bucket = examples.setdefault(path, [])
            if len(bucket) < max_examples and value not in bucket:
                bucket.append(value)
    return [
        PathProfile(
            path=path,
            count=counts[path],
            types=dict(sorted(counters[path].items())),
            examples=examples.get(path, []),
        )
        for path in sorted(counts)
    ]


def _walk_leaves(value: Any, prefix: str = "$") -> list[tuple[str, Any]]:
    if isinstance(value, dict):
        leaves: list[tuple[str, Any]] = []
        for key, child in value.items():
            leaves.extend(_walk_leaves(child, f"{prefix}.{key}"))
        return leaves
    if isinstance(value, list):
        leaves = []
        if not value:
            return [(f"{prefix}[]", [])]
        for child in value:
            leaves.extend(_walk_leaves(child, f"{prefix}[]"))
        return leaves
    return [(prefix, value)]


def _type_name(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, int):
        return "int"
    if isinstance(value, float):
        return "float"
    if isinstance(value, str):
        return "str"
    return type(value).__name__
