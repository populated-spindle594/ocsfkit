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

Homebrew:

```bash
brew tap pfrederiksen/tap
brew install ocsfkit
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
- [Docs Site](docs/site/index.html): static site source for GitHub Pages.

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
ocsfkit coverage fixtures/guardduty.ndjson --mapping examples/guardduty-mapping.yaml
ocsfkit coverage fixtures/guardduty.ndjson --mapping examples/guardduty-mapping.yaml --min-confidence 0.7 --max-unmapped 10 --github-summary
ocsfkit validate-mapping examples/guardduty-mapping.yaml
ocsfkit init-mapping fixtures/aws_guardduty_finding.json
ocsfkit test-mapping tests/fixtures/guardduty-test.yaml
ocsfkit report fixtures/guardduty.ndjson --mapping examples/guardduty-mapping.yaml --output report.html
ocsfkit workshop fixtures/aws_guardduty_finding.json --mapping examples/guardduty-mapping.yaml
ocsfkit targets search user
ocsfkit pack list
ocsfkit import-schema ./ocsf-schema-export
ocsfkit sync-schema --output ocsf-schema.json
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
ocsfkit map <input> --mapping mapping.yaml [--format json|ndjson] [--explain] [--strict]
```

Without `--explain`, output is the mapped event. With `--explain`, each output
item contains both `event` and `explanation`.
`--strict` fails on guessed fields, missing targets, and unmapped source fields.
When strict mode is enabled, Python `custom_transforms` files are blocked unless
`--allow-unsafe-transforms` is also set.

### `explain`

Shows the mapping decision report without making users inspect the mapped event
by hand.

```bash
ocsfkit explain <input> --mapping mapping.yaml [--json] [--github-annotations]
ocsfkit explain <input> --mapping mapping.yaml --markdown
ocsfkit explain <input> --mapping mapping.yaml --html --output explanation.html
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

### `coverage`

Summarizes mapping quality across an event stream.

```bash
ocsfkit coverage <input> --mapping mapping.yaml [--json|--markdown]
ocsfkit coverage <input> --mapping mapping.yaml --min-confidence 0.80 --max-unmapped 25
```

Coverage exits non-zero when a configured quality budget fails. This is useful
for CI gates that allow gradual mapping work while preventing regressions.
Use `--github-summary` in GitHub Actions to append a Markdown summary to the job
summary.

### `validate-mapping`

Checks a mapping file before it is used against events.

```bash
ocsfkit validate-mapping examples/guardduty-mapping.yaml
ocsfkit validate-mapping examples/guardduty-mapping.yaml --strict
```

It reports malformed field specs, unknown built-in transforms, and likely schema
issues without needing a source event. Strict validation treats warnings as
release-blocking failures.

### `init-mapping`

Generates a starter mapping from a representative event.

```bash
ocsfkit init-mapping fixtures/aws_guardduty_finding.json --product-name "Amazon GuardDuty"
```

Treat the output as a review worksheet, not a complete mapping.

### `test-mapping`

Runs a fixture-based mapping regression test.

```bash
ocsfkit test-mapping tests/fixtures/guardduty-test.yaml
```

The spec points at a source input, a mapping, and expected OCSF JSON. Any
semantic difference is reported with the same diff engine as `ocsfkit diff`.

### `report`

Writes a standalone HTML mapping coverage report.

```bash
ocsfkit report fixtures/guardduty.ndjson \
  --mapping examples/guardduty-mapping.yaml \
  --output report.html
```

Use this when a mapping review needs to be shared outside a terminal or CI log.

### `workshop`

Prints a guided mapping worksheet from a source event. With a mapping, it also
renders the explanation report.

```bash
ocsfkit workshop fixtures/aws_guardduty_finding.json
ocsfkit workshop fixtures/aws_guardduty_finding.json --mapping examples/guardduty-mapping.yaml
```

### `schema` and `import-schema`

`schema` emits the bundled minimal registry. `import-schema` converts an
upstream-style JSON/YAML schema file or directory into the small registry shape
that `ocsfkit` understands.

```bash
ocsfkit schema --schema-version 1.7.0
ocsfkit import-schema ./ocsf-schema-export > schema.json
ocsfkit sync-schema --output schema.json
```

`sync-schema` downloads the upstream OCSF schema archive and imports it into the
same compact registry format. This keeps production pipelines able to refresh
schema data without vendoring the full upstream repository.

### `targets`

Search bundled target fields from the terminal:

```bash
ocsfkit targets list
ocsfkit targets search endpoint
ocsfkit targets show actor.user.name
```

### `pack`

List and validate built-in mapping packs:

```bash
ocsfkit pack list
ocsfkit pack validate
```

Packs group included mappings by source family, such as AWS, identity, network,
detections, and infrastructure.

## Mapping Format

Mappings are YAML. Source paths use a deliberate JSONPath subset such as
`$.eventTime`, `$.Resources[*].Id`, `$.items[0].name`, and
`$.items[?type==instance].id`. Target paths use dotted OCSF paths such as
`cloud.account_uid` and `actor.user.name`.

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

Built-in transforms include common OCSF helpers plus vendor-oriented transform
packs such as `aws.severity`, `azure.status_id`, `azure.status`,
`okta.status_id`, `okta.status`, and `network.activity_id`.

Included examples:

- [GuardDuty mapping](examples/guardduty-mapping.yaml)
- [Security Hub mapping](examples/securityhub-mapping.yaml)
- [CloudTrail console login mapping](examples/cloudtrail-console-login-mapping.yaml)
- [Custom transform module](examples/custom_transforms.py)
- Okta, Microsoft Entra ID, GitHub Audit Log, CrowdStrike, Palo Alto, and Zeek mappings.
- Splunk ES, Microsoft Sentinel, Defender, Wiz, Lacework, GCP SCC, Cloudflare,
  and Kubernetes audit mappings.

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
- `fixtures/azure_ad_signin.json`
- `fixtures/okta_login_event.json`
- `fixtures/github_audit_event.json`
- `fixtures/crowdstrike_detection.json`
- `fixtures/paloalto_traffic.json`
- `fixtures/zeek_conn.json`
- `fixtures/splunk_notable.json`
- `fixtures/sentinel_alert.json`
- `fixtures/defender_alert.json`
- `fixtures/wiz_finding.json`
- `fixtures/lacework_alert.json`
- `fixtures/gcp_scc_finding.json`
- `fixtures/cloudflare_log.json`
- `fixtures/kubernetes_audit.json`
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

1. Tag a version: `git tag v0.5.0 && git push --tags`
2. The `.github/workflows/release.yml` workflow builds distributions.
3. PyPI publishing uses Trusted Publishing when configured, with
   `PYPI_API_TOKEN` as a fallback.
4. Homebrew tap updates run when `HOMEBREW_TAP_ENABLED=true` is set as a
   repository variable and `HOMEBREW_TAP_TOKEN` is available as a secret.
5. GitHub Actions are pinned to commit SHAs, and release artifacts get GitHub
   provenance attestations.

Do not commit package index tokens. Use PyPI trusted publishing or repository
secrets for release automation.
