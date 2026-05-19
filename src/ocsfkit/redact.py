from __future__ import annotations

import re
from typing import Any

from ocsfkit.privacy import PATTERNS

REDACTED = "<redacted>"


def redact_value(value: Any, replacement: str = REDACTED) -> Any:
    if isinstance(value, dict):
        return {
            key: replacement if _sensitive_key(str(key)) else redact_value(child, replacement)
            for key, child in value.items()
        }
    if isinstance(value, list):
        return [redact_value(child, replacement) for child in value]
    if isinstance(value, str):
        return _redact_string(value, replacement)
    return value


def _sensitive_key(key: str) -> bool:
    return bool(PATTERNS["generic_secret"].search(key))


def _redact_string(value: str, replacement: str) -> str:
    redacted = value
    for kind, pattern in PATTERNS.items():
        if kind == "generic_secret":
            continue
        redacted = pattern.sub(replacement, redacted)
    return _ACCOUNT_ID.sub(replacement, redacted)


_ACCOUNT_ID = re.compile(r"\b\d{12}\b")
