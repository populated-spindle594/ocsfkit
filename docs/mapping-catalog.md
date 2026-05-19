# ocsfkit Mapping Catalog

Generated from `examples/*.yaml`.

| Mapping | Target class | Quality | Fields | Transforms | Drops | Validation |
| --- | --- | --- | ---: | --- | ---: | --- |
| `examples/aws-vpc-flow-mapping.yaml` | Network Activity (4001) | required 75%, recommended 100%, confidence 0.850, secrets 3 | 12 | `epoch_seconds_to_ms` | 6 | ok |
| `examples/azure-activity-mapping.yaml` | Authentication (3002) | required 75%, recommended 100%, confidence 0.841, secrets 3 | 11 | `parse_timestamp` | 1 | ok |
| `examples/azure-ad-signin-mapping.yaml` | Authentication (3002) | required 75%, recommended 100%, confidence n/a, secrets 4 | 11 | `azure_status_id`, `azure_status_text`, `parse_timestamp` | 0 | ok |
| `examples/cloudflare-log-mapping.yaml` | Network Activity (4001) | required 75%, recommended 75%, confidence 0.775, secrets 1 | 7 | `parse_timestamp` | 3 | ok |
| `examples/cloudtrail-console-login-mapping.yaml` | Authentication (3002) | required 75%, recommended 100%, confidence n/a, secrets 4 | 11 | `login_status_to_id`, `normalize_login_status`, `parse_timestamp` | 1 | ok |
| `examples/crowdstrike-detection-mapping.yaml` | Detection Finding (2004) | required 80%, recommended 100%, confidence 0.808, secrets 0 | 9 | `lower`, `parse_timestamp`, `severity_text_to_id`, `title_case` | 1 | ok |
| `examples/defender-alert-mapping.yaml` | Detection Finding (2004) | required 80%, recommended 100%, confidence 0.850, secrets 1 | 7 | `parse_timestamp`, `severity_text_to_id` | 1 | ok |
| `examples/gcp-scc-finding-mapping.yaml` | Detection Finding (2004) | required 80%, recommended 100%, confidence 0.862, secrets 0 | 8 | `parse_timestamp`, `severity_text_to_id`, `title_case` | 0 | ok |
| `examples/github-audit-mapping.yaml` | Process Activity (1007) | required 75%, recommended 67%, confidence 0.715, secrets 1 | 9 | `parse_timestamp`, `to_string` | 1 | ok |
| `examples/google-cloud-audit-mapping.yaml` | Authentication (3002) | required 75%, recommended 100%, confidence 0.618, secrets 2 | 11 | `parse_timestamp` | 2 | ok |
| `examples/guardduty-mapping.yaml` | Detection Finding (2004) | required 80%, recommended 100%, confidence 0.462, secrets 2 | 10 | `parse_timestamp`, `severity_text_to_id` | 2 | ok |
| `examples/kubernetes-audit-mapping.yaml` | Process Activity (1007) | required 75%, recommended 33%, confidence 0.687, secrets 1 | 10 | `parse_timestamp` | 1 | ok |
| `examples/lacework-alert-mapping.yaml` | Network Activity (4001) | required 75%, recommended 100%, confidence 0.829, secrets 3 | 9 | `parse_timestamp` | 1 | ok |
| `examples/okta-authentication-mapping.yaml` | Authentication (3002) | required 75%, recommended 100%, confidence n/a, secrets 2 | 10 | `login_status_to_id`, `normalize_login_status`, `parse_timestamp` | 1 | ok |
| `examples/paloalto-traffic-mapping.yaml` | Network Activity (4001) | required 75%, recommended 100%, confidence 0.840, secrets 2 | 10 | `parse_timestamp` | 2 | ok |
| `examples/securityhub-mapping.yaml` | Detection Finding (2004) | required 80%, recommended 100%, confidence 0.637, secrets 2 | 9 | `parse_timestamp`, `severity_text_to_id` | 0 | ok |
| `examples/sentinel-alert-mapping.yaml` | Detection Finding (2004) | required 80%, recommended 100%, confidence 0.875, secrets 2 | 7 | `parse_timestamp`, `severity_text_to_id` | 0 | ok |
| `examples/splunk-notable-mapping.yaml` | Detection Finding (2004) | required 80%, recommended 100%, confidence 0.850, secrets 1 | 7 | `parse_timestamp`, `severity_text_to_id`, `title_case` | 1 | ok |
| `examples/sysmon-process-mapping.yaml` | Process Activity (1007) | required 75%, recommended 100%, confidence 0.829, secrets 0 | 8 | `parse_timestamp` | 2 | ok |
| `examples/windows-security-auth-mapping.yaml` | Authentication (3002) | required 75%, recommended 100%, confidence 0.713, secrets 1 | 10 | `parse_timestamp` | 2 | ok |
| `examples/wiz-finding-mapping.yaml` | Detection Finding (2004) | required 80%, recommended 100%, confidence 0.871, secrets 0 | 9 | `parse_timestamp`, `severity_text_to_id`, `title_case` | 0 | ok |
| `examples/zeek-conn-mapping.yaml` | Network Activity (4001) | required 75%, recommended 100%, confidence 0.715, secrets 2 | 9 | `epoch_seconds_to_ms` | 2 | ok |

