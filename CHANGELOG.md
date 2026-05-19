# Changelog

## 0.11.0

- Added `ocsfkit batch` for corpus conversion with normalized output,
  explanation JSON, lint JSON, unmapped-field inventory, and HTML coverage
  artifacts.
- Added `ocsfkit describe` for bundled OCSF fields, classes, enums, and schema
  version support.
- Added `ocsfkit score` as a shorter alias for `ocsfkit scorecard`.
- Added `ocsfkit mapping test` as a namespaced alias for golden mapping tests.
- Added a reusable GitHub composite action for mapping-quality gates.
- Added a documented demo walkthrough for raw GuardDuty to reviewed OCSF.

## 0.10.0

- Added external mapping pack install/update support with local and HTTPS zip
  sources.
- Added `ocsfkit suggest` to propose likely OCSF target fields and starter YAML
  from representative events.
- Added `ocsfkit completions` for shell completion setup snippets.
- Added `ocsfkit doctor --ci` release-readiness checks for GitHub automation.
- Added post-release verification for PyPI and Homebrew installs.
- Improved HTML explanation and coverage reports with richer review context.

## 0.9.0

- Added `ocsfkit --version`.
- Added built-in mapping-pack aliases through `--pack` on mapping-quality
  commands, with packaged example mappings available from installed wheels.
- Added `ocsfkit gate` as a strict CI-oriented readiness gate with JSON and
  SARIF output.
- Added SARIF output for `coverage` and `scorecard`.
- Added JSON Schema export through `ocsfkit schema --format jsonschema`.
- Added streaming NDJSON mapping for `ocsfkit map --format ndjson`.
- Removed PyPI token fallback from the release workflow so releases use Trusted
  Publishing only.
- Added deterministic Homebrew tap updates that hash the GitHub release
  archive before committing formula changes.

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
