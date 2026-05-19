from __future__ import annotations

from pathlib import Path
from typing import Any

from ocsfkit.io import load_mapping_file
from ocsfkit.mapping_test import run_mapping_tests
from ocsfkit.validation import validate_mapping_doc

BUILTIN_PACKS = {
    "aws": [
        "examples/guardduty-mapping.yaml",
        "examples/securityhub-mapping.yaml",
        "examples/cloudtrail-console-login-mapping.yaml",
        "examples/aws-vpc-flow-mapping.yaml",
    ],
    "identity": [
        "examples/okta-authentication-mapping.yaml",
        "examples/azure-ad-signin-mapping.yaml",
        "examples/azure-activity-mapping.yaml",
        "examples/github-audit-mapping.yaml",
        "examples/google-cloud-audit-mapping.yaml",
        "examples/windows-security-auth-mapping.yaml",
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
    "infrastructure": [
        "examples/kubernetes-audit-mapping.yaml",
        "examples/sysmon-process-mapping.yaml",
    ],
}


def resolve_pack_mapping(name: str) -> str:
    aliases = _pack_aliases()
    key = name.removesuffix(".yaml")
    if key not in aliases:
        available = ", ".join(sorted(aliases))
        raise KeyError(f"Unknown mapping pack {name!r}. Available packs: {available}")
    return _mapping_path(aliases[key])


def load_pack_mapping(name: str) -> dict[str, Any]:
    return load_mapping_file(resolve_pack_mapping(name))


def list_packs() -> list[dict[str, Any]]:
    return [
        {
            "name": name,
            "mappings": mappings,
            "aliases": [_aliases_for_mapping(name, mapping) for mapping in mappings],
            "mapping_count": len(mappings),
        }
        for name, mappings in sorted(BUILTIN_PACKS.items())
    ]


def validate_pack(root: str = ".") -> list[dict[str, Any]]:
    base = Path(root)
    results: list[dict[str, Any]] = []
    for pack_name, mappings in sorted(BUILTIN_PACKS.items()):
        for mapping in mappings:
            path = base / mapping
            issues = validate_mapping_doc(load_mapping_file(str(path)))
            issues.extend(_contract_issues(base, mapping, str(path)))
            results.append(
                {
                    "pack": pack_name,
                    "mapping": mapping,
                    "issues": [issue.model_dump() for issue in issues],
                }
            )
    return results


def _pack_aliases() -> dict[str, str]:
    aliases: dict[str, str] = {}
    for pack_name, mappings in BUILTIN_PACKS.items():
        for mapping in mappings:
            stem = Path(mapping).stem
            short = stem.removesuffix("-mapping")
            aliases[stem] = mapping
            aliases[short] = mapping
            aliases[f"{pack_name}-{short}"] = mapping
            aliases[f"{pack_name}/{short}"] = mapping
    return aliases


def _aliases_for_mapping(pack_name: str, mapping: str) -> str:
    short = Path(mapping).stem.removesuffix("-mapping")
    if short == pack_name or short.startswith(f"{pack_name}-"):
        return short
    return f"{pack_name}-{short}"


def _mapping_path(mapping: str) -> str:
    repo_path = Path(mapping)
    if repo_path.exists():
        return str(repo_path)
    packaged_path = Path(__file__).resolve().parent / mapping
    if packaged_path.exists():
        return str(packaged_path)
    return str(repo_path)


def _contract_issues(base: Path, mapping: str, mapping_path: str) -> list[Any]:
    from ocsfkit.models import LintIssue

    issues: list[LintIssue] = []
    mapping_doc = load_mapping_file(mapping_path)
    metadata = mapping_doc.get("metadata") if isinstance(mapping_doc, dict) else None
    if not isinstance(metadata, dict):
        issues.append(LintIssue(level="warning", path="metadata", message="Missing metadata"))
        return issues
    fixture = metadata.get("fixture")
    if not isinstance(fixture, str) or not (base / fixture).exists():
        issues.append(
            LintIssue(level="error", path="metadata.fixture", message="Fixture is missing")
        )
    golden = base / "tests" / "goldens" / Path(mapping).name
    if not golden.exists():
        issues.append(
            LintIssue(level="error", path="tests.golden", message="Golden mapping test is missing")
        )
    else:
        result = run_mapping_tests(str(golden))[0]
        if not result["passed"]:
            issues.append(
                LintIssue(level="error", path="tests.golden", message="Golden mapping test fails")
            )
    return issues
