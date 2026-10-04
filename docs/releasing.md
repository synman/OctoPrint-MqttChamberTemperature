# Runbook: Releasing a New Version

How to publish a release that OctoPrint's Software Update picks up. For maintainers with push access to `synman/OctoPrint-MqttChamberTemperature`.

## How users receive releases

This contract comes from `get_update_information` in `octoprint_mqttchambertemperature/__init__.py`. Update this runbook if that function changes.

- Check type `github_release`, compared against `current = plugin_version` from `setup.py`.
- Install URL: `https://github.com/synman/OctoPrint-MqttChamberTemperature/archive/{target_version}.zip`, where `{target_version}` is the release **tag name**.
- **Stable** channel: non-prerelease releases targeting `main`.
- **Release Candidate** channel: GitHub **pre-releases** targeting `rc` (users opt in; `commitish: ["rc", "main"]`).

Two rules follow, and breaking either leaves users stuck:

1. The tag is the bare version: `0.0.4`, never `v0.0.4`.
2. `plugin_version` in `setup.py` at the tagged commit equals the tag. Otherwise users see "update available" forever.

## Branches

| Branch | Role |
|---|---|
| `devel` | Day-to-day work. Contains `main`. |
| `rc` | Release candidates. Moves forward to the commit being tested. |
| `main` | Stable. Fast-forwards to the released commit. Default branch. |

## When an RC is required

An RC is **required** when heater behavior changes, since the plugin drives real hardware. Doc-only or cosmetic releases may go straight to stable.

Promote an RC to stable when one real-hardware print with the change has behaved as expected and no RC user has reported a regression.

## Preflight

1. Working tree clean on `devel`, with every commit for the release present.
2. `main` is an ancestor of your local `devel`, so it can fast-forward:
   ```bash
   git fetch origin
   git merge-base --is-ancestor origin/main devel && echo ff-ok
   ```
   Expect `ff-ok`. No output means `main` has commits `devel` lacks: merge `origin/main` into `devel` first.
3. Syntax check passes:
   ```bash
   python3 -m py_compile octoprint_mqttchambertemperature/*.py setup.py
   ```
4. The [local verification SOP](local-verification-sop.md) passes on the target OctoPrint version, run on the commit you are releasing. The version bump only touches `setup.py`, so a pass on the commit just before the bump counts.
5. For heater behavior changes: one real-hardware print has run with the change (before stable; it may happen during the RC).
6. README and [operator guide](operator-guide.md) describe any new or changed setting.

## Procedure

### Release candidate (optional)

1. Set `plugin_version = "0.0.4rc1"` in `setup.py` on `devel` and commit (`bump version`).
2. Push `devel`. Then move `rc` to the same commit and push it:
   ```bash
   git push origin devel
   git push origin devel:rc
   ```
   Expected: both push as fast-forwards. If `rc` is rejected as non-fast-forward, stop and find out what is on `rc`.
3. Create the pre-release:
   ```bash
   gh release create 0.0.4rc1 -R synman/OctoPrint-MqttChamberTemperature \
     --target rc --prerelease --title 0.0.4rc1 --generate-notes
   ```
4. Repeat with `rc2`, `rc3` and so on as fixes land.

### Stable

1. Set `plugin_version = "0.0.4"` in `setup.py` on `devel` and commit (`bump version`).
2. Push `devel`, then fast-forward `main` to it:
   ```bash
   git push origin devel
   git push origin devel:main
   ```
3. Create the release:
   ```bash
   gh release create 0.0.4 -R synman/OctoPrint-MqttChamberTemperature \
     --target main --title 0.0.4 --generate-notes
   ```
   `--generate-notes` produces the "What's Changed" list used by earlier releases.
4. Bring `rc` up to `main` so the next RC push is a fast-forward:
   ```bash
   git push origin devel:rc
   ```

## Verification

1. The release zip resolves:
   ```bash
   curl -sI https://github.com/synman/OctoPrint-MqttChamberTemperature/archive/0.0.4.zip | head -1
   ```
   Expect `HTTP/2 302` to `codeload.github.com`.
2. It installs into an OctoPrint environment: `pip install --no-deps <zip URL>` reports `Successfully installed MQTT-Chamber-Temperature-0.0.4`.
3. On an OctoPrint running the previous version (a real install, or the SOP rig with the previous release installed from its zip), Software Update offers the new version (force a check under Settings → Software Update), installs it, and asks for a restart. After the restart the version shows the new number.
4. Issues referenced with `Closes #N` in released commits are closed. GitHub closes them when the commits reach `main`.

## Failure branches

- **Users keep seeing "update available" after updating:** the tag and the installed `plugin_version` differ, so the comparison never matches. A `v` prefix on the tag causes the same loop. Confirm with:
  ```bash
  gh api "repos/synman/OctoPrint-MqttChamberTemperature/contents/setup.py?ref=0.0.4" --jq .content | base64 -d | grep plugin_version
  ```
  Fix by releasing a **higher** version whose tag and `plugin_version` match. Do not move or rewrite an existing tag.
- **Software Update fails to install:** read the pip output in Software Update's log. If the zip fails to build, reproduce with `pip install --no-deps <zip URL>` in the same OctoPrint version.
- **Wrong channel:** a stable release marked prerelease, or an RC targeting `main`, reaches the wrong users. Edit the release's prerelease flag or target on GitHub (`gh release edit`).
- **Bad release already shipped:** publish a fixed version with a higher number. Deleting a release does not downgrade users who installed it.

## Done definition

- Tag `X.Y.Z` exists on `main`, with a GitHub release (not prerelease) and generated notes.
- `setup.py` at that tag says `X.Y.Z`.
- Verification steps 1–3 pass.
- For heater behavior changes: an RC shipped first and a real-hardware print passed.
- Related issues are closed, with a comment where the reporter asked for the change.

## plugins.octoprint.org listing

The listing lives in [OctoPrint/plugins.octoprint.org](https://github.com/OctoPrint/plugins.octoprint.org) at `_plugins/mqttchambertemperature.md`. A release does not require changing it. Open a pull request there only when metadata changes: description, compatibility, Python range, or screenshots. Its `archive:` URL points at `archive/master.zip`, which GitHub redirects to `main`.

## Keeping this current

Update this runbook when `get_update_information`, the branch names, or the packaging (`setup.py`, a future `pyproject.toml`) change.