## aws-vpc-flow-mapping

- File: `examples/aws-vpc-flow-mapping.yaml`
- Source product: AWS VPC Flow Logs
- Maturity: `example`
- Owner: `ocsfkit maintainers`
- Last reviewed: `2026-05-18`
- Quality: required 75%, recommended 100%, confidence 0.850, secrets 3
- Target class: Network Activity (`4001`)
- Schema version: `1.7.0`
- Mapped targets:
  - `activity_id`
  - `activity_name`
  - `cloud.account_uid`
  - `cloud.region`
  - `dst_endpoint.ip`
  - `dst_endpoint.port`
  - `resources[].name`
  - `resources[].type`
  - `src_endpoint.ip`
  - `src_endpoint.port`
  - `status`
  - `time`

## azure-activity-mapping

- File: `examples/azure-activity-mapping.yaml`
- Source product: Azure Activity Logs
- Maturity: `example`
- Owner: `ocsfkit maintainers`
- Last reviewed: `2026-05-18`
- Quality: required 75%, recommended 100%, confidence 0.841, secrets 3
- Target class: Authentication (`3002`)
- Schema version: `1.7.0`
- Mapped targets:
  - `activity_id`
  - `activity_name`
  - `actor.user.name`
  - `cloud.account_uid`
  - `cloud.region`
  - `message`
  - `resources[].name`
  - `resources[].type`
  - `status`
  - `status_id`
  - `time`

## azure-ad-signin-mapping

- File: `examples/azure-ad-signin-mapping.yaml`
- Source product: Microsoft Entra ID
- Maturity: `example`
- Owner: `ocsfkit maintainers`
- Last reviewed: `2026-05-18`
- Quality: required 75%, recommended 100%, confidence n/a, secrets 4
- Target class: Authentication (`3002`)
- Schema version: `1.7.0`
- Mapped targets:
  - `activity_id`
  - `activity_name`
  - `actor.user.name`
  - `actor.user.uid`
  - `cloud.account_uid`
  - `message`
  - `metadata.product.name`
  - `src_endpoint.ip`
  - `status`
  - `status_id`
  - `time`

## cloudflare-log-mapping

- File: `examples/cloudflare-log-mapping.yaml`
- Source product: Cloudflare Logs
- Maturity: `example`
- Owner: `ocsfkit maintainers`
- Last reviewed: `2026-05-18`
- Quality: required 75%, recommended 75%, confidence 0.775, secrets 1
- Target class: Network Activity (`4001`)
- Schema version: `1.7.0`
- Mapped targets:
  - `activity_id`
  - `activity_name`
  - `dst_endpoint.port`
  - `message`
  - `metadata.product.name`
  - `src_endpoint.ip`
  - `time`

