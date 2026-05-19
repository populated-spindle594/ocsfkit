from __future__ import annotations

import html
from typing import Any

from ocsfkit.coverage import CoverageReport
from ocsfkit.models import MappingExplanation


def coverage_html(report: CoverageReport) -> str:
    rows = "\n".join(
        "<tr>"
        f"<td>{html.escape(path)}</td>"
        f"<td>{count}</td>"
        f"<td><div class=\"bar\" style=\"width: {_bar_width(count, report)}%\"></div></td>"
        "</tr>"
        for path, count in report.unmapped_source_fields.items()
    )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>ocsfkit Mapping Report</title>
  <style>
    body {{ font-family: system-ui, sans-serif; margin: 32px; line-height: 1.5; color: #172033; }}
    .summary {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 12px;
    }}
    .metric {{
      border: 1px solid #d0d7de;
      border-radius: 8px;
      padding: 12px;
      background: #f6f8fa;
    }}
    .metric strong {{ display: block; font-size: 24px; }}
    input {{ width: 100%; box-sizing: border-box; padding: 8px; margin: 12px 0; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ border: 1px solid #d0d7de; padding: 8px; text-align: left; }}
    th {{ background: #f6f8fa; }}
    .bar {{ height: 10px; background: #cf222e; border-radius: 999px; }}
    .hint {{ color: #57606a; }}
  </style>
</head>
<body>
  <h1>ocsfkit Mapping Report</h1>
  <p class="hint">
    Use this report to prioritize mapping work: high-count unmapped source fields are where
    visibility is most likely being lost.
  </p>
  <div class="summary">
    <div class="metric"><strong>{report.events}</strong>Events</div>
    <div class="metric"><strong>{report.average_confidence:.3f}</strong>Average confidence</div>
    <div class="metric">
      <strong>{report.source_field_coverage:.3f}</strong>Source field coverage
    </div>
    <div class="metric">
      <strong>{sum(report.unmapped_source_fields.values())}</strong>Unmapped fields
    </div>
  </div>
  <h2>Unmapped Source Fields</h2>
  <input id="filter" placeholder="Filter table" oninput="filterRows()">
  <table>
    <thead><tr><th>Path</th><th>Count</th><th>Relative frequency</th></tr></thead>
    <tbody>{rows}</tbody>
  </table>
  <script>
    function filterRows() {{
      const needle = document.getElementById('filter').value.toLowerCase();
      for (const row of document.querySelectorAll('tbody tr')) {{
        row.style.display = row.textContent.toLowerCase().includes(needle) ? '' : 'none';
      }}
    }}
  </script>
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
    mapped_rows = _decision_rows(explanation.mapped_fields)
    defaulted_rows = _decision_rows(explanation.defaulted_fields)
    guessed_rows = _decision_rows(explanation.guessed_fields)
    payload = html.escape(explanation.model_dump_json(indent=2))
    all_source_fields = sorted(
        {
            str(field.source)
            for field in [
                *explanation.mapped_fields,
                *explanation.defaulted_fields,
                *explanation.guessed_fields,
            ]
            if field.source
        }
    )
    source_rows = "\n".join(
        f"<tr><td><code>{html.escape(path)}</code></td></tr>" for path in all_source_fields
    )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>ocsfkit Mapping Explanation</title>
  <style>
    body {{ font-family: system-ui, sans-serif; margin: 32px; line-height: 1.5; color: #172033; }}
    .summary {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 12px;
    }}
    .metric {{
      border: 1px solid #d0d7de;
      border-radius: 8px;
      padding: 12px;
      background: #f6f8fa;
    }}
    .metric strong {{ display: block; font-size: 24px; }}
    table {{ border-collapse: collapse; width: 100%; margin: 12px 0 24px; }}
    th, td {{ border: 1px solid #d0d7de; padding: 8px; text-align: left; vertical-align: top; }}
    th {{ background: #f6f8fa; }}
    code, pre {{ background: #f6f8fa; padding: 2px 4px; }}
    details {{ margin: 16px 0; }}
  </style>
</head>
<body>
  <h1>ocsfkit Mapping Explanation</h1>
  <div class="summary">
    <div class="metric"><strong>{explanation.confidence:.3f}</strong>Confidence</div>
    <div class="metric"><strong>{len(explanation.mapped_fields)}</strong>Mapped</div>
    <div class="metric"><strong>{len(explanation.unmapped_source_fields)}</strong>Unmapped</div>
    <div class="metric">
      <strong>{len(explanation.missing_target_fields)}</strong>Missing targets
    </div>
  </div>
  <p>Schema version: {html.escape(str(explanation.schema_version))}</p>
  <h2>Mapped Fields</h2>
  {_decision_table(mapped_rows)}
  <h2>Defaulted Fields</h2>
  {_decision_table(defaulted_rows)}
  <h2>Guessed Fields</h2>
  {_decision_table(guessed_rows)}
  <h2>Source Fields Used</h2>
  <table><thead><tr><th>Source path</th></tr></thead><tbody>{source_rows}</tbody></table>
  {sections}
  <details>
    <summary>Raw explanation JSON</summary>
    <pre>{payload}</pre>
  </details>
</body>
</html>
"""


def _decision_rows(fields: list[Any]) -> str:
    return "\n".join(
        "<tr>"
        f"<td>{html.escape(field.target)}</td>"
        f"<td>{html.escape(str(field.source or ''))}</td>"
        f"<td>{html.escape(field.provenance)}</td>"
        f"<td>{html.escape(str(field.transform or ''))}</td>"
        "</tr>"
        for field in fields
    )


def _decision_table(rows: str) -> str:
    if not rows:
        return "<p>None.</p>"
    return f"""
  <table>
    <thead><tr><th>Target</th><th>Source</th><th>Provenance</th><th>Transform</th></tr></thead>
    <tbody>{rows}</tbody>
  </table>
"""


def _list_section(title: str, values: list[str]) -> str:
    if not values:
        return ""
    items = "\n".join(f"<li><code>{html.escape(value)}</code></li>" for value in values)
    return f"<h2>{html.escape(title)}</h2><ul>{items}</ul>"


def _bar_width(count: int, report: CoverageReport) -> int:
    maximum = max(report.unmapped_source_fields.values(), default=1)
    return max(4, round((count / maximum) * 100))
