#!/usr/bin/env python3
"""
authentik-rbac-setup.py — Idempotent Authentik RBAC provisioner for minicloud.

Usage:
    python3 authentik-rbac-setup.py [--dry-run] [--token TOKEN] [--url URL]

    --dry-run   Print what would be created without making any API calls.
    --token     Authentik API token (default: read from ~/.authentik-api-token)
    --url       Authentik base URL (default: https://auth.devandre.sbs)

Idempotency: every create is guarded by a lookup. Re-running the script is
safe — existing groups, users, and bindings are left unchanged.

Sections (run in order):
    1. Groups      — create department groups
    2. Users       — create demo users, set passwords, assign to groups
    3. Bindings    — bind groups to applications (controls app access)

To add a new department:
    - Add an entry to GROUPS
    - Add an entry to USERS pointing to the new group slug
    - Update APP_ACCESS if the department needs app access

To change app permissions:
    - Edit APP_ACCESS: map app slug → list of group slugs that may access it
    - Apps not listed here keep their current bindings unchanged (no bindings = all users allowed)
"""

import argparse
import json
import ssl
import sys
import urllib.error
import urllib.request
from pathlib import Path

# ─── Configuration ──────────────────────────────────────────────────────────

DEFAULT_URL = "https://auth.devandre.sbs"
DEFAULT_TOKEN_FILE = Path.home() / ".authentik-api-token"

DEMO_PASSWORD = "Minicloud2026!"   # shared demo password for all demo.* users

# Department groups — slug → display name
GROUPS = {
    "platform-admins":            "Platform Admins",
    "direction-it":               "Direction IT / SI",
    "direction-cybersecurity":    "Direction Cybersécurité",
    "direction-data-analytics":   "Direction Data & Analytics",
    "direction-transformation":   "Direction Transformation & Innovation",
    "direction-actuariat":        "Direction Risques & Actuariat",
    "direction-souscription":     "Direction Souscription",
    "direction-sinistres":        "Direction Sinistres",
    "direction-finance":          "Direction Finance",
    "direction-reinsurance":      "Direction Réassurance",
    "direction-commercial":       "Direction Commerciale & Distribution",
    "direction-juridique":        "Direction Juridique & Compliance",
    "direction-operations":       "Direction Opérations",
    "direction-rh":               "Direction RH",
    "direction-audit":            "Direction Audit Interne",
    "direction-services-generaux":"Direction Services Généraux",
}

# Demo users — username → { name, group_slug, email }
USERS = {
    "demo.admin":          {"name": "Demo Platform Admin",       "group": "platform-admins",            "email": "demo.admin@ktayl.local"},
    "demo.it":             {"name": "Demo IT Engineer",          "group": "direction-it",               "email": "demo.it@ktayl.local"},
    "demo.cybersecurity":  {"name": "Demo Security Analyst",     "group": "direction-cybersecurity",    "email": "demo.cybersecurity@ktayl.local"},
    "demo.data":           {"name": "Demo Data Analyst",         "group": "direction-data-analytics",   "email": "demo.data@ktayl.local"},
    "demo.transformation": {"name": "Demo Innovation Lead",      "group": "direction-transformation",   "email": "demo.transformation@ktayl.local"},
    "demo.actuariat":      {"name": "Demo Actuaire",             "group": "direction-actuariat",        "email": "demo.actuariat@ktayl.local"},
    "demo.souscription":   {"name": "Demo Souscripteur",         "group": "direction-souscription",     "email": "demo.souscription@ktayl.local"},
    "demo.sinistres":      {"name": "Demo Gestionnaire Sinistre","group": "direction-sinistres",        "email": "demo.sinistres@ktayl.local"},
    "demo.finance":        {"name": "Demo Contrôleur Finance",   "group": "direction-finance",          "email": "demo.finance@ktayl.local"},
    "demo.reinsurance":    {"name": "Demo Réassureur",           "group": "direction-reinsurance",      "email": "demo.reinsurance@ktayl.local"},
    "demo.commercial":     {"name": "Demo Commercial",           "group": "direction-commercial",       "email": "demo.commercial@ktayl.local"},
    "demo.juridique":      {"name": "Demo Juriste",              "group": "direction-juridique",        "email": "demo.juridique@ktayl.local"},
    "demo.operations":     {"name": "Demo Ops Manager",          "group": "direction-operations",       "email": "demo.operations@ktayl.local"},
    "demo.rh":             {"name": "Demo RH Manager",           "group": "direction-rh",               "email": "demo.rh@ktayl.local"},
    "demo.audit":          {"name": "Demo Auditeur Interne",     "group": "direction-audit",            "email": "demo.audit@ktayl.local"},
    "demo.services":       {"name": "Demo Services Généraux",    "group": "direction-services-generaux","email": "demo.services@ktayl.local"},
}

