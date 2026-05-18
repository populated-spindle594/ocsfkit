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


def test_query_smoke() -> None:
    result = runner.invoke(app, ["query", "fixtures/ocsf_detection_finding.json", "severity_id"])
    assert result.exit_code == 0
    assert "4" in result.stdout

