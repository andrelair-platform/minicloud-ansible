#!/usr/bin/env python3
"""
Add an Authentik user to one or more groups by slug/name pattern.

Usage (run from the controller or any host with access to auth.10.0.0.200.nip.io):

  # Add kanmegnea to all department groups + Platform Admins:
  python3 authentik-add-user-to-groups.py --user kanmegnea --all-groups

  # Add a user to specific groups by name substring:
  python3 authentik-add-user-to-groups.py --user kanmegnea --groups "Direction IT" "Platform Admins"

  # Dry-run (print what would be done):
  python3 authentik-add-user-to-groups.py --user kanmegnea --all-groups --dry-run

Environment / config:
  AUTHENTIK_TOKEN   API token (or read from ~/.authentik-api-token)
  AUTHENTIK_URL     Base URL (default: https://auth.10.0.0.200.nip.io)
  AUTHENTIK_CACERT  CA cert path (default: ~/minicloud-ca.crt)
"""

import argparse
import json
import os
import ssl
import sys
import urllib.error
import urllib.request
from pathlib import Path


def get_token() -> str:
    token = os.environ.get('AUTHENTIK_TOKEN')
    if token:
        return token
    path = Path.home() / '.authentik-api-token'
    if path.exists():
        return path.read_text().strip()
    sys.exit('ERROR: Set AUTHENTIK_TOKEN or create ~/.authentik-api-token')


def build_ctx(cacert: str) -> ssl.SSLContext:
    ctx = ssl.create_default_context()
    ctx.load_verify_locations(cacert)
    return ctx


def api_get(url: str, token: str, ctx: ssl.SSLContext) -> dict:
    req = urllib.request.Request(url, headers={'Authorization': f'Bearer {token}'})
    with urllib.request.urlopen(req, context=ctx) as r:
        return json.load(r)


def api_post(url: str, data: dict, token: str, ctx: ssl.SSLContext) -> int:
    body = json.dumps(data).encode()
    req = urllib.request.Request(
        url, data=body,
        headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'},
        method='POST',
    )
    try:
        with urllib.request.urlopen(req, context=ctx) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code


def fetch_user(username: str, base: str, token: str, ctx: ssl.SSLContext) -> dict:
    data = api_get(f'{base}/api/v3/core/users/?search={username}', token, ctx)
    matches = [u for u in data['results'] if u['username'] == username]
    if not matches:
        sys.exit(f'ERROR: user "{username}" not found in Authentik')
    return matches[0]


def fetch_all_groups(base: str, token: str, ctx: ssl.SSLContext) -> list[dict]:
    groups, page = [], 1
    while True:
        data = api_get(f'{base}/api/v3/core/groups/?page_size=100&page={page}', token, ctx)
        groups.extend(data['results'])
        if not data['pagination']['next']:
            break
        page += 1
    return groups


def main():
    parser = argparse.ArgumentParser(description='Add an Authentik user to groups')
    parser.add_argument('--user', required=True, help='Authentik username')
    parser.add_argument('--all-groups', action='store_true',
                        help='Add to every group (except authentik built-ins)')
    parser.add_argument('--groups', nargs='+', metavar='NAME',
                        help='Name substrings to match (case-insensitive)')
    parser.add_argument('--dry-run', action='store_true', help='Print actions, do not execute')
    parser.add_argument('--url', default=os.environ.get('AUTHENTIK_URL', 'https://auth.10.0.0.200.nip.io'))
    parser.add_argument('--cacert', default=os.environ.get('AUTHENTIK_CACERT',
                        str(Path.home() / 'minicloud-ca.crt')))
    args = parser.parse_args()

    if not args.all_groups and not args.groups:
        parser.error('Provide --all-groups or --groups NAME [NAME ...]')

    token = get_token()
    ctx = build_ctx(args.cacert)
    base = args.url.rstrip('/')

    user = fetch_user(args.user, base, token, ctx)
    user_pk = user['pk']
    current_groups = {g['pk'] for g in user.get('groups_obj', [])}
    print(f'User: {user["username"]} (pk={user_pk})')
    print(f'Currently in {len(current_groups)} group(s)')

    all_groups = fetch_all_groups(base, token, ctx)

    # Filter target groups
    if args.all_groups:
        skip_prefixes = ('authentik ',)
        targets = [g for g in all_groups
                   if not any(g['name'].startswith(p) for p in skip_prefixes)]
    else:
        targets = []
        for pattern in args.groups:
            matched = [g for g in all_groups if pattern.lower() in g['name'].lower()]
            if not matched:
                print(f'WARNING: no group matched "{pattern}"')
            targets.extend(matched)
        # deduplicate preserving order
        seen = set()
        targets = [g for g in targets if not (g['pk'] in seen or seen.add(g['pk']))]

    print(f'\nTarget: {len(targets)} group(s)\n')

    added = skipped = errors = 0
    for g in targets:
        if g['pk'] in current_groups:
            print(f'  SKIP  {g["name"]} (already member)')
            skipped += 1
            continue
        if args.dry_run:
            print(f'  DRY   {g["name"]}')
            added += 1
            continue
        code = api_post(f'{base}/api/v3/core/groups/{g["pk"]}/add_user/', {'pk': user_pk}, token, ctx)
        if code in (200, 204):
            print(f'  OK    {g["name"]}')
            added += 1
        else:
            print(f'  ERR   {g["name"]} (HTTP {code})')
            errors += 1

    print(f'\nDone: {added} added, {skipped} skipped, {errors} errors')
    if errors:
        sys.exit(1)


if __name__ == '__main__':
    main()
