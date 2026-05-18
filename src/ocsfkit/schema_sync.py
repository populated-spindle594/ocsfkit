from __future__ import annotations

import json
import tempfile
import urllib.request
import zipfile
from pathlib import Path
from typing import Any

from ocsfkit.errors import InputLoadError
from ocsfkit.schema_import import import_schema

DEFAULT_OCSF_ARCHIVE = "https://github.com/ocsf/ocsf-schema/archive/refs/heads/main.zip"


def sync_schema(output: str, url: str = DEFAULT_OCSF_ARCHIVE) -> dict[str, Any]:
    with tempfile.TemporaryDirectory() as temp_dir:
        archive_path = Path(temp_dir) / "ocsf-schema.zip"
        try:
            urllib.request.urlretrieve(url, archive_path)  # noqa: S310
        except OSError as exc:
            raise InputLoadError(f"Could not download schema archive: {exc}") from exc
        extract_dir = Path(temp_dir) / "schema"
        try:
            with zipfile.ZipFile(archive_path) as archive:
                _safe_extract(archive, extract_dir)
        except zipfile.BadZipFile as exc:
            raise InputLoadError(f"Downloaded schema archive is not a zip file: {exc}") from exc
        imported = import_schema(str(extract_dir))
    Path(output).write_text(json.dumps(imported, indent=2, sort_keys=True) + "\n")
    return imported


def _safe_extract(archive: zipfile.ZipFile, destination: Path) -> None:
    destination = destination.resolve()
    for member in archive.infolist():
        target = (destination / member.filename).resolve()
        if destination not in target.parents and target != destination:
            raise InputLoadError(f"Unsafe path in schema archive: {member.filename}")
        archive.extract(member, destination)
