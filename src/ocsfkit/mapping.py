from __future__ import annotations

from typing import Any

from ocsfkit.errors import MappingError
from ocsfkit.models import FieldDecision, MappingExplanation, MappingResult
from ocsfkit.paths import append_dotted, extract_json_path, flatten_paths, set_dotted
from ocsfkit.registry import DEFAULT_SCHEMA_VERSION, required_fields_for
from ocsfkit.transforms import apply_transform


def apply_mapping(
    source: dict[str, Any],
    mapping: dict[str, Any],
    custom_transforms: dict[str, Any] | None = None,
) -> MappingResult:
    target: dict[str, Any] = {}
    schema_version = str(mapping.get("schema_version") or DEFAULT_SCHEMA_VERSION)
    explanation = MappingExplanation(
        schema_version=schema_version,
        target_class=dict(mapping.get("target_class") or {}),
    )

    target_class = mapping.get("target_class") or {}
    if not isinstance(target_class, dict):
        raise MappingError("target_class must be a mapping")
    if "metadata.version" not in target_class:
        target_class = dict(target_class)
        target_class["metadata.version"] = schema_version
    for key, value in target_class.items():
        set_dotted(target, key, value)
        explanation.defaulted_fields.append(
            FieldDecision(target=key, value=value, provenance="defaulted")
        )

    fields = mapping.get("fields") or {}
    if not isinstance(fields, dict):
        raise MappingError("fields must be a mapping")

    consumed_paths: set[str] = set()
    for target_path, spec in fields.items():
        if isinstance(spec, dict) and "foreach" in spec:
            _apply_foreach(source, target, explanation, str(target_path), spec, custom_transforms)
            foreach_path = (
                spec["foreach"].get("from") if isinstance(spec.get("foreach"), dict) else None
            )
            if isinstance(foreach_path, str):
                consumed_paths.add(foreach_path)
            continue
        if not isinstance(spec, dict):
            raise MappingError(f"Field mapping for {target_path!r} must be a mapping")
        required = bool(spec.get("required", False))
        source_path = spec.get("from")
        value_missing = True
        value: Any = None
        if source_path is not None:
            if not isinstance(source_path, str):
                raise MappingError(f"from for {target_path!r} must be a string")
            value = extract_json_path(source, source_path)
            value_missing = value is None
            consumed_paths.add(source_path)
        if value_missing and "default" in spec:
            value = spec["default"]
            value_missing = False
            provenance = "defaulted"
        elif value_missing and "guess" in spec:
            value = spec["guess"]
            value_missing = False
            provenance = "guessed"
        else:
            provenance = "mapped"
        if value_missing:
            if required:
                explanation.missing_target_fields.append(str(target_path))
            continue
        transform = spec.get("transform")
        if transform:
            transform_names = transform if isinstance(transform, list) else [transform]
            if not all(isinstance(item, str) for item in transform_names):
                raise MappingError(f"transform for {target_path!r} must be a string or list")
            for transform_name in transform_names:
                value = apply_transform(transform_name, value, custom_transforms)
            provenance = "transformed" if provenance == "mapped" else provenance
        set_dotted(target, str(target_path), value)
        decision = FieldDecision(
            target=str(target_path),
            source=source_path,
            value=value,
            transform=", ".join(transform) if isinstance(transform, list) else transform,
            provenance=provenance,  # type: ignore[arg-type]
            required=required,
        )
        if provenance == "defaulted":
            explanation.defaulted_fields.append(decision)
        elif provenance == "guessed":
            explanation.guessed_fields.append(decision)
        else:
            explanation.mapped_fields.append(decision)

    drop = mapping.get("drop") or []
    if not isinstance(drop, list) or not all(isinstance(item, str) for item in drop):
        raise MappingError("drop must be a list of JSONPath strings")
    explanation.dropped_fields = sorted(drop)

    all_leaf_paths = flatten_paths(source)
    dropped = _expand_consumed(source, set(drop))
    consumed = _expand_consumed(source, consumed_paths)
    explanation.unmapped_source_fields = sorted(
        path for path in all_leaf_paths if path not in consumed and path not in dropped
    )
    for path in sorted(required_fields_for(target, schema_version)):
        if _target_missing(target, path) and path not in explanation.missing_target_fields:
            explanation.missing_target_fields.append(path)
    explanation.confidence = _confidence(explanation)
    return MappingResult(event=target, explanation=explanation)


