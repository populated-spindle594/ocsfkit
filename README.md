# ocsfkit

`ocsfkit` is an OCSF workbench for security engineers who need to normalize,
lint, explain, diff, and query security events without hiding mapping quality.

The first version focuses on a practical Detection Finding workflow and a minimal
schema registry that can grow over time.

## Why This Exists

Moving telemetry into OCSF is rarely a pure parsing problem. The hard part is
knowing what happened during normalization:

- Which class did the source event become?
- Which source fields mapped cleanly?
- Which target fields were defaulted or guessed?
- Which fields were intentionally dropped?
- Which source fields are still unmapped?
- Which required or recommended OCSF fields are missing?

`ocsfkit` keeps those answers attached to the mapping workflow.

## Install

```bash
pip install ocsfkit
```

For local development:

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e ".[dev]"
```

## Documentation

- [Getting Started](docs/getting-started.md): first mapping, lint, query, and diff workflow.
- [Mapping Guide](docs/mapping-guide.md): YAML format, provenance, transforms, drops, and required fields.
- [Real-World Workflows](docs/real-world-workflows.md): GuardDuty, Security Hub, CloudTrail, CI gates, and mapping comparisons.

## Quick Start

Parse JSON, YAML, or NDJSON:

```bash
ocsfkit parse fixtures/aws_guardduty_finding.json
ocsfkit parse fixtures/guardduty.ndjson --format ndjson
cat fixtures/aws_guardduty_finding.json | ocsfkit parse -
```

Map AWS GuardDuty into an OCSF Detection Finding:

```bash
ocsfkit map fixtures/aws_guardduty_finding.json --mapping examples/guardduty-mapping.yaml
ocsfkit map fixtures/aws_guardduty_finding.json --mapping examples/guardduty-mapping.yaml --explain
```

Explain mapping quality before trusting the output:

```bash
ocsfkit explain fixtures/aws_guardduty_finding.json --mapping examples/guardduty-mapping.yaml
ocsfkit explain fixtures/aws_guardduty_finding.json --mapping examples/guardduty-mapping.yaml --json
```

Lint OCSF-looking events:

```bash
ocsfkit lint fixtures/ocsf_detection_finding.json
ocsfkit lint fixtures/broken_ocsf_event.json --json
ocsfkit lint fixtures/broken_ocsf_event.json --sarif
ocsfkit lint fixtures/broken_ocsf_event.json --warn-only
```

Diff two events or streams:

```bash
ocsfkit diff fixtures/ocsf_detection_finding.json fixtures/broken_ocsf_event.json
ocsfkit diff before.ndjson after.ndjson --json
```

Query common OCSF fields:

```bash
ocsfkit query fixtures/ocsf_detection_finding.json severity_id
ocsfkit query fixtures/ocsf_detection_finding.json metadata.product.name
ocsfkit query fixtures/ocsf_detection_finding.json cloud.account_uid
```

## Command Reference

### `parse`

Reads JSON, YAML, or NDJSON and emits normalized JSON. Use this to make sure
input data can be loaded before writing mappings.

```bash
ocsfkit parse <input> [--format json|ndjson]
```

`<input>` can be a file path or `-` for stdin.

### `map`

Applies a mapping YAML and emits OCSF JSON.

```bash
ocsfkit map <input> --mapping mapping.yaml [--format json|ndjson] [--explain]
```

Without `--explain`, output is the mapped event. With `--explain`, each output
item contains both `event` and `explanation`.

### `explain`

Shows the mapping decision report without making users inspect the mapped event
by hand.

```bash
ocsfkit explain <input> --mapping mapping.yaml [--json] [--github-annotations]
```

The report includes mapped fields, defaulted fields, guessed fields, dropped
fields, unmapped source fields, missing target fields, and a confidence score.
`--github-annotations` emits missing targets and unmapped source fields as
GitHub Actions annotations.

### `lint`

Validates OCSF-looking events against the built-in minimal registry.

```bash
ocsfkit lint <input> [--json] [--sarif] [--github-annotations] [--warn-only]
```

Lint exits non-zero on errors unless `--warn-only` is set. Warnings are used for
recommended fields and unknown class IDs.
Use `--schema-version` to enforce the expected OCSF version, and `--sarif` or
`--github-annotations` in CI.

### `diff`

Compares two OCSF events or two streams with the same event count.

```bash
ocsfkit diff <before> <after> [--json]
```

The human output highlights class and severity changes because those fields tend
to affect downstream routing, alerting, and dashboards.

### `query`

Extracts common OCSF fields using dotted paths.

```bash
ocsfkit query <input> metadata.product.name
ocsfkit query <input> resources[].name
```

For NDJSON, one result is printed per event.

## Mapping Format

Mappings are YAML. Source paths use a deliberately small JSONPath subset such as
`$.eventTime` and `$.userIdentity.userName`. Target paths use dotted OCSF paths
such as `cloud.account_uid` and `actor.user.name`.

```yaml
schema_version: 1.7.0

