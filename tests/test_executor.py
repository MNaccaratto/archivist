from archivist.executor import apply_moves, undo_last, unique_path
from archivist.planner import plan_moves
from archivist.scanner import scan
from conftest import make_file


def run(root, cfg):
    files, _ = scan(root, cfg)
    return apply_moves(plan_moves(files, root, cfg), root)


def test_organizes_files_into_folders(tmp_path, cfg):
    make_file(tmp_path / "a.pdf")
    make_file(tmp_path / "b.png")
    done, errors = run(tmp_path, cfg)
    assert not errors and len(done) == 2
    assert (tmp_path / "Documents" / "a.pdf").exists()
    assert (tmp_path / "Images" / "b.png").exists()


def test_never_overwrites(tmp_path, cfg):
    make_file(tmp_path / "Documents" / "a.pdf", content="old")
    make_file(tmp_path / "a.pdf", content="new")
    run(tmp_path, cfg)
    assert (tmp_path / "Documents" / "a.pdf").read_text() == "old"
    assert (tmp_path / "Documents" / "a (1).pdf").read_text() == "new"


def test_unique_path(tmp_path):
    (tmp_path / "x.txt").write_text("1")
    (tmp_path / "x (1).txt").write_text("2")
    assert unique_path(tmp_path / "x.txt") == tmp_path / "x (2).txt"


def test_undo_restores_and_removes_empty_folders(tmp_path, cfg):
    make_file(tmp_path / "a.pdf")
    run(tmp_path, cfg)
    restored, skipped = undo_last()
    assert restored == 1 and skipped == []
    assert (tmp_path / "a.pdf").exists()
    assert not (tmp_path / "Documents").exists()
    assert undo_last() is None  # history consumed


def test_undo_skips_when_original_spot_taken(tmp_path, cfg):
    make_file(tmp_path / "a.pdf", content="first")
    run(tmp_path, cfg)
    make_file(tmp_path / "a.pdf", content="second")
    restored, skipped = undo_last()
    assert restored == 0 and len(skipped) == 1
    assert (tmp_path / "a.pdf").read_text() == "second"
    assert (tmp_path / "Documents" / "a.pdf").read_text() == "first"
