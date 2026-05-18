from typer.testing import CliRunner

from ocsfkit.cli import app

runner = CliRunner()


def test_parse_smoke() -> None:
    result = runner.invoke(app, ["parse", "fixtures/aws_guardduty_finding.json"])
    assert result.exit_code == 0
    assert "111122223333" in result.stdout


def test_lint_smoke_failure() -> None:
    result = runner.invoke(app, ["lint", "fixtures/broken_ocsf_event.json"])
    assert result.exit_code == 1
    assert "Invalid severity_id" in result.stdout


def test_lint_sarif_smoke() -> None:
    result = runner.invoke(app, ["lint", "fixtures/broken_ocsf_event.json", "--sarif"])
    assert result.exit_code == 1
    assert '"version": "2.1.0"' in result.stdout


def test_map_smoke() -> None:
    result = runner.invoke(
        app,
        [
            "map",
            "fixtures/aws_guardduty_finding.json",
            "--mapping",
            "examples/guardduty-mapping.yaml",
        ],
    )
    assert result.exit_code == 0
    assert "Detection Finding" in result.stdout


def test_explain_json_smoke() -> None:
    result = runner.invoke(
        app,
        [
            "explain",
            "fixtures/aws_guardduty_finding.json",
            "--mapping",
            "examples/guardduty-mapping.yaml",
            "--json",
        ],
    )
    assert result.exit_code == 0
    assert "unmapped_source_fields" in result.stdout


def test_explain_github_annotations_smoke() -> None:
    result = runner.invoke(
        app,
        [
            "explain",
            "fixtures/aws_guardduty_finding.json",
            "--mapping",
            "examples/guardduty-mapping.yaml",
            "--github-annotations",
        ],
    )
    assert result.exit_code == 0
    assert "::warning file=fixtures/aws_guardduty_finding.json,line=1::" in result.stdout


def test_query_smoke() -> None:
    result = runner.invoke(app, ["query", "fixtures/ocsf_detection_finding.json", "severity_id"])
    assert result.exit_code == 0
    assert "4" in result.stdout


def test_coverage_smoke() -> None:
    result = runner.invoke(
        app,
        [
            "coverage",
            "fixtures/aws_guardduty_finding.json",
            "--mapping",
            "examples/guardduty-mapping.yaml",
            "--json",
        ],
    )
    assert result.exit_code == 0
    assert "source_field_coverage" in result.stdout


def test_validate_mapping_smoke() -> None:
    result = runner.invoke(app, ["validate-mapping", "examples/guardduty-mapping.yaml"])
    assert result.exit_code == 0


def test_init_mapping_smoke() -> None:
    result = runner.invoke(app, ["init-mapping", "fixtures/aws_guardduty_finding.json"])
    assert result.exit_code == 0
    assert "schema_version" in result.stdout


def test_schema_smoke() -> None:
    result = runner.invoke(app, ["schema"])
    assert result.exit_code == 0
    assert "Detection Finding" in result.stdout


def test_test_mapping_smoke() -> None:
    result = runner.invoke(app, ["test-mapping", "tests/fixtures/guardduty-test.yaml"])
    assert result.exit_code == 0
    assert "passed" in result.stdout


def test_report_smoke(tmp_path) -> None:
    output = tmp_path / "report.html"
    result = runner.invoke(
        app,
        [
            "report",
            "fixtures/aws_guardduty_finding.json",
            "--mapping",
            "examples/guardduty-mapping.yaml",
            "--output",
            str(output),
        ],
    )
    assert result.exit_code == 0
    assert "Mapping Report" in output.read_text()


def test_import_schema_smoke(tmp_path) -> None:
    schema = tmp_path / "schema.json"
    schema.write_text('{"schema_version": "test", "classes": {"1": {"class_name": "X"}}}')
    result = runner.invoke(app, ["import-schema", str(schema)])
    assert result.exit_code == 0
    assert "schema_version" in result.stdout


def test_workshop_smoke() -> None:
    result = runner.invoke(app, ["workshop", "fixtures/okta_login_event.json"])
    assert result.exit_code == 0
    assert "$.published" in result.stdout
