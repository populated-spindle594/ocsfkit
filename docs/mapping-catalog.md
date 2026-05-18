# ocsfkit Mapping Catalog

Generated from `examples/*.yaml`.

| Mapping | Target class | Fields | Transforms | Drops | Validation |
| --- | --- | ---: | --- | ---: | --- |
| `examples/aws-vpc-flow-mapping.yaml` | Network Activity (4001) | 12 | `epoch_seconds_to_ms` | 6 | ok |
| `examples/azure-activity-mapping.yaml` | Authentication (3002) | 11 | `parse_timestamp` | 1 | ok |
| `examples/azure-ad-signin-mapping.yaml` | Authentication (3002) | 11 | `azure_status_id`, `azure_status_text`, `parse_timestamp` | 0 | ok |
| `examples/cloudflare-log-mapping.yaml` | Network Activity (4001) | 7 | `parse_timestamp` | 3 | ok |
| `examples/cloudtrail-console-login-mapping.yaml` | Authentication (3002) | 11 | `login_status_to_id`, `normalize_login_status`, `parse_timestamp` | 1 | ok |
| `examples/crowdstrike-detection-mapping.yaml` | Detection Finding (2004) | 9 | `lower`, `parse_timestamp`, `severity_text_to_id`, `title_case` | 1 | ok |
| `examples/defender-alert-mapping.yaml` | Detection Finding (2004) | 7 | `parse_timestamp`, `severity_text_to_id` | 1 | ok |
| `examples/gcp-scc-finding-mapping.yaml` | Detection Finding (2004) | 8 | `parse_timestamp`, `severity_text_to_id`, `title_case` | 0 | ok |
| `examples/github-audit-mapping.yaml` | Process Activity (1007) | 9 | `parse_timestamp`, `to_string` | 1 | ok |
| `examples/google-cloud-audit-mapping.yaml` | Authentication (3002) | 11 | `parse_timestamp` | 2 | ok |
| `examples/guardduty-mapping.yaml` | Detection Finding (2004) | 10 | `parse_timestamp`, `severity_text_to_id` | 2 | ok |
| `examples/kubernetes-audit-mapping.yaml` | Process Activity (1007) | 10 | `parse_timestamp` | 1 | ok |
| `examples/lacework-alert-mapping.yaml` | Network Activity (4001) | 9 | `parse_timestamp` | 1 | ok |
| `examples/okta-authentication-mapping.yaml` | Authentication (3002) | 10 | `login_status_to_id`, `normalize_login_status`, `parse_timestamp` | 1 | ok |
| `examples/paloalto-traffic-mapping.yaml` | Network Activity (4001) | 10 | `parse_timestamp` | 2 | ok |
| `examples/securityhub-mapping.yaml` | Detection Finding (2004) | 9 | `parse_timestamp`, `severity_text_to_id` | 0 | ok |
| `examples/sentinel-alert-mapping.yaml` | Detection Finding (2004) | 7 | `parse_timestamp`, `severity_text_to_id` | 0 | ok |
| `examples/splunk-notable-mapping.yaml` | Detection Finding (2004) | 7 | `parse_timestamp`, `severity_text_to_id`, `title_case` | 1 | ok |
| `examples/sysmon-process-mapping.yaml` | Process Activity (1007) | 8 | `parse_timestamp` | 2 | ok |
| `examples/windows-security-auth-mapping.yaml` | Authentication (3002) | 10 | `parse_timestamp` | 2 | ok |
| `examples/wiz-finding-mapping.yaml` | Detection Finding (2004) | 9 | `parse_timestamp`, `severity_text_to_id`, `title_case` | 0 | ok |
| `examples/zeek-conn-mapping.yaml` | Network Activity (4001) | 9 | `epoch_seconds_to_ms` | 2 | ok |

## aws-vpc-flow-mapping

- File: `examples/aws-vpc-flow-mapping.yaml`
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
