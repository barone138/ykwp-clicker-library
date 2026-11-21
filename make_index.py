"""Rebuilds index.json from the clicker backups in configs/.

Each zip can have an info file next to it, configs/<zip name>.info.json, with the fields written by hand: name,
description, author, tags, screen and, to force it, updated. A zip with no info file gets one, filled with what the
zip tells and with what index.json already said. index.json itself is never edited by hand."""
import hashlib
import json
import subprocess
import zipfile
from datetime import date
from pathlib import Path
from urllib.parse import quote

HERE = Path(__file__).parent
CONFIGS = HERE / "configs"
INDEX = HERE / "index.json"
INFO_SUFFIX = ".info.json"
TEXT_FIELDS = ("name", "description", "author", "screen", "updated")


def warn(path: Path, text: str) -> None:
    print(f"::warning file=configs/{path.name}::{text}")


def describe(path: Path) -> dict:
    with zipfile.ZipFile(path) as archive:
        backups = [json.loads(archive.read(name)) for name in archive.namelist() if name.endswith(".json")]
    if not backups:
        raise ValueError("it has no scenario")
    first = backups[0]
    width, height = sorted((first.get("screenWidth", 0), first.get("screenHeight", 0)))
    return {
        "name": first["scenario"]["scenario"]["name"] if len(backups) == 1 else path.stem,
        "screen": f"{width}x{height}" if width else "",
        "events": sum(len(backup["scenario"]["events"]) for backup in backups),
    }


def info_file(zip_path: Path) -> Path:
    return zip_path.with_name(zip_path.stem + INFO_SUFFIX)


def read_info(path: Path) -> dict | None:
    """The hand-written fields of one config, or None when the file can't be read. A field that is not text (or a list
    of texts for tags) is ignored."""
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as exc:
        warn(path, f"{path.name} can't be read, its config keeps the info it had ({exc})")
        return None
    if not isinstance(data, dict):
        warn(path, f"{path.name} must be an object between braces, its config keeps the info it had")
        return None
    info = {key: data[key].strip() for key in TEXT_FIELDS if isinstance(data.get(key), str) and data[key].strip()}
    tags = data.get("tags")
    if isinstance(tags, list):
        info["tags"] = [tag.strip() for tag in tags if isinstance(tag, str) and tag.strip()]
    if "updated" in info and not is_date(info["updated"]):
        warn(path, f"updated must be written like 2026-11-20, '{info.pop('updated')}' is ignored")
    return info


def write_info(path: Path, entry: dict) -> None:
    fields = {"name": entry["name"], "description": entry["description"], "author": entry["author"],
              "tags": entry["tags"], "screen": entry["screen"]}
    path.write_text(json.dumps(fields, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def is_date(text: str) -> bool:
    try:
        return date.fromisoformat(text).isoformat() == text
    except ValueError:
        return False


def committed(path: Path) -> str:
    """The day the zip was last committed, or "" when it never was."""
    return subprocess.run(["git", "log", "-1", "--format=%cs", "--", path.name], cwd=path.parent,
                          capture_output=True, text=True).stdout.strip()


def updated(path: Path, sha: str, known: dict | None) -> str:
    """A new or replaced zip is dated today; otherwise the date already in the index stays, and an entry without one
    takes the day its zip was last committed."""
    if known is None or known.get("sha") != sha:
        return date.today().isoformat()
    return known.get("updated") or committed(path) or date.today().isoformat()


def main() -> None:
    known = {entry["file"]: entry for entry in json.loads(INDEX.read_text(encoding="utf-8"))["configs"]} \
        if INDEX.exists() else {}
    zips = sorted(CONFIGS.glob("*.zip"))
    configs = []
    for path in zips:
        file = f"configs/{quote(path.name)}"
        try:
            found = describe(path)
        except (zipfile.BadZipFile, KeyError, TypeError, ValueError) as exc:
            warn(path, f"{path.name} is not a clicker export, left out ({exc})")
            continue
        old = known.get(file)
        sha = hashlib.sha256(path.read_bytes()).hexdigest()[:12]
        entry = {"name": found["name"], "description": "", "author": "", "tags": [], "screen": found["screen"]}
        kept = {key: old[key] for key in entry if old and old.get(key)}
        info = info_file(path)
        hand = read_info(info) if info.exists() else None
        if not info.exists():
            write_info(info, {**entry, **kept})
            print(f"configs/{info.name}: created, fill in its description, author and tags")
        entry.update(kept if hand is None else {key: value for key, value in hand.items() if key != "updated"})
        hand = hand or {}
        entry.update({"events": found["events"], "file": file, "sha": sha,
                      "updated": hand.get("updated") or updated(path, sha, old)})
        configs.append(entry)
        print(f"{file}: {entry['name']} ({entry['screen'] or 'unknown screen'}, {entry['events']} events, "
              f"updated {entry['updated']})")
    for orphan in CONFIGS.glob("*" + INFO_SUFFIX):
        if not orphan.with_name(orphan.name[:-len(INFO_SUFFIX)] + ".zip").exists():
            orphan.unlink()
            print(f"configs/{orphan.name}: removed, its zip is gone")
    INDEX.write_text(json.dumps({"configs": configs}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
