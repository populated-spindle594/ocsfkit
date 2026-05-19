#!/usr/bin/env sh
set -eu

docker run --rm -v "$PWD:/work" -w /work ghcr.io/pfrederiksen/ocsfkit:latest \
  scorecard fixtures/guardduty.ndjson \
  --pack aws-guardduty \
  --min-confidence 0.80 \
  --max-unmapped 25
