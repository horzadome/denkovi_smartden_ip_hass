# The repository carries no GitHub topics

bug

## Cause

The job `validate` of the workflow `HACS validation` in `.github/workflows/hacs.yaml` runs
the action `hacs/action@main` with `category: integration`. The action reads the topics of the
repository. The topic list of `horzadome/denkovi-smartden-ip-hass` is empty, so the action
reports this line:

```text
<Validation topics> failed: The repository has no valid topics (More info: https://hacs.xyz/docs/publish/include#check-repository )
```

The check then fails, and the job fails with it. HACS requires the action to pass before it
accepts the repository in its default list.

HACS drops the generic topics of a repository. The list `TOPIC_FILTER` holds words such as
`hacs`, `home-assistant`, `home-assistant-integration`, `integration` and `home-automation`.
The check passes only when at least one topic stays after that filter.

## Fix

The repository needs these topics:

- `denkovi`
- `smartden`
- `home-assistant`
- `home-assistant-integration`
- `hacs`
- `relay`

The decision follows. The topics `denkovi` and `smartden` name the vendor and the device family.
A user of the Home Assistant community searches for those two words.
The topics `home-assistant`, `home-assistant-integration` and `hacs` name the platform and
the store, and they help a browse of GitHub.
The topic `relay` names the device class that the integration controls.
The topics `denkovi` and `smartden` stay after `TOPIC_FILTER`, so the check passes.

The command below sets the topics:

```bash
gh repo edit horzadome/denkovi-smartden-ip-hass --add-topic denkovi,smartden,home-assistant,home-assistant-integration,hacs,relay
```

This command writes to the GitHub repository `horzadome/denkovi-smartden-ip-hass`, and it
needs an authenticated `gh`. The user runs the command or approves it. This task does not run
the command and does not authenticate anywhere.

## Evidence

The HACS validation job reports this log line:

```text
<Validation topics> failed: The repository has no valid topics (More info: https://hacs.xyz/docs/publish/include#check-repository )
```

The item "Set the GitHub repository topics" in `TODO.md` records the same message, "The repository has no valid topics".

The check is `custom_components/hacs/validate/topics.py` in `hacs/integration`. It raises
`ValidationException("The repository has no valid topics")` when `repository.data.topics` is
empty. `custom_components/hacs/repositories/base.py` builds that list, and it removes each
topic that `TOPIC_FILTER` names.
