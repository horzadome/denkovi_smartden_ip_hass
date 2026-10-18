# Contributing

## How it works

Denkovi smartDEN devices expose their current state through a JSON API.
The devices accept control with rudimentary JSON commands.
The integration interacts with this API using HTTP requests. For example, to retrieve the current state:

`GET /current_state.json?pw=PASSWORD`

The integration reads every channel array of `/current_state.json`. A digital input becomes
a binary sensor, and its `Count` becomes an attribute. An analog or temperature channel
takes the scaled number of its `Measure` text, with the unit and the device class of that
text. The analog reading of `Value` and the `Measure` text stay as the `device_value` and
`device_measure` attributes. An output the owner sets (`AnalogOutput`, `PWM`) becomes a
number entity. The integration shows a device value such as `---` as unknown, so the entity
stays available.

A relay of the smartDEN family changes with the `RelayN` query parameter. An example is
`/current_state.json?pw=PASSWORD&Relay1=1`. The DAEnetIP4 uses `OutputN`. Each group lists
its arrays, the kind of its value and its parameter names in `CHANNEL_GROUPS` in `const.py`.

## Out of scope

The integration omits SNMP, because SNMP differs a lot from HTTP and the devices rarely need
it. It does not use XML or HTML unless necessary, because JSON is more efficient. It does
not encrypt the password, because the device then loses the Multiple Access feature.

## Development and validation

The repository uses GitHub Actions for hassfest, HACS validation and MegaLinter.
Every check must pass in CI before publication.

Lint with MegaLinter. Its result is the only result that counts.

If you really need a linter of your own, run it. It reads the configuration in the project
root, never a file in `megalinter-reports/`, which is temporary. Settle any difference between
it and MegaLinter yourself. Keep one configuration file for each linter.

Read the result of a MegaLinter run from the files in `megalinter-reports/`:

- `linters_logs/` holds one file for each linter. A name that ends in `-SUCCESS.log` is a
  linter that passed. A name that ends in `-ERROR.log` is a linter that failed, and the file
  holds the findings.
- `megalinter.log` holds the log of the run.
- `tap/` holds one result file for each linter, in the TAP format.
- `updated_sources/` holds a copy of each file the run repaired.
- `IDE-config/` holds configuration for editors, and `IDE-config.txt` explains it.

The setting `CLEAR_REPORT_FOLDER: true` in `.mega-linter.yml` empties the directory at the start
of each run, so it holds one run only. Read `megalinter.log` when a run fails without an error
file.

Do not read the output of the container. That output is long, and it changes with the terminal
and with a pipe.

When the run is over, delete the whole directory `megalinter-reports/`. The next run writes it
again, and an old directory misleads a later scan.

MegaLinter reads a configuration file from the project root, under the name it expects for that
linter. The run log names the file in its `Rules config:` line. The names are `.mypy.ini`,
`.pylintrc`, `.markdownlint.json`, `.yamllint.yml`, `.ruff.toml` and `.bandit.yml`.

Add a file only for a setting that differs from the default.

When the file is absent, MegaLinter uses its own default and copies that default into
`megalinter-reports/IDE-config/`. Read that folder to compare your editor settings with those of
MegaLinter.

Check which file a run used. Read the `Rules config:` line and the `--config` or `--rcfile`
argument in `megalinter-reports/megalinter.log`. A path under `/tmp/lint/` is a file of the
project. A path under `/action/lib/.automation/` is a default of the image, and the project
settings then do not apply.

Run every Python command in a container that holds the packages of
[requirements_test.txt](requirements_test.txt). Run the tests with `python -m pytest -q`
inside that container. Never run Python on the host machine.

The `CHANNEL_GROUPS` table in `const.py` holds the channel groups. Add an array there after you
check its format against the manual and, where possible, against a device.

## Branch and release flow

`main` accepts changes only through a pull request. A pull request can come from a fork or
from a branch in this repository. The repository owner applies the ruleset in
[.github/rulesets/main.json](.github/rulesets/main.json) one time:

```bash
gh api --method POST repos/horzadome/denkovi_smartden_ip_hass/rulesets \
  --input .github/rulesets/main.json
```

The ruleset requires a pull request, one approving review and the `MegaLinter`, `Hassfest`
and `HACS validation` checks. It requires the code owner in
[.github/CODEOWNERS](.github/CODEOWNERS) to approve, dismisses stale reviews, and blocks
force pushes and deletion. The repository admin can bypass the rules only through a pull
request. Direct pushes stay blocked.

A merge to `main` starts [.github/workflows/release.yml](.github/workflows/release.yml).
The workflow creates a GitHub release for the `version` in
[manifest.json](custom_components/denkovi_smartden_ip/manifest.json) and tags it
`v<version>`. The notes hold [.github/release-notes.md](.github/release-notes.md), then the
list of merged pull requests that GitHub generates. Bump `version` in `manifest.json` in the
PR that releases, so the tag and the manifest hold the same value. A merge that leaves the
version unchanged gets no new release. Do not create a tag or a release by hand.

## Manuals

[Denkovi smartDEN IP-16R Manual](https://denkovi.com/Documents/smartDen-IP-16R/Current-Version/UserManual.pdf)
[Denkovi smartDEN IP-32IN Manual](https://denkovi.com/Documents/smartDen-IP-32IN/Current-Version/smartDEN-IP-32IN.pdf)

<!-- ste-disable-file STE005 STE022 -->