# App access matrix — app slug → list of group slugs allowed to access it.
# Apps NOT listed here are left untouched (no bindings = all authenticated users allowed).
# Homer is intentionally omitted — all users can access the portal.
APP_ACCESS = {
    "argo-cd": [
        "platform-admins",
        "direction-it",
        "direction-cybersecurity",
        "direction-audit",
    ],
    "grafana": [
        "platform-admins",
        "direction-it",
        "direction-cybersecurity",
        "direction-data-analytics",
        "direction-transformation",
        "direction-actuariat",
        "direction-souscription",
        "direction-sinistres",
        "direction-finance",
        "direction-reinsurance",
        "direction-juridique",
        "direction-operations",
        "direction-audit",
    ],
    "harbor": [
        "platform-admins",
        "direction-it",
    ],
    "backstage": [
        "platform-admins",
        "direction-it",
        "direction-cybersecurity",
        "direction-data-analytics",
        "direction-transformation",
        "direction-juridique",
        "direction-audit",
    ],
    "open-webui": [
        "platform-admins",
        "direction-it",
        "direction-cybersecurity",
        "direction-data-analytics",
        "direction-transformation",
        "direction-actuariat",
    ],
    "nats": [
        "platform-admins",
        "direction-it",
        "direction-cybersecurity",
    ],
}

# ─── API client ─────────────────────────────────────────────────────────────

class AuthentikAPI:
    def __init__(self, url: str, token: str, dry_run: bool = False):
        self.base = url.rstrip("/") + "/api/v3"
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            # Cloudflare bot protection blocks Python-urllib default UA
            "User-Agent": "authentik-rbac-setup/1.0 (minicloud; +https://github.com/andrelair-platform)",
        }
        self.dry_run = dry_run
        # Trust system CAs; don't verify for internal nip.io endpoints
        self._ssl = ssl.create_default_context()

    def _req(self, method: str, path: str, body=None):
        url = self.base + path
        data = json.dumps(body).encode() if body else None
        headers = dict(self.headers)
        if method == "GET":
            headers.pop("Content-Type", None)
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, context=self._ssl) as r:
                raw = r.read()
                return json.loads(raw) if raw else {}
        except urllib.error.HTTPError as e:
            detail = e.read().decode()
            raise RuntimeError(f"{method} {path} → HTTP {e.code}: {detail}") from e

    def get(self, path: str):
        return self._req("GET", path)

    def post(self, path: str, body: dict):
        if self.dry_run:
            print(f"  [dry-run] POST {path} {json.dumps(body)[:80]}")
            return {"pk": "dry-run-pk"}
        return self._req("POST", path, body)

    def list_all(self, path: str, params: str = "") -> list:
        results = []
        page = 1
        while True:
            url = f"{path}?page_size=200&page={page}"
            if params:
                url += f"&{params}"
            data = self.get(url)
            results.extend(data.get("results", []))
            if data.get("pagination", {}).get("next", 0) == 0:
                break
            page += 1
        return results


# ─── Helpers ────────────────────────────────────────────────────────────────

def ok(msg):  print(f"  ✓ {msg}")
def skip(msg):print(f"  – {msg} (already exists)")
def info(msg):print(f"  · {msg}")
def section(title): print(f"\n{'─'*60}\n{title}\n{'─'*60}")


def ensure_groups(api: AuthentikAPI) -> dict:
    """Create missing groups. Return slug→pk map for all configured groups."""
    section("Step 1 — Groups")
    existing = {g["name"]: g["pk"] for g in api.list_all("/core/groups/")}
    slug_to_pk = {}
    for slug, display in GROUPS.items():
        if display in existing:
            skip(f"group '{slug}'")
            slug_to_pk[slug] = existing[display]
        else:
            resp = api.post("/core/groups/", {"name": display, "is_superuser": False})
            slug_to_pk[slug] = resp.get("pk", "dry-run-pk")
            ok(f"created group '{slug}'")
    return slug_to_pk


