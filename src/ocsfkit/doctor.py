from __future__ import annotations

import os
import platform
import shutil
import subprocess
from pathlib import Path
from typing import Any

from ocsfkit import __version__
from ocsfkit.packs import validate_pack
from ocsfkit.registry import DEFAULT_SCHEMA_VERSION, SUPPORTED_SCHEMA_VERSIONS


def run_doctor(root: str = ".", ci: bool = False) -> dict[str, Any]:
    pack_results = validate_pack(root)
    pack_errors = sum(
        1
        for result in pack_results
        for issue in result["issues"]
        if issue.get("level") == "error"
    )
    checks = [
        _check("ocsfkit_version", True, __version__),
        _check("python", True, platform.python_version()),
        _check(
            "bundled_schema",
            DEFAULT_SCHEMA_VERSION in SUPPORTED_SCHEMA_VERSIONS,
            DEFAULT_SCHEMA_VERSION,
        ),
        _check("examples_dir", (Path(root) / "examples").is_dir(), str(Path(root) / "examples")),
        _check("mapping_packs", pack_errors == 0, f"{pack_errors} errors"),
        _check("git", True, shutil.which("git") or "not found"),
        _check("brew", True, shutil.which("brew") or "not found"),
    ]
    if ci:
        checks.extend(_ci_checks())
    return {"passed": all(check["passed"] for check in checks), "checks": checks}


def _check(name: str, passed: bool, detail: str) -> dict[str, Any]:
    return {"name": name, "passed": passed, "detail": detail}


def _ci_checks() -> list[dict[str, Any]]:
    repository = os.environ.get("GITHUB_REPOSITORY", "pfrederiksen/ocsfkit")
    checks = [
        _check("gh", shutil.which("gh") is not None, shutil.which("gh") or "not found"),
    ]
    if shutil.which("gh") is None:
        return checks
    checks.extend(
        [
            _github_check(
                "github_release_workflow",
                "api",
                f"repos/{repository}/contents/.github/workflows/release.yml",
            ),
            _github_check(
                "github_pypi_environment",
                "api",
                f"repos/{repository}/environments/pypi",
            ),
            _github_check(
                "github_homebrew_variable",
                "api",
                f"repos/{repository}/actions/variables/HOMEBREW_TAP_ENABLED",
            ),
            _github_check(
                "github_homebrew_secret_visibility",
                "api",
                f"repos/{repository}/actions/secrets/HOMEBREW_TAP_TOKEN",
            ),
        ]
    )
    return checks


def _github_check(name: str, *args: str) -> dict[str, Any]:
    try:
        subprocess.run(("gh", *args), check=True, capture_output=True, text=True, timeout=20)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        detail = getattr(exc, "stderr", "") or str(exc)
        return _check(name, False, detail.strip() or "failed")
    return _check(name, True, "ok")
