# Agent Instructions

Read and obey the following in their entirety before doing any work on this project:

- Global AGENTS.md (not AGENT_RULES.md !!!)
- Project's AGENTS.md
- [CONTRIBUTING.md](CONTRIBUTING.md) for development rules
- [docs/LOCALDEV.md](docs/LOCALDEV.md) for rules and instructions for working on this
  specific project and on this specific machine

## Scope

Only work on integration `denkovi_smartden_ip`, a custom component for Home Assistant.  
Never work on homeassistant code - it is only there as a reference. We do not develop homeassistant, only our integration.

## Linters - IMPORTANT

- Lint using MegaLinter container with the same configuration as github pipeline, prefer
  Megalinter over other linters which do the same job
- If you really need a linter of your own, run it with the configuration in the project root.
  Check that MegaLinter reuses the same configuration file, so the pipeline and the development
  environment use the same configuration.
- Check the configuration MegaLinter reads: the `Rules config:` line of `megalinter-reports/megalinter.log` names it.
- Read MegaLinter results from the files in `megalinter-reports/`. Never read the output of the MegaLinter container.
- Delete the directory `megalinter-reports/` after you finish the analysis of a run. A stale
  directory makes a later run read a result that is out of date.

## Shell

- Run every Python command in the dev container. Never run Python on the host machine.
- Check the running integration in the `homeassistant` container. Do not develop in it.
- The commands are in [docs/LOCALDEV.md](docs/LOCALDEV.md).
- `systemctl --user` and `podman` need a wider sandbox mode. Pass it with a justification.
- `journalctl --user` and `busctl --user` work under the default sandbox.

## Home Assistant access

- Home Assistant serves its web interface at <http://127.0.0.1:8123>.
- The `homeassistant` MCP server reads only the entities exposed to Assist, a small subset.
- For the full list of entity values, ask the user to create a token. Then use the Home Assistant API.

## Reference checkout

`homeassistant_repo/` is a read-only copy of Home Assistant. Never edit anything there.
Read it for the Home Assistant APIs, the entity platforms, the config flows and the test helpers.

## Research

- Read `homeassistant_repo/` and the Home Assistant documentation before an implementation.
- Check syntax and patterns in an authoritative source.
- Use the patterns of the core integrations.

## Documentation

- Index the documents before a task. List every file under `docs/` recursively with `glob`
  and the pattern `docs/**`. The project documents are in `docs/` and the research notes are
  in `docs/research/`.
- Read a document only when its file name concerns the current task. Do not read the
  documents during the index. A file name tells the kind of document, for example `TEST_`,
  `TRIAGE_` or `FEATURE_`.

## Documentation Writing Rules

- Follow rules from CONTRIBUTING.md and from docs/LOCALDEV.md.
- Make sure that all documentation is clear, concise, and follows the established style guide.
