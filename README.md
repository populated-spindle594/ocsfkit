# ocsfkit

`ocsfkit` is an OCSF workbench for security engineers who need to normalize,
lint, explain, diff, and query security events without losing sight of mapping
quality.

Most OCSF migration work fails in the gaps between "the JSON parsed" and "the
event is trustworthy." `ocsfkit` is built for those gaps. It shows what class an
event became, which fields mapped cleanly, which values were defaulted or
guessed, which source fields were dropped, and what is still missing.

## Why Use It?

- **Make mappings reviewable.** Every mapped value carries provenance: source,
  transform, default, or guess.
- **Catch silent data loss.** Dropped and unmapped source fields are visible in
  explain, coverage, and strict mode.
- **Ship safer pipelines.** Lint, coverage budgets, SARIF, GitHub annotations,
  and GitHub summaries fit naturally into CI.
- **Compare semantic changes.** Diff OCSF events by field meaning instead of raw
  formatting noise.
- **Start small, grow later.** The built-in registry covers practical OCSF
  Detection Finding, Authentication, Network Activity, and Process Activity
  workflows, and can import or sync upstream schema data.

## Contents

- [Install](#install)
- [Five Minute Tour](#five-minute-tour)
- [Example Output](#example-output)
- [Common Workflows](#common-workflows)
- [Command Reference](#command-reference)
- [Mapping Files](#mapping-files)
- [Built-In OCSF Scope](#built-in-ocsf-scope)
- [Fixtures and Examples](#fixtures-and-examples)
- [Production Use](#production-use)
- [Development](#development)
- [Release Automation](#release-automation)

## Install

```bash
pip install ocsfkit
```

Homebrew:

```bash
brew tap pfrederiksen/tap
brew install ocsfkit
```

From a checkout:

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e ".[dev]"
```

## Five Minute Tour

Parse JSON, YAML, NDJSON, or stdin:

```bash
ocsfkit parse fixtures/aws_guardduty_finding.json
ocsfkit parse fixtures/guardduty.ndjson --format ndjson
cat fixtures/aws_guardduty_finding.json | ocsfkit parse -
```

Map a GuardDuty finding into an OCSF Detection Finding:

```bash
ocsfkit map fixtures/aws_guardduty_finding.json \
  --mapping examples/guardduty-mapping.yaml
```

Explain whether that mapping is good enough to trust:

```bash
ocsfkit explain fixtures/aws_guardduty_finding.json \
  --mapping examples/guardduty-mapping.yaml
```

Gate a stream in CI:

```bash
ocsfkit scorecard fixtures/guardduty.ndjson \
  --mapping examples/guardduty-mapping.yaml \
  --min-confidence 0.70 \
  --max-unmapped 10 \
  --github-summary
```

Lint OCSF-looking events:

```bash
ocsfkit lint fixtures/ocsf_detection_finding.json
ocsfkit lint fixtures/broken_ocsf_event.json --sarif
```

Query common OCSF fields:

```bash
ocsfkit query fixtures/ocsf_detection_finding.json metadata.product.name
```

## Example Output

### Mapping output

```bash
ocsfkit map fixtures/aws_guardduty_finding.json \
  --mapping examples/guardduty-mapping.yaml
```

Abbreviated output:

```json
{
  "class_uid": 2004,
  "class_name": "Detection Finding",
  "category_uid": 2,
  "category_name": "Findings",
  "severity_id": 4,
  "severity": "High",
  "time": 1768386104000,
  "message": "EC2 instance i-0123456789abcdef0 communicating with suspicious host",
  "cloud": {
    "account_uid": "111122223333",
    "region": "us-east-1"
  },
  "metadata": {
    "product": {
      "name": "Amazon GuardDuty"
    },
    "version": "1.7.0"
  }
}
```

### Explain output

```bash
ocsfkit explain fixtures/aws_guardduty_finding.json \
  --mapping examples/guardduty-mapping.yaml
```

Abbreviated output:

```text
Confidence: 0.462
Target class: Detection Finding (class_uid 2004)

Mapped fields
  time              $.eventTime     parse_timestamp       1768386104000
  severity_id       $.severity      severity_text_to_id   4
  severity          $.severity                            "High"
  message           $.title                               "EC2 instance..."
  cloud.account_uid $.accountId                           "111122223333"
  cloud.region      $.region                              "us-east-1"

Defaulted fields
  class_uid              2004
  class_name             "Detection Finding"
  category_uid           2
  metadata.version       "1.7.0"
  metadata.product.name  "Amazon GuardDuty"

Dropped fields
  $.debug
  $.rawPayload

Unmapped source fields
  $.id
  $.resource.instanceDetails.instanceType
  $.service.action.awsApiCallAction.remoteIpDetails.ipAddressV4
```

The real terminal output uses Rich tables. JSON, Markdown, HTML, and GitHub
annotation modes are available when the report needs to feed another tool.

### Lint output

```bash
ocsfkit lint fixtures/broken_ocsf_event.json
```

```text
Event 1 lint
  warning  message                Missing recommended field
  warning  metadata.product.name  Missing recommended field
  error    time                   Expected int, got str
  error    class_name             Expected 'Detection Finding' for class_uid 2004
  error    severity_id            Invalid severity_id
```

`lint` exits non-zero on errors unless `--warn-only` is set.

### Coverage output

```bash
ocsfkit coverage fixtures/guardduty.ndjson \
  --mapping examples/guardduty-mapping.yaml \
  --markdown
```

### Scorecard output

```bash
ocsfkit scorecard fixtures/guardduty.ndjson \
  --mapping examples/guardduty-mapping.yaml \
  --min-confidence 0.70 \
  --max-unmapped 10
```

```text
Grade: C
Passed: yes
Events: 2
Average confidence: 0.734
Source field coverage: 0.889
Unmapped source fields: 4
Missing target fields: 0
Lint errors: 0
```

```markdown
## ocsfkit Coverage

- Events: 2
- Average confidence: 0.734
- Source field coverage: 0.889

### Top Unmapped Source Fields

- `$.resource`: 2
- `$.resource.instanceDetails`: 2
```

## Common Workflows

### Review a New Vendor Mapping

```bash
ocsfkit init-mapping fixtures/aws_guardduty_finding.json \
  --product-name "Amazon GuardDuty" > mapping-draft.yaml

ocsfkit explain fixtures/aws_guardduty_finding.json \
  --mapping mapping-draft.yaml \
  --markdown

ocsfkit validate-mapping mapping-draft.yaml --strict
```

Use this when onboarding a new log source. The generated mapping is a worksheet,
not a finished answer. Review unmapped fields before production use.

### Prevent Regressions in CI

```bash
ocsfkit lint fixtures/ocsf_detection_finding.json --sarif

ocsfkit coverage fixtures/guardduty.ndjson \
  --mapping examples/guardduty-mapping.yaml \
  --min-confidence 0.80 \
  --max-unmapped 25 \
  --github-summary

ocsfkit scorecard fixtures/guardduty.ndjson \
  --mapping examples/guardduty-mapping.yaml \
  --min-confidence 0.80 \
  --max-unmapped 25 \
  --github-summary
```

This catches missing OCSF fields, invalid types, falling confidence, and newly
unmapped vendor fields.

### Compare Mapping Versions

```bash
ocsfkit map sample.json --mapping mapping-v1.yaml > before.json
ocsfkit map sample.json --mapping mapping-v2.yaml > after.json
ocsfkit diff before.json after.json
```

This highlights field-level OCSF changes, including class and severity changes
that can affect routing, alerting, and dashboards.

### Explore Supported Targets

```bash
ocsfkit targets search user
ocsfkit targets show actor.user.name
ocsfkit pack list
ocsfkit pack validate
```

Use target discovery and mapping packs when building mappings for common source
families such as AWS, identity, network, detections, and infrastructure.

## Command Reference

| Command | Purpose |
| --- | --- |
| `parse <input>` | Load JSON, YAML, NDJSON, or stdin and emit normalized JSON. |
| `map <input> --mapping mapping.yaml` | Apply a mapping and emit OCSF JSON. |
| `explain <input> --mapping mapping.yaml` | Show mapping decisions, dropped fields, unmapped fields, missing targets, and confidence. |
| `lint <input>` | Validate OCSF-looking events against the bundled registry. |
| `diff <before> <after>` | Compare two OCSF events or same-length event streams. |
| `query <input> <path>` | Extract common OCSF fields with dotted paths. |
| `coverage <input> --mapping mapping.yaml` | Summarize mapping quality across a stream and enforce quality budgets. |
| `scorecard <input> --mapping mapping.yaml` | Grade mapping readiness with coverage, lint, and strict checks. |
| `validate-mapping mapping.yaml` | Check mapping syntax, transforms, and likely schema issues. |
| `schema-drift mapping.yaml` | Compare a mapping against bundled or synced schema data. |
| `catalog` | Generate Markdown or JSON docs from mapping YAML files. |
| `init-mapping <input>` | Generate a starter mapping worksheet from a representative event. |
| `test-mapping spec.yaml` | Run fixture-based mapping regression tests. |
| `test-transform spec.yaml` | Run YAML-defined tests for built-in or custom transforms. |
| `report <input> --mapping mapping.yaml` | Write a standalone HTML mapping coverage report. |
| `workshop <input>` | Print a guided mapping worksheet and optional explanation report. |
| `schema` | Print the bundled minimal OCSF registry. |
| `import-schema <path>` | Convert upstream-style schema files into the compact registry format. |
| `sync-schema --output schema.json` | Download upstream OCSF schema data and import it. |
| `targets list/search/show` | Discover known OCSF target fields. |
| `pack list/validate` | Inspect and validate included mapping packs. |

Useful output modes:

```bash
ocsfkit explain sample.json --mapping mapping.yaml --json
ocsfkit explain sample.json --mapping mapping.yaml --markdown
ocsfkit explain sample.json --mapping mapping.yaml --html --output explanation.html
ocsfkit lint sample.json --github-annotations
ocsfkit coverage sample.ndjson --mapping mapping.yaml --github-summary
ocsfkit scorecard sample.ndjson --mapping mapping.yaml --markdown
ocsfkit catalog --output docs/mapping-catalog.md
```

Strict mode is available on mapping-quality commands:

```bash
ocsfkit map sample.json --mapping mapping.yaml --strict
ocsfkit explain sample.json --mapping mapping.yaml --strict
ocsfkit coverage sample.ndjson --mapping mapping.yaml --strict
ocsfkit validate-mapping mapping.yaml --strict
ocsfkit schema-drift mapping.yaml
```

Strict mode fails on guessed fields, missing targets, and unmapped source fields.
Python `custom_transforms` are blocked in strict mode unless
`--allow-unsafe-transforms` is explicitly provided.

## Mapping Files

Mappings are YAML. Source paths use a deliberate JSONPath subset, and target
paths use dotted OCSF paths.

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

  actor.user.name:
    from: $.userIdentity.userName

drop:
  - $.debug
  - $.rawPayload
```

Supported source path examples:

- `$.eventTime`
- `$.Resources[*].Id`
- `$.items[0].name`
- `$.items[?type==instance].id`

The mapping engine tracks whether every target value came from a source field,
a transform, a default, or a guess. Unknown source fields that are not mapped or
explicitly dropped are reported as unmapped.

Built-in transforms include OCSF helpers and vendor-oriented transform packs:

- `parse_timestamp`
- `severity_text_to_id`
- `aws.severity`
- `azure.status_id`
- `azure.status`
- `okta.status_id`
- `okta.status`
- `network.activity_id`

See the [Mapping Guide](docs/mapping-guide.md) for advanced examples,
provenance details, custom transforms, and strict-mode guidance.

## Built-In OCSF Scope

`ocsfkit` intentionally starts with a practical minimal registry. It currently
focuses on these classes:

- Detection Finding (`class_uid: 2004`)
- Authentication (`class_uid: 3002`)
- Network Activity (`class_uid: 4001`)
- Process Activity (`class_uid: 1007`)

Common fields include:

- Base event fields: `time`, `class_uid`, `class_name`, `category_uid`,
  `category_name`, `activity_id`, `activity_name`, `type_uid`, `type_name`,
  `severity_id`, `severity`, `message`
- Metadata: `metadata.version`, `metadata.product.name`
- Identity and cloud: `actor.user.name`, `actor.user.uid`,
  `cloud.account_uid`, `cloud.region`
- Endpoint and process: `device.hostname`, `src_endpoint.ip`,
  `src_endpoint.port`, `dst_endpoint.ip`, `dst_endpoint.port`, `process.name`,
  `process.pid`
- Resources and status: `resources[].name`, `resources[].type`, `status`,
  `status_id`

Schema-version awareness currently supports `1.6.0` and `1.7.0`, with `1.7.0`
as the default expected version.

## Fixtures and Examples

The repository includes fake but realistic fixtures. They are designed for
tests, demos, mapping review, and documentation. No fixture contains real
secrets or real account IDs.

Included source fixtures cover:

- AWS GuardDuty
- AWS Security Hub
- AWS CloudTrail
- AWS VPC Flow Logs
- Azure AD sign-in
- Azure Activity Logs
- Okta login
- GitHub Audit Log
- Google Cloud Audit Logs
- CrowdStrike detection
- Palo Alto traffic
- Zeek connection logs
- Splunk ES notable events
- Microsoft Sentinel alerts
- Microsoft Defender alerts
- Wiz findings
- Lacework alerts
- GCP Security Command Center findings
- Cloudflare logs
- Kubernetes audit events
- Microsoft Sysmon process events
- Windows Security authentication events

Important files:

- [GuardDuty mapping](examples/guardduty-mapping.yaml)
- [Security Hub mapping](examples/securityhub-mapping.yaml)
- [CloudTrail console login mapping](examples/cloudtrail-console-login-mapping.yaml)
- [AWS VPC Flow Logs mapping](examples/aws-vpc-flow-mapping.yaml)
- [Google Cloud Audit mapping](examples/google-cloud-audit-mapping.yaml)
- [Sysmon process mapping](examples/sysmon-process-mapping.yaml)
- [Windows Security authentication mapping](examples/windows-security-auth-mapping.yaml)
- [Custom transform module](examples/custom_transforms.py)
- [OCSF Detection Finding fixture](fixtures/ocsf_detection_finding.json)
- [Broken OCSF fixture](fixtures/broken_ocsf_event.json)
- [GuardDuty NDJSON fixture](fixtures/guardduty.ndjson)

More workflow documentation:

- [Getting Started](docs/getting-started.md)
- [Install Guide](docs/install.md)
- [Mapping Guide](docs/mapping-guide.md)
- [Mapping Catalog](docs/mapping-catalog.md)
- [Real-World Workflows](docs/real-world-workflows.md)
- [Static Docs Site](docs/site/index.html)

## Production Use

`ocsfkit` includes supporting files for common production paths:

- `Dockerfile` for containerized CI or build-agent usage.
- `.github/workflows/docker.yml` for GHCR image builds on pushes and tagged releases.
- `.pre-commit-hooks.yaml` for validating mappings before commit.
- `ocsfkit scorecard` for a single pass/fail readiness gate.
- `ocsfkit catalog` for generated mapping documentation.
- `ocsfkit schema-drift` for checking mappings against bundled or synced schema data.

See the [Install Guide](docs/install.md) for `pipx`, `uvx`, `pip`, Homebrew,
Docker, GitHub Actions, and pre-commit examples.

## Development

```bash
uv run --extra dev pytest
uv run --extra dev ruff check .
uv build
```

The CLI entry point is:

```text
ocsfkit = "ocsfkit.cli:app"
```

## Release Automation

The repository is configured for normal Python and Homebrew releases:

1. Tag a version, for example `git tag v0.5.0 && git push --tags`.
2. `.github/workflows/release.yml` builds source and wheel distributions.
3. PyPI publishing uses Trusted Publishing when configured, with
   `PYPI_API_TOKEN` as a fallback.
4. Homebrew tap updates run when `HOMEBREW_TAP_ENABLED=true` is set and
   `HOMEBREW_TAP_TOKEN` is available.
5. GitHub Actions are pinned to commit SHAs.
6. Release artifacts get GitHub provenance attestations.

Do not commit package index tokens. Use PyPI Trusted Publishing or repository
secrets for release automation.
