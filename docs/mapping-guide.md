# Mapping Guide

Mappings are intentionally small YAML documents. They are designed for
incremental adoption: start with the fields you understand, explicitly drop
fields you have reviewed, then drive the unmapped list toward zero.

## File Structure

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
    required: true

drop:
  - $.debug
```

## `schema_version`

Set the OCSF version your mapping targets:

```yaml
schema_version: 1.7.0
```

`ocsfkit` writes this to `metadata.version` unless the mapping explicitly sets a
different value in `target_class`. The linter supports `1.6.0` and `1.7.0` in
this release and defaults to `1.7.0`.

## `target_class`

`target_class` sets stable event classification fields before field mappings are
applied. Today the built-in registry focuses on Detection Finding:

```yaml
target_class:
  class_uid: 2004
  class_name: Detection Finding
  category_uid: 2
  category_name: Findings
```

These values are tracked as `defaulted_fields` in explain output because they
come from mapping intent rather than from the source event.

## `fields`

Each key under `fields` is an OCSF target path:

```yaml
fields:
  cloud.account_uid:
    from: $.accountId
```

Nested objects are created automatically. Array markers use `[]`:

```yaml
fields:
  resources[].name:
    from: $.Resources[].Id
```

The supported JSONPath subset is intentionally small but practical:

- `$` for the whole source event.
- `$.a.b.c` for nested object lookup.
- `$.items[].name` and `$.items[*].name` for collecting a field from each
  object in an array.
- `$.items[0].name` for selecting a single array index.
- `$.items[?type==instance].id` for simple equality filters on arrays of
  objects.

It does not support recursive descent, arbitrary expressions, joins, or complex
boolean filters. Keep enrichment outside the mapping for now.

## Provenance

Every target value gets provenance:

- `mapped`: copied from a source path.
- `transformed`: copied from source and passed through a transform.
- `defaulted`: supplied by `default` or `target_class`.
- `guessed`: supplied by `guess` to make uncertainty explicit.

Example:

```yaml
fields:
  severity_id:
    from: $.risk_label
    transform: severity_text_to_id
    default: 1

  metadata.product.name:
    default: Example EDR

  cloud.region:
    guess: us-east-1
```

Use `guess` when the value is operationally useful but not trustworthy enough to
pretend it came from the source event.

## Required Fields

Mark mapping entries as required when absence should reduce confidence and show
up in `missing_target_fields`:

```yaml
fields:
  time:
    from: $.eventTime
    transform: parse_timestamp
    required: true
```

The linter also enforces required fields from the minimal schema registry.

## Transforms

Built-in transforms:

- `parse_timestamp`: accepts epoch milliseconds, epoch seconds-like integers as
  provided, and ISO-8601 strings such as `2026-01-14T10:21:44Z`; output is epoch
  milliseconds.
- `severity_text_to_id`: maps common severity labels to OCSF-style IDs:
  `Unknown=0`, `Informational=1`, `Low=2`, `Medium=3`, `High=4`,
  `Critical=5`, `Fatal=6`.
- `severity_id_to_text`: converts the same IDs back to text.
- `to_string`: converts any value to a string.
- `to_int`: converts numeric strings and numbers to integers.
- `lower`, `upper`, `title_case`: common string normalization helpers.
- `epoch_seconds_to_ms`: converts epoch seconds to epoch milliseconds.

Vendor-oriented transform packs:

- `aws.severity`: maps AWS-style numeric or text severity values to
  `severity_id`.
- `azure.status_id` and `azure.status`: normalize common Microsoft Entra ID and
  Sentinel result/status values.
- `okta.status_id` and `okta.status`: normalize Okta outcome results.
- `network.activity_id`: maps common network actions such as allow, deny, and
  connect to stable activity IDs.

Transforms can be chained:

```yaml
fields:
  severity:
    from: $.Severity.Label
    transform:
      - lower
      - title_case
```

## Repeated Objects

Use `foreach` when a source array should become repeated OCSF objects:

```yaml
fields:
  resources[]:
    foreach:
      from: $.resources
      fields:
        name:
          from: $.id
        type:
          from: $.type
```

Each item is mapped independently. Item-level `from` paths are evaluated
relative to the current source object.

## Custom Transforms

Mappings can load local Python files that expose a `TRANSFORMS` dictionary:

```yaml
custom_transforms:
  - custom_transforms.py
custom_transforms_trusted: true

fields:
  status_id:
    from: $.responseElements.ConsoleLogin
    transform: login_status_to_id
```

Example module:

```python
def login_status_to_id(value):
    return 1 if str(value).lower() == "success" else 2


TRANSFORMS = {"login_status_to_id": login_status_to_id}
```

Custom transform files execute as Python code. Treat them like source code, not
data from untrusted parties. `validate-mapping` warns when a mapping references
custom transforms without `custom_transforms_trusted: true`, and strict mapping
commands still require `--allow-unsafe-transforms` before loading Python code.

Reusable transform packages should prefer Python entry points:

```toml
[project.entry-points."ocsfkit.transforms"]
vendor_status_id = "vendor_ocsf.transforms:status_id"
```

The entry point name becomes the transform name in mapping YAML.

## Mapping Tests

Use `test-mapping` when a mapping becomes important enough to review and release.
The spec is a tiny YAML file:

```yaml
input: ../../fixtures/aws_guardduty_finding.json
mapping: ../../examples/guardduty-mapping.yaml
expected: guardduty-expected.json
```

CI systems that collect test reports can consume JUnit directly:

```bash
ocsfkit test-mapping tests/goldens --junit ocsfkit-mapping.xml
```

Run:

```bash
ocsfkit test-mapping tests/fixtures/guardduty-test.yaml
ocsfkit test-mapping tests/fixtures/guardduty-test.yaml --json
```

The expected file should contain the mapped OCSF event. Failures are reported as
semantic field changes, additions, and removals.

## Coverage Budgets

Use `coverage` to review mapping quality across NDJSON streams:

```bash
ocsfkit coverage fixtures/guardduty.ndjson \
  --mapping examples/guardduty-mapping.yaml
