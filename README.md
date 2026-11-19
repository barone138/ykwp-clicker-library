# YKWP clicker library

Ready-made configs for the ADB Smart AutoClicker. The clicker's **Library** (⋮ menu on the config list) reads
`index.json` from this repository every time it opens, so adding, changing or removing a config here reaches every
user with no new APK.

## Adding a config

1. In the clicker, export the config (⋮ → Export) and copy the `.zip` into `configs/`.
2. Run `py make_index.py`. It lists every zip of `configs/` in `index.json`, with its name, screen and number of
   events.
3. In `index.json`, fill the `description` and `author` of the new entry. Names, descriptions and authors written by
   hand are kept the next time the script runs.
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
      "screen": "900x1600",
      "events": 12,
      "file": "configs/stage-farm.zip"
    }
  ]
}
```

`file` is relative to `index.json` and can also be a full link. Configs made for the screen of the device are listed
first. An entry the clicker can't read is skipped, the others still show.
