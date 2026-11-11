"""
Photo album — local storage, JSON index, age-based cleanup.

Layout under ``~/.herandhim/context/photos/``:

    index.json                  ← chronological metadata index
    2026-05-23_1002_selfie.jpg
    2026-05-23_1604_selfie.jpg
    reference/                  ← user-supplied character reference images
        portrait_01.jpg
        ...
"""

from __future__ import annotations

import json
import logging
import os
import shutil
from datetime import datetime, timedelta
from typing import Any

from ... import config

logger = logging.getLogger(__name__)


def _photos_dir() -> str:
    return os.path.join(str(config.HERANDHIM_HOME), "context", "photos")


def _reference_dir(root: str | None = None) -> str:
    """Reference directory for this album (or the configured home by default)."""
    base = root or _photos_dir()
    return os.path.join(base, "reference")


def _reference_source_dir() -> str:
    """Optional read-only directory containing user-supplied reference images."""
    return config.get_str(
        "skills", "image", "referenceDirectory",
        env="HERANDHIM_IMAGE_REFERENCE_DIR", default="",
    ).strip()


def _primary_reference_override() -> str:
    """Optional exact face-master path; takes precedence over directory sorting."""
    return config.get_str(
        "skills", "image", "primaryReference",
        env="HERANDHIM_IMAGE_PRIMARY_REFERENCE", default="",
    ).strip()


