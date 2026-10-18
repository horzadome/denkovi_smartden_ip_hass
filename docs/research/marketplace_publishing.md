# Marketplace publishing requirements

Date: 2026-10-18

The Marketplace replaces HACS in Home Assistant 2026.11. This note records what a
repository needs so that the Marketplace installs it and the catalog lists it, and what
this repository holds today.

## Sources

- [Marketplace](https://contributors.home-assistant.io/marketplace/), the documentation
  for contributors of Home Assistant. It holds the guides and the reference for the
  Marketplace. Last updated 2026-10-12.
- [Publish](https://hacs.xyz/docs/publish/start/), the general requirements of HACS.
- [Include default repositories](https://hacs.xyz/docs/publish/include/), the review of the
  catalog. The catalog is the same.
- [Marketplace](https://hacs.xyz/docs/marketplace/), the page of HACS about the move.
- [Marketplace](https://next.home-assistant.io/integrations/marketplace/), the user
  documentation.
- The integration source in the checkout `homeassistant_repo/homeassistant/components/marketplace`,
  from `homeassistant/core` pull request 183502.

## What the feature is

- The Marketplace is a system integration. Home Assistant sets it up by default. It is
  available to administrators only, under **Settings** > **Marketplace**.
- It is HACS moved into core. It reads the same catalog at `data-v2.hacs.xyz`, built from
  the same `hacs/default` lists, and the same `hacs.json` file in each repository.
- Home Assistant blocks the HACS custom integration on 2026.11 and later. The installed
  content stays installed and keeps its updates.
- The Marketplace does not install AppDaemon apps and Python scripts.
- It reads the catalog every 6 hours. A catalog version installs from its archive, so it
  needs no GitHub account. A custom repository needs a GitHub connection.
- Each installed repository gets one update entity. A pre-release switch allows a release
  marked as a pre-release.

## Where the requirements live

The catalog submission did not move. A repository enters the catalog with a pull request to
the `integration` file of the repository `hacs/default`.

The two requirement pages are:

- [Publish a custom integration](https://contributors.home-assistant.io/marketplace/guides/integrations/)
  and [Get into the catalog](https://contributors.home-assistant.io/marketplace/guides/catalog/).
- The reference pages: [hacs.json](https://contributors.home-assistant.io/marketplace/reference/hacs-json/),
  [Repository structure](https://contributors.home-assistant.io/marketplace/reference/repository-structure/)
  and [Validation checks](https://contributors.home-assistant.io/marketplace/reference/validation/).

## What the catalog review checks

Only the repository owner or a major contributor can submit the pull request. The catalog
review refuses an integration that only tests an alpha or a beta of a core integration, or
that replaces a core integration. Users can still add such an integration from a link.

| Check           | What it wants from this repository                                                                            |
|-----------------|---------------------------------------------------------------------------------------------------------------|
| Repository      | A description, topics, and issues turned on.                                                                  |
| HACS manifest   | A `hacs.json` in the root, with at least `name`.                                                              |
| Manifest        | A valid `manifest.json`, with `domain`, `documentation`, `issue_tracker`, `codeowners`, `name` and `version`. |
| Brands          | A `brand` folder in the integration folder, with at least `icon.png`.                                         |
| HACS validation | The HACS action passes without `ignore`.                                                                      |
| Hassfest        | The hassfest action passes. Integrations only.                                                                |
| Releases        | At least one full GitHub release.                                                                             |
| Archived        | The repository is active.                                                                                     |
| License         | GitHub identifies an OSI-approved license.                                                                    |
| Lint            | The files of the pull request are valid JSON and sorted.                                                      |

The pull request goes from the owner's own account, not from an organization. The entry
goes into the list in alphabetical order. The pull request template needs the checklist, a
link to the latest release, and a link to a passing run of each action. The review takes
months. Until then, a user adds the repository from a link.

## What the repository needs

- One integration in `custom_components/<domain>/`. The Marketplace takes the first folder
  below `custom_components/`. Every file the integration needs is inside that folder.
- `manifest.json` with a `domain` of lowercase letters, numbers, underscores and hyphens.
- `manifest.json` with a `version` the loader accepts. The Marketplace refuses an install
  without it. The version of the release tag is the version that users get.
- `manifest.json` with `documentation`, `issue_tracker`, `codeowners` and `name`.
- `requirements` lists only libraries that Home Assistant does not ship.
- `brand/icon.png` inside the integration folder. The brands site shows it from the latest
  release of each catalog integration.
- `translations/en.json` complete. The Marketplace installs the folder as it is, and the
  runtime reads the translation files.
- `hacs.json` in the root, with `name`. The keys the Marketplace reads are `name`,
  `homeassistant`, `hacs`, `content_in_root`, `filename`, `zip_release`,
  `persistent_directory` and `hide_default_branch`. The Marketplace ignores other keys.
- `homeassistant` in `hacs.json` sets the minimum Home Assistant version of a release. The
  Marketplace compares it only for repositories with releases. Add `b0` to include the
  betas.
- A README in the root, next to `hacs.json`.

`strings.json` is the translation source of an integration in core. The documentation for
custom integrations says that the Marketplace does not use it.

## What the Marketplace checks at install

A failed check stops the install. A failed check after the write restores the old files.

| Check                    | What fails                                                                                       |
|--------------------------|--------------------------------------------------------------------------------------------------|
| `hacs.json` in the root  | It is absent.                                                                                    |
| Archived or removed      | An archived repository fails, and so does one that the catalog removed.                          |
| Files in the right place | No files where the structure says.                                                               |
| Minimum version          | The release needs a newer version of Home Assistant. The user can pick an older version instead. |
| Domain characters        | The domain has a character other than lowercase letters, numbers, underscores and hyphens.       |
| Domain owner             | Another installed repository has the same domain.                                                |
| Built-in replacement     | The domain belongs to core, and the user did not confirm.                                        |
| Loadable manifest        | Another domain, or no `version` the loader accepts.                                              |
| Download size            | More than 100 MiB, or more than 50 000 files.                                                    |

## What differs from HACS

- The Marketplace reads the `hacs` key of `hacs.json` but does not compare it.
- The Marketplace ignores `render_readme`. It shows the README of every repository.
- The link for a README is `marketplace_repository`, available in 2026.11. The older
  `hacs_repository` link works on both.
- A repository without `hacs.json` cannot be installed or updated.

## What this repository holds

Checked on 2026-10-18 in the checkout:

- `custom_components/denkovi_smartden_ip/manifest.json`: `domain`, `name`, `codeowners`,
  `documentation`, `issue_tracker`, `config_flow`, `integration_type`, `iot_class`,
  `loggers`, `requirements` and `version` `0.1.0`.
- `custom_components/denkovi_smartden_ip/brand/`: `icon.png`, `icon@2x.png` and `logo.png`.
- `custom_components/denkovi_smartden_ip/translations/en.json`.
- `hacs.json`: `name`, `homeassistant` `2026.10.0` and `render_readme`.
- `LICENSE`: MIT.
- `.github/workflows/ci.yml`: MegaLinter, hassfest, and the HACS action. The HACS action
  names the category `integration`. The last two run for a pull request.
- `.github/workflows/release.yml`: creates the release `v<version>` from the `version` in
  `manifest.json` after a merged pull request reaches `main`. Git does not track the file
  yet. The checkout holds no tag.

## Reads that a checkout cannot answer

Four catalog checks read GitHub settings, not files: the description, the topics, issues
turned on, and a release. An earlier run of the HACS action reported that the repository
has no valid topics, so confirm the current settings in the GitHub web interface. The same
applies to the result of the HACS action and of hassfest.

## Next steps

1. Commit `release.yml`, merge one version bump, and let the workflow publish the first
   release.
2. Run the HACS action and hassfest on a push and on a schedule. A change in the GitHub
   settings then shows up in the run.
3. Confirm the description, the topics and issues in the GitHub web interface.
4. Fork `hacs/default`, add `horzadome/denkovi_smartden_ip_hass` to the `integration` list
   in alphabetical order, and open the pull request from your own account.
5. Until the catalog lists the repository, a user adds it from the My link that names the
   category `integration`.
