# ocsfkit Demo: GuardDuty to Reviewed OCSF

This walkthrough shows the full review loop for a real-world style source event:
raw AWS GuardDuty JSON, OCSF normalization, explainability, linting, scoring,
and release-friendly artifacts.

All identifiers in the fixture are fake.

## 1. Inspect the Raw Event

```bash
ocsfkit parse fixtures/aws_guardduty_finding.json
```

The raw event contains useful AWS-specific context such as the account, region,
finding title, severity, resource details, and nested action data.

## 2. Generate a Starter Mapping

```bash
ocsfkit suggest fixtures/aws_guardduty_finding.json --mapping-yaml \
  --product-name "Amazon GuardDuty" > /tmp/guardduty-starter.yaml
```

Suggestions are intentionally reviewable. They are a fast draft, not a silent
auto-mapper.

## 3. Map with the Reviewed Pack

```bash
ocsfkit map fixtures/aws_guardduty_finding.json --pack aws-guardduty
```

This emits an OCSF Detection Finding with `class_uid: 2004`, normalized
`severity_id`, epoch-millisecond `time`, cloud account details, product
metadata, and resource objects.

## 4. Explain Mapping Quality

```bash
ocsfkit explain fixtures/aws_guardduty_finding.json --pack aws-guardduty
```

Use this view during mapping review. It shows mapped, transformed, defaulted,
dropped, unmapped, and missing fields plus a confidence score.

## 5. Batch Convert and Generate Artifacts

```bash
ocsfkit batch fixtures/guardduty.ndjson \
  --pack aws-guardduty \
  --output /tmp/guardduty.ocsf.ndjson \
  --explain-json /tmp/guardduty.explain.json \
  --lint-json /tmp/guardduty.lint.json \
  --unmapped-json /tmp/guardduty.unmapped.json \
  --coverage-html /tmp/guardduty.coverage.html \
  --report-json /tmp/guardduty.report.json
```

These files are useful in migration pull requests because reviewers can inspect
the normalized payload and the mapping-quality evidence side by side.

## 6. Gate in CI

```bash
ocsfkit score fixtures/guardduty.ndjson \
  --pack aws-guardduty \
  --min-confidence 0.70 \
  --max-unmapped 10 \
  --github-summary
```

For code scanning, use SARIF:

```bash
ocsfkit gate fixtures/guardduty.ndjson \
  --pack aws-guardduty \
  --min-confidence 0.70 \
  --max-unmapped 10 \
  --no-strict \
  --sarif > /tmp/ocsfkit-gate.sarif
```
