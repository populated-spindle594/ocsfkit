# Installing ocsfkit

Use the installation path that matches where you run security engineering tools.

## pipx

`pipx` keeps CLI tools isolated from application environments.

```bash
pipx install ocsfkit
ocsfkit --help
```

## uvx

`uvx` is useful for one-off CI or workstation runs.

```bash
uvx ocsfkit --help
uvx ocsfkit lint fixtures/ocsf_detection_finding.json
```

## pip

Use `pip` inside a virtual environment.

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install ocsfkit
```

## Homebrew

```bash
brew tap pfrederiksen/tap
brew install ocsfkit
```

## Shell Completions

Print the setup snippet for your shell and add it to your shell profile:

```bash
ocsfkit completions zsh
ocsfkit completions bash
ocsfkit completions fish
```

## Docker

Build locally:

```bash
docker build -t ocsfkit .
docker run --rm ocsfkit --help
```

Release tags publish a container to GitHub Container Registry:

```bash
docker pull ghcr.io/pfrederiksen/ocsfkit:latest
docker run --rm ghcr.io/pfrederiksen/ocsfkit:latest --help
```

Run against files in the current checkout:

```bash
docker run --rm -v "$PWD:/work" -w /work ocsfkit \
  explain fixtures/aws_guardduty_finding.json \
  --mapping examples/guardduty-mapping.yaml
```

## GitHub Actions

```yaml
- name: Install ocsfkit
  run: python -m pip install ocsfkit

- name: Validate mapping quality
  run: |
    ocsfkit scorecard fixtures/guardduty.ndjson \
      --pack aws-guardduty \
      --min-confidence 0.80 \
      --max-unmapped 25 \
      --github-summary
```

## pre-commit

Use the repo hooks directly:

```yaml
repos:
  - repo: https://github.com/pfrederiksen/ocsfkit
    rev: v0.9.0
    hooks:
      - id: ocsfkit-validate-mapping
      - id: ocsfkit-pack-validate
```

## Mapping Packs

Built-in packs are bundled with the Python package and Homebrew formula. Teams
can also install reviewed external packs from a local directory, zip file, or
HTTPS zip archive:

```bash
ocsfkit pack install ./company-ocsfkit-pack --name company
ocsfkit pack list
ocsfkit map sample.json --pack company/guardduty
ocsfkit pack update company
```

For reproducible CI, install external packs from immutable release archives
rather than branch archives.
