from ocsfkit.io import load_events, load_mapping_file
from ocsfkit.mapping import apply_mapping


def test_mapping_application() -> None:
    source = load_events("fixtures/aws_guardduty_finding.json")[0]
    mapping = load_mapping_file("examples/guardduty-mapping.yaml")
    result = apply_mapping(source, mapping)
    assert result.event["class_uid"] == 2004
    assert result.event["severity_id"] == 4
    assert result.event["cloud"]["account_uid"] == "111122223333"
    assert result.event["resources"][0]["name"] == "i-0123456789abcdef0"


def test_securityhub_mapping_application() -> None:
    source = load_events("fixtures/aws_securityhub_finding.json")[0]
    mapping = load_mapping_file("examples/securityhub-mapping.yaml")
    result = apply_mapping(source, mapping)
    assert result.event["severity_id"] == 3
    assert result.event["metadata"]["product"]["name"] == "Security Hub"
    assert result.event["resources"][0]["name"] == "sg-0123456789abcdef0"


def test_cloudtrail_mapping_application() -> None:
    source = load_events("fixtures/cloudtrail_event.json")[0]
    mapping = load_mapping_file("examples/cloudtrail-console-login-mapping.yaml")
    from pathlib import Path

    from ocsfkit.transforms import load_custom_transforms

    custom_transforms = load_custom_transforms(
        mapping["custom_transforms"],
        Path("examples"),
    )
    result = apply_mapping(source, mapping, custom_transforms)
    assert result.event["class_uid"] == 3002
    assert result.event["metadata"]["product"]["name"] == "AWS CloudTrail"
    assert result.event["actor"]["user"]["name"] == "alice"
    assert result.event["status"] == "Failure"
    assert result.event["status_id"] == 2


def test_explain_contains_mapping_quality_categories() -> None:
    source = load_events("fixtures/aws_guardduty_finding.json")[0]
    mapping = load_mapping_file("examples/guardduty-mapping.yaml")
    explanation = apply_mapping(source, mapping).explanation
    assert any(field.target == "time" for field in explanation.mapped_fields)
    assert any(field.target == "metadata.product.name" for field in explanation.defaulted_fields)
    assert "$.debug" in explanation.dropped_fields
    assert "$.id" in explanation.unmapped_source_fields
    assert explanation.confidence > 0


def test_explain_tracks_missing_required_target() -> None:
    source = {"severity": "Low"}
    mapping = {
        "target_class": {"class_uid": 2004, "class_name": "Detection Finding"},
        "fields": {"time": {"from": "$.missing", "required": True}},
    }
    explanation = apply_mapping(source, mapping).explanation
    assert "time" in explanation.missing_target_fields
