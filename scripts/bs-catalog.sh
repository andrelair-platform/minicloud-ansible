#!/usr/bin/env bash
#
# bs-catalog.sh — Browse the Backstage service catalog via API.
#
# Workaround for the upstream off-the-shelf Backstage image bug where the
# notifications plugin is registered in the frontend bundle without the
# matching apiRef factory, throwing NotImplementedError on every page load
# and blocking the UI. See:
#   minicloud-platform-docs/docs/developer-platform/01-backstage.md
#     section "Image tag pinning (2026-06-15)"
#
# The Backstage CATALOG API itself is unaffected by the UI bug, so this
# script gives equivalent functionality to "browsing the catalog" until
# the proper fix lands (a custom-built Backstage image with a corrected
# packages/app/src/apis.ts).
#
# Usage:
#   ./bs-catalog.sh                       # all Components (default)
#   ./bs-catalog.sh system                # all Systems
#   ./bs-catalog.sh api                   # all APIs
#   ./bs-catalog.sh location              # all catalog Locations
#   ./bs-catalog.sh resource              # all Resources
#
# Or source it as a shell function:
#   source bs-catalog.sh
#   bs_catalog
#   bs_catalog system
#
# Environment:
#   BS_HOST  — Backstage hostname (default: backstage.10.0.0.200.nip.io)
#   BS_CA    — path to your minicloud root CA cert
#              (default: $HOME/minicloud-ca.crt)
#              On the controller: /home/ktayl/minicloud-ca.crt
#              On the Mac: scp the cert from the controller first
#
# Note: this script is designed to be sourced into ~/.bashrc, so it
# deliberately does NOT use `set -euo pipefail` at the top level —
# those options would pollute the caller's shell after sourcing.
# Error handling lives inside the function (curl -sf and jq's strict mode).

BS_HOST="${BS_HOST:-backstage.10.0.0.200.nip.io}"
BS_CA="${BS_CA:-$HOME/minicloud-ca.crt}"

bs_catalog() {
  local kind="${1:-component}"
  local token
  token=$(curl -sf --cacert "$BS_CA" \
    -X POST "https://${BS_HOST}/api/auth/guest/refresh" \
    | jq -r '.backstageIdentity.token')
  curl -sf --cacert "$BS_CA" \
    -H "Authorization: Bearer $token" \
    "https://${BS_HOST}/api/catalog/entities?filter=kind=${kind}" \
  | jq -r '.[] | "\(.metadata.name) [\(.kind)] (\(.spec.type // "n/a")) — owner: \(.spec.owner // "n/a") — \(.metadata.description // "no description")"'
}

# If sourced, just expose the function. If executed as a script, run it.
# Detect by checking BASH_SOURCE vs argv[0].
(return 0 2>/dev/null) || bs_catalog "$@"
