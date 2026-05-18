from __future__ import annotations

import html

from ocsfkit.coverage import CoverageReport
from ocsfkit.models import MappingExplanation


def coverage_html(report: CoverageReport) -> str:
    rows = "\n".join(
        f"<tr><td>{html.escape(path)}</td><td>{count}</td></tr>"
        for path, count in report.unmapped_source_fields.items()
    )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>ocsfkit Mapping Report</title>
  <style>
    body {{ font-family: system-ui, sans-serif; margin: 32px; line-height: 1.5; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ border: 1px solid #d0d7de; padding: 8px; text-align: left; }}
    th {{ background: #f6f8fa; }}
  </style>
</head>
<body>
  <h1>ocsfkit Mapping Report</h1>
  <p>Events: {report.events}</p>
  <p>Average confidence: {report.average_confidence:.3f}</p>
  <p>Source field coverage: {report.source_field_coverage:.3f}</p>
  <h2>Unmapped Source Fields</h2>
  <table>
    <thead><tr><th>Path</th><th>Count</th></tr></thead>
    <tbody>{rows}</tbody>
  </table>
</body>
</html>
"""


def explanation_html(explanation: MappingExplanation) -> str:
    sections = "\n".join(
        _list_section(title, values)
        for title, values in (
            ("Missing Target Fields", explanation.missing_target_fields),
            ("Unmapped Source Fields", explanation.unmapped_source_fields),
            ("Dropped Fields", explanation.dropped_fields),
        )
    )
    mapped_rows = "\n".join(
        "<tr>"
        f"<td>{html.escape(field.target)}</td>"
        f"<td>{html.escape(str(field.source or ''))}</td>"
        f"<td>{html.escape(field.provenance)}</td>"
        f"<td>{html.escape(str(field.transform or ''))}</td>"
        "</tr>"
        for field in [
            *explanation.mapped_fields,
            *explanation.defaulted_fields,
            *explanation.guessed_fields,
        ]
    )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>ocsfkit Mapping Explanation</title>
  <style>
    body {{ font-family: system-ui, sans-serif; margin: 32px; line-height: 1.5; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ border: 1px solid #d0d7de; padding: 8px; text-align: left; }}
    th {{ background: #f6f8fa; }}
    code {{ background: #f6f8fa; padding: 2px 4px; }}
  </style>
</head>
<body>
  <h1>ocsfkit Mapping Explanation</h1>
  <p>Schema version: {html.escape(str(explanation.schema_version))}</p>
  <p>Confidence: {explanation.confidence:.3f}</p>
  <h2>Field Decisions</h2>
  <table>
    <thead><tr><th>Target</th><th>Source</th><th>Provenance</th><th>Transform</th></tr></thead>
    <tbody>{mapped_rows}</tbody>
  </table>
  {sections}
</body>
</html>
"""


def _list_section(title: str, values: list[str]) -> str:
    if not values:
        return ""
    items = "\n".join(f"<li><code>{html.escape(value)}</code></li>" for value in values)
    return f"<h2>{html.escape(title)}</h2><ul>{items}</ul>"
