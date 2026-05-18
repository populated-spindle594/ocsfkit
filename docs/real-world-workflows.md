# Real-World Workflows

These examples use fake account IDs and fixture data, but the command patterns
match common security engineering work.

## Normalize GuardDuty Findings

GuardDuty findings are already detection-like, so the mapping is direct:

```bash
ocsfkit explain fixtures/aws_guardduty_finding.json \
  --mapping examples/guardduty-mapping.yaml
```

Typical review questions:

- Did `severity` become a valid `severity_id`?
- Did `accountId` and `region` land in `cloud`?
- Did the affected EC2 instance land in `resources[]`?
- Which network details are still unmapped?

The fixture intentionally leaves fields such as remote IP address unmapped
because the first schema slice does not yet include network endpoint objects.
That is visible rather than silently discarded.

## Normalize Security Hub Findings

Security Hub findings often aggregate products and controls. Start with the
included mapping:

```bash
ocsfkit map fixtures/aws_securityhub_finding.json \
  --mapping examples/securityhub-mapping.yaml
```

Then inspect quality:

```bash
ocsfkit explain fixtures/aws_securityhub_finding.json \
  --mapping examples/securityhub-mapping.yaml \
  --json
```

Useful fields to check:

```bash
ocsfkit map fixtures/aws_securityhub_finding.json \
  --mapping examples/securityhub-mapping.yaml \
  > /tmp/securityhub-ocsf.json

ocsfkit query /tmp/securityhub-ocsf.json metadata.product.name
ocsfkit query /tmp/securityhub-ocsf.json resources[].name
ocsfkit lint /tmp/securityhub-ocsf.json
```

## Promote CloudTrail Events Into Findings

Raw CloudTrail events are not always findings. A failed console login may become
a Detection Finding when your detection logic decides it is suspicious:

```bash
ocsfkit explain fixtures/cloudtrail_event.json \
  --mapping examples/cloudtrail-console-login-mapping.yaml
```

Notice that severity is defaulted in this example. That is intentional: the raw
CloudTrail event does not carry a finding severity. If a SIEM rule supplies a
risk score, map that field instead of defaulting.

## CI Gate for Mapping Regressions

A simple CI job can reject mapping changes that break required OCSF fields:

```bash
ocsfkit map fixtures/guardduty.ndjson \
  --mapping examples/guardduty-mapping.yaml \
  --format ndjson \
  > /tmp/mapped.ndjson

ocsfkit lint /tmp/mapped.ndjson
```

For a softer rollout, keep the report but avoid failing the job:

```bash
ocsfkit lint /tmp/mapped.ndjson --warn-only --json
```

## Compare Mapping Versions

When changing mappings, produce before and after streams:

```bash
ocsfkit map fixtures/guardduty.ndjson \
  --mapping /path/to/old-mapping.yaml \
  --format ndjson \
  > /tmp/old.ndjson

ocsfkit map fixtures/guardduty.ndjson \
  --mapping examples/guardduty-mapping.yaml \
  --format ndjson \
  > /tmp/new.ndjson

ocsfkit diff /tmp/old.ndjson /tmp/new.ndjson
```

Pay special attention to `class_uid`, `class_name`, `severity_id`, and
`severity` changes because those fields commonly drive routing and dashboards.

## Triage Unmapped Fields Across a Stream

Use JSON explain output with your existing JSON tooling:

```bash
ocsfkit explain fixtures/aws_guardduty_finding.json \
  --mapping examples/guardduty-mapping.yaml \
  --json
```

The JSON output contains `unmapped_source_fields`, so you can collect recurring
source paths and decide whether to map, drop, or wait for a broader OCSF schema
slice.

