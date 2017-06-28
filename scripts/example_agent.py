#!/usr/bin/env python3

import argparse
from datetime import datetime
import json
import os
import requests
import socket
import sys


requests.adapters.DEFAULT_RETRIES = 1

default_report_url = 'http://127.0.0.1:5000/report'
default_agent_token = 'examplesecrettoken'
default_series_id = None

default_tags = {
    'agent': 'example_agent',
    'host': socket.getfqdn(),
}

default_values = {
    'load': {
        '1m':  os.getloadavg()[0],
        '5m':  os.getloadavg()[1],
        '15m': os.getloadavg()[2],
    },
    'uname': {
        'sysname':  os.uname().sysname,
        'nodename': os.uname().nodename,
        'release':  os.uname().release,
        'version':  os.uname().version,
        'machine':  os.uname().machine,
    },
}


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--url', default=default_report_url, help='report URL')
    p.add_argument('--token', default=default_agent_token)
    p.add_argument('--series', default=default_series_id)
    p.add_argument('--tags', default=json.dumps(default_tags))
    p.add_argument('--values', default=json.dumps(default_values))
    args = p.parse_args()
    report_url = args.url
    state = {
        'agent_token': args.token,
        'series_id': args.series,
        'date': datetime.utcnow().isoformat(),
        'tags': json.loads(args.tags),
        'values': json.loads(args.values),
    }
    try:
        r = requests.post(report_url, json=state)
    except Exception as e:
        sys.exit('POST to {!r} failed: {}'.format(report_url, e))
    r.raise_for_status()
    print(r.text.rstrip())


if __name__ == '__main__':
    main()
