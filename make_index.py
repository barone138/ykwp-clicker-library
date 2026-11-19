"""Rebuilds index.json from the clicker backups in configs/, keeping the descriptions and authors already written."""
import json
import zipfile
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


def main() -> None:
    known = {entry["file"]: entry for entry in json.loads(INDEX.read_text(encoding="utf-8"))["configs"]} \
        if INDEX.exists() else {}
    configs = []
    for path in sorted((HERE / "configs").glob("*.zip")):
        file = f"configs/{quote(path.name)}"
        found = describe(path)
        entry = {"name": found["name"], "description": "", "author": "", "tags": [], **known.get(file, {}),
                 "screen": found["screen"], "events": found["events"], "file": file}
        configs.append(entry)
        print(f"{file}: {entry['name']} ({entry['screen'] or 'unknown screen'}, {entry['events']} events)")
    INDEX.write_text(json.dumps({"configs": configs}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
