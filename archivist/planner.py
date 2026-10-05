"""Pure logic: decide where each file should go. No filesystem access."""

from __future__ import annotations

import re
import time
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class FileInfo:
    path: Path
    name: str
    size: int
    mtime: float


@dataclass(frozen=True)
class Move:
    src: Path
    dest: Path
    reason: str
    size: int


def classify(name: str, cfg: dict):
    """Return (folder, reason). folder is None when the file should stay put."""
    for rule in cfg["rules"]:
        if re.search(rule["pattern"], name, re.IGNORECASE):
            return rule["dest"], f"rule /{rule['pattern']}/"
    ext = Path(name).suffix.lower().lstrip(".")
    if ext:
        for folder, exts in cfg["categories"].items():
            if ext in (e.lower().lstrip(".") for e in exts):
                return folder, f".{ext}"
    return cfg["other_folder"], "unknown type"


def plan_moves(files, root: Path, cfg: dict, dest_base: Path | None = None) -> list:
    moves = []
    # If no custom destination is provided, organize them inside the root folder
    base = dest_base if dest_base else root

    for f in files:
        folder, reason = classify(f.name, cfg)
        if folder is None:
            continue
        parts = folder.replace("\\", "/").split("/")
        stamp = time.localtime(f.mtime)
        if cfg["group_by"] == "year":
            parts.append(time.strftime("%Y", stamp))
        elif cfg["group_by"] == "month":
            parts.append(time.strftime("%Y-%m", stamp))

        dest = base.joinpath(*parts, f.name)
        if dest == f.path:
            continue  # already where it belongs
        moves.append(Move(f.path, dest, reason, f.size))
    return moves
