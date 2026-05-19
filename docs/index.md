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
ocsfkit explain fixtures/aws_guardduty_finding.json \
  --mapping examples/guardduty-mapping.yaml
ocsfkit scorecard fixtures/guardduty.ndjson \
  --mapping examples/guardduty-mapping.yaml \
  --min-confidence 0.80 \
  --max-unmapped 25
```

## Production Checks

```bash
ocsfkit validate-mapping examples/guardduty-mapping.yaml --strict
ocsfkit test-mapping tests/goldens --junit ocsfkit-mapping.xml
ocsfkit scan fixtures --sarif --warn-only > ocsfkit-privacy.sarif
ocsfkit doctor
```

Start with the getting started guide, then use the mapping guide and catalog
when building or reviewing mappings for a specific telemetry source.
