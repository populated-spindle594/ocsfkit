from __future__ import annotations

import html

from ocsfkit.coverage import CoverageReport


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
