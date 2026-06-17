#!/usr/bin/env bash
#
# pin-audit.sh — Surface every pod in the cluster running an image with
# the `:latest` tag.
#
# Why this matters: `:latest` is a rolling reference. Any pod restart —
# including ones triggered by node reboot, node drain, or completely
# unrelated cluster maintenance — can silently pull a new image with
# different behavior. The June 2026 :latest audit found 3 such pods
# (Backstage, Homer, Ollama) and surfaced one upstream bug
# (NotImplementedError on plugin.notifications.service) that was masked
# by the rolling tag. Treat ANY `:latest` reference on a long-running
# cluster as a time bomb.
#
# Output: one line per pod, formatted as "<namespace>/<pod>: <image>".
# Empty output = cluster is fully pinned (good). Exit code is always 0
# when kubectl succeeds — empty result is healthy, not an error.
#
# Note: this script is designed to be sourced into ~/.bashrc, so it
# deliberately does NOT use `set -euo pipefail` at the top level —
# those options would pollute the caller's shell after sourcing.
#
# See:
#   minicloud-platform-docs/docs/developer-platform/01-backstage.md
#     section "Image tag pinning (2026-06-15)" — full incident write-up
#
# Usage:
#   ./pin-audit.sh            # one-shot check (running as script)
#   pin_audit                 # if sourced into shell

pin_audit() {
  kubectl get pods -A -o jsonpath='{range .items[*]}{.metadata.namespace}/{.metadata.name}: {range .spec.containers[*]}{.image}{"\n"}{end}{end}' \
    | { grep ':latest$' || true; } \
    | sort -u
}

# If executed as a script, run the function. If sourced, just expose it.
(return 0 2>/dev/null) || pin_audit "$@"
