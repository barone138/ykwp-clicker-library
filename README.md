# YKWP clicker library

Ready-made configs for the ADB Smart AutoClicker. The clicker's **Library** (⋮ menu on the config list) reads
`index.json` from this repository every time it opens, so adding, changing or removing a config here reaches every
user with no new APK.

## Adding a config

1. In the clicker, export the config (⋮ → Export) and copy the `.zip` into `configs/`.
2. Run `py make_index.py`. It lists every zip of `configs/` in `index.json`, with its name, screen and number of
   events.
3. In `index.json`, fill the `description`, `author` and `tags` of the new entry, and correct its `screen` when the
   config was made for another resolution. Names, descriptions, authors, tags and screens written by hand are kept the
   next time the script runs.
4. Commit and push. The Library shows the change within a few minutes.

To update a config, replace its zip with the new export (same file name) and run the script again. To remove one,
delete its zip and run the script again.

## index.json

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
      "sha": "3f9a0c1d22b7"
    }
  ]
}
```

`file` is relative to `index.json` and can also be a full link. `screen` is the resolution the config was made for;
the clicker also gives it to the imported config when its export didn't keep one. `sha` is written by the script from
the zip, so replacing a zip changes the index too.

Every change of `index.json` puts a red ! on the clicker's Library button, until the Library is opened.

## Tags

Each tag has its own color in the clicker: `Pseudokai`, `Gates`, `Energy`, `Score Attack`, `Maps` and `General`. Write
them as in this list, inside the brackets, between quotes and separated by commas. A new tag works too, with a color of
its own, and needs no new APK.

The Library can be searched by name, description, author and tag, and its filter button narrows the list by resolution,
author and tags. Configs made for the screen of the device are listed
first. An entry the clicker can't read is skipped, the others still show.

## New versions of the clicker

`app.json` holds the latest published version of the clicker:

```json
{
  "versionCode": 17,
  "versionName": "1.6.0",
  "url": "https://github.com/barone138/ykwp-clicker-library/releases/latest",
  "notes": ""
}
```

When `versionCode` is higher than the installed one, the clicker puts a red ! on its i button and opens the news page
once, with a Download button that opens `url` and the `notes` text. To publish a version, attach the APK to a release
of this repository, then raise `versionCode` and `versionName` here to the ones of the new APK.
