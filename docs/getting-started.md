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

