# Changelog

## 0.8.0

- Added semantic mapping diffs through `ocsfkit diff-mapping`.
- Added `foreach` array/object mapping for repeated OCSF objects.
- Added transform plugin support through the `ocsfkit.transforms` entry point
  group.
- Added Hypothesis-based property tests for path handling, transforms, and
  redaction.
- Strengthened mapping pack validation with fixture and golden-test contracts.
- Added MkDocs Material publishing in the Pages workflow.
- Added reusable CI templates for GitHub code scanning, GitLab, pre-commit, and
  Docker runners.

## 0.7.2

- Removed Node 20 artifact/release actions from the release workflow.
- Restored OpenSSF Scorecard publishing compatibility by avoiding global
  workflow environment variables in the Scorecard workflow.

## 0.7.1

- Opted GitHub Actions workflows into Node 24 execution to clear hosted-runner
  deprecation annotations.

## 0.7.0

- Added SARIF output for privacy scans and schema drift checks.
- Added JUnit XML output for mapping golden tests.
- Added `redact`, `doctor`, and `benchmark` commands.
- Added target path prefix completion through `ocsfkit targets complete`.
- Added mapping pack compatibility metadata with `ocsf_version` and
  `requires_ocsfkit`.
- Added explicit custom transform trust validation.
- Added mapping catalog quality badges for required/recommended coverage,
  confidence, and fixture scan findings.
- Added MkDocs configuration and expanded production documentation.

## 0.6.0

- Added mapping readiness scorecards.
- Added approved baseline create/check workflows for migration-safe CI gates.
- Added schema drift checks against bundled or synced schema data.
- Added mapping catalog generation with source metadata.
- Added YAML transform tests and directory-based mapping golden tests.
- Added likely secret and sensitive identifier scanning.
- Added event ID path support to human reports.
- Added Dockerfile, GHCR workflow, pre-commit hooks, and CI documentation.
- Added fixtures and mappings for AWS VPC Flow Logs, Azure Activity Logs,
  Google Cloud Audit Logs, Microsoft Sysmon, and Windows Security events.
- Improved HTML mapping reports with summary metrics and table filtering.

## 0.5.0

- Added strict mapping mode, mapping packs, target discovery, upstream schema
  sync, Markdown/HTML reports, and production release automation.