class PhotoAlbum:
    """Stores generated photos with metadata, prunes old entries."""

    def __init__(self, root: str | None = None, retention_days: int = 30) -> None:
        self.root = root or _photos_dir()
        self.retention_days = retention_days
        os.makedirs(self.root, exist_ok=True)
        os.makedirs(_reference_dir(self.root), exist_ok=True)

    # ── Index ────────────────────────────────────────────────────────────

    @property
    def _index_path(self) -> str:
        return os.path.join(self.root, "index.json")

    def _load_index(self) -> list[dict[str, Any]]:
        if not os.path.exists(self._index_path):
            return []
        try:
            with open(self._index_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                return data
            return data.get("entries", [])
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning("[PhotoAlbum] failed to load index: %s", exc)
            return []

    def _save_index(self, entries: list[dict[str, Any]]) -> None:
        with open(self._index_path, "w", encoding="utf-8") as f:
            json.dump(entries, f, indent=2, ensure_ascii=False)

    # ── Reference images ─────────────────────────────────────────────────

    def list_references(self) -> list[str]:
        """List local and optional external reference images without modifying either."""
        roots = [_reference_dir(self.root)]
        source = _reference_source_dir()
        if source:
            roots.append(os.path.expanduser(source))

        found: list[str] = []
        seen: set[str] = set()
        for directory in roots:
            if not os.path.isdir(directory):
                continue
            for name in sorted(os.listdir(directory)):
                if not name.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
                    continue
                path = os.path.realpath(os.path.join(directory, name))
                if path not in seen and os.path.isfile(path):
                    seen.add(path)
                    found.append(path)
        return found

    def primary_reference(self) -> str | None:
        """Resolve the canonical face reference without guessing from body/tattoo files.

        Prefer an explicitly configured master, then recognisable Sheridan/master
        filenames, then the app's own canonical reference. Only as a last resort
        use the first image in the configured reference directory.
        """
        override = os.path.expanduser(_primary_reference_override())
        if override:
            if not os.path.isfile(override):
                raise FileNotFoundError(
                    f"Configured Sheridan primaryReference does not exist: {override}"
                )
            return os.path.realpath(override)

        refs = self.list_references()
        if not refs:
            return None

        def rank(path: str) -> tuple[int, str]:
            name = os.path.basename(path).lower()
            stem = os.path.splitext(name)[0]
            if stem in {"sheridan_master", "sheridan_primary", "sheridan_face_master",
                        "primary_face", "face_master"}:
                return (0, name)
            if "sheridan" in stem and any(k in stem for k in ("master", "primary", "face")):
                return (1, name)
            if stem == "companion_reference":
                return (2, name)
            if any(k in stem for k in ("face", "portrait", "headshot")):
                return (3, name)
            return (4, name)

        return sorted(refs, key=rank)[0]

    # Canonical face reference stored by the app. External reference collections
    # are read-only and are never deleted when this value is refreshed.
    REFERENCE_NAME = "companion_reference"

    def set_reference(self, src_path: str) -> str:
        """Store/replace only the app-managed canonical reference; preserve all others."""
        d = _reference_dir(self.root)
        os.makedirs(d, exist_ok=True)
        ext = os.path.splitext(src_path)[1].lower() or ".jpg"
        if ext not in {".jpg", ".jpeg", ".png", ".webp"}:
            ext = ".jpg"
        dst = os.path.join(d, self.REFERENCE_NAME + ext)
        for old in os.listdir(d):
            if os.path.splitext(old)[0] == self.REFERENCE_NAME and old != os.path.basename(dst):
                try:
                    os.remove(os.path.join(d, old))
                except OSError:
                    pass
        shutil.copyfile(src_path, dst)
        return dst

    def save_reference_bytes(self, data: bytes) -> str:
        """Write raw image bytes as the app-managed canonical reference."""
        d = _reference_dir(self.root)
        os.makedirs(d, exist_ok=True)
        dst = os.path.join(d, self.REFERENCE_NAME + ".jpg")
        with open(dst, "wb") as f:
            f.write(data)
        return dst

    def clear_references(self) -> None:
        """Clear only app-managed references; never delete the user's source collection."""
        d = _reference_dir(self.root)
        if not os.path.isdir(d):
            return
        for name in os.listdir(d):
            path = os.path.join(d, name)
            if os.path.isfile(path) and name.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
                try:
                    os.remove(path)
                except OSError:
                    pass

    # ── Save ─────────────────────────────────────────────────────────────

    def add(self, src_path: str, *, kind: str, prompt: str, metadata: dict[str, Any]) -> str:
        """Move a freshly generated image into the album and index it.

        Returns the new absolute path inside the album.
        """
        if not os.path.isfile(src_path):
            raise FileNotFoundError(src_path)

        now = datetime.now()
        ext = os.path.splitext(src_path)[1] or ".jpg"
        name = f"{now.strftime('%Y-%m-%d_%H%M%S')}_{kind}{ext}"
        dst = os.path.join(self.root, name)

        if os.path.dirname(os.path.realpath(src_path)) != os.path.realpath(self.root):
            shutil.move(src_path, dst)
        else:
            dst = src_path

        entry = {
            "filename": os.path.basename(dst),
            "path": dst,
            "kind": kind,
            "timestamp": now.isoformat(timespec="seconds"),
            "prompt": prompt,
            **metadata,
        }
        entries = self._load_index()
        entries.append(entry)
        self._save_index(entries)
        return dst

    # ── Query ────────────────────────────────────────────────────────────

    def recent(self, days: int = 7, kind: str | None = None) -> list[dict[str, Any]]:
        cutoff = datetime.now() - timedelta(days=days)
        out = []
        for e in self._load_index():
            try:
                ts = datetime.fromisoformat(e["timestamp"])
            except (KeyError, ValueError):
                continue
            if ts < cutoff:
                continue
            if kind and e.get("kind") != kind:
                continue
            out.append(e)
        return out

    def latest(self, kind: str | None = None) -> dict[str, Any] | None:
        entries = self._load_index()
        for e in reversed(entries):
            if kind is None or e.get("kind") == kind:
                return e
        return None

    # ── Cleanup ──────────────────────────────────────────────────────────

    def cleanup(self) -> int:
        """Delete photos older than ``retention_days``. Returns count removed."""
        cutoff = datetime.now() - timedelta(days=self.retention_days)
        entries = self._load_index()
        keep: list[dict[str, Any]] = []
        removed = 0
        for e in entries:
            try:
                ts = datetime.fromisoformat(e["timestamp"])
            except (KeyError, ValueError):
                keep.append(e)
                continue
            if ts < cutoff:
                path = e.get("path", "")
                if path and os.path.isfile(path):
                    try:
                        os.remove(path)
                        removed += 1
                    except OSError as exc:
                        logger.warning("[PhotoAlbum] failed to delete %s: %s", path, exc)
                        keep.append(e)
                        continue
            else:
                keep.append(e)
        self._save_index(keep)
        if removed:
            logger.info("[PhotoAlbum] cleaned up %d photo(s) older than %d days",
                        removed, self.retention_days)
        return removed



