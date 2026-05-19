from __future__ import annotations

import shutil
import tempfile
import urllib.request
import zipfile
from pathlib import Path
from typing import Any

import yaml

from ocsfkit.errors import OCSFKitError

PACK_HOME_ENV = "OCSFKIT_PACK_HOME"


def pack_home() -> Path:
    import os

    configured = os.environ.get(PACK_HOME_ENV)
    if configured:
        return Path(configured).expanduser()
    return Path.home() / ".config" / "ocsfkit" / "packs"


def installed_packs() -> list[dict[str, Any]]:
    root = pack_home()
    if not root.exists():
        return []
    packs: list[dict[str, Any]] = []
    for manifest_path in sorted(root.glob("*/pack.yaml")):
        manifest = _read_manifest(manifest_path)
        pack_dir = manifest_path.parent
        mappings = sorted(str(path.relative_to(pack_dir)) for path in pack_dir.rglob("*.yaml"))
        mappings = [path for path in mappings if path != "pack.yaml"]
        packs.append(
            {
                "name": manifest.get("name", pack_dir.name),
                "version": manifest.get("version"),
                "source": manifest.get("source"),
                "path": str(pack_dir),
                "mappings": mappings,
                "mapping_count": len(mappings),
            }
        )
    return packs


def resolve_installed_mapping(name: str) -> str | None:
    key = name.removesuffix(".yaml")
    for pack in installed_packs():
        pack_name = str(pack["name"])
        for mapping in pack["mappings"]:
            stem = Path(mapping).stem
            short = stem.removesuffix("-mapping")
            aliases = {
                stem,
                short,
                f"{pack_name}-{short}",
                f"{pack_name}/{short}",
            }
            if key in aliases:
                return str(Path(pack["path"]) / mapping)
    return None


def install_pack(source: str, name: str | None = None, force: bool = False) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="ocsfkit-pack-") as tmp:
        source_root = _materialize_source(source, Path(tmp))
        manifest = _discover_manifest(source_root)
        pack_name = name or manifest.get("name") or source_root.name
        if not isinstance(pack_name, str) or not pack_name:
            raise OCSFKitError("Pack name could not be determined")
        destination = pack_home() / _safe_name(pack_name)
        if destination.exists():
            if not force:
                raise OCSFKitError(f"Pack {pack_name!r} is already installed; use --force")
            shutil.rmtree(destination)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(source_root, destination)
        manifest_path = destination / "pack.yaml"
        manifest = _read_manifest(manifest_path) if manifest_path.exists() else {}
        manifest.update({"name": pack_name, "source": source})
        manifest_path.write_text(yaml.safe_dump(manifest, sort_keys=False))
        mapping_count = len(
            [path for path in destination.rglob("*.yaml") if path.name != "pack.yaml"]
        )
        return {
            "name": pack_name,
            "path": str(destination),
            "mapping_count": mapping_count,
        }


def update_pack(name: str, force: bool = True) -> dict[str, Any]:
    current = next((pack for pack in installed_packs() if pack["name"] == name), None)
    if current is None:
        raise OCSFKitError(f"Installed pack not found: {name}")
    source = current.get("source")
    if not isinstance(source, str) or not source:
        raise OCSFKitError(f"Pack {name!r} does not record an update source")
    return install_pack(source, name=name, force=force)


def uninstall_pack(name: str) -> dict[str, Any]:
    current = next((pack for pack in installed_packs() if pack["name"] == name), None)
    if current is None:
        raise OCSFKitError(f"Installed pack not found: {name}")
    path = Path(str(current["path"]))
    shutil.rmtree(path)
    return {"name": name, "path": str(path), "removed": True}


def _materialize_source(source: str, tmp: Path) -> Path:
    path = Path(source).expanduser()
    if path.exists():
        if path.is_dir():
            return path
        if zipfile.is_zipfile(path):
            return _extract_zip(path, tmp)
        raise OCSFKitError(f"Unsupported pack source file: {source}")
    if source.startswith(("https://", "http://")):
        archive = tmp / "pack.zip"
        urllib.request.urlretrieve(source, archive)
        if not zipfile.is_zipfile(archive):
            raise OCSFKitError("Pack URL must point to a zip archive")
        return _extract_zip(archive, tmp)
    raise OCSFKitError(f"Pack source not found: {source}")


def _extract_zip(archive: Path, tmp: Path) -> Path:
    extract_root = tmp / "extract"
    with zipfile.ZipFile(archive) as package:
        package.extractall(extract_root)
    children = [path for path in extract_root.iterdir() if path.is_dir()]
    return children[0] if len(children) == 1 else extract_root


def _discover_manifest(root: Path) -> dict[str, Any]:
    manifest_path = root / "pack.yaml"
    return _read_manifest(manifest_path) if manifest_path.exists() else {}


def _read_manifest(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text()) or {}
    if not isinstance(data, dict):
        raise OCSFKitError(f"Pack manifest must be an object: {path}")
    return data


def _safe_name(name: str) -> str:
    return "".join(char if char.isalnum() or char in {"-", "_", "."} else "-" for char in name)
