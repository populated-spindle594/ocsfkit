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

## Normalize CloudTrail Authentication

Raw CloudTrail events are not always findings. A console login event is better
represented as Authentication unless a separate detection rule promotes it into
a finding:

```bash
ocsfkit explain fixtures/cloudtrail_event.json \
  --mapping examples/cloudtrail-console-login-mapping.yaml
```

This mapping uses the Authentication class (`class_uid: 3002`) and a custom
transform module to convert AWS `ConsoleLogin` values into normalized status
fields:

```yaml
custom_transforms:
  - custom_transforms.py
custom_transforms_trusted: true

fields:
  status:
    from: $.responseElements.ConsoleLogin
    transform: normalize_login_status

  status_id:
    from: $.responseElements.ConsoleLogin
    transform: login_status_to_id
```

## Normalize Identity and SaaS Audit Logs

The repo includes starter mappings for Okta, Microsoft Entra ID, and GitHub
Audit Log events:

```bash
ocsfkit explain fixtures/okta_login_event.json \
  --mapping examples/okta-authentication-mapping.yaml

ocsfkit explain fixtures/azure_ad_signin.json \
  --mapping examples/azure-ad-signin-mapping.yaml

ocsfkit explain fixtures/github_audit_event.json \
  --mapping examples/github-audit-mapping.yaml
```

These sources are useful for exercising Authentication and audit-like workflows.
Review actor identity, status, product name, and cloud tenant/account fields
first. Built-in transform packs such as `okta.status_id`, `okta.status`,
`azure.status_id`, and `azure.status` are available when source-specific status
normalization is needed.

## Normalize Detection Platforms

Detection products tend to have rich alert metadata and product-specific
resource formats. Start with explanation output, then use coverage to find
recurring gaps across samples:

```bash
ocsfkit explain fixtures/crowdstrike_detection.json \
  --mapping examples/crowdstrike-detection-mapping.yaml

ocsfkit explain fixtures/sentinel_alert.json \
  --mapping examples/sentinel-alert-mapping.yaml

ocsfkit explain fixtures/defender_alert.json \
  --mapping examples/defender-alert-mapping.yaml

ocsfkit explain fixtures/wiz_finding.json \
  --mapping examples/wiz-finding-mapping.yaml

ocsfkit explain fixtures/lacework_alert.json \
  --mapping examples/lacework-alert-mapping.yaml
```

For these mappings, pay close attention to `message`, `severity_id`,
`metadata.product.name`, `cloud.account_uid`, `cloud.region`, and
`resources[]`. If a vendor provides both a display name and a stable resource
ID, prefer the stable ID in a structured target when the current schema slice
has one, and keep the human text in `message` or `resources[].name`.

## Normalize Network and Infrastructure Logs

Network and infrastructure events are often better represented as Network
Activity or Process Activity rather than Detection Finding:

```bash
ocsfkit explain fixtures/paloalto_traffic.json \
  --mapping examples/paloalto-traffic-mapping.yaml

ocsfkit explain fixtures/zeek_conn.json \
  --mapping examples/zeek-conn-mapping.yaml

ocsfkit explain fixtures/cloudflare_log.json \
  --mapping examples/cloudflare-log-mapping.yaml

ocsfkit explain fixtures/kubernetes_audit.json \
  --mapping examples/kubernetes-audit-mapping.yaml

ocsfkit explain fixtures/aws_vpc_flow_log.json \
  --mapping examples/aws-vpc-flow-mapping.yaml

ocsfkit explain fixtures/sysmon_process_event.json \
  --mapping examples/sysmon-process-mapping.yaml

ocsfkit explain fixtures/windows_security_event.json \
  --mapping examples/windows-security-auth-mapping.yaml
```

Diff class and severity changes before routing these events into production.
Those fields commonly drive SIEM indexes, detection rules, and dashboard
filters.

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

Upload SARIF from GitHub Actions:

```bash
ocsfkit lint /tmp/mapped.ndjson --sarif > ocsfkit.sarif
```

Or emit native workflow annotations:

```bash
ocsfkit lint /tmp/mapped.ndjson --github-annotations
ocsfkit explain fixtures/aws_guardduty_finding.json \
  --mapping examples/guardduty-mapping.yaml \
  --github-annotations
```

Add a coverage budget when a mapping is mature enough to protect:

```bash
ocsfkit coverage fixtures/guardduty.ndjson \
  --mapping examples/guardduty-mapping.yaml \
  --min-confidence 0.80 \
  --max-unmapped 25
```

Use `scorecard` when you want one readiness gate that combines mapped-event
lint, coverage, and optional strict checks:

```bash
ocsfkit scorecard fixtures/guardduty.ndjson \
  --mapping examples/guardduty-mapping.yaml \
  --min-confidence 0.80 \
  --max-unmapped 25 \
  --strict
```

Append the same review to a GitHub Actions job summary:

```bash
ocsfkit coverage fixtures/guardduty.ndjson \
  --mapping examples/guardduty-mapping.yaml \
  --min-confidence 0.80 \
  --max-unmapped 25 \
  --github-summary
```

Generate HTML for human review artifacts:

```bash
ocsfkit report fixtures/guardduty.ndjson \
  --mapping examples/guardduty-mapping.yaml \
  --output report.html
```

Protect individual mappings with fixture tests:

```bash
ocsfkit test-mapping tests/fixtures/guardduty-test.yaml
```

For release pipelines, add strict validation:

```bash
ocsfkit validate-mapping examples/guardduty-mapping.yaml --strict
ocsfkit schema-drift examples/guardduty-mapping.yaml
ocsfkit explain fixtures/aws_guardduty_finding.json \
  --mapping examples/guardduty-mapping.yaml \
  --strict
```

Regenerate mapping catalog documentation before releasing mapping pack changes:

```bash
ocsfkit catalog --output docs/mapping-catalog.md
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

The faster terminal workflow is:

```bash
ocsfkit coverage fixtures/guardduty.ndjson \
  --mapping examples/guardduty-mapping.yaml
```

For a new source, start with:

```bash
ocsfkit workshop fixtures/gcp_scc_finding.json
ocsfkit init-mapping fixtures/gcp_scc_finding.json \
  --product-name "Google Security Command Center"
```

Then iterate until the explanation output makes each mapped, dropped, defaulted,
guessed, and unmapped field intentional.
