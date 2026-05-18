from __future__ import annotations

from ocsfkit.models import MappingExplanation


def strict_mapping_failures(explanation: MappingExplanation) -> list[str]:
    failures: list[str] = []
    for path in explanation.missing_target_fields:
        failures.append(f"Missing target field: {path}")
    for path in explanation.unmapped_source_fields:
        failures.append(f"Unmapped source field: {path}")
    for field in explanation.guessed_fields:
        failures.append(f"Guessed target field: {field.target}")
    return failures
