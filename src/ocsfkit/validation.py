from __future__ import annotations

from typing import Any

from ocsfkit.errors import MappingError
from ocsfkit.models import LintIssue
from ocsfkit.paths import extract_json_path, parse_dotted_path
from ocsfkit.registry import BASE_FIELDS, CLASS_REGISTRY
from ocsfkit.transform_packs import TRANSFORM_PACKS
from ocsfkit.transforms import TRANSFORMS


def validate_mapping_doc(mapping: dict[str, Any]) -> list[LintIssue]:
    issues: list[LintIssue] = []
    target_class = mapping.get("target_class")
    if not isinstance(target_class, dict):
        issues.append(_error("target_class", "target_class must be a mapping"))
    else:
        class_uid = target_class.get("class_uid")
        class_name = target_class.get("class_name")
        if not isinstance(class_uid, int):
            issues.append(_error("target_class.class_uid", "class_uid must be an integer"))
        elif class_uid not in CLASS_REGISTRY:
            issues.append(_warning("target_class.class_uid", "Unknown class_uid"))
        elif class_name != CLASS_REGISTRY[class_uid].class_name:
            issues.append(
                _error(
                    "target_class.class_name",
                    f"Expected {CLASS_REGISTRY[class_uid].class_name!r}",
                )
            )
    fields = mapping.get("fields")
    if not isinstance(fields, dict):
        issues.append(_error("fields", "fields must be a mapping"))
        fields = {}
    for target_path, spec in fields.items():
        if not isinstance(spec, dict):
            issues.append(_error(f"fields.{target_path}", "field spec must be a mapping"))
            continue
        try:
            parse_dotted_path(str(target_path))
        except MappingError as exc:
            issues.append(_error(f"fields.{target_path}", str(exc)))
        if str(target_path) not in BASE_FIELDS:
            issues.append(_warning(str(target_path), "Target path is not in bundled schema"))
        source_path = spec.get("from")
        if source_path is not None:
            try:
                extract_json_path({}, str(source_path))
            except MappingError as exc:
                issues.append(_error(f"fields.{target_path}.from", str(exc)))
        transform = spec.get("transform")
        transforms = transform if isinstance(transform, list) else [transform] if transform else []
        if not all(isinstance(item, str) for item in transforms):
            issues.append(_error(f"fields.{target_path}.transform", "must be a string or list"))
        has_custom_transforms = bool(mapping.get("custom_transforms"))
        for transform_name in transforms:
            if (
                transform_name not in TRANSFORMS
                and transform_name not in TRANSFORM_PACKS
                and not has_custom_transforms
            ):
                issues.append(
                    _warning(
                        f"fields.{target_path}.transform",
                        f"Unknown built-in transform {transform_name!r}; may be custom",
                    )
                )
    drop = mapping.get("drop", [])
    if not isinstance(drop, list) or not all(isinstance(item, str) for item in drop):
        issues.append(_error("drop", "drop must be a list of JSONPath strings"))
    return issues


def _error(path: str, message: str) -> LintIssue:
    return LintIssue(level="error", path=path, message=message)


def _warning(path: str, message: str) -> LintIssue:
    return LintIssue(level="warning", path=path, message=message)