## cloudtrail-console-login-mapping

- File: `examples/cloudtrail-console-login-mapping.yaml`
- Source product: AWS CloudTrail
- Maturity: `example`
- Owner: `ocsfkit maintainers`
- Last reviewed: `2026-05-18`
- Quality: required 75%, recommended 100%, confidence n/a, secrets 4
- Target class: Authentication (`3002`)
- Schema version: `1.7.0`
- Mapped targets:
  - `activity_id`
  - `activity_name`
  - `actor.user.name`
  - `actor.user.uid`
  - `cloud.account_uid`
  - `cloud.region`
  - `message`
  - `metadata.product.name`
  - `status`
  - `status_id`
  - `time`

## crowdstrike-detection-mapping

- File: `examples/crowdstrike-detection-mapping.yaml`
- Source product: CrowdStrike Falcon
- Maturity: `example`
- Owner: `ocsfkit maintainers`
- Last reviewed: `2026-05-18`
- Quality: required 80%, recommended 100%, confidence 0.808, secrets 0
- Target class: Detection Finding (`2004`)
- Schema version: `1.7.0`
- Mapped targets:
  - `actor.user.name`
  - `device.hostname`
  - `message`
  - `metadata.product.name`
  - `process.name`
  - `process.pid`
  - `severity`
  - `severity_id`
  - `time`

## defender-alert-mapping

- File: `examples/defender-alert-mapping.yaml`
- Source product: Microsoft Defender
- Maturity: `example`
- Owner: `ocsfkit maintainers`
- Last reviewed: `2026-05-18`
- Quality: required 80%, recommended 100%, confidence 0.850, secrets 1
- Target class: Detection Finding (`2004`)
- Schema version: `1.7.0`
- Mapped targets:
  - `cloud.account_uid`
  - `device.hostname`
  - `message`
  - `metadata.product.name`
  - `severity`
  - `severity_id`
  - `time`

## gcp-scc-finding-mapping

- File: `examples/gcp-scc-finding-mapping.yaml`
- Source product: Google Security Command Center
- Maturity: `example`
- Owner: `ocsfkit maintainers`
- Last reviewed: `2026-05-18`
- Quality: required 80%, recommended 100%, confidence 0.862, secrets 0
- Target class: Detection Finding (`2004`)
- Schema version: `1.7.0`
- Mapped targets:
  - `cloud.account_uid`
  - `cloud.region`
  - `message`
  - `metadata.product.name`
  - `resources[].name`
  - `severity`
  - `severity_id`
  - `time`

## github-audit-mapping

- File: `examples/github-audit-mapping.yaml`
- Source product: GitHub Audit Log
- Maturity: `example`
- Owner: `ocsfkit maintainers`
- Last reviewed: `2026-05-18`
- Quality: required 75%, recommended 67%, confidence 0.715, secrets 1
- Target class: Process Activity (`1007`)
- Schema version: `1.7.0`
- Mapped targets:
  - `activity_id`
  - `activity_name`
  - `actor.user.name`
  - `actor.user.uid`
  - `message`
  - `metadata.product.name`
  - `process.name`
  - `src_endpoint.ip`
  - `time`

## google-cloud-audit-mapping

- File: `examples/google-cloud-audit-mapping.yaml`
- Source product: Google Cloud Audit Logs
- Maturity: `example`
- Owner: `ocsfkit maintainers`
- Last reviewed: `2026-05-18`
- Quality: required 75%, recommended 100%, confidence 0.618, secrets 2
- Target class: Authentication (`3002`)
- Schema version: `1.7.0`
- Mapped targets:
  - `activity_id`
  - `activity_name`
  - `actor.user.name`
  - `cloud.account_uid`
  - `cloud.region`
  - `message`
  - `resources[].name`
  - `resources[].type`
  - `status`
  - `status_id`
  - `time`

