# Getting Started

This guide walks through the fastest path from raw cloud telemetry to an OCSF
Detection Finding with mapping quality visible at every step.

## 1. Inspect the Raw Event

Start by confirming that the input loader understands the file:

```bash
ocsfkit parse fixtures/aws_guardduty_finding.json
```

For log streams, use NDJSON:

```bash
ocsfkit parse fixtures/guardduty.ndjson --format ndjson
```

Use `-` for stdin when data comes from another tool:

```bash
aws guardduty get-findings --detector-id d-EXAMPLE --finding-ids sample \
  | ocsfkit parse -
```

`parse` does not claim the event is OCSF. It only normalizes JSON, YAML, or
NDJSON into predictable JSON output so the next command gets clean input.

## 2. Apply a Mapping

Map the GuardDuty fixture into the initial Detection Finding schema:

```bash
ocsfkit map fixtures/aws_guardduty_finding.json \
  --mapping examples/guardduty-mapping.yaml
```

Built-in mapping packs are available in installed releases. For GuardDuty, the
equivalent shortcut is:

```bash
ocsfkit map fixtures/aws_guardduty_finding.json --pack aws-guardduty
```

Expected high-value fields in the output include:

```json
{
  "class_uid": 2004,
  "class_name": "Detection Finding",
  "severity_id": 4,
  "metadata": {
    "product": {
      "name": "Amazon GuardDuty"
    }
  },
  "cloud": {
    "account_uid": "111122223333",
    "region": "us-east-1"
  }
}
```

## 3. Explain the Mapping

The explain command is the main workbench view:

```bash
ocsfkit explain fixtures/aws_guardduty_finding.json \
  --mapping examples/guardduty-mapping.yaml
```

You can use `--pack aws-guardduty` with `explain` as well.

Use JSON for automation or CI:

```bash
ocsfkit explain fixtures/aws_guardduty_finding.json \
  --mapping examples/guardduty-mapping.yaml \
  --json
```

Review these sections first:

- `mapped_fields`: source fields that landed in OCSF targets.
- `defaulted_fields`: values supplied by the mapping, such as product name.
- `guessed_fields`: values intentionally marked as lower confidence guesses.
- `dropped_fields`: fields explicitly ignored by the mapping.
- `unmapped_source_fields`: source fields that were neither mapped nor dropped.
- `missing_target_fields`: required target fields still absent after mapping.
- `confidence`: a compact score for triage, not a formal OCSF certification.

## 4. Lint the OCSF Event

After mapping, lint the event:

```bash
ocsfkit map fixtures/aws_guardduty_finding.json \
  --mapping examples/guardduty-mapping.yaml \
  > /tmp/guardduty-ocsf.json

ocsfkit lint /tmp/guardduty-ocsf.json
```

Lint exits non-zero when required fields or bad types are found. Use
`--warn-only` during exploratory migrations where you want a report without
failing the job.

For CI systems that understand SARIF:

```bash
ocsfkit lint /tmp/guardduty-ocsf.json --sarif > ocsfkit.sarif
```

For GitHub Actions log annotations:

```bash
ocsfkit lint /tmp/guardduty-ocsf.json --github-annotations
ocsfkit explain fixtures/aws_guardduty_finding.json \
  --mapping examples/guardduty-mapping.yaml \
  --github-annotations
```

## 5. Query Fields for Checks

Use `query` for quick shell-friendly assertions:

```bash
ocsfkit query /tmp/guardduty-ocsf.json severity_id
ocsfkit query /tmp/guardduty-ocsf.json metadata.product.name
ocsfkit query /tmp/guardduty-ocsf.json cloud.account_uid
```

For NDJSON streams, one result is printed per event.

## 6. Diff Mapping Changes

When changing a mapping, compare the old and new output:

```bash
ocsfkit diff /tmp/old-ocsf.ndjson /tmp/new-ocsf.ndjson
```

Class and severity changes are highlighted in the human-readable output because
they tend to affect downstream detections, dashboards, and routing.

## 7. Measure Coverage Across a Stream

Once one event looks right, run the mapping over a stream and look for recurring
unmapped fields:

```bash
ocsfkit coverage fixtures/guardduty.ndjson \
  --mapping examples/guardduty-mapping.yaml
```

Use quality budgets in CI:

```bash
ocsfkit coverage fixtures/guardduty.ndjson \
  --mapping examples/guardduty-mapping.yaml \
  --min-confidence 0.80 \
  --max-unmapped 25 \
  --github-summary
```

The command exits non-zero when a budget fails. JSON mode includes
`threshold_failures` so CI logs and dashboards can explain the failure.
SARIF mode can publish threshold failures into code scanning:

```bash
ocsfkit coverage fixtures/guardduty.ndjson \
  --pack aws-guardduty \
  --min-confidence 0.80 \
  --max-unmapped 25 \
  --sarif > ocsfkit-coverage.sarif
```

