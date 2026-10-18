# TODO

This file lists unfinished work only.

## Open work

Write a new item here as `needs_triage` first. Then write `docs/TRIAGE_<name>.md` with the
cause and the decision, classify the item as a bug, an improvement or a feature, and fix
the cause. See [CONTRIBUTING.md](CONTRIBUTING.md).

- `bug` Set the GitHub repository topics. The HACS validation job reports that the
  repository holds no valid topics while the topic list is empty. The document
  [docs/TRIAGE_github_topics.md](docs/TRIAGE_github_topics.md) holds the list of topics and
  the command that sets them. The command waits for you, because it changes the GitHub
  repository.
- `bug` Create a release. HACS installs an integration from a release. The repository
  carries no tag and no release. The document
  [docs/TRIAGE_release.md](docs/TRIAGE_release.md) holds the version, the tag and the
  command that creates the release. The command waits for you, because it changes the
  GitHub repository.
- `needs_triage` Separate a missing program page from a failed program request in the
  coordinator. `_async_program` caches `False` after the first `/program.json` failure,
  so a transient failure hides the program for the life of the entry. Evidence:
  `coordinator.py:65-72`. Next step: keep the failure and the absence apart.
- `needs_triage` When the entry has no MAC, check the device identity in the options
  flow. `_async_address_error` compares the MAC only when `entry.data[CONF_MAC]` is set,
  so an entry without a MAC can move to another device. Evidence:
  `config_flow.py:240-254`. Next step: decide the check for an entry without a MAC.