## guardduty-mapping

- File: `examples/guardduty-mapping.yaml`
- Source product: Amazon GuardDuty
- Maturity: `example`
- Owner: `ocsfkit maintainers`
- Last reviewed: `2026-05-18`
- Quality: required 80%, recommended 100%, confidence 0.462, secrets 2
- Target class: Detection Finding (`2004`)
- Schema version: `1.7.0`
- Mapped targets:
  - `actor.user.name`
  - `cloud.account_uid`
  - `cloud.region`
  - `message`
  - `metadata.product.name`
  - `resources[].name`
  - `resources[].type`
  - `severity`
  - `severity_id`
  - `time`

## kubernetes-audit-mapping

- File: `examples/kubernetes-audit-mapping.yaml`
- Source product: Kubernetes Audit
- Maturity: `example`
- Owner: `ocsfkit maintainers`
- Last reviewed: `2026-05-18`
- Quality: required 75%, recommended 33%, confidence 0.687, secrets 1
- Target class: Process Activity (`1007`)
- Schema version: `1.7.0`
- Mapped targets:
  - `activity_id`
  - `activity_name`
  - `actor.user.name`
  - `actor.user.uid`
  - `message`
  - `metadata.product.name`
  - `resources[].name`
  - `resources[].type`
  - `src_endpoint.ip`
  - `time`

## lacework-alert-mapping

- File: `examples/lacework-alert-mapping.yaml`
- Source product: Lacework
- Maturity: `example`
- Owner: `ocsfkit maintainers`
- Last reviewed: `2026-05-18`
- Quality: required 75%, recommended 100%, confidence 0.829, secrets 3
- Target class: Network Activity (`4001`)
- Schema version: `1.7.0`
- Mapped targets:
  - `activity_id`
  - `activity_name`
  - `cloud.account_uid`
  - `device.hostname`
  - `dst_endpoint.ip`
  - `message`
  - `metadata.product.name`
  - `src_endpoint.ip`
  - `time`

## okta-authentication-mapping

- File: `examples/okta-authentication-mapping.yaml`
- Source product: Okta System Log
- Maturity: `example`
- Owner: `ocsfkit maintainers`
- Last reviewed: `2026-05-18`
- Quality: required 75%, recommended 100%, confidence n/a, secrets 2
- Target class: Authentication (`3002`)
- Schema version: `1.7.0`
- Mapped targets:
  - `activity_id`
  - `activity_name`
  - `actor.user.name`
  - `actor.user.uid`
  - `message`
  - `metadata.product.name`
  - `src_endpoint.ip`
  - `status`
  - `status_id`
  - `time`

## paloalto-traffic-mapping

- File: `examples/paloalto-traffic-mapping.yaml`
- Source product: Palo Alto Networks
- Maturity: `example`
- Owner: `ocsfkit maintainers`
- Last reviewed: `2026-05-18`
- Quality: required 75%, recommended 100%, confidence 0.840, secrets 2
- Target class: Network Activity (`4001`)
- Schema version: `1.7.0`
- Mapped targets:
  - `activity_id`
  - `activity_name`
  - `device.hostname`
  - `dst_endpoint.ip`
  - `dst_endpoint.port`
  - `message`
  - `metadata.product.name`
  - `src_endpoint.ip`
  - `src_endpoint.port`
  - `time`

## securityhub-mapping

- File: `examples/securityhub-mapping.yaml`
- Source product: AWS Security Hub
- Maturity: `example`
- Owner: `ocsfkit maintainers`
- Last reviewed: `2026-05-18`
- Quality: required 80%, recommended 100%, confidence 0.637, secrets 2
- Target class: Detection Finding (`2004`)
- Schema version: `1.7.0`
- Mapped targets:
  - `cloud.account_uid`
  - `cloud.region`
  - `message`
  - `metadata.product.name`
  - `resources[].name`
  - `resources[].type`
  - `severity`
  - `severity_id`
  - `time`