```

Quality budgets make this useful in CI:

```bash
ocsfkit coverage fixtures/guardduty.ndjson \
  --mapping examples/guardduty-mapping.yaml \
  --min-confidence 0.80 \
  --max-unmapped 25
```

Budgets are intentionally simple:

- `--min-confidence` fails when average explanation confidence is below the
  threshold.
- `--max-unmapped` fails when the total unmapped source-field observations are
  above the threshold.

Generate a shareable HTML version with:

```bash
ocsfkit report fixtures/guardduty.ndjson \
  --mapping examples/guardduty-mapping.yaml \
  --output report.html
```

Generate Markdown or GitHub Actions job summaries with:

```bash
ocsfkit coverage fixtures/guardduty.ndjson \
  --mapping examples/guardduty-mapping.yaml \
  --markdown

ocsfkit coverage fixtures/guardduty.ndjson \
  --mapping examples/guardduty-mapping.yaml \
  --github-summary
```

Use SARIF when coverage or scorecard failures should appear in code scanning:

```bash
ocsfkit coverage fixtures/guardduty.ndjson \
  --mapping examples/guardduty-mapping.yaml \
  --min-confidence 0.80 \
  --max-unmapped 25 \
  --sarif > ocsfkit-coverage.sarif

ocsfkit scorecard fixtures/guardduty.ndjson \
  --mapping examples/guardduty-mapping.yaml \
  --min-confidence 0.80 \
  --max-unmapped 25 \
  --sarif > ocsfkit-scorecard.sarif
```

Strict mode turns explanation uncertainty into failures:

```bash
ocsfkit explain fixtures/aws_guardduty_finding.json \
  --mapping examples/guardduty-mapping.yaml \
  --strict
```

## Workshop Flow

For a new source, workshop mode prints all source paths:

```bash
ocsfkit workshop fixtures/wiz_finding.json
```

With an existing mapping, it appends the explanation report:

```bash
ocsfkit workshop fixtures/wiz_finding.json \
  --mapping examples/wiz-finding-mapping.yaml
```

Pair it with `init-mapping` to create a first draft, then iterate through
`explain`, `coverage`, and `test-mapping`.

For an even faster starting point, use heuristic suggestions:

```bash
ocsfkit suggest fixtures/wiz_finding.json
ocsfkit suggest fixtures/wiz_finding.json --mapping-yaml > starter.yaml
```

Suggestions are intentionally conservative. Treat them as a review queue, not as
an automatic migration.

## Target Discovery

Use `targets` when choosing OCSF fields:

```bash
ocsfkit targets list
ocsfkit targets search endpoint
ocsfkit targets show metadata.product.name
```

This is intentionally a local convenience layer over the bundled registry, not a
replacement for the full OCSF documentation.

## Mapping Packs

Built-in packs group included examples by source family:

```bash
ocsfkit pack list
ocsfkit pack validate
ocsfkit map fixtures/aws_guardduty_finding.json --pack aws-guardduty
ocsfkit explain fixtures/aws_guardduty_finding.json --pack guardduty
```

Packs are included in installed wheels, so CI jobs can use aliases without
checking out the repository's `examples/` directory. Use the aliases printed by
`pack list`, such as `aws-guardduty`, `identity-okta-authentication`, or
`network-zeek-conn`.

External packs can be installed from a local directory, local zip, or HTTPS zip
archive. A pack can include a `pack.yaml` manifest and any number of mapping
YAML files:

```bash
ocsfkit pack install ./company-packs --name company
ocsfkit pack list
ocsfkit explain sample.json --pack company/guardduty
ocsfkit pack update company
```

Prefer immutable release archives in CI so mapping pack updates are reviewed and
repeatable.

Once a mapping has no unexpected unmapped fields, use a strict production gate:

```bash
ocsfkit gate fixtures/guardduty.ndjson \
  --pack aws-guardduty \
  --min-confidence 0.85 \
  --max-unmapped 0
```

## Dropping Source Fields

Use `drop` only for fields you intentionally reviewed:

```yaml
drop:
  - $.debug
  - $.rawPayload
```

Dropped fields remain visible in explain output. Unreviewed fields stay in
`unmapped_source_fields`, which is the main guardrail against silent data loss.

## Real Mapping Workflow

1. Map only the fields you understand.
2. Use `workshop` to inspect source paths and review the draft.
3. Run `ocsfkit explain --json` and sort by `unmapped_source_fields`.
4. Add mappings for high-value fields.
5. Add `drop` entries for noisy fields after review.
6. Run `ocsfkit coverage` with budgets on representative streams.
7. Add `test-mapping` fixtures for important mappings.
8. Run `ocsfkit lint` on mapped output.
9. Use `ocsfkit diff` before replacing a production mapping.

## Built-In Class Coverage

The registry is intentionally small but no longer single-class:

- `2004` Detection Finding
- `3002` Authentication
- `4001` Network Activity
- `1007` Process Activity

Each class defines required and recommended fields independently so mappings can
be linted according to the class they produce.
