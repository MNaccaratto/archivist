import time
from pathlib import Path

from archivist.planner import FileInfo, classify, plan_moves

ROOT = Path("/tmp/dl")


def info(name, mtime=None):
    return FileInfo(ROOT / name, name, 10, mtime or time.time())


def test_extension_maps_to_category(cfg):
    assert classify("notes.PDF", cfg)[0] == "Documents"
    assert classify("song.mp3", cfg)[0] == "Audio"


def test_unknown_type_goes_to_other(cfg):
    assert classify("weird.xyz123", cfg)[0] == "Other"
    assert classify("README", cfg)[0] == "Other"


def test_other_folder_none_leaves_file(cfg):
    cfg["other_folder"] = None
    assert plan_moves([info("weird.xyz123")], ROOT, cfg) == []


def test_screenshot_rule_beats_extension(cfg):
    assert classify("Screenshot 2026-10-04 at 9.00.00 AM.png", cfg)[0] == "Images/Screenshots"


def test_user_rules_run_first(cfg):
    cfg["rules"].insert(0, {"pattern": r"CSCI-?\d+", "dest": "Academic/CSCI"})
    assert classify("CSCI-262_hw3.pdf", cfg)[0] == "Academic/CSCI"


def test_group_by_month(cfg):
    cfg["group_by"] = "month"
    ts = time.mktime((2026, 3, 15, 12, 0, 0, 0, 0, -1))
    (move,) = plan_moves([info("a.pdf", ts)], ROOT, cfg)
    assert move.dest == ROOT / "Documents" / "2026-03" / "a.pdf"


def test_file_already_in_place_is_skipped(cfg):
    placed = FileInfo(ROOT / "Documents" / "a.pdf", "a.pdf", 1, time.time())
    assert plan_moves([placed], ROOT, cfg) == []