## sentinel-alert-mapping

- File: `examples/sentinel-alert-mapping.yaml`
- Source product: Microsoft Sentinel
- Maturity: `example`
- Owner: `ocsfkit maintainers`
- Last reviewed: `2026-05-18`
- Quality: required 80%, recommended 100%, confidence 0.875, secrets 2
- Target class: Detection Finding (`2004`)
- Schema version: `1.7.0`
- Mapped targets:
  - `actor.user.name`
  - `cloud.account_uid`
  - `message`
  - `metadata.product.name`
  - `severity`
  - `severity_id`
  - `time`

## splunk-notable-mapping

- File: `examples/splunk-notable-mapping.yaml`
- Source product: Splunk Enterprise Security
- Maturity: `example`
- Owner: `ocsfkit maintainers`
- Last reviewed: `2026-05-18`
- Quality: required 80%, recommended 100%, confidence 0.850, secrets 1
- Target class: Detection Finding (`2004`)
- Schema version: `1.7.0`
- Mapped targets:
  - `actor.user.name`
  - `message`
  - `metadata.product.name`
  - `severity`
  - `severity_id`
  - `src_endpoint.ip`
  - `time`

## sysmon-process-mapping

- File: `examples/sysmon-process-mapping.yaml`
- Source product: Microsoft Sysmon
- Maturity: `example`
- Owner: `ocsfkit maintainers`
- Last reviewed: `2026-05-18`
- Quality: required 75%, recommended 100%, confidence 0.829, secrets 0
- Target class: Process Activity (`1007`)
- Schema version: `1.7.0`
- Mapped targets:
  - `activity_id`
  - `activity_name`
  - `actor.user.name`
  - `device.hostname`
  - `message`
  - `process.name`
  - `process.pid`
  - `time`

## windows-security-auth-mapping

- File: `examples/windows-security-auth-mapping.yaml`
- Source product: Windows Security Event Log
- Maturity: `example`
- Owner: `ocsfkit maintainers`
- Last reviewed: `2026-05-18`
- Quality: required 75%, recommended 100%, confidence 0.713, secrets 1
- Target class: Authentication (`3002`)
- Schema version: `1.7.0`
- Mapped targets:
  - `activity_id`
  - `activity_name`
  - `actor.user.name`
  - `actor.user.uid`
  - `device.hostname`
  - `message`
  - `src_endpoint.ip`
  - `status`
  - `status_id`
  - `time`

## wiz-finding-mapping

- File: `examples/wiz-finding-mapping.yaml`
- Source product: Wiz
- Maturity: `example`
- Owner: `ocsfkit maintainers`
- Last reviewed: `2026-05-18`
- Quality: required 80%, recommended 100%, confidence 0.871, secrets 0
- Target class: Detection Finding (`2004`)
- Schema version: `1.7.0`
- Mapped targets:
  - `cloud.account_uid`
  - `cloud.region`
  - `message`
  - `metadata.product.name`
  - `resources[].name`
  - `resources[].type`
  - `severity`
  - `severity_id`
  - `time`

## zeek-conn-mapping

- File: `examples/zeek-conn-mapping.yaml`
- Source product: Zeek
- Maturity: `example`
- Owner: `ocsfkit maintainers`
- Last reviewed: `2026-05-18`
- Quality: required 75%, recommended 100%, confidence 0.715, secrets 2
- Target class: Network Activity (`4001`)
- Schema version: `1.7.0`
- Mapped targets:
  - `activity_id`
  - `activity_name`
  - `dst_endpoint.ip`
  - `dst_endpoint.port`
  - `message`
  - `metadata.product.name`
  - `src_endpoint.ip`
  - `src_endpoint.port`
  - `time`
