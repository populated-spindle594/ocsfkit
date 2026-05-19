# CI Integration Examples

## GitHub Actions

```yaml
name: ocsfkit

on: [pull_request]

jobs:
  mapping-quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd
      - name: Install ocsfkit
        run: python -m pip install ocsfkit
      - name: Check release automation readiness
        run: ocsfkit doctor --ci
      - name: Validate mappings
        run: ocsfkit pack validate
      - name: Score GuardDuty mapping
        run: |
          ocsfkit scorecard fixtures/guardduty.ndjson \
            --pack aws-guardduty \
            --min-confidence 0.80 \
            --max-unmapped 25 \
            --github-summary
      - name: Publish mapping-quality SARIF
        run: |
          ocsfkit gate fixtures/guardduty.ndjson \
            --pack aws-guardduty \
            --min-confidence 0.70 \
            --max-unmapped 10 \
            --no-strict \
            --sarif > ocsfkit-gate.sarif
      - name: Write mapping test report
        run: ocsfkit test-mapping tests/goldens --junit ocsfkit-mapping.xml
      - name: Scan fixtures for sensitive data
        run: ocsfkit scan fixtures --sarif --warn-only > ocsfkit-privacy.sarif
      - name: Check schema drift
        run: ocsfkit schema-drift examples/guardduty-mapping.yaml --sarif > ocsfkit-drift.sarif
```

## GitLab CI

```yaml
ocsfkit:
  image: python:3.12-slim
  script:
    - python -m pip install ocsfkit
    - ocsfkit pack validate
    - ocsfkit test-mapping tests/goldens --junit ocsfkit-mapping.xml
    - ocsfkit scan fixtures --warn-only
    - ocsfkit scorecard fixtures/guardduty.ndjson --pack aws-guardduty --min-confidence 0.80 --max-unmapped 25
  artifacts:
    reports:
      junit: ocsfkit-mapping.xml
```

## Buildkite

```yaml
steps:
  - label: ":shield: ocsfkit"
    command:
      - "python -m pip install ocsfkit"
      - "ocsfkit pack validate"
      - "ocsfkit test-mapping tests/goldens --junit ocsfkit-mapping.xml"
      - "ocsfkit scan fixtures --warn-only"
      - "ocsfkit doctor --ci"
```

## Makefile

```makefile
.PHONY: ocsfkit
ocsfkit:
	ocsfkit pack validate
	ocsfkit test-mapping tests/goldens --junit ocsfkit-mapping.xml
	ocsfkit scan fixtures --warn-only
	ocsfkit doctor --ci
	ocsfkit benchmark fixtures/guardduty.ndjson --mapping examples/guardduty-mapping.yaml --iterations 3
	ocsfkit gate fixtures/guardduty.ndjson --pack aws-guardduty --min-confidence 0.70 --max-unmapped 10 --no-strict --sarif > ocsfkit-gate.sarif
```

## Docker

```bash
docker run --rm -v "$PWD:/work" -w /work ghcr.io/pfrederiksen/ocsfkit:latest \
  scorecard fixtures/guardduty.ndjson \
  --pack aws-guardduty \
  --min-confidence 0.80 \
  --max-unmapped 25
```

## Post-Release Verification

The repository includes `.github/workflows/post-release.yml`. When a GitHub
release is published, it installs the released version from PyPI and reinstalls
the Homebrew formula from `pfrederiksen/tap`, then runs smoke commands. This
catches packaging or tap drift after the release workflow has completed.

Before tagging a release, run:

```bash
ocsfkit doctor --ci
uv build
```

## Templates

Copy-paste starter templates live under `docs/templates/`:

- `github-code-scanning.yml`
- `gitlab-ci.yml`
- `pre-commit.yaml`
- `docker-runner.sh`
