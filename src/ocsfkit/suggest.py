from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Any

from ocsfkit.paths import leaf_paths
from ocsfkit.targets import list_targets


@dataclass(frozen=True)
class MappingSuggestion:
    source: str
    target: str
    confidence: float
    reason: str
    transform: str | None = None


TARGET_HINTS = {
    "time": {"time", "timestamp", "eventtime", "created", "published"},
    "severity_id": {"severity", "severityid", "level", "risk", "priority"},
    "message": {"message", "title", "description", "summary", "name"},
    "metadata.product.name": {"product", "productname", "vendor", "service"},
    "actor.user.name": {"username", "user", "principal", "actor", "email"},
    "actor.user.uid": {"userid", "uid", "user_id", "principalid"},
    "cloud.account_uid": {"account", "accountid", "account_uid", "subscriptionid", "projectid"},
    "cloud.region": {"region", "location"},
    "src_endpoint.ip": {"srcip", "sourceip", "sourceaddress", "clientip"},
    "dst_endpoint.ip": {"dstip", "destinationip", "destinationaddress", "serverip"},
    "src_endpoint.port": {"srcport", "sourceport"},
    "dst_endpoint.port": {"dstport", "destinationport"},
    "device.hostname": {"hostname", "host", "computer", "device"},
    "process.name": {"process", "processname", "image", "command"},
    "process.pid": {"pid", "processid"},
}


def suggest_mappings(event: dict[str, Any], limit: int = 20) -> list[MappingSuggestion]:
    source_paths = sorted(leaf_paths(event))
    targets = [str(target["path"]) for target in list_targets()]
    suggestions: list[MappingSuggestion] = []
    used_targets: set[str] = set()
    for source in source_paths:
        best = _best_target(source, targets)
        if best is None or best.target in used_targets:
            continue
        used_targets.add(best.target)
        suggestions.append(best)
    return sorted(suggestions, key=lambda item: item.confidence, reverse=True)[:limit]


def suggestions_mapping_yaml(
    event: dict[str, Any],
    class_uid: int = 2004,
    class_name: str = "Detection Finding",
    product_name: str = "Unknown Product",
    limit: int = 20,
) -> dict[str, Any]:
    fields: dict[str, Any] = {
        "time": {"from": "$.time", "transform": "parse_timestamp", "required": True},
        "metadata.product.name": {"default": product_name},
    }
    for suggestion in suggest_mappings(event, limit):
        rule: dict[str, Any] = {"from": f"$.{suggestion.source}"}
        if suggestion.transform:
            rule["transform"] = suggestion.transform
        fields.setdefault(suggestion.target, rule)
    return {
        "schema_version": "1.7.0",
        "target_class": {"class_uid": class_uid, "class_name": class_name},
        "fields": fields,
        "drop": [],
    }


def _best_target(source: str, targets: list[str]) -> MappingSuggestion | None:
    normalized_source = _normalize(source.split(".")[-1])
    scored: list[MappingSuggestion] = []
    for target in targets:
        normalized_target = _normalize(target.split(".")[-1].replace("[]", ""))
        score = SequenceMatcher(None, normalized_source, normalized_target).ratio()
        reason = "name similarity"
        hints = TARGET_HINTS.get(target, set())
        if normalized_source in {_normalize(hint) for hint in hints}:
            score = max(score, 0.92)
            reason = "known telemetry synonym"
        elif any(hint in normalized_source for hint in {_normalize(item) for item in hints}):
            score = max(score, 0.82)
            reason = "partial telemetry synonym"
        transform = _suggest_transform(target, normalized_source)
        if transform:
            score = max(score, 0.84)
        if target == "severity_id" and normalized_source == "severity":
            score = 1.0
            reason = "severity normalization"
        elif target == "severity" and normalized_source == "severity":
            score = min(score, 0.9)
        if score >= 0.72:
            scored.append(
                MappingSuggestion(
                    source=source,
                    target=target,
                    confidence=round(score, 3),
                    reason=reason,
                    transform=transform,
                )
            )
    return max(scored, key=lambda item: item.confidence) if scored else None


def _normalize(value: str) -> str:
    return "".join(char.lower() for char in value if char.isalnum())


def _suggest_transform(target: str, normalized_source: str) -> str | None:
    if target == "time" and any(
        marker in normalized_source
        for marker in {"time", "date", "timestamp", "published", "created", "updated"}
    ):
        return "parse_timestamp"
    if target == "severity_id" and "severity" in normalized_source:
        return "severity_text_to_id"
    return None
