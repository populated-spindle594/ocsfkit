from ocsfkit.io import load_events, load_mapping_file
from ocsfkit.mapping import apply_mapping
from ocsfkit.transforms import load_custom_transforms


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


def test_vendor_mapping_examples() -> None:
    from pathlib import Path

    cases = [
        ("fixtures/okta_login_event.json", "examples/okta-authentication-mapping.yaml", 3002),
        ("fixtures/azure_ad_signin.json", "examples/azure-ad-signin-mapping.yaml", 3002),
        ("fixtures/github_audit_event.json", "examples/github-audit-mapping.yaml", 1007),
        (
            "fixtures/crowdstrike_detection.json",
            "examples/crowdstrike-detection-mapping.yaml",
            2004,
        ),
        ("fixtures/paloalto_traffic.json", "examples/paloalto-traffic-mapping.yaml", 4001),
        ("fixtures/zeek_conn.json", "examples/zeek-conn-mapping.yaml", 4001),
        ("fixtures/splunk_notable.json", "examples/splunk-notable-mapping.yaml", 2004),
        ("fixtures/sentinel_alert.json", "examples/sentinel-alert-mapping.yaml", 2004),
        ("fixtures/defender_alert.json", "examples/defender-alert-mapping.yaml", 2004),
        ("fixtures/wiz_finding.json", "examples/wiz-finding-mapping.yaml", 2004),
        ("fixtures/lacework_alert.json", "examples/lacework-alert-mapping.yaml", 4001),
        ("fixtures/gcp_scc_finding.json", "examples/gcp-scc-finding-mapping.yaml", 2004),
        ("fixtures/cloudflare_log.json", "examples/cloudflare-log-mapping.yaml", 4001),
        ("fixtures/kubernetes_audit.json", "examples/kubernetes-audit-mapping.yaml", 1007),
    ]
    for fixture, mapping_path, class_uid in cases:
        source = load_events(fixture)[0]
        mapping = load_mapping_file(mapping_path)
        custom_transforms = load_custom_transforms(
            mapping.get("custom_transforms") or [],
            Path(mapping_path).parent,
        )
        result = apply_mapping(source, mapping, custom_transforms)
        assert result.event["class_uid"] == class_uid
        assert result.event["metadata"]["version"] == "1.7.0"
        assert result.explanation.missing_target_fields == []


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


def test_foreach_array_mapping() -> None:
    source = {
        "assets": [
            {"id": "i-1", "kind": "EC2"},
            {"id": "bucket-1", "kind": "S3"},
        ]
    }
    mapping = {
        "target_class": {"class_uid": 2004, "class_name": "Detection Finding"},
        "fields": {
            "resources[]": {
                "foreach": {
                    "from": "$.assets",
                    "fields": {
                        "name": {"from": "$.id"},
                        "type": {"from": "$.kind"},
                    },
                }
            }
        },
    }
    result = apply_mapping(source, mapping).event
    assert result["resources"] == [
        {"name": "i-1", "type": "EC2"},
        {"name": "bucket-1", "type": "S3"},
    ]
