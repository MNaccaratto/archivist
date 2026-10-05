from archivist.scanner import scan
from conftest import make_file


def names(files):
    return sorted(f.name for f in files)


def test_skips_recent_hidden_partial_and_folders(tmp_path, cfg):
    make_file(tmp_path / "ok.pdf")
    make_file(tmp_path / "fresh.pdf", age_minutes=1)
    make_file(tmp_path / ".hidden")
    make_file(tmp_path / "movie.mp4.crdownload")
    (tmp_path / "SomeFolder").mkdir()
    files, skipped = scan(tmp_path, cfg)
    assert names(files) == ["ok.pdf"]
    assert skipped["modified too recently"] == 1
    assert skipped["hidden/system files"] == 1
    assert skipped["unfinished downloads/temp files"] == 1
    assert skipped["folders (left alone)"] == 1


def test_top_level_does_not_descend(tmp_path, cfg):
    make_file(tmp_path / "sub" / "deep.pdf")
    files, _ = scan(tmp_path, cfg)
    assert files == []


def test_recursive_skips_projects_and_organized_folders(tmp_path, cfg):
    make_file(tmp_path / "sub" / "loose.pdf")
    make_file(tmp_path / "myapp" / "package.json")
    make_file(tmp_path / "myapp" / "notes.pdf")
    make_file(tmp_path / "Documents" / "already.pdf")
    make_file(tmp_path / ".git" / "config")
    files, skipped = scan(tmp_path, cfg, recursive=True)
    assert names(files) == ["loose.pdf"]
    assert skipped["project folders"] == 1
    assert skipped["already-organized folders"] == 1
