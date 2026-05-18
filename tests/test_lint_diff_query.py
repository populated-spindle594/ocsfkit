from ocsfkit.diff import diff_events
from ocsfkit.io import load_events
from ocsfkit.paths import query_field
from ocsfkit.registry import lint_event


def test_lint_catches_missing_required_fields() -> None:
    issues = lint_event({"class_uid": 2004, "class_name": "Detection Finding"})
    assert any(issue.level == "error" and issue.path == "severity_id" for issue in issues)
    assert any(issue.level == "error" and issue.path == "time" for issue in issues)
    assert any(issue.level == "error" and issue.path == "metadata.version" for issue in issues)


def test_lint_catches_bad_types_and_values() -> None:
    event = load_events("fixtures/broken_ocsf_event.json")[0]
    issues = lint_event(event)
    assert any(issue.path == "time" and "Expected int" in issue.message for issue in issues)
    assert any(
        issue.path == "severity_id" and "Invalid severity_id" in issue.message
        for issue in issues
    )
    assert any(issue.path == "class_name" for issue in issues)


def test_diff_detects_semantic_changes() -> None:
    before = {"class_uid": 2004, "severity_id": 3, "message": "old"}
    after = {"class_uid": 2004, "severity_id": 4, "message": "new", "cloud": {"region": "us"}}
    changes = diff_events(before, after)
    assert any(change.path == "severity_id" and change.kind == "changed" for change in changes)
    assert any(change.path == "cloud" and change.kind == "added" for change in changes)


def test_query_field() -> None:
    event = load_events("fixtures/ocsf_detection_finding.json")[0]
    assert query_field(event, "metadata.product.name") == "Amazon GuardDuty"
    assert query_field(event, "resources[].name") == ["i-0123456789abcdef0"]


def test_lint_catches_schema_version_mismatch() -> None:
    event = load_events("fixtures/ocsf_detection_finding.json")[0]
    issues = lint_event(event, schema_version="1.6.0")
    assert any(issue.path == "metadata.version" and issue.level == "error" for issue in issues)
