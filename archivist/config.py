"""Default rules plus optional user overrides from ~/.archivist/config.json."""
from __future__ import annotations

import copy
import json
import os
import re
from pathlib import Path, PurePosixPath


class ConfigError(Exception):
    pass


DEFAULT_CATEGORIES = {
    "Documents": ["pdf", "doc", "docx", "txt", "rtf", "md", "odt", "pages"],
    "Spreadsheets": ["xls", "xlsx", "csv", "numbers", "ods"],
    "Presentations": ["ppt", "pptx", "key", "odp"],
    "Images": ["jpg", "jpeg", "png", "gif", "heic", "webp", "svg", "bmp", "tiff"],
    "Videos": ["mp4", "mov", "mkv", "avi", "webm", "m4v"],
    "Audio": ["mp3", "wav", "flac", "m4a", "aac", "ogg"],
    "Archives": ["zip", "tar", "gz", "tgz", "7z", "rar", "bz2"],
    "Installers": ["dmg", "pkg", "exe", "msi", "deb", "appimage"],
    "Books": ["epub", "mobi", "azw3"],
    "Code": ["py", "js", "ts", "tsx", "jsx", "java", "c", "cpp", "h", "rs", "go", "sh", "ipynb", "html", "css"],
    "Design": ["psd", "ai", "fig", "sketch", "xd", "indd"],
    "Data": ["json", "xml", "yaml", "yml", "sql", "db", "sqlite"],
}

DEFAULTS = {
    "categories": DEFAULT_CATEGORIES,
    # Rules run before extension matching. First match wins. Patterns are
    # case-insensitive regexes searched against the file name.
    "rules": [{"pattern": r"^(Screenshot|Screen Shot|CleanShot)", "dest": "Images/Screenshots"}],
    "group_by": "none",  # none | year | month (by modified date)
    "min_age_minutes": 10,  # skip files touched more recently than this
    "ignore_extensions": ["crdownload", "part", "download", "tmp", "partial", "opdownload"],
    "ignore_names": ["desktop.ini", "Thumbs.db"],
    "project_markers": [
        ".git", "package.json", "pyproject.toml", "Cargo.toml",
        "project.godot", "pom.xml", "build.gradle", "Makefile",
    ],
    "other_folder": "Other",  # set to null to leave unknown file types alone
}


def home_dir() -> Path:
    """Where config and undo history live. Override with ARCHIVIST_HOME."""
    return Path(os.environ.get("ARCHIVIST_HOME", Path.home() / ".archivist"))


def _check_rel(label: str, value) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ConfigError(f"{label}: must be a non-empty string")
    norm = value.replace("\\", "/")
    p = PurePosixPath(norm)
    if p.is_absolute() or ".." in p.parts or norm.startswith("~") or re.match(r"^[A-Za-z]:", norm):
        raise ConfigError(f"{label}: '{value}' must be a relative folder inside the target folder")


def validate(cfg: dict) -> None:
    for name, exts in cfg["categories"].items():
        _check_rel(f"category '{name}'", name)
        if not isinstance(exts, list):
            raise ConfigError(f"category '{name}': extensions must be a list")
    for i, rule in enumerate(cfg["rules"]):
        if "pattern" not in rule or "dest" not in rule:
            raise ConfigError(f"rule #{i + 1}: needs 'pattern' and 'dest'")
        try:
            re.compile(rule["pattern"])
        except re.error as e:
            raise ConfigError(f"rule #{i + 1}: bad pattern ({e})")
        _check_rel(f"rule #{i + 1} dest", rule["dest"])
    if cfg["other_folder"] is not None:
        _check_rel("other_folder", cfg["other_folder"])
    if cfg["group_by"] not in ("none", "year", "month"):
        raise ConfigError("group_by must be 'none', 'year', or 'month'")
    if not isinstance(cfg["min_age_minutes"], (int, float)) or cfg["min_age_minutes"] < 0:
        raise ConfigError("min_age_minutes must be a number >= 0")


def load_config(path: Path | None = None) -> dict:
    cfg = copy.deepcopy(DEFAULTS)
    path = path or home_dir() / "config.json"
    if path.exists():
        try:
            user = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            raise ConfigError(f"{path}: invalid JSON ({e})")
        for key, value in user.items():
            if key not in DEFAULTS:
                raise ConfigError(f"{path}: unknown setting '{key}'")
            if key == "categories":
                cfg["categories"].update(value)
            elif key == "rules":
                cfg["rules"] = list(value) + cfg["rules"]  # yours run first
            else:
                cfg[key] = value
    validate(cfg)
    return cfg
