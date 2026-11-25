"""Makes the creator codes of the library, on the maintainer's computer.

    python creator_code.py add "Name" <github token>   makes the code to give to the creator
    python creator_code.py remove "Name"                takes a creator out
    python creator_code.py list                         shows the creators

A code holds the creator name, a new personal key and the GitHub token the clicker posts with. The keys are kept in
creators.json, next to this file and never committed: after each change, copy all of creators.json into the CREATORS
secret of the repository (Settings > Secrets and variables > Actions)."""
import base64
import json
import secrets
import sys
from pathlib import Path

CREATORS = Path(__file__).with_name("creators.json")
PREFIX = "SACP1:"


def load() -> dict:
    return json.loads(CREATORS.read_text(encoding="utf-8")) if CREATORS.exists() else {}


def save(creators: dict) -> None:
    CREATORS.write_text(json.dumps(creators, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"\nNow copy all of {CREATORS.name} into the CREATORS secret of the repository:\n")
    print(json.dumps(creators, ensure_ascii=False))


def add(name: str, token: str) -> None:
    name, token = name.strip(), token.strip()
    if not name or not token:
        sys.exit("The name and the token can't be empty.")
    creators = load()
    if name in creators:
        print(f"{name} was already a creator: the new code replaces the old one, which stops working.")
    creators[name] = secrets.token_hex(24)
    payload = json.dumps({"n": name, "k": creators[name], "t": token}, ensure_ascii=False).encode("utf-8")
    code = PREFIX + base64.urlsafe_b64encode(payload).decode("ascii").rstrip("=")
    print(f"Creator code of {name}, to paste in Settings > Creator of the clicker:\n\n{code}")
    save(creators)


def remove(name: str) -> None:
    creators = load()
    if creators.pop(name.strip(), None) is None:
        sys.exit(f"{name} is not a creator.")
    print(f"{name} can't post anymore once the secret is updated. Revoke the token of {name} on GitHub too.")
    save(creators)


def main() -> None:
    args = sys.argv[1:]
    if args[:1] == ["add"] and len(args) == 3:
        add(args[1], args[2])
    elif args[:1] == ["remove"] and len(args) == 2:
        remove(args[1])
    elif args == ["list"]:
        print("\n".join(load()) or "No creators yet.")
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
