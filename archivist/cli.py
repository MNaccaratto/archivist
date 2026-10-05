"""Command-line interface."""
from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from pathlib import Path

from . import __version__
from .config import ConfigError, load_config
from .executor import apply_moves, undo_last
from .planner import plan_moves
from .scanner import scan

SHOW_PER_FOLDER = 5


def human(n: float) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1024
    return f"{n} B"


def check_root(root: Path) -> None:
    if not root.is_dir():
        raise SystemExit(f"error: {root} is not a folder")
    if root == Path.home() or root.parent == root:
        raise SystemExit("error: refusing to organize your home folder or a drive root. Pick a specific folder.")
    if (root / ".git").exists():
        raise SystemExit("error: that folder is a git repository. Refusing to reorganize a code project.")


def cmd_organize(args) -> int:
    cfg = load_config(Path(args.config).expanduser() if args.config else None)
    if args.group_by:
        cfg["group_by"] = args.group_by
    if args.min_age is not None:
        cfg["min_age_minutes"] = args.min_age

    root = Path(args.path).expanduser().resolve()
    check_root(root)

    files, skipped = scan(root, cfg, recursive=args.recursive)
    moves = plan_moves(files, root, cfg)

    if not moves:
        print(f"Nothing to move in {root}.")
    else:
        groups = defaultdict(list)
        for m in moves:
            groups[m.dest.parent.relative_to(root).as_posix()].append(m)
        print(f"{'Moving' if args.apply else 'Would move'} {len(moves)} file(s) in {root}\n")
        for folder in sorted(groups):
            items = groups[folder]
            print(f"  {folder}/  ({len(items)} file(s), {human(sum(i.size for i in items))})")
            shown = items if args.verbose else items[:SHOW_PER_FOLDER]
            for m in shown:
                print(f"      {m.src.name}")
            if len(shown) < len(items):
                print(f"      ... and {len(items) - len(shown)} more (use --verbose to list all)")

    if skipped:
        print("\nLeft alone: " + ", ".join(f"{n} {why}" for why, n in sorted(skipped.items())))

    if not moves:
        return 0
    if not args.apply:
        print("\nDry run, nothing was moved. Re-run with --apply to do it. Undo anytime with: archivist undo")
        return 0

    done, errors = apply_moves(moves, root)
    print(f"\nMoved {len(done)} file(s). Undo with: archivist undo")
    for e in errors:
        print(f"  could not move {e}", file=sys.stderr)
    return 1 if errors else 0


def cmd_undo(_args) -> int:
    result = undo_last()
    if result is None:
        print("No history to undo.")
        return 0
    restored, skipped = result
    print(f"Restored {restored} file(s) to where they were.")
    for s in skipped:
        print(f"  skipped {s}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="archivist", description="Safely sort messy folders. Dry run by default.")
    p.add_argument("--version", action="version", version=f"archivist {__version__}")
    sub = p.add_subparsers(dest="command", required=True)

    o = sub.add_parser("organize", help="sort a folder (defaults to ~/Downloads)")
    o.add_argument("path", nargs="?", default=str(Path.home() / "Downloads"))
    o.add_argument("--apply", action="store_true", help="actually move files (otherwise preview only)")
    o.add_argument("--recursive", action="store_true",
                   help="also pull files out of subfolders (flattens them into category folders)")
    o.add_argument("--group-by", choices=["none", "year", "month"], help="add date subfolders")
    o.add_argument("--min-age", type=float, metavar="MINUTES", help="skip files modified more recently than this")
    o.add_argument("--config", help="path to a config.json (default: ~/.archivist/config.json)")
    o.add_argument("--verbose", "-v", action="store_true", help="list every file")
    o.set_defaults(func=cmd_organize)

    u = sub.add_parser("undo", help="reverse the most recent organize run")
    u.set_defaults(func=cmd_undo)
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except ConfigError as e:
        print(f"config error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
