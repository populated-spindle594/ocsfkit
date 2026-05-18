# CI Integration Examples

## GitHub Actions

```yaml
name: ocsfkit

on: [pull_request]

jobs:
  mapping-quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@34e114876b0b11c390a56381ad16ebd13914f8d5
      - name: Install ocsfkit
        run: python -m pip install ocsfkit
      - name: Validate mappings
        run: ocsfkit pack validate
      - name: Score GuardDuty mapping
        run: |
          ocsfkit scorecard fixtures/guardduty.ndjson \
            --mapping examples/guardduty-mapping.yaml \
            --min-confidence 0.80 \
            --max-unmapped 25 \
            --github-summary
```

## GitLab CI

```yaml
ocsfkit:
  image: python:3.12-slim
  script:
    - python -m pip install ocsfkit
    - ocsfkit pack validate
    - ocsfkit test-mapping tests/goldens
    - ocsfkit scorecard fixtures/guardduty.ndjson --mapping examples/guardduty-mapping.yaml --min-confidence 0.80 --max-unmapped 25
```

## Buildkite

```yaml
steps:
  - label: ":shield: ocsfkit"
    command:
      - "python -m pip install ocsfkit"
      - "ocsfkit pack validate"
      - "ocsfkit test-mapping tests/goldens"
```

## Makefile

```makefile
.PHONY: ocsfkit
ocsfkit:
	ocsfkit pack validate
	ocsfkit test-mapping tests/goldens
	ocsfkit scan fixtures --warn-only
```

## Docker

```bash
docker run --rm -v "$PWD:/work" -w /work ghcr.io/pfrederiksen/ocsfkit:latest \
  scorecard fixtures/guardduty.ndjson \
  --mapping examples/guardduty-mapping.yaml \
  --min-confidence 0.80 \
  --max-unmapped 25
```
