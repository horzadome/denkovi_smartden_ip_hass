# Local Development instructions

This document tells agents and developers how to work on this project on this specific machine.

Run every Python command in a container. Never run Python on the host machine.

## The three containers

| Container     | Image                                                 | What runs in it                      |
|---------------|-------------------------------------------------------|--------------------------------------|
| dev           | `denkovi-dev`, built from `containers/dev/Dockerfile` | Python, pytest and the tests         |
| MegaLinter    | `ghcr.io/oxsecurity/megalinter-python:v10`            | every linter                         |
| homeassistant | `ghcr.io/home-assistant/home-assistant:2026.10`       | the integration, for the final check |

## The dev container

The image holds Python 3.14, Home Assistant 2026.10.0 and the test packages pinned in
`requirements_test.txt`. Home Assistant arrives with the package
`pytest-homeassistant-custom-component`, which pins it. Build the image before the first run.
Build it again after that file changes:

```bash
podman build -t denkovi-dev -f containers/dev/Dockerfile .
```

The build reads the repository root. The file `.dockerignore` keeps the large directories out
of the build context.

Run a command in the image. The checkout arrives at `/workspace`, so the command reads and
writes the files of the host:

```bash
podman run --rm --userns=keep-id -v "$PWD":/workspace -w /workspace denkovi-dev <command>
```

Run the tests:

```bash
podman run --rm --userns=keep-id -v "$PWD":/workspace -w /workspace denkovi-dev python -m pytest -q
```

The tests of the config flow and of the relay platforms need the harness of
`requirements_test.txt`. The harness sets `asyncio_mode` in `pyproject.toml`, because it
needs the automatic mode of pytest-asyncio.

## Linters

Lint with MegaLinter. Its result is the only result that counts.

If you really need a linter of your own, run it. It reads the configuration in the project
root, never a file in `megalinter-reports/`. Its display does not count. Settle any difference
between it and MegaLinter yourself, and keep one configuration file for each linter.

Check the configuration that MegaLinter reads. The line `Rules config:` of
`megalinter-reports/megalinter.log` names the file, and the command names it again. A path under
`/tmp/lint/` is a file of the project. A path under `/action/lib/.automation/` is a default of
the image.

Run every enabled linter:

```bash
podman run --rm -v "$PWD":/tmp/lint:rw -e DEFAULT_WORKSPACE=/tmp/lint -e MEGALINTER_CONFIG=.mega-linter.yml ghcr.io/oxsecurity/megalinter-python:v10 /entrypoint.sh
```

Run one family when the whole run takes too long. This example runs the Markdown linters:

```bash
podman run --rm -v "$PWD":/tmp/lint:rw -e DEFAULT_WORKSPACE=/tmp/lint -e MEGALINTER_CONFIG=.mega-linter.yml -e ENABLE=MARKDOWN ghcr.io/oxsecurity/megalinter-python:v10 /entrypoint.sh
```

MegaLinter checks Python code, YAML, JSON, Markdown, shell scripts and secrets.

Read the result from the files in `megalinter-reports/`. Do not read the output of the
container.

A linter that passes writes `megalinter-reports/linters_logs/<DESCRIPTOR>_<LINTER>-SUCCESS.log`.
A linter that fails writes `<DESCRIPTOR>_<LINTER>-ERROR.log`. The file `megalinter.log` holds
the log of the run, and the directory `tap/` holds the results as TAP.

When you finish the analysis of a run, delete the whole directory `megalinter-reports/`.

CI runs the same image, the same tag, the same configuration file and the same environment
variables, with one exception: `APPLY_FIXES`. The job is in `.github/workflows/ci.yml`.

A local run rewrites the files it can repair. The file `.mega-linter.yml` sets
`APPLY_FIXES: all`, and the run writes a copy of each changed file under
`megalinter-reports/updated_sources/`.

CI must not change a file, so the job sets `APPLY_FIXES=none` and a run leaves the file alone. A
formatter reports a file that needs a change. It applies the change only when `APPLY_FIXES` is
not `none`, so CI reports the file and a local run repairs it.

## Home Assistant validation

Run hassfest in its own image:

```bash
podman run --rm -v "$PWD":/github/workspace ghcr.io/home-assistant/hassfest
```

## The running container

The quadlet unit is installed at `~/.config/containers/systemd/homeassistant.container`. The
unit runs Home Assistant 2026.10.0 on Python 3.14 and mounts
`custom_components/denkovi_smartden_ip/` at `/config/custom_components/denkovi_smartden_ip/`.

This container is the final validation. It shows that Home Assistant loads the integration
and that the entities work. Do not develop in it. Do not run the tests in it. Do not run a
linter in it.

```bash
systemctl --user start homeassistant
systemctl --user restart homeassistant
systemctl --user status homeassistant
journalctl --user -u homeassistant -f
podman logs -f homeassistant
```

Restart the service after a code change. Home Assistant keeps imported modules in memory, so
a config entry reload runs the old code.

## Records and workflow

- `TODO.md` lists only unfinished work. When you notice a bug immediately put it in TODO.md and classify as "needs_triage".
  - Remove a resolved issue from `TODO.md`.
  - Put every issue report into `needs_triage` as soon as you notice it. The item becomes a
    bug, an improvement or a feature only after the triage.
  - The triage writes `docs/TRIAGE_bug_name.md`. Write the same document for an improvement and for a feature.
  - The workflow of a bug in `TODO.md` starts at `needs_triage`, then gets classified as
    bug/improvement/feature. If triage shows no work, remove the issue and delete the triage
    document.
  - When the work is complete, remove the item from `TODO.md`.
  - When you finish the work and every check passes, delete `docs/TRIAGE_<name>.md` or `docs/FEATURE_<name>.md`.
