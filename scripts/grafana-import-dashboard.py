#!/usr/bin/env python3
"""Import a Grafana dashboard from grafana.com by ID. Run on the controller."""
import json, sys, ssl, urllib.request, urllib.error
from pathlib import Path
import base64

GRAFANA_URL = 'https://grafana.10.0.0.200.nip.io'
CACERT = str(Path.home() / 'minicloud-ca.crt')
DASHBOARD_ID = 20842
DATASOURCE_NAME = 'Prometheus'

def main():
    password = Path.home().joinpath('.grafana-admin').read_text().strip()
    creds = base64.b64encode(f'admin:{password}'.encode()).decode()

    ctx = ssl.create_default_context()
    ctx.load_verify_locations(CACERT)

    # Download dashboard JSON from grafana.com
    print(f'Downloading dashboard {DASHBOARD_ID} from grafana.com...')
    with urllib.request.urlopen(
        f'https://grafana.com/api/dashboards/{DASHBOARD_ID}/revisions/latest/download',
        context=ssl.create_default_context()
    ) as r:
        dash = json.load(r)

    dash['id'] = None  # let Grafana assign a new ID

    payload = json.dumps({
        'dashboard': dash,
        'overwrite': True,
        'folderId': 0,
        'inputs': [{'name': 'DS_PROMETHEUS', 'type': 'datasource',
                    'pluginId': 'prometheus', 'value': DATASOURCE_NAME}],
    }).encode()

    req = urllib.request.Request(
        f'{GRAFANA_URL}/api/dashboards/import',
        data=payload,
        headers={'Content-Type': 'application/json', 'Authorization': f'Basic {creds}'},
        method='POST',
    )
    try:
        with urllib.request.urlopen(req, context=ctx) as r:
            result = json.load(r)
            print(f'Imported: {result.get("title")}')
            print(f'URL:      {GRAFANA_URL}{result.get("importedUrl")}')
    except urllib.error.HTTPError as e:
        print(f'ERROR {e.code}: {e.read().decode()}')
        sys.exit(1)

if __name__ == '__main__':
    main()
