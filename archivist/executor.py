"""Perform moves, record history, and undo."""
from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path

from .config import home_dir


def history_dir() -> Path:
    return home_dir() / "history"


def unique_path(dest: Path) -> Path:
    """Never overwrite: 'a.pdf' becomes 'a (1).pdf', 'a (2).pdf', ..."""
    if not dest.exists():
        return dest
    i = 1
    while True:
        candidate = dest.with_name(f"{dest.stem} ({i}){dest.suffix}")
        if not candidate.exists():
            return candidate
        i += 1


def _write_history(root: Path, done: list) -> Path:
    history_dir().mkdir(parents=True, exist_ok=True)
    path = history_dir() / f"{datetime.now().strftime('%Y%m%d-%H%M%S-%f')}.json"
    record = {"created": datetime.now().isoformat(timespec="seconds"), "root": str(root), "moves": done}
    path.write_text(json.dumps(record, indent=2), encoding="utf-8")
    return path


def apply_moves(moves, root: Path):
    """Move files. Returns (done, errors). History is saved even if interrupted."""
    done: list = []
    errors: list = []
    try:
        for m in moves:
            try:
                dest = unique_path(m.dest)
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(m.src), str(dest))
                done.append({"from": str(m.src), "to": str(dest)})
            except OSError as e:
                errors.append(f"{m.src.name}: {e}")
    finally:
        if done:
            _write_history(root, done)
    return done, errors


def _prune_empty_parents(path: Path, root: Path) -> None:
    parent = path.parent
    while parent != root and root in parent.parents:
        try:
            parent.rmdir()  # only succeeds when empty
        except OSError:
            break
        parent = parent.parent


def undo_last():
    """Reverse the most recent run. Returns None, or (restored_count, skipped_messages)."""
    runs = sorted(history_dir().glob("*.json")) if history_dir().exists() else []
    if not runs:
        return None
    latest = runs[-1]
    record = json.loads(latest.read_text(encoding="utf-8"))
    root = Path(record["root"])
    restored = 0
    skipped: list = []
    for mv in reversed(record["moves"]):
        moved, original = Path(mv["to"]), Path(mv["from"])
        if not moved.exists():
            skipped.append(f"{moved.name}: no longer at {moved.parent}")
        elif original.exists():
            skipped.append(f"{original.name}: something already exists at the original location")
        else:
            original.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(moved), str(original))
            _prune_empty_parents(moved, root)
            restored += 1
    done_dir = history_dir() / "undone"
    done_dir.mkdir(exist_ok=True)
    latest.rename(done_dir / latest.name)
    return restored, skipped
