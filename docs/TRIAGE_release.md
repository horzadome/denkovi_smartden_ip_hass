# HACS needs a release, and the repository has none

bug

## Cause

HACS installs an integration from a release of the repository.
This repository carries no release.
The repository also carries no tag.

The HACS review of a repository holds a check named `Check releases`.
That check makes sure the repository has at least one release.

## Fix

The field `version` of `custom_components/denkovi_smartden_ip/manifest.json` holds `0.1.0`.
The repository must carry the version `0.1.0` and the tag `v0.1.0`.
The version part of the tag matches the manifest.

The HACS review needs a full release, and not a tag alone.
The command that creates the release is:

```bash
gh release create v0.1.0 \
  --repo horzadome/denkovi-smartden-ip-hass \
  --title "v0.1.0" \
  --notes "First release of the Denkovi smartDEN IP Devices integration, version 0.1.0. The integration reads and controls the channel groups of a Denkovi smartDEN IP device over its JSON API. Add it to HACS as a custom repository of category Integration, then install it and restart Home Assistant."
```

The command runs against the GitHub repository of the user.
The user runs the command, or approves it.
This document does not run the command.
This document does not authenticate to GitHub.

Commit and push the work before the release.
The release carries the files of the commit that its tag points at.
The tag points at the head of the default branch of the repository.
The work of this repository sits in the working tree, so the tag points at an earlier commit
until the user commits and pushes.

## Evidence

The check that reports the missing release is `Check releases` in the HACS review.
The HACS page `https://hacs.xyz/docs/publish/include/` says the rule of the check.
The rule is that the repository holds at least one release.

The command `git tag -l` prints no line.
The command `git tag -l | wc -l` prints `0`.

The GitHub check `gh release list --repo horzadome/denkovi-smartden-ip-hass` reports no release.
This document does not run that command, because the command needs a GitHub login.

The command below prints the version of the manifest:

```bash
.venv/bin/python -c "import json; print(json.load(open('custom_components/denkovi_smartden_ip/manifest.json'))['version'])"
```

It prints `0.1.0`.
