# ocsfkit

`ocsfkit` is an OCSF workbench for security engineers moving real telemetry
into OCSF while keeping mapping quality visible.

Use it to answer practical review questions:

- What OCSF class did this source event become?
- Which source fields mapped cleanly?
- Which fields were defaulted, guessed, dropped, or left unmapped?
- Which required or recommended OCSF fields are still missing?
- Can this mapping pass CI without silent data loss?

## Fast Path

```bash
pip install ocsfkit
ocsfkit explain fixtures/aws_guardduty_finding.json --pack aws-guardduty
ocsfkit suggest fixtures/aws_guardduty_finding.json
ocsfkit scorecard fixtures/guardduty.ndjson \
  --pack aws-guardduty \
  --min-confidence 0.80 \
  --max-unmapped 25
```

## Production Checks

```bash
ocsfkit validate-mapping examples/guardduty-mapping.yaml --strict
ocsfkit test-mapping tests/goldens --junit ocsfkit-mapping.xml
ocsfkit scan fixtures --sarif --warn-only > ocsfkit-privacy.sarif
ocsfkit gate fixtures/guardduty.ndjson --pack aws-guardduty --min-confidence 0.70 --max-unmapped 10 --no-strict --sarif > ocsfkit-gate.sarif
ocsfkit schema --format jsonschema > ocsfkit.schema.json
ocsfkit doctor --ci
```

External mapping packs can be installed with `ocsfkit pack install` and then
used anywhere `--pack` is accepted.

Start with the getting started guide, then use the mapping guide and catalog
when building or reviewing mappings for a specific telemetry source.
