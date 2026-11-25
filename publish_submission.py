"""Publishes or removes a config for a creator, as asked from the clicker.

The clicker pushes a request on its own submit/... branch, signed with the creator key in submission.json:
- post: configs/<name>.zip and configs/<name>.info.json, copied to main;
- remove: nothing else, the config and its info file are deleted from main.
Then index.json is rebuilt and the branch deleted. A request is refused when:
- the signature doesn't match the key of its author in the CREATORS secret ({"Name": "key", ...});
- it touches other files than the ones of its config and submission.json;
- the zip of a post is not a clicker export;
- the config was posted by another creator, or a config to remove doesn't exist.
The author shown in the library is the one the creator wrote, the creator who posted it is kept as its owner.

Run by .github/workflows/submission.yml with the BRANCH and CREATORS environment variables, on a checkout of main."""
import hashlib
import hmac
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import make_index

SUBMISSION = "submission.json"
STEM = re.compile(r"^[\w ()-]+$")
POST, REMOVE = "post", "remove"


class Refused(Exception):
    pass


def git(*args: str, binary: bool = False):
    result = subprocess.run(["git", *args], check=True, capture_output=True)
    return result.stdout if binary else result.stdout.decode("utf-8").strip()


def read(branch: str, path: str) -> bytes:
    try:
        return git("show", f"origin/{branch}:{path}", binary=True)
    except subprocess.CalledProcessError:
        raise Refused(f"{path} is missing")


def owner(file: str) -> str | None:
    """The creator who posted a config on main, or its author for a config posted before the author could be changed;
    "" when it has none, None when there is no such config."""
    if not (make_index.CONFIGS / file).exists():
        return None
    info = make_index.CONFIGS / f"{file[:-len('.zip')]}{make_index.INFO_SUFFIX}"
    fields = (make_index.read_info(info) or {}) if info.exists() else {}
    return fields.get("creator") or fields.get("author", "")


def check(branch: str, creators: dict) -> tuple[str, str, str, bytes, dict]:
    """The action, author and file of a valid request, with the zip and info of a post. Raises Refused otherwise."""
    try:
        submission = json.loads(read(branch, SUBMISSION))
        action, author, file = submission["action"], submission["author"], submission["file"]
        zip_sha, info_sha, time, signature = (submission[key] for key in ("zip_sha256", "info_sha256", "time", "signature"))
    except (ValueError, KeyError, TypeError):
        raise Refused(f"{SUBMISSION} can't be read")
    if action not in (POST, REMOVE):
        raise Refused(f"unknown action {action}")

    key = creators.get(author)
    if not isinstance(key, str) or not key:
        raise Refused(f"{author} is not a creator")
    message = "\n".join([action, author, file, zip_sha, info_sha, time]).encode("utf-8")
    if not hmac.compare_digest(hmac.new(key.encode("utf-8"), message, hashlib.sha256).hexdigest(), str(signature)):
        raise Refused(f"the signature of {author} doesn't match")

    stem = file[:-len(".zip")] if file.endswith(".zip") else ""
    if not STEM.match(stem) or stem.startswith((" ", "-")) or stem != stem.strip():
        raise Refused(f"{file} is not a valid config name")
    zip_path, info_path = f"configs/{file}", f"configs/{stem}{make_index.INFO_SUFFIX}"
    allowed = {zip_path, info_path, SUBMISSION} if action == POST else {SUBMISSION}
    changed = set(git("diff", "--name-only", f"origin/main...origin/{branch}").splitlines())
    if not changed <= allowed:
        raise Refused(f"the request changes other files: {', '.join(sorted(changed - allowed))}")

    current = owner(file)
    if current is not None and current.casefold() != author.casefold():
        raise Refused(f"{file} belongs to {current or 'the library maintainers'}, not to {author}")
    if action == REMOVE:
        if current is None:
            raise Refused(f"{file} is not in the library")
        return action, author, file, b"", {}

    content = read(branch, zip_path)
    info_bytes = read(branch, info_path)
    if hashlib.sha256(content).hexdigest() != zip_sha or hashlib.sha256(info_bytes).hexdigest() != info_sha:
        raise Refused("the files don't match the signed post")
    try:
        info = json.loads(info_bytes.decode("utf-8-sig"))
        if not isinstance(info, dict):
            raise ValueError
    except ValueError:
        raise Refused(f"{info_path} can't be read")

    with tempfile.TemporaryDirectory() as folder:
        check_zip = Path(folder) / file
        check_zip.write_bytes(content)
        try:
            make_index.describe(check_zip)
        except Exception as exc:
            raise Refused(f"{file} is not a clicker export ({exc})")

    fields = {"name": str(info.get("name") or stem).strip(), "description": str(info.get("description") or "").strip(),
              "author": str(info.get("author") or "").strip() or author, "creator": author,
              "tags": [str(tag).strip() for tag in info.get("tags") or [] if str(tag).strip()],
              "screen": str(info.get("screen") or "").strip()}
    return action, author, file, content, fields


def apply(action: str, author: str, file: str, content: bytes, info: dict) -> None:
    stem = file[:-len(".zip")]
    zip_path = make_index.CONFIGS / file
    info_path = make_index.CONFIGS / f"{stem}{make_index.INFO_SUFFIX}"
    if action == POST:
        zip_path.write_bytes(content)
        info_path.write_text(json.dumps(info, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        message = f"Post {info['name']} by {author}"
    else:
        zip_path.unlink()
        info_path.unlink(missing_ok=True)
        message = f"Remove {stem} by {author}"
    make_index.main()
    git("config", "user.name", "github-actions[bot]")
    git("config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com")
    git("add", "-A", "configs", "index.json")
    if subprocess.run(["git", "diff", "--cached", "--quiet"]).returncode == 0:
        print(f"configs/{file}: already in the library as posted")
        return
    git("commit", "-m", message)
    git("pull", "--rebase", "origin", "main")
    git("push", "origin", "HEAD:main")
    print(f"configs/{file}: {'published' if action == POST else 'removed'} for {author}")


def main() -> int:
    branch = os.environ["BRANCH"]
    try:
        creators = json.loads(os.environ.get("CREATORS") or "{}")
        if not isinstance(creators, dict):
            raise ValueError
    except ValueError:
        print("::error::the CREATORS secret must be written like {\"Name\": \"key\"}")
        return 1
    try:
        git("fetch", "origin", branch, "main")
        apply(*check(branch, creators))
        return 0
    except Refused as exc:
        print(f"::error::Request refused: {exc}")
        return 1
    finally:
        subprocess.run(["git", "push", "origin", "--delete", branch], capture_output=True)


if __name__ == "__main__":
    sys.exit(main())
