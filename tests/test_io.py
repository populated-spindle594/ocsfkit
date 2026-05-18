from pathlib import Path

from ocsfkit.io import load_events


def test_load_json_fixture() -> None:
    events = load_events("fixtures/aws_guardduty_finding.json")
    assert len(events) == 1
    assert events[0]["accountId"] == "111122223333"


def test_load_ndjson_fixture() -> None:
    events = load_events("fixtures/guardduty.ndjson")
    assert len(events) == 2
    assert events[1]["severity"] == "Low"


def test_load_yaml(tmp_path: Path) -> None:
    path = tmp_path / "event.yaml"
    path.write_text("time: 1\nclass_uid: 2004\n")
    assert load_events(str(path))[0]["class_uid"] == 2004

