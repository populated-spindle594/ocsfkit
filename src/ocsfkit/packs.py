from __future__ import annotations

from pathlib import Path
from typing import Any

from ocsfkit.io import load_mapping_file
from ocsfkit.validation import validate_mapping_doc

BUILTIN_PACKS = {
    "aws": [
        "examples/guardduty-mapping.yaml",
        "examples/securityhub-mapping.yaml",
        "examples/cloudtrail-console-login-mapping.yaml",
    ],
    "identity": [
        "examples/okta-authentication-mapping.yaml",
        "examples/azure-ad-signin-mapping.yaml",
        "examples/github-audit-mapping.yaml",
    ],
    "network": [
        "examples/paloalto-traffic-mapping.yaml",
        "examples/zeek-conn-mapping.yaml",
        "examples/cloudflare-log-mapping.yaml",
    ],
    "detections": [
        "examples/crowdstrike-detection-mapping.yaml",
        "examples/sentinel-alert-mapping.yaml",
        "examples/defender-alert-mapping.yaml",
        "examples/wiz-finding-mapping.yaml",
        "examples/lacework-alert-mapping.yaml",
        "examples/splunk-notable-mapping.yaml",
        "examples/gcp-scc-finding-mapping.yaml",
    ],
    "infrastructure": ["examples/kubernetes-audit-mapping.yaml"],
}


def list_packs() -> list[dict[str, Any]]:
    return [
        {"name": name, "mappings": mappings, "mapping_count": len(mappings)}
        for name, mappings in sorted(BUILTIN_PACKS.items())
    ]


def validate_pack(root: str = ".") -> list[dict[str, Any]]:
    base = Path(root)
    results: list[dict[str, Any]] = []
    for pack_name, mappings in sorted(BUILTIN_PACKS.items()):
        for mapping in mappings:
            path = base / mapping
            issues = validate_mapping_doc(load_mapping_file(str(path)))
            results.append(
                {
                    "pack": pack_name,
                    "mapping": mapping,
                    "issues": [issue.model_dump() for issue in issues],
                }
            )
    return results
