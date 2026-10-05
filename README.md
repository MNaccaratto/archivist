# Archivist

A small command-line tool that sorts a messy folder into a tidy structure. It previews first, never deletes or overwrites anything, and every run can be undone.

```
$ archivist organize ~/Downloads

Would move 9 file(s) in /Users/you/Downloads

  Documents/  (3 file(s), 6 B)
      hw3.docx
      report (1).pdf
      resume_v3.pdf
  Images/Screenshots/  (1 file(s), 2 B)
      Screenshot 2026-10-01 at 4.12.09 PM.png
  ...

Dry run, nothing was moved. Re-run with --apply to do it.
```

Pure Python, no dependencies, works the same on macOS, Windows, and Linux.

## Install

Requires Python 3.9 or newer.

```bash
git clone https://github.com/<your-username>/archivist.git
cd archivist
pipx install -e .        # or: pip install -e .
```

Run `archivist --version` to check it worked.

## Usage

```bash
archivist organize                      # preview for ~/Downloads (default)
archivist organize --apply              # actually do it
archivist organize ~/Desktop --apply    # any folder
archivist organize --group-by month     # Documents/2026-10/...
archivist undo                          # reverse the most recent run
```

| Option | What it does |
| --- | --- |
| `--apply` | Move files. Without it you only get a preview. |
| `--recursive` | Also pull files out of subfolders. This flattens them into category folders, so use it on inbox-style folders, not on folders you've already organized by hand. |
| `--group-by none\|year\|month` | Add date subfolders based on modified time. |
| `--min-age MINUTES` | Skip files modified more recently than this (default 10). |
| `--config FILE` | Use a specific config file. |
| `--verbose` | List every file instead of the first few per folder. |

## What it does and doesn't touch

- **Moves** loose files into folders by type (Documents, Images, Videos, ...), with screenshots going to `Images/Screenshots`.
- **Never deletes or overwrites.** If `Documents/a.pdf` exists, the new file becomes `a (1).pdf`.
- **Skips** hidden files, symlinks, unfinished downloads (`.crdownload`, `.part`, ...), and anything modified in the last 10 minutes.
- **Leaves folders alone** by default. With `--recursive`, it also skips code projects (anything containing `.git`, `package.json`, `pyproject.toml`, etc.), app bundles, and hidden folders.
- **Refuses** to run on your home folder, a drive root, or a git repository.
- **Undo** restores files to their original locations and removes the folders it created if they're empty. If something now occupies the original spot, that file is skipped and reported.

## Configuration

Optional. Put a `config.json` in `~/.archivist/` (or pass `--config`). Your settings are merged with the defaults:

```json
{
  "rules": [
    { "pattern": "CSCI-?\\d+", "dest": "Academic/CSCI" },
    { "pattern": "resume|cover.?letter", "dest": "Career" }
  ],
  "categories": {
    "Fonts": ["ttf", "otf"]
  },
  "group_by": "none",
  "min_age_minutes": 10,
  "other_folder": "Other"
}
```

- **`rules`** are case-insensitive regexes matched against the file name. Yours run before the built-in ones, and the first match wins.
- **`categories`** maps a folder name to file extensions. Entries are added to (or replace) the defaults.
- **`other_folder`**: set to `null` to leave unrecognized file types where they are.
- Destinations must be relative folders. Absolute paths and `..` are rejected, so a rule can't send files outside the target folder.

## Using it with Google Drive

Drive for desktop mirrors your files to a normal folder, so point Archivist at it like any other (for example the `00_Inbox` folder in your Drive). Run it without `--recursive` on anything you've already organized.

## Project structure

```
archivist/
  planner.py    # decides where each file goes (pure, no filesystem access)
  scanner.py    # finds candidate files and skips risky ones
  executor.py   # moves files, writes history, undoes runs
  config.py     # defaults, loading, and validation
  cli.py        # argument parsing and output
tests/          # pytest suite
```

## Development

```bash
pip install -e ".[dev]"
pytest
```

## Ideas for later

- Run on a schedule (launchd on macOS, Task Scheduler on Windows, cron on Linux)
- Content-based rules (read PDFs to detect course names)
- Duplicate detection by file hash
