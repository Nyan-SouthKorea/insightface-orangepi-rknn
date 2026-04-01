"""Gallery storage helpers for SDK and web backend.

Smoke:
  python - <<'PY'
from runtime.gallery_store import GalleryStore
store = GalleryStore('runtime/gallery')
print(store.list_people())
PY

Full:
  python - <<'PY'
from runtime.gallery_store import GalleryStore
store = GalleryStore('runtime/gallery')
person = store.create_person(name_ko='홍길동', name_en='GilDong')
print(person['person_id'])
print(store.list_people())
PY

Main inputs:
  - gallery root path
  - person names and uploaded image bytes

Main outputs:
  - `runtime/gallery/<person_id>/meta.json`
  - `runtime/gallery/<person_id>/images/*`
"""

from __future__ import annotations

import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable
from uuid import uuid4

try:
    from .gallery_utils import parse_identity
except ImportError:
    from gallery_utils import parse_identity


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def slugify_name(text: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9]+", "-", text.strip().lower()).strip("-")
    return value or "person"


def is_image_path(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS


class GalleryStore:
    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def _person_dir(self, person_id: str) -> Path:
        return self.root / person_id

    def _meta_path(self, person_id: str) -> Path:
        return self._person_dir(person_id) / "meta.json"

    def _images_dir(self, person_id: str) -> Path:
        return self._person_dir(person_id) / "images"

    def _legacy_meta(self, folder: Path) -> dict:
        name_ko, name_en = parse_identity(folder.name)
        return {
            "person_id": folder.name,
            "name_ko": name_ko,
            "name_en": name_en,
            "legacy": True,
            "created_at": None,
            "updated_at": None,
        }

    def _load_meta(self, folder: Path) -> dict | None:
        meta_path = folder / "meta.json"
        if meta_path.exists():
            payload = json.loads(meta_path.read_text())
            payload.setdefault("person_id", folder.name)
            payload.setdefault("name_ko", payload.get("kr_name") or folder.name)
            payload.setdefault("name_en", payload.get("en_name") or payload["name_ko"])
            payload["legacy"] = False
            return payload

        image_files = [path for path in sorted(folder.iterdir()) if is_image_path(path)]
        if image_files:
            return self._legacy_meta(folder)
        return None

    def _image_paths(self, folder: Path, meta: dict) -> list[Path]:
        if meta.get("legacy"):
            return [path for path in sorted(folder.iterdir()) if is_image_path(path)]
        images_dir = folder / "images"
        if not images_dir.exists():
            return []
        return [path for path in sorted(images_dir.iterdir()) if is_image_path(path)]

    def list_people(self) -> list[dict]:
        people = []
        for folder in sorted(path for path in self.root.iterdir() if path.is_dir()):
            meta = self._load_meta(folder)
            if meta is None:
                continue
            image_paths = self._image_paths(folder, meta)
            people.append(
                {
                    "person_id": meta["person_id"],
                    "name_ko": meta["name_ko"],
                    "name_en": meta["name_en"],
                    "legacy": bool(meta.get("legacy")),
                    "created_at": meta.get("created_at"),
                    "updated_at": meta.get("updated_at"),
                    "image_count": len(image_paths),
                    "images": [
                        {
                            "image_id": path.name,
                            "filename": path.name,
                            "path": str(path),
                        }
                        for path in image_paths
                    ],
                }
            )
        return people

    def get_person(self, person_id: str) -> dict:
        for person in self.list_people():
            if person["person_id"] == person_id:
                return person
        raise FileNotFoundError(f"갤러리 인물을 찾지 못했습니다: {person_id}")

    def iter_embedding_targets(self) -> Iterable[dict]:
        for folder in sorted(path for path in self.root.iterdir() if path.is_dir()):
            meta = self._load_meta(folder)
            if meta is None:
                continue
            image_paths = self._image_paths(folder, meta)
            if not image_paths:
                continue
            yield {
                "person_id": meta["person_id"],
                "name_ko": meta["name_ko"],
                "name_en": meta["name_en"],
                "legacy": bool(meta.get("legacy")),
                "image_paths": image_paths,
            }

    def create_person(self, name_ko: str, name_en: str) -> dict:
        created_at = utc_now_iso()
        person_id = f"{slugify_name(name_en or name_ko)}-{uuid4().hex[:8]}"
        person_dir = self._person_dir(person_id)
        images_dir = self._images_dir(person_id)
        images_dir.mkdir(parents=True, exist_ok=False)
        meta = {
            "person_id": person_id,
            "name_ko": name_ko.strip(),
            "name_en": name_en.strip() or name_ko.strip(),
            "created_at": created_at,
            "updated_at": created_at,
        }
        self._meta_path(person_id).write_text(json.dumps(meta, indent=2, ensure_ascii=False))
        return self.get_person(person_id)

    def update_person(self, person_id: str, name_ko: str, name_en: str) -> dict:
        meta_path = self._meta_path(person_id)
        if not meta_path.exists():
            raise FileNotFoundError(f"수정할 갤러리 meta를 찾지 못했습니다: {person_id}")
        meta = json.loads(meta_path.read_text())
        meta["name_ko"] = name_ko.strip()
        meta["name_en"] = name_en.strip() or name_ko.strip()
        meta["updated_at"] = utc_now_iso()
        meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False))
        return self.get_person(person_id)

    def delete_person(self, person_id: str) -> None:
        person_dir = self._person_dir(person_id)
        if not person_dir.exists():
            raise FileNotFoundError(f"삭제할 갤러리 인물을 찾지 못했습니다: {person_id}")
        shutil.rmtree(person_dir)

    def save_image_bytes(
        self,
        person_id: str,
        content: bytes,
        *,
        extension: str = ".jpg",
        filename_prefix: str = "capture",
    ) -> dict:
        images_dir = self._images_dir(person_id)
        if not images_dir.exists():
            raise FileNotFoundError(f"이미지를 저장할 갤러리 인물을 찾지 못했습니다: {person_id}")
        safe_extension = extension.lower()
        if safe_extension not in IMAGE_EXTENSIONS:
            safe_extension = ".jpg"
        filename = f"{filename_prefix}-{uuid4().hex[:8]}{safe_extension}"
        image_path = images_dir / filename
        image_path.write_bytes(content)
        self._touch_person_meta(person_id)
        return {
            "image_id": filename,
            "filename": filename,
            "path": str(image_path),
        }

    def save_image_file(self, person_id: str, source_path: str | Path, *, filename_prefix: str = "upload") -> dict:
        source_path = Path(source_path)
        suffix = source_path.suffix or ".jpg"
        return self.save_image_bytes(
            person_id,
            source_path.read_bytes(),
            extension=suffix,
            filename_prefix=filename_prefix,
        )

    def delete_image(self, person_id: str, image_id: str) -> None:
        person = self.get_person(person_id)
        if person["legacy"]:
            raise RuntimeError("legacy gallery 폴더의 이미지는 web API로 삭제하지 않습니다.")
        image_path = self._images_dir(person_id) / image_id
        if not image_path.exists():
            raise FileNotFoundError(f"삭제할 이미지를 찾지 못했습니다: {person_id}/{image_id}")
        image_path.unlink()
        self._touch_person_meta(person_id)

    def _touch_person_meta(self, person_id: str) -> None:
        meta_path = self._meta_path(person_id)
        if not meta_path.exists():
            return
        meta = json.loads(meta_path.read_text())
        meta["updated_at"] = utc_now_iso()
        meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False))

    def clear_empty_people(self) -> list[str]:
        removed = []
        for person in self.list_people():
            if person["legacy"]:
                continue
            if person["image_count"] != 0:
                continue
            self.delete_person(person["person_id"])
            removed.append(person["person_id"])
        return removed

    def get_image_path(self, person_id: str, image_id: str) -> Path:
        person = self.get_person(person_id)
        if person["legacy"]:
            path = self.root / person_id / image_id
        else:
            path = self._images_dir(person_id) / image_id
        if not path.exists():
            raise FileNotFoundError(f"이미지 파일을 찾지 못했습니다: {person_id}/{image_id}")
        return path