For a single production-readiness gate that combines coverage, lint, and
strict-mode checks, use `scorecard` or the stricter `gate` shortcut:

```bash
ocsfkit scorecard fixtures/guardduty.ndjson \
  --mapping examples/guardduty-mapping.yaml \
  --min-confidence 0.80 \
  --max-unmapped 25 \
  --github-summary

ocsfkit gate fixtures/guardduty.ndjson \
  --pack aws-guardduty \
  --min-confidence 0.70 \
  --max-unmapped 10 \
  --no-strict \
  --sarif > ocsfkit-gate.sarif
```

For review meetings or tickets, generate a standalone HTML report:

```bash
ocsfkit report fixtures/guardduty.ndjson \
  --mapping examples/guardduty-mapping.yaml \
  --output report.html
```

## 8. Lock in Regression Tests

Mapping behavior should be testable like code. A mapping test spec names the
input event, mapping, and expected OCSF output:

```yaml
input: ../../fixtures/aws_guardduty_finding.json
mapping: ../../examples/guardduty-mapping.yaml
expected: guardduty-expected.json
```

Run it with:

```bash
ocsfkit test-mapping tests/fixtures/guardduty-test.yaml
ocsfkit test-mapping tests/fixtures
ocsfkit test-mapping tests/fixtures --junit ocsfkit-mapping.xml
```

If the mapping output changes, `test-mapping` prints a semantic diff and exits
non-zero.

Use strict mode once a mapping is expected to be production-ready:

```bash
ocsfkit map fixtures/aws_guardduty_finding.json \
  --mapping examples/guardduty-mapping.yaml \
  --strict
```

Strict mode fails on guessed fields, missing target fields, and unmapped source
fields. It also blocks Python `custom_transforms` files unless
`--allow-unsafe-transforms` is set.
Mappings that use reviewed Python transforms should set
`custom_transforms_trusted: true` so validation makes the trust decision
explicit.

## 9. Scan, Redact, and Benchmark Fixtures

Before a fixture goes into a ticket, docs page, or public repository, scan it:

```bash
ocsfkit scan fixtures --warn-only
ocsfkit scan fixtures --sarif --warn-only > ocsfkit-privacy.sarif
```

Create a shareable redacted sample while preserving the original event shape:

```bash
ocsfkit redact fixtures/aws_guardduty_finding.json --output /tmp/guardduty-redacted.json
```

Check local release readiness and mapping throughput:

```bash
ocsfkit doctor
ocsfkit benchmark fixtures/guardduty.ndjson \
  --mapping examples/guardduty-mapping.yaml \
  --iterations 3
```

## 10. Use Workshop Mode for New Sources

When onboarding a new product, start by listing every source path:

```bash
ocsfkit workshop fixtures/splunk_notable.json
```

After drafting a mapping, rerun workshop with the mapping to view source paths
and explanation output together:

```bash
ocsfkit workshop fixtures/splunk_notable.json \
  --mapping examples/splunk-notable-mapping.yaml
```

For an interactive first pass, write accepted mappings and drops directly to a
new YAML file:

```bash
ocsfkit workshop fixtures/splunk_notable.json \
  --interactive \
  --output splunk-draft.yaml
```

`init-mapping` can generate a starter YAML from common field names:

```bash
ocsfkit init-mapping fixtures/splunk_notable.json \
  --product-name "Splunk Enterprise Security"
```

## 10. Check Schema Version

Mappings default to OCSF `1.7.0` unless `schema_version` is set. Lint can enforce
the expected version:

```bash
ocsfkit lint /tmp/guardduty-ocsf.json --schema-version 1.7.0
```

The bundled schema slice can be inspected directly:

```bash
ocsfkit schema --schema-version 1.7.0
```

For editor integrations or external validators, export JSON Schema:

```bash
ocsfkit schema --schema-version 1.7.0 --format jsonschema > ocsfkit.schema.json
```

If you have a JSON/YAML export from an upstream schema source, normalize it into
the small registry shape used by `ocsfkit`:

```bash
ocsfkit import-schema ./ocsf-schema-export > imported-schema.json
ocsfkit sync-schema --output imported-schema.json
```

## 11. Discover Targets and Packs

Search the bundled schema slice without leaving the terminal:

```bash
ocsfkit targets search user
ocsfkit targets show actor.user.name
```

Review the included mapping packs:

```bash
ocsfkit pack list
ocsfkit pack validate
```

Pack aliases work directly with mapping-quality commands:

```bash
ocsfkit explain fixtures/aws_guardduty_finding.json --pack aws-guardduty
ocsfkit scorecard fixtures/guardduty.ndjson --pack aws-guardduty --max-unmapped 25
```

Generate the mapping catalog and check for schema drift:

```bash
ocsfkit catalog --output docs/mapping-catalog.md
ocsfkit schema-drift examples/guardduty-mapping.yaml
```

Custom transform behavior can be tested with YAML cases:

```bash
ocsfkit test-transform tests/fixtures/transform-test.yaml
```
