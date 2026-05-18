from __future__ import annotations

from typing import Any

from ocsfkit.errors import MappingError
from ocsfkit.models import FieldDecision, MappingExplanation, MappingResult
from ocsfkit.paths import extract_json_path, flatten_paths, set_dotted
from ocsfkit.registry import required_fields_for
from ocsfkit.transforms import apply_transform


def apply_mapping(source: dict[str, Any], mapping: dict[str, Any]) -> MappingResult:
    target: dict[str, Any] = {}
    explanation = MappingExplanation(target_class=dict(mapping.get("target_class") or {}))

    target_class = mapping.get("target_class") or {}
    if not isinstance(target_class, dict):
        raise MappingError("target_class must be a mapping")
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
            value = apply_transform(str(transform), value)
            provenance = "transformed" if provenance == "mapped" else provenance
        set_dotted(target, str(target_path), value)
        decision = FieldDecision(
            target=str(target_path),
            source=source_path,
            value=value,
            transform=str(transform) if transform else None,
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
    for path in sorted(required_fields_for(target)):
        if _target_missing(target, path) and path not in explanation.missing_target_fields:
            explanation.missing_target_fields.append(path)
    explanation.confidence = _confidence(explanation)
    return MappingResult(event=target, explanation=explanation)


def _expand_consumed(source: dict[str, Any], roots: set[str]) -> set[str]:
    all_paths = flatten_paths(source)
    expanded: set[str] = set()
    for root in roots:
        expanded.add(root)
        expanded.update(path for path in all_paths if path.startswith(f"{root}."))
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