def ensure_users(api: AuthentikAPI, group_pk: dict) -> dict:
    """Create missing demo users, set passwords, assign to groups. Return username→pk."""
    section("Step 2 — Users")
    existing = {u["username"]: u["pk"] for u in api.list_all("/core/users/")}
    username_to_pk = {}

    for username, cfg in USERS.items():
        if username in existing:
            skip(f"user '{username}'")
            username_to_pk[username] = existing[username]
            continue

        resp = api.post("/core/users/", {
            "username": username,
            "name": cfg["name"],
            "email": cfg["email"],
            "is_active": True,
            "type": "internal",
            "groups": [group_pk[cfg["group"]]],
        })
        pk = resp.get("pk", "dry-run-pk")
        username_to_pk[username] = pk
        ok(f"created user '{username}' → group '{cfg['group']}'")

        # Set password
        if not api.dry_run:
            api.post(f"/core/users/{pk}/set_password/", {"password": DEMO_PASSWORD})
            info(f"password set for '{username}'")

    return username_to_pk


def ensure_bindings(api: AuthentikAPI, group_pk: dict):
    """Add missing group→app policy bindings. Never removes existing bindings."""
    section("Step 3 — Application Policy Bindings")

    # Build app slug→pk map
    apps = {a["slug"]: a["pk"] for a in api.list_all("/core/applications/")}

    for app_slug, allowed_groups in APP_ACCESS.items():
        app_pk = apps.get(app_slug)
        if not app_pk:
            print(f"  ⚠ app '{app_slug}' not found in Authentik — skipping")
            continue

        # Fetch existing bindings for this app
        existing_bindings = api.list_all("/policies/bindings/", f"target={app_pk}")
        existing_group_pks = {
            b["group"] for b in existing_bindings if b.get("group")
        }

        print(f"\n  [{app_slug}]")
        for group_slug in allowed_groups:
            gpk = group_pk.get(group_slug)
            if not gpk:
                print(f"    ⚠ group '{group_slug}' pk not found — skipping")
                continue
            if gpk in existing_group_pks:
                skip(f"binding {group_slug} → {app_slug}")
            else:
                api.post("/policies/bindings/", {
                    "target": app_pk,
                    "group": gpk,
                    "enabled": True,
                    "order": 0,
                    "negate": False,
                    "timeout": 30,
                })
                ok(f"bound {group_slug} → {app_slug}")


# ─── Entry point ────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Provision Authentik groups, users, and app bindings")
    parser.add_argument("--dry-run", action="store_true", help="Print actions without making API calls")
    parser.add_argument("--token", help="Authentik API token")
    parser.add_argument("--url", default=DEFAULT_URL, help=f"Authentik base URL (default: {DEFAULT_URL})")
    args = parser.parse_args()

    # Resolve token
    token = args.token
    if not token:
        if DEFAULT_TOKEN_FILE.exists():
            token = DEFAULT_TOKEN_FILE.read_text().strip()
        else:
            print(f"ERROR: no token provided and {DEFAULT_TOKEN_FILE} not found", file=sys.stderr)
            print("Usage: python3 authentik-rbac-setup.py --token <TOKEN>", file=sys.stderr)
            sys.exit(1)

    if args.dry_run:
        print("DRY RUN — no changes will be made\n")

    api = AuthentikAPI(url=args.url, token=token, dry_run=args.dry_run)

    group_pk = ensure_groups(api)
    ensure_users(api, group_pk)
    ensure_bindings(api, group_pk)

    print(f"\n{'─'*60}")
    print("Done. Next steps:")
    print("  • Update ArgoCD RBAC:  minicloud-ansible/helm-values/argocd-values.yaml")
    print("  • Update Grafana role: minicloud-ansible/helm-values/kube-prometheus-stack-values.yaml")
    print("  • helm upgrade both   (see #33 Steps 6-7)")
    print(f"{'─'*60}\n")


if __name__ == "__main__":
    main()
