from __future__ import annotations

from ocsfkit.coverage import CoverageReport
from ocsfkit.models import MappingExplanation


def coverage_markdown(report: CoverageReport, failures: list[str] | None = None) -> str:
    failures = failures or []
    lines = [
        "## ocsfkit Coverage",
        "",
        f"- Events: {report.events}",
        f"- Average confidence: {report.average_confidence:.3f}",
        f"- Source field coverage: {report.source_field_coverage:.3f}",
    ]
    if failures:
        lines.append("- Threshold failures: " + "; ".join(failures))
    if report.unmapped_source_fields:
        lines.extend(["", "### Top Unmapped Source Fields", ""])
        for path, count in sorted(
            report.unmapped_source_fields.items(), key=lambda item: item[1], reverse=True
        )[:20]:
            lines.append(f"- `{path}`: {count}")
    return "\n".join(lines) + "\n"


def explanation_markdown(explanation: MappingExplanation) -> str:
    lines = [
        "## ocsfkit Mapping Explanation",
        "",
        f"- Schema version: {explanation.schema_version}",
        f"- Confidence: {explanation.confidence:.3f}",
        f"- Mapped fields: {len(explanation.mapped_fields)}",
        f"- Defaulted fields: {len(explanation.defaulted_fields)}",
        f"- Guessed fields: {len(explanation.guessed_fields)}",
        f"- Dropped fields: {len(explanation.dropped_fields)}",
        f"- Unmapped source fields: {len(explanation.unmapped_source_fields)}",
        f"- Missing target fields: {len(explanation.missing_target_fields)}",
    ]
    for title, values in (
        ("Missing Target Fields", explanation.missing_target_fields),
        ("Unmapped Source Fields", explanation.unmapped_source_fields),
        ("Dropped Fields", explanation.dropped_fields),
    ):
        if values:
            lines.extend(["", f"### {title}", ""])
            lines.extend(f"- `{value}`" for value in values)
    return "\n".join(lines) + "\n"