target_class:
  class_uid: 2004
  class_name: Detection Finding
  category_uid: 2
  category_name: Findings

fields:
  time:
    from: $.eventTime
    transform: parse_timestamp
    required: true

  severity_id:
    from: $.severity
    transform: severity_text_to_id
    default: 1

  message:
    from: $.title

  cloud.account_uid:
    from: $.accountId

drop:
  - $.debug
  - $.rawPayload
```

The explanation model tracks mapped, transformed, defaulted, guessed, dropped,
unmapped, and missing fields, plus a confidence score.

Included examples:

- [GuardDuty mapping](examples/guardduty-mapping.yaml)
- [Security Hub mapping](examples/securityhub-mapping.yaml)
- [CloudTrail console login mapping](examples/cloudtrail-console-login-mapping.yaml)
- [Custom transform module](examples/custom_transforms.py)

## Minimal OCSF Scope

Implemented fields:

- `time`
- `class_uid`
- `class_name`
- `category_uid`
- `category_name`
- `activity_id`
- `activity_name`
- `type_uid`
- `type_name`
- `severity_id`
- `severity`
- `message`
- `metadata.version`
- `metadata.product.name`
- `actor.user.name`
- `actor.user.uid`
- `cloud.account_uid`
- `cloud.region`
- `device.hostname`
- `dst_endpoint.ip`
- `dst_endpoint.port`
- `process.name`
- `process.pid`
- `resources[].name`
- `resources[].type`
- `src_endpoint.ip`
- `src_endpoint.port`
- `status`
- `status_id`

Implemented class registry:

- Detection Finding (`class_uid: 2004`)
- Authentication (`class_uid: 3002`)
- Network Activity (`class_uid: 4001`)
- Process Activity (`class_uid: 1007`)

Schema-version awareness currently supports `1.6.0` and `1.7.0`, with `1.7.0`
as the default expected version.

## Fixtures

The repository includes fake, realistic fixtures for local testing:

- `fixtures/aws_guardduty_finding.json`
- `fixtures/aws_securityhub_finding.json`
- `fixtures/cloudtrail_event.json`
- `fixtures/ocsf_detection_finding.json`
- `fixtures/broken_ocsf_event.json`
- `fixtures/guardduty.ndjson`

No fixture contains real secrets or real account IDs.

## Development

```bash
uv run --extra dev pytest
uv run --extra dev ruff check .
uv build
```

The CLI entry point is `ocsfkit = "ocsfkit.cli:app"`.

## Release Notes

This repository is ready for normal Python packaging with `pyproject.toml`.
Recommended release flow:

1. Tag a version: `git tag v0.2.1 && git push --tags`
2. The `.github/workflows/release.yml` workflow builds distributions.
3. PyPI publishing uses trusted publishing through `pypa/gh-action-pypi-publish`
   when `PYPI_PUBLISH_ENABLED=true` is configured as a repository variable.
4. Homebrew tap updates run when `HOMEBREW_TAP_ENABLED=true` is set as a
   repository variable and `HOMEBREW_TAP_TOKEN` is available as a secret.

Do not commit package index tokens. Use PyPI trusted publishing or repository
secrets for release automation.
