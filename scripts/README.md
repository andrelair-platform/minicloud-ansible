# Scripts

Small standalone helpers that don't fit cleanly as Ansible roles or playbooks.

## Files

| File | Purpose | When to use |
|---|---|---|
| `bs-catalog.sh` | Browse the Backstage service catalog via API | Workaround for the upstream off-the-shelf Backstage image's broken UI (notifications plugin `NotImplementedError` overlay). Use until the custom-image phase ships. |
| `pin-audit.sh` | List every pod running an image with the `:latest` tag | Periodic hygiene check — drift detection. Empty output = cluster fully pinned (healthy). Non-empty = something silently regressed to `:latest`; fix immediately. Run after every install/upgrade. |

## Conventions

- All scripts use `#!/usr/bin/env bash` + `set -euo pipefail`.
- Scripts that need shared credentials read from `~/.<name>-admin` (mode 600).
- Configuration via env vars with sensible defaults (e.g. `BS_HOST`, `BS_CA`) so the script works on the controller AND any tailnet-connected device with the CA cert.
- Each script is self-documenting in its header — `head -30 <script>` shows usage.
