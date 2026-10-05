"""Find candidate files, skipping anything risky."""
from __future__ import annotations

import os
import time
from collections import Counter
from pathlib import Path

from .planner import FileInfo

SKIP_DIR_SUFFIXES = {".app", ".photoslibrary", ".xcodeproj", ".framework", ".bundle", ".lproj"}


def is_project(directory: Path, markers) -> bool:
    return any((directory / m).exists() for m in markers)


def reserved_folders(cfg: dict) -> set:
    """Top-level folders archivist creates, so re-runs don't re-process them."""
    names = set(cfg["categories"])
    if cfg["other_folder"]:
        names.add(cfg["other_folder"].replace("\\", "/").split("/")[0])
    for rule in cfg["rules"]:
        names.add(rule["dest"].replace("\\", "/").split("/")[0])
    for name in list(names):
        names.add(name.replace("\\", "/").split("/")[0])
    return names


def scan(root: Path, cfg: dict, recursive: bool = False, now: float | None = None):
    """Return (files, skipped) where skipped maps a reason to a count."""
    now = time.time() if now is None else now
    min_age = cfg["min_age_minutes"] * 60
    ignore_names = set(cfg["ignore_names"])
    ignore_ext = {e.lower().lstrip(".") for e in cfg["ignore_extensions"]}
    skipped: Counter = Counter()
    files: list = []

    def consider(p: Path) -> None:
        if p.is_symlink():
            skipped["symlinks"] += 1
        elif p.name.startswith(".") or p.name in ignore_names:
            skipped["hidden/system files"] += 1
        elif p.suffix.lower().lstrip(".") in ignore_ext:
            skipped["unfinished downloads/temp files"] += 1
        else:
            try:
                st = p.stat()
            except OSError:
                skipped["unreadable files"] += 1
                return
            if now - st.st_mtime < min_age:
                skipped["modified too recently"] += 1
            else:
                files.append(FileInfo(p, p.name, st.st_size, st.st_mtime))

    if not recursive:
        for p in sorted(root.iterdir()):
            if p.is_dir():
                skipped["folders (left alone)"] += 1
            else:
                consider(p)
        return files, skipped

    reserved = reserved_folders(cfg)
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        here = Path(dirpath)
        keep = []
        for d in sorted(dirnames):
            full = here / d
            if d.startswith(".") or full.suffix.lower() in SKIP_DIR_SUFFIXES or full.is_symlink():
                skipped["system/bundle folders"] += 1
            elif here == root and d in reserved:
                skipped["already-organized folders"] += 1
            elif is_project(full, cfg["project_markers"]):
                skipped["project folders"] += 1
            else:
                keep.append(d)
        dirnames[:] = keep
        for name in sorted(filenames):
            consider(here / name)
    return files, skipped
