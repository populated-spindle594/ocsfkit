from __future__ import annotations

import platform
import shutil
from pathlib import Path
from typing import Any

from ocsfkit import __version__
from ocsfkit.packs import validate_pack
from ocsfkit.registry import DEFAULT_SCHEMA_VERSION, SUPPORTED_SCHEMA_VERSIONS


def run_doctor(root: str = ".") -> dict[str, Any]:
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
    return {"passed": all(check["passed"] for check in checks), "checks": checks}


def _check(name: str, passed: bool, detail: str) -> dict[str, Any]:
    return {"name": name, "passed": passed, "detail": detail}
