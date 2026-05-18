# Mapping Guide

Mappings are intentionally small YAML documents. They are designed for
incremental adoption: start with the fields you understand, explicitly drop
fields you have reviewed, then drive the unmapped list toward zero.

## File Structure

```yaml
schema_version: 1.7.0

target_class:
  class_uid: 2004
  class_name: Detection Finding
  category_uid: 2
  category_name: Findings

fields:
  time:
    from: $.eventTime
    transform: parse_timestamp
    required: true

  severity_id:
    from: $.severity
    transform: severity_text_to_id
    default: 1
    required: true

drop:
  - $.debug
```

## `schema_version`

Set the OCSF version your mapping targets:

```yaml
schema_version: 1.7.0
```

`ocsfkit` writes this to `metadata.version` unless the mapping explicitly sets a
different value in `target_class`. The linter supports `1.6.0` and `1.7.0` in
this release and defaults to `1.7.0`.

## `target_class`

`target_class` sets stable event classification fields before field mappings are
applied. Today the built-in registry focuses on Detection Finding:

```yaml
target_class:
  class_uid: 2004
  class_name: Detection Finding
  category_uid: 2
  category_name: Findings
```

These values are tracked as `defaulted_fields` in explain output because they
come from mapping intent rather than from the source event.

## `fields`

Each key under `fields` is an OCSF target path:

```yaml
fields:
  cloud.account_uid:
    from: $.accountId
```

Nested objects are created automatically. Array markers use `[]`:

```yaml
fields:
  resources[].name:
    from: $.Resources[].Id
```

The first release supports a simple JSONPath subset:

- `$` for the whole source event.
- `$.a.b.c` for nested object lookup.
- `$.items[].name` for collecting a field from each object in an array.

It does not support filters, recursive descent, arbitrary expressions, or joins.
Keep enrichment outside the mapping for now.

## Provenance

Every target value gets provenance:

- `mapped`: copied from a source path.
- `transformed`: copied from source and passed through a transform.
- `defaulted`: supplied by `default` or `target_class`.
- `guessed`: supplied by `guess` to make uncertainty explicit.

Example:

```yaml
fields:
  severity_id:
    from: $.risk_label
    transform: severity_text_to_id
    default: 1

  metadata.product.name:
    default: Example EDR

  cloud.region:
    guess: us-east-1
```

Use `guess` when the value is operationally useful but not trustworthy enough to
pretend it came from the source event.

## Required Fields

Mark mapping entries as required when absence should reduce confidence and show
up in `missing_target_fields`:

```yaml
fields:
  time:
    from: $.eventTime
    transform: parse_timestamp
    required: true
```

The linter also enforces required fields from the minimal schema registry.

## Transforms

Built-in transforms:

- `parse_timestamp`: accepts epoch milliseconds, epoch seconds-like integers as
  provided, and ISO-8601 strings such as `2026-01-14T10:21:44Z`; output is epoch
  milliseconds.
- `severity_text_to_id`: maps common severity labels to OCSF-style IDs:
  `Unknown=0`, `Informational=1`, `Low=2`, `Medium=3`, `High=4`,
  `Critical=5`, `Fatal=6`.
- `severity_id_to_text`: converts the same IDs back to text.
- `to_string`: converts any value to a string.
- `to_int`: converts numeric strings and numbers to integers.
- `lower`, `upper`, `title_case`: common string normalization helpers.
- `epoch_seconds_to_ms`: converts epoch seconds to epoch milliseconds.

Transforms can be chained:

```yaml
fields:
  severity:
    from: $.Severity.Label
    transform:
      - lower
      - title_case
```

## Custom Transforms

Mappings can load local Python files that expose a `TRANSFORMS` dictionary:

```yaml
custom_transforms:
  - custom_transforms.py

fields:
  status_id:
    from: $.responseElements.ConsoleLogin
    transform: login_status_to_id
```

Example module:

```python
def login_status_to_id(value):
    return 1 if str(value).lower() == "success" else 2


TRANSFORMS = {"login_status_to_id": login_status_to_id}
```

Custom transform files execute as Python code. Treat them like source code, not
data from untrusted parties.

## Dropping Source Fields

Use `drop` only for fields you intentionally reviewed:

```yaml
drop:
  - $.debug
  - $.rawPayload
```

Dropped fields remain visible in explain output. Unreviewed fields stay in
`unmapped_source_fields`, which is the main guardrail against silent data loss.

## Real Mapping Workflow

1. Map only the fields you understand.
2. Run `ocsfkit explain --json` and sort by `unmapped_source_fields`.
3. Add mappings for high-value fields.
4. Add `drop` entries for noisy fields after review.
5. Run `ocsfkit lint` on mapped output.
6. Use `ocsfkit diff` before replacing a production mapping.

## Built-In Class Coverage

The registry is intentionally small but no longer single-class:

- `2004` Detection Finding
- `3002` Authentication
- `4001` Network Activity
- `1007` Process Activity

Each class defines required and recommended fields independently so mappings can
be linted according to the class they produce.
