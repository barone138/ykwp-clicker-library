# YKWP clicker library

Ready-made configs for SmartAutoclicker+. The clicker's **Library** (⋮ menu on the config list) reads
`index.json` from this repository every time it opens, so adding, changing or removing a config here reaches every
user with no new APK.

## Adding, updating and removing a config

Everything is done on GitHub, from the browser; nobody needs to run anything on their computer. Collaborators of this
repository can change it directly.

- **Add:** in the clicker, export the config (⋮ → Export). On GitHub open the `configs` folder, press **Add file →
  Upload files**, drop the `.zip` and press **Commit changes**. Within a minute an info file with the same name,
  `<name>.info.json`, appears next to it: open it, press the pencil, fill the description, author and tags, and commit.
- **Update:** upload the new export with **exactly the same file name**: it replaces the old zip, and the config gets
  today's date.
- **Remove:** open the zip in `configs`, press **⋯ → Delete file** and commit. Its info file goes away by itself.

After every change, the **Rebuild index.json** action (Actions tab) rebuilds `index.json` from every zip in `configs`
and saves it. The Library shows the change within a few minutes, with a red ! on its button. Never edit `index.json`
by hand: the action writes it again from the zips and the info files.

## Posting from the clicker (creators)

A creator posts a config straight from the clicker, with no GitHub account and no approval: with a creator code in
**Settings → Creator**, each config of the list has a **Post** button. The clicker pushes the zip, its info file and a
signed `submission.json` on a branch of its own (`submit/<creator>/<time>`), and the **Publish a post** action checks
it, copies it to `configs`, rebuilds `index.json` and deletes the branch. The config is online a few minutes later.

The action refuses a post when its signature doesn't match the key of its author, when it touches other files, when
its zip isn't a clicker export, or when a config with the same name belongs to someone else. The author always comes
from the code, so nobody can post as another creator, and posting again with the same name updates one's own config.

The maintainer makes the codes on a computer:

1. On GitHub, **Settings → Developer settings → Personal access tokens → Fine-grained tokens → Generate new token**:
   only this repository, permission **Contents: Read and write**. One token per creator, so each can be revoked alone.
2. `py creator_code.py add "Name" <token>` prints the code to give to the creator and updates `creators.json` (kept on
   the computer, never committed).
3. Copy all of `creators.json` into the **CREATORS** secret of this repository (**Settings → Secrets and variables →
   Actions**). Do it again after every change.

`py creator_code.py remove "Name"` takes a creator out (update the secret and revoke the token too), and
`py creator_code.py list` shows the creators. A token holds write access to this repository: give codes only to people
you trust; if one is misused, revoke its token and restore the files from the history.

## The info file

```json
{
  "name": "Stage farm",
  "description": "Plays the event stages, with the stage clear and login events ready for Dual.",
  "author": "Author",
  "tags": ["Gates", "Energy"],
  "screen": "900x1600"
}
```

- `name`: the name shown in the Library.
- `screen`: the resolution the config was made for, written as width x height. The clicker also gives it to the
  imported config when its export didn't keep one.
- `tags`: see Tags below.
- `updated` (optional, like `"updated": "2026-11-20"`): forces the date shown in the Library. Leave it out and the date
  is automatic: the day the zip was added or last replaced.

Each config has its own info file, so two people editing two configs never touch the same file. If an info file has a
mistake (a missing quote or comma), the action shows a warning on that file and the config keeps the info it had; the
other configs are not affected. A zip that isn't a clicker export is left out with a warning too.

## index.json

Written by the action, for the clicker:

```json
{
  "configs": [
    {
      "name": "Stage farm",
      "description": "Plays the event stages, with the stage clear and login events ready for Dual.",
      "author": "Author",
      "tags": ["Gates", "Energy"],
      "screen": "900x1600",
      "events": 12,
      "file": "configs/stage-farm.zip",
      "sha": "3f9a0c1d22b7",
      "updated": "2026-11-20"
    }
  ]
}
```

`events` is counted from the zip, `sha` is its fingerprint (replacing a zip changes the index, so the clicker puts a
red ! on its Library button until the Library is opened) and `updated` is the date the Library shows next to the
config, listing the newest first.

`py make_index.py` does the same as the action on a computer, for testing; pull first, so the index is built from
every config.

## Tags

Each tag has its own color in the clicker: `Pseudokai`, `Gates`, `Energy`, `Score Attack`, `Maps` and `General`. Write
them as in this list, inside the brackets, between quotes and separated by commas. A new tag works too, with a color of
its own, and needs no new APK.

The Library can be searched by name, description, author and tag, and its filter button narrows the list by resolution,
author and tags. The list starts with the newest configs; **Sort** switches to names. On the same date, or sorted by
name, configs made for the screen of the device are listed first. An entry the clicker can't read is skipped, the others still show.

## New versions of the clicker

`app.json` holds the latest published version of the clicker:

```json
{
  "versionCode": 19,
  "versionName": "1.7.0",
  "url": "https://github.com/barone138/ykwp-clicker-library/releases/latest/download/smartautoclicker.apk",
  "notes": ""
}
```

When `versionCode` is higher than the installed one, the clicker puts a red ! on its i button and opens the news page
once, with a Download button that opens `url` and the `notes` text. To publish a version, attach the APK to a release
of this repository with the file name `smartautoclicker.apk`, then raise `versionCode` and `versionName` here to the
ones of the new APK. The `url` always downloads the APK of the latest release, and ADB-YKWP-Dual's **Install
clicker** downloads it from the same link.
