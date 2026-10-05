import pytest

from archivist.cli import main
from archivist.config import ConfigError, load_config
from conftest import make_file


def test_dry_run_moves_nothing(tmp_path, capsys):
    make_file(tmp_path / "a.pdf")
    assert main(["organize", str(tmp_path)]) == 0
    assert (tmp_path / "a.pdf").exists()
    assert "Dry run" in capsys.readouterr().out


def test_apply_then_undo(tmp_path):
    make_file(tmp_path / "a.pdf")
    assert main(["organize", str(tmp_path), "--apply"]) == 0
    assert (tmp_path / "Documents" / "a.pdf").exists()
    assert main(["undo"]) == 0
    assert (tmp_path / "a.pdf").exists()


def test_refuses_git_repo(tmp_path):
    (tmp_path / ".git").mkdir()
    with pytest.raises(SystemExit):
        main(["organize", str(tmp_path)])


def test_refuses_home_folder(monkeypatch, tmp_path):
    monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)
    with pytest.raises(SystemExit):
        main(["organize", str(tmp_path)])


def test_config_rejects_path_escape(tmp_path):
    bad = tmp_path / "c.json"
    bad.write_text('{"rules": [{"pattern": "x", "dest": "../outside"}]}')
    with pytest.raises(ConfigError):
        load_config(bad)


def test_config_rejects_unknown_key(tmp_path):
    bad = tmp_path / "c.json"
    bad.write_text('{"nope": 1}')
    with pytest.raises(ConfigError):
        load_config(bad)
