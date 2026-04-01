"""Locate converted RKNN model packs for runtime code.

Smoke:
  python - <<'PY'
from runtime.rknn_model_zoo import resolve_rknn_model_pack
print(resolve_rknn_model_pack('buffalo_sc')['model_pack'])
PY

Full:
  python - <<'PY'
from runtime.rknn_model_zoo import resolve_rknn_model_pack
info = resolve_rknn_model_pack('buffalo_sc')
print(info['detector_path'])
print(info['recognizer_path'])
PY

Main inputs:
  - `model_pack`: pack name such as `buffalo_sc`
  - optional `model_zoo_root`

Main outputs:
  - detector / recognizer RKNN paths and metadata
"""

from __future__ import annotations

import json
from pathlib import Path


def default_model_zoo_root() -> Path:
    repo_root = Path(__file__).resolve().parent.parent
    return repo_root / "conversion" / "results" / "model_zoo"


def _load_metadata(model_path: Path):
    meta_path = model_path.with_suffix(".json")
    if not meta_path.exists():
        return None
    return json.loads(meta_path.read_text())


def _load_json(json_path: Path):
    if not json_path.exists():
        return None
    return json.loads(json_path.read_text())


def _pick_first(paths: list[Path], label: str) -> Path:
    if not paths:
        raise FileNotFoundError(f"{label} RKNN 파일을 찾지 못했습니다.")
    return sorted(paths)[0]


def resolve_rknn_model_pack(
    model_pack: str,
    target_platform: str = "rk3588",
    model_zoo_root: str | Path | None = None,
    _visited: set[str] | None = None,
):
    root = default_model_zoo_root() if model_zoo_root is None else Path(model_zoo_root)
    pack_dir = root / target_platform / model_pack
    if not pack_dir.exists():
        raise FileNotFoundError(f"RKNN model pack 경로를 찾지 못했습니다: {pack_dir}")

    manifest = _load_json(pack_dir / "pack.json")
    visited = set() if _visited is None else set(_visited)
    if model_pack in visited:
        raise RuntimeError(f"순환 alias를 감지했습니다: {sorted(visited | {model_pack})}")
    visited.add(model_pack)

    if manifest and manifest.get("alias_of"):
        alias_of = manifest["alias_of"]
        resolved = resolve_rknn_model_pack(
            model_pack=alias_of,
            target_platform=target_platform,
            model_zoo_root=root,
            _visited=visited,
        )
        resolved["requested_model_pack"] = model_pack
        resolved["requested_pack_dir"] = pack_dir
        resolved["requested_pack_manifest"] = manifest
        resolved["alias_of"] = alias_of
        return resolved

    if manifest and manifest.get("models"):
        detector_entry = manifest["models"].get("detector")
        recognizer_entry = manifest["models"].get("recognizer")
        if not detector_entry or not recognizer_entry:
            raise FileNotFoundError(f"pack.json에 detector/recognizer 정보가 없습니다: {pack_dir / 'pack.json'}")
        detector_path = pack_dir / detector_entry["output_filename"]
        recognizer_path = pack_dir / recognizer_entry["output_filename"]
    else:
        detector_candidates = list(pack_dir.glob("det*_fp16.rknn")) + list(pack_dir.glob("det*.rknn"))
        recognizer_candidates = [
            path
            for path in sorted(pack_dir.glob("*_fp16.rknn")) + sorted(pack_dir.glob("*.rknn"))
            if not path.name.startswith("det")
        ]
        detector_path = _pick_first(detector_candidates, "detector")
        recognizer_path = _pick_first(recognizer_candidates, "recognizer")

    return {
        "model_pack": model_pack,
        "target_platform": target_platform,
        "pack_dir": pack_dir,
        "pack_manifest": manifest,
        "detector_path": detector_path,
        "recognizer_path": recognizer_path,
        "detector_meta": _load_metadata(detector_path),
        "recognizer_meta": _load_metadata(recognizer_path),
    }


def list_rknn_model_packs(
    target_platform: str = "rk3588",
    model_zoo_root: str | Path | None = None,
):
    root = default_model_zoo_root() if model_zoo_root is None else Path(model_zoo_root)
    platform_dir = root / target_platform
    if not platform_dir.exists():
        return []

    items = []
    for pack_dir in sorted(path for path in platform_dir.iterdir() if path.is_dir()):
        pack_name = pack_dir.name
        try:
            info = resolve_rknn_model_pack(
                model_pack=pack_name,
                target_platform=target_platform,
                model_zoo_root=root,
            )
        except Exception as error:
            items.append(
                {
                    "model_pack": pack_name,
                    "target_platform": target_platform,
                    "pack_dir": pack_dir,
                    "error": str(error),
                }
            )
            continue

        items.append(
            {
                "model_pack": pack_name,
                "requested_model_pack": info.get("requested_model_pack", pack_name),
                "resolved_model_pack": info["model_pack"],
                "alias_of": info.get("alias_of"),
                "target_platform": info["target_platform"],
                "pack_dir": info["pack_dir"],
                "detector_path": info["detector_path"],
                "recognizer_path": info["recognizer_path"],
                "pack_manifest": info.get("pack_manifest"),
            }
        )
    return items
