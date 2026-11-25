"""Publishes a config posted by a creator from the clicker.

The clicker pushes a post on its own submit/... branch: configs/<name>.zip, configs/<name>.info.json and
submission.json, signed with the creator key. This checks the post, then copies it to main, rebuilds index.json and
deletes the branch. A post is refused when:
- the signature doesn't match the key of its author in the CREATORS secret ({"Name": "key", ...});
- it touches other files than its zip, its info and submission.json;
- its zip is not a clicker export;
- a config with the same name already belongs to another author.

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


def check(branch: str, creators: dict) -> tuple[str, bytes, dict]:
    """The file name, the zip and the info of a valid post. Raises Refused otherwise."""
    try:
        submission = json.loads(read(branch, SUBMISSION))
        author, file = submission["author"], submission["file"]
        zip_sha, info_sha, time, signature = (submission[key] for key in ("zip_sha256", "info_sha256", "time", "signature"))
    except (ValueError, KeyError, TypeError):
        raise Refused(f"{SUBMISSION} can't be read")

    key = creators.get(author)
    if not isinstance(key, str) or not key:
        raise Refused(f"{author} is not a creator")
    message = "\n".join([author, file, zip_sha, info_sha, time]).encode("utf-8")
    if not hmac.compare_digest(hmac.new(key.encode("utf-8"), message, hashlib.sha256).hexdigest(), str(signature)):
        raise Refused(f"the signature of {author} doesn't match")

    stem = file[:-len(".zip")] if file.endswith(".zip") else ""
    if not STEM.match(stem) or stem.startswith((" ", "-")) or stem != stem.strip():
        raise Refused(f"{file} is not a valid config name")
    zip_path, info_path = f"configs/{file}", f"configs/{stem}{make_index.INFO_SUFFIX}"
    allowed = {zip_path, info_path, SUBMISSION}
    changed = set(git("diff", "--name-only", f"origin/main...origin/{branch}").splitlines())
    if not changed <= allowed:
        raise Refused(f"the post changes other files: {', '.join(sorted(changed - allowed))}")

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

    owner_info = make_index.CONFIGS / f"{stem}{make_index.INFO_SUFFIX}"
    if (make_index.CONFIGS / file).exists():
        owner = (make_index.read_info(owner_info) or {}).get("author", "") if owner_info.exists() else ""
        if owner.casefold() != author.casefold():
            raise Refused(f"{file} belongs to {owner or 'the library maintainers'}, not to {author}")

    fields = {"name": str(info.get("name") or stem).strip(), "description": str(info.get("description") or "").strip(),
              "author": author, "tags": [str(tag).strip() for tag in info.get("tags") or [] if str(tag).strip()],
              "screen": str(info.get("screen") or "").strip()}
    return file, content, fields


def publish(file: str, content: bytes, info: dict) -> None:
    stem = file[:-len(".zip")]
    (make_index.CONFIGS / file).write_bytes(content)
    (make_index.CONFIGS / f"{stem}{make_index.INFO_SUFFIX}").write_text(
        json.dumps(info, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    make_index.main()
    git("config", "user.name", "github-actions[bot]")
    git("config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com")
    git("add", "configs", "index.json")
    if subprocess.run(["git", "diff", "--cached", "--quiet"]).returncode == 0:
        print(f"configs/{file}: already in the library as posted")
        return
    git("commit", "-m", f"Post {info['name']} by {info['author']}")
    git("pull", "--rebase", "origin", "main")
    git("push", "origin", "HEAD:main")
    print(f"configs/{file}: published for {info['author']}")


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
        file, content, info = check(branch, creators)
        publish(file, content, info)
        return 0
    except Refused as exc:
        print(f"::error::Post refused: {exc}")
        return 1
    finally:
        subprocess.run(["git", "push", "origin", "--delete", branch], capture_output=True)


if __name__ == "__main__":
    sys.exit(main())
