from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

from ocsfkit.errors import MappingError, QueryError


@dataclass(frozen=True)
class PathToken:
    key: str
    is_array: bool = False
    index: int | None = None
    wildcard: bool = False
    filter_key: str | None = None
    filter_value: str | None = None


def parse_dotted_path(path: str) -> list[PathToken]:
    if not path or path.startswith(".") or path.endswith("."):
        raise MappingError(f"Invalid target path: {path!r}")
    tokens: list[PathToken] = []
    for part in path.split("."):
        if not part:
            raise MappingError(f"Invalid target path: {path!r}")
        if part.endswith("[*]"):
            key = part[:-3]
            if not key:
                raise MappingError(f"Invalid wildcard target path segment: {part!r}")
            tokens.append(PathToken(key=key, is_array=True, wildcard=True))
        elif part.endswith("[]"):
            key = part[:-2]
            if not key:
                raise MappingError(f"Invalid array target path segment: {part!r}")
            tokens.append(PathToken(key=key, is_array=True))
        elif "[" in part and part.endswith("]"):
            key, selector = part.split("[", 1)
            selector = selector[:-1]
            if not key:
                raise MappingError(f"Invalid array path segment: {part!r}")
            if selector.isdigit():
                tokens.append(PathToken(key=key, is_array=True, index=int(selector)))
            elif selector.startswith("?") and "==" in selector:
                filter_key, filter_value = selector[1:].split("==", 1)
                tokens.append(
                    PathToken(
                        key=key,
                        is_array=True,
                        filter_key=filter_key.strip(),
                        filter_value=filter_value.strip().strip("'\""),
                    )
                )
            else:
                raise MappingError(f"Unsupported array selector: {part!r}")
        elif "[]" in part:
            raise MappingError(f"Array marker is only supported at the end of a segment: {part!r}")
        else:
            tokens.append(PathToken(key=part))
    return tokens


def set_dotted(target: dict[str, Any], path: str, value: Any) -> None:
    tokens = parse_dotted_path(path)
    cursor: Any = target
    for index, token in enumerate(tokens):
        last = index == len(tokens) - 1
        if isinstance(cursor, list) and not token.is_array:
            _assign_list_segment(cursor, token.key, value, last)
            if last:
                return
            cursor = cursor[0]
            continue
        if token.is_array:
            if token.key not in cursor or not isinstance(cursor[token.key], list):
                cursor[token.key] = []
            if last:
                cursor[token.key] = value if isinstance(value, list) else [value]
                return
            if not cursor[token.key] or not isinstance(cursor[token.key][0], dict):
                cursor[token.key] = [{}]
            cursor = cursor[token.key]
            continue
        if last:
            cursor[token.key] = value
            return
        next_token = tokens[index + 1]
        if token.key not in cursor or not isinstance(cursor[token.key], dict | list):
            cursor[token.key] = [] if next_token.is_array else {}
        cursor = cursor[token.key]


def _assign_list_segment(items: list[Any], key: str, value: Any, last: bool) -> None:
    if not items:
        items.append({})
    if not all(isinstance(item, dict) for item in items):
        items.clear()
        items.append({})
    if last:
        values = value if isinstance(value, list) else [value] * len(items)
        while len(items) < len(values):
            items.append({})
        for item, item_value in zip(items, values, strict=False):
            item[key] = item_value
        return
    first = items[0]
    if key not in first or not isinstance(first[key], dict):
        first[key] = {}


def get_dotted(source: dict[str, Any], path: str) -> Any:
    tokens = parse_dotted_path(path)
    cursor: Any = source
    for token in tokens:
        if token.is_array:
            if not isinstance(cursor, dict) or token.key not in cursor:
                return None
            value = cursor[token.key]
            if not isinstance(value, list):
                return None
            if token.index is not None:
                cursor = value[token.index] if token.index < len(value) else None
            elif token.filter_key is not None:
                cursor = [
                    item
                    for item in value
                    if isinstance(item, dict)
                    and str(item.get(token.filter_key)) == token.filter_value
                ]
            else:
                cursor = value
            continue
        if isinstance(cursor, list):
            cursor = [
                item.get(token.key)
                for item in cursor
                if isinstance(item, dict) and token.key in item
            ]
        elif isinstance(cursor, dict) and token.key in cursor:
            cursor = cursor[token.key]
        else:
            return None
    return cursor


def extract_json_path(source: dict[str, Any], path: str) -> Any:
    if path == "$":
        return source
    if not path.startswith("$."):
        raise MappingError(f"Only JSONPath expressions like $.a.b are supported: {path!r}")
    return get_dotted(source, path[2:])


def flatten_paths(value: Any, prefix: str = "$") -> set[str]:
    paths: set[str] = set()
    if isinstance(value, dict):
        for key, child in value.items():
            child_prefix = f"{prefix}.{key}"
            paths.add(child_prefix)
            paths.update(flatten_paths(child, child_prefix))
    elif isinstance(value, list):
        for child in value:
            paths.update(flatten_paths(child, f"{prefix}[]"))
    return paths


def leaf_paths(value: Any, prefix: str = "") -> set[str]:
    paths: set[str] = set()
    if isinstance(value, dict):
        for key, child in value.items():
            child_prefix = f"{prefix}.{key}" if prefix else key
            paths.update(leaf_paths(child, child_prefix))
    elif isinstance(value, list):
        for child in value:
            paths.update(leaf_paths(child, f"{prefix}[]"))
    elif prefix:
        paths.add(prefix)
    return paths


def common_parent_paths(paths: Iterable[str]) -> set[str]:
    parents: set[str] = set()
    for path in paths:
        bits = path.split(".")
        for end in range(1, len(bits)):
            parents.add(".".join(bits[:end]))
    return parents


def query_field(event: dict[str, Any], expression: str) -> Any:
    if expression.startswith("$."):
        expression = expression[2:]
    if not expression or expression.startswith("."):
        raise QueryError(f"Invalid query expression: {expression!r}")
    return get_dotted(event, expression)
