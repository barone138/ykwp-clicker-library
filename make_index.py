"""Rebuilds index.json from the clicker backups in configs/, keeping the names, descriptions, authors, tags,
screens and dates already written."""
import hashlib
import json
import subprocess
import zipfile
from datetime import date
from urllib.parse import quote
from pathlib import Path

HERE = Path(__file__).parent
INDEX = HERE / "index.json"


def describe(path: Path) -> dict:
    with zipfile.ZipFile(path) as archive:
        backups = [json.loads(archive.read(name)) for name in archive.namelist() if name.endswith(".json")]
    if not backups:
        raise ValueError(f"{path.name} has no scenario")
    first = backups[0]
    width, height = sorted((first.get("screenWidth", 0), first.get("screenHeight", 0)))
    return {
        "name": first["scenario"]["scenario"]["name"] if len(backups) == 1 else path.stem,
        "screen": f"{width}x{height}" if width else "",
        "events": sum(len(backup["scenario"]["events"]) for backup in backups),
    }


def committed(path: Path) -> str:
    """The day the zip was last committed, or "" when it never was."""
    out = subprocess.run(["git", "log", "-1", "--format=%cs", "--", str(path)], cwd=HERE, capture_output=True,
                         text=True).stdout.strip()
    return out


def updated(path: Path, sha: str, known: dict | None) -> str:
    """A new or replaced zip is dated today; otherwise the date already written stays, and an entry without one takes
    the day its zip was last committed."""
    if known is None or known.get("sha") != sha:
        return date.today().isoformat()
    return known.get("updated") or committed(path) or date.today().isoformat()


def main() -> None:
    known = {entry["file"]: entry for entry in json.loads(INDEX.read_text(encoding="utf-8"))["configs"]} \
        if INDEX.exists() else {}
    configs = []
    for path in sorted((HERE / "configs").glob("*.zip")):
        file = f"configs/{quote(path.name)}"
        found = describe(path)
        sha = hashlib.sha256(path.read_bytes()).hexdigest()[:12]
        entry = {"name": found["name"], "description": "", "author": "", "tags": [], "screen": found["screen"],
                 **known.get(file, {}), "events": found["events"], "file": file, "sha": sha,
                 "updated": updated(path, sha, known.get(file))}
        configs.append(entry)
        print(f"{file}: {entry['name']} ({entry['screen'] or 'unknown screen'}, {entry['events']} events, "
              f"updated {entry['updated']})")
    INDEX.write_text(json.dumps({"configs": configs}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
