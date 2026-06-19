#!/usr/bin/env bash
#
# authentik-apps-create.sh — Idempotently create the 5 forward-auth
# Applications in Authentik and bind the `minicloud-forward-auth` Proxy
# Provider to the embedded Outpost.
#
# Phase 23 Stage 2 — replaces the manual click-through documented in
# minicloud-platform-docs/docs/security-enterprise/02-sso-authentik.md.
#
# Prerequisites:
#   - The Proxy Provider `minicloud-forward-auth` MUST already exist
#     (Stage 2 Browser Step 1 — domain-level forward-auth provider).
#     This script does NOT create the provider because forward-auth
#     domain-level providers have ~12 fields with non-obvious defaults;
#     creating them via the UI is the right design choice.
#   - AUTHENTIK_TOKEN env var or ~/.authentik-api-token file
#     containing an API Token minted by an admin user. Mint via UI:
#       Directory -> Tokens & App Passwords -> Create
#       Type: API Token, Intent: api, User: <your admin user>
#
# Idempotency: re-running is safe. Existing apps (matched by slug) are
# left alone with a "skipping" log line.

set -euo pipefail

AUTHENTIK_URL="${AUTHENTIK_URL:-https://auth.10.0.0.200.nip.io}"
AUTHENTIK_TOKEN="${AUTHENTIK_TOKEN:-$(cat ~/.authentik-api-token 2>/dev/null || true)}"
CA="${CA:-$HOME/minicloud-ca.crt}"

if [[ -z "$AUTHENTIK_TOKEN" ]]; then
  echo "ERROR: AUTHENTIK_TOKEN not set and ~/.authentik-api-token is empty" >&2
  exit 1
fi

api() {
  curl -sS --cacert "$CA" \
    -H "Authorization: Bearer $AUTHENTIK_TOKEN" \
    -H "Content-Type: application/json" \
    "$@"
}

# Quick auth check
echo "=== Verifying API token ==="
ME=$(api "$AUTHENTIK_URL/api/v3/core/users/me/" 2>&1)
if ! echo "$ME" | jq -e '.user.username' >/dev/null 2>&1; then
  echo "ERROR: API token rejected. Response:"
  echo "$ME" | head -c 500
  echo ""
  exit 1
fi
echo "Authenticated as: $(echo "$ME" | jq -r '.user.username')"
echo ""

# Look up the provider PK
echo "=== Looking up provider 'minicloud-forward-auth' ==="
PROVIDER_ID=$(api "$AUTHENTIK_URL/api/v3/providers/proxy/?name=minicloud-forward-auth" | jq -r '.results[0].pk // empty')
if [[ -z "$PROVIDER_ID" ]]; then
  echo "ERROR: provider 'minicloud-forward-auth' not found." >&2
  echo "Create it in the UI first (Stage 2 Browser Step 1 in the runbook)." >&2
  exit 1
fi
echo "Provider PK: $PROVIDER_ID"
echo ""

# Apps to ensure exist: slug -> "Display Name|Launch URL"
declare -A APPS=(
  ["homer"]="Homer Dashboard|https://homer.10.0.0.200.nip.io"
  ["podinfo"]="podinfo|https://podinfo.10.0.0.200.nip.io"
  ["platform-demo"]="Platform Demo|https://platform-demo.10.0.0.200.nip.io"
  ["whoami"]="whoami|https://whoami.10.0.0.200.nip.io"
  ["nats"]="NATS Monitoring|https://nats.10.0.0.200.nip.io"
)

echo "=== Creating Applications ==="
# Domain-level forward-auth model: ONE app holds the provider (the "anchor"),
# OTHER apps are catalog tiles without a provider. The Outpost (bound to
# the provider) intercepts all traffic to the cookie domain regardless of
# which app's URL the user hits — so app-level provider attachment is only
# needed for the anchor. Authentik enforces 1:1 between app and provider,
# so trying to attach the same provider to multiple apps returns
# "Application with this provider already exists."
#
# We detect which app currently holds the provider and skip it; the rest
# are created with no provider field (catalog tiles only).
ANCHOR_APP=$(api "$AUTHENTIK_URL/api/v3/core/applications/?provider=$PROVIDER_ID" | jq -r '.results[0].slug // empty')
if [[ -n "$ANCHOR_APP" ]]; then
  echo "  Anchor app (holds provider): $ANCHOR_APP"
fi

for slug in "${!APPS[@]}"; do
  IFS='|' read -r name launch_url <<< "${APPS[$slug]}"

  # Idempotency: skip if app with this slug already exists
  EXISTING=$(api "$AUTHENTIK_URL/api/v3/core/applications/?slug=$slug" | jq -r '.results[0].slug // empty')
  if [[ "$EXISTING" == "$slug" ]]; then
    echo "  $slug — already exists, skipping"
    continue
  fi

  # Catalog-only tile (no provider attached — the anchor app handles that)
  RESP=$(api -X POST "$AUTHENTIK_URL/api/v3/core/applications/" \
    -d "$(jq -n \
      --arg name "$name" \
      --arg slug "$slug" \
      --arg launch_url "$launch_url" \
      '{name: $name, slug: $slug, meta_launch_url: $launch_url}')")

  if echo "$RESP" | jq -e '.slug' >/dev/null 2>&1; then
    echo "  $slug — created ($(echo "$RESP" | jq -r '.name'))"
  else
    echo "  $slug — ERROR creating:"
    echo "$RESP" | jq . 2>&1 | sed 's/^/    /'
  fi
done
echo ""

# Bind the provider to the embedded Outpost.
# For domain-level forward-auth: ONE provider covers all apps; the Outpost
# binds to the provider, not to each individual app.
echo "=== Binding 'minicloud-forward-auth' to the embedded Outpost ==="
OUTPOST_ID=$(api "$AUTHENTIK_URL/api/v3/outposts/instances/?name__icontains=embedded" | jq -r '.results[0].pk // empty')
if [[ -z "$OUTPOST_ID" ]]; then
  echo "ERROR: embedded Outpost not found (was the chart fresh-installed?)" >&2
  exit 1
fi
echo "Embedded Outpost PK: $OUTPOST_ID"

CURRENT_PROVIDERS=$(api "$AUTHENTIK_URL/api/v3/outposts/instances/$OUTPOST_ID/" | jq '.providers')
if echo "$CURRENT_PROVIDERS" | jq -e "contains([$PROVIDER_ID])" >/dev/null 2>&1; then
  echo "  Provider already bound to embedded Outpost, skipping"
else
  NEW_PROVIDERS=$(echo "$CURRENT_PROVIDERS" | jq ". + [$PROVIDER_ID]")
  api -X PATCH "$AUTHENTIK_URL/api/v3/outposts/instances/$OUTPOST_ID/" \
    -d "$(jq -n --argjson providers "$NEW_PROVIDERS" '{providers: $providers}')" \
    | jq -r '"  bound — outpost now has providers: \(.providers)"'
fi
echo ""

echo "=== Done ==="
echo "Stage 2 Browser Steps 2 + 3 complete. Proceed with cluster-side Ingress annotations."
