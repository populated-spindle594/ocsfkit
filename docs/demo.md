# Demo: GuardDuty to Reviewed OCSF

This demo uses fake AWS GuardDuty fixtures to show the workflow security teams
usually need during an OCSF migration: normalize, explain, lint, score, and
produce review artifacts.

## Raw to OCSF

```bash
ocsfkit parse fixtures/aws_guardduty_finding.json
ocsfkit inspect fixtures/aws_guardduty_finding.json
ocsfkit path fixtures/aws_guardduty_finding.json '$.severity'
ocsfkit map fixtures/aws_guardduty_finding.json --pack aws-guardduty
```

The reviewed pack emits an OCSF Detection Finding with normalized time,
severity, cloud account, region, product metadata, and resource objects.

## Explainability

```bash
ocsfkit explain fixtures/aws_guardduty_finding.json --pack aws-guardduty
```

Review mapped, transformed, defaulted, dropped, unmapped, and missing fields
before trusting a mapping in a production pipeline.

## Batch Artifacts

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

These files make migration pull requests easier to review because the normalized
data and mapping-quality evidence are generated from the same input corpus.

## CI Gate

```bash
ocsfkit score fixtures/guardduty.ndjson \
  --pack aws-guardduty \
  --min-confidence 0.70 \
  --max-unmapped 10 \
  --github-summary
```

Or use the repository action:

```yaml
- uses: pfrederiksen/ocsfkit@v0.11.0
  with:
    input: fixtures/guardduty.ndjson
    pack: aws-guardduty
    min-confidence: "0.70"
    max-unmapped: "10"
```