def _apply_foreach(
    source: dict[str, Any],
    target: dict[str, Any],
    explanation: MappingExplanation,
    target_path: str,
    spec: dict[str, Any],
    custom_transforms: dict[str, Any] | None,
) -> None:
    foreach = spec.get("foreach")
    if not isinstance(foreach, dict):
        raise MappingError(f"foreach for {target_path!r} must be a mapping")
    source_path = foreach.get("from")
    if not isinstance(source_path, str):
        raise MappingError(f"foreach.from for {target_path!r} must be a string")
    item_fields = foreach.get("fields")
    if not isinstance(item_fields, dict):
        raise MappingError(f"foreach.fields for {target_path!r} must be a mapping")
    values = extract_json_path(source, source_path)
    if values is None:
        return
    items = values if isinstance(values, list) else [values]
    for item in items:
        if not isinstance(item, dict):
            continue
        output_item: dict[str, Any] = {}
        for child_target, child_spec in item_fields.items():
            if not isinstance(child_spec, dict):
                raise MappingError(
                    f"foreach field mapping for {target_path}.{child_target} must be a mapping"
                )
            value_missing = True
            value: Any = None
            child_source = child_spec.get("from")
            if child_source is not None:
                if not isinstance(child_source, str):
                    raise MappingError(
                        f"foreach field from for {target_path}.{child_target} must be a string"
                    )
                value = extract_json_path(item, child_source)
                value_missing = value is None
            if value_missing and "default" in child_spec:
                value = child_spec["default"]
                value_missing = False
                provenance = "defaulted"
            elif value_missing and "guess" in child_spec:
                value = child_spec["guess"]
                value_missing = False
                provenance = "guessed"
            else:
                provenance = "mapped"
            if value_missing:
                continue
            transform = child_spec.get("transform")
            if transform:
                transform_names = transform if isinstance(transform, list) else [transform]
                if not all(isinstance(name, str) for name in transform_names):
                    raise MappingError(
                        f"foreach transform for {target_path}.{child_target} must be a string "
                        "or list"
                    )
                for transform_name in transform_names:
                    value = apply_transform(transform_name, value, custom_transforms)
                provenance = "transformed" if provenance == "mapped" else provenance
            set_dotted(output_item, str(child_target), value)
            decision = FieldDecision(
                target=f"{target_path}.{child_target}",
                source=(
                    f"{source_path}.{child_source[2:]}"
                    if isinstance(child_source, str)
                    else source_path
                ),
                value=value,
                transform=", ".join(transform) if isinstance(transform, list) else transform,
                provenance=provenance,  # type: ignore[arg-type]
                required=bool(child_spec.get("required", False)),
            )
            if provenance == "defaulted":
                explanation.defaulted_fields.append(decision)
            elif provenance == "guessed":
                explanation.guessed_fields.append(decision)
            else:
                explanation.mapped_fields.append(decision)
        if output_item:
            append_dotted(target, target_path, output_item)


def _expand_consumed(source: dict[str, Any], roots: set[str]) -> set[str]:
    all_paths = flatten_paths(source)
    expanded: set[str] = set()
    for root in roots:
        expanded.add(root)
        expanded.update(path for path in all_paths if path.startswith(f"{root}."))
        expanded.update(path for path in all_paths if path.startswith(f"{root}[]"))
    return expanded


def _target_missing(target: dict[str, Any], path: str) -> bool:
    from ocsfkit.paths import get_dotted

    return get_dotted(target, path) is None


def _confidence(explanation: MappingExplanation) -> float:
    mapped = len(explanation.mapped_fields)
    defaulted = len(explanation.defaulted_fields)
    guessed = len(explanation.guessed_fields)
    missing = len(explanation.missing_target_fields)
    unmapped = len(explanation.unmapped_source_fields)
    total = mapped + defaulted + guessed + missing + unmapped
    if total == 0:
        return 1.0
    score = (mapped + 0.7 * defaulted + 0.4 * guessed - 0.8 * missing - 0.08 * unmapped) / total
    return round(max(0.0, min(1.0, score)), 3)
