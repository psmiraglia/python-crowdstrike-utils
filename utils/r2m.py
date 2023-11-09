#!/usr/bin/env python
'''
Copyright 2023 Paolo Smiraglia <paolo.smiraglia@gmail.com>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
'''

import datetime
import logging
import random
import string
from argparse import ArgumentParser

from falconpy import APIHarnessV2
from tabulate import tabulate

import commons
from creds import CLIENT_ID, CLIENT_SECRET

logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s',
                    level=logging.DEBUG,
                    filename='r2m.log')

TAG_BASE = 'FalconGroupingTags/r2m'


def generate_tag():
    today = datetime.datetime.now().strftime('%Y%m%d')
    salt = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
    tag = '-'.join([TAG_BASE, today, salt])
    return tag


def cmd_line():
    parser = ArgumentParser()
    parser.add_argument('--debug', action='store_true', required=False)
    parser.add_argument('--dry-run', action='store_true', required=False)
    parser.add_argument('-d', '--days', required=False, default='7')
    parser.add_argument('-f', '--from', required=False, default='', dest='dt_from')  # noqa
    parser.add_argument('-g', '--group', required=False)
    parser.add_argument('-t', '--to', required=False, default='', dest='dt_to')
    return parser.parse_args()


if __name__ == '__main__':
    args = cmd_line()

    # get today's date
    today = datetime.datetime.now()

    # build the filter
    if args.dt_from or args.dt_to:
        dt_to = None
        dt_from = None
        if args.dt_to and not args.dt_from:
            dt_from = '1970-01-01'
            dt_to = args.dt_to
        if args.dt_from:
            dt_from = args.dt_from
            if args.dt_to:
                dt_to = args.dt_to
            else:
                dt_to = today.strftime('%Y-%m-%d')
        f_dev = f"first_seen:>='{dt_from}'+first_seen:<='{dt_to}'"
        print(f'(>) f_dev: {f_dev}')
        f_det = f"last_behavior:>='{dt_from}'+last_behavior:<='{dt_to}'"
        print(f'(>) f_det: {f_det}')
    else:
        days = int(args.days)
        days_ago = (today - datetime.timedelta(days=days)).strftime('%Y-%m-%d')
        f_dev = f"first_seen:>='{days_ago}'"
        print(f'(>) f_dev: {f_dev}')
        f_det = f"last_behavior:>='{days_ago}'"
        print(f'(>) f_det: {f_det}')

    # init the Falcon api
    api = APIHarnessV2(client_id=CLIENT_ID,
                       client_secret=CLIENT_SECRET,
                       debug=args.debug)

    # get endpoints that were linked in the last N days
    devices_ids = commons.query_devices_by_filter(api, f_dev, 'first_seen.desc')  # noqa
    devices = commons.get_device_details(api, devices_ids)

    # get detections that appeared in the last N days
    detections_ids = commons.query_detects(api, f_det)
    detections = commons.get_detect_summaries(api, detections_ids)

    # do the dirty job
    to_be_tagged = []
    table = []
    for d in devices:
        if args.group:
            if ('groups' not in d) or (args.group not in d['groups']):
                continue

        # skip the defice if it has been already marked for moving
        tags = [t for t in d['tags'] if t.startswith(TAG_BASE)]
        if tags:
            continue

        device_id = d.get('device_id')
        hostname = d.get('hostname')
        first_seen = d.get('first_seen')[0:10]
        dts = [dt for dt in detections if dt['device']['device_id'] == device_id]  # noqa
        n_detections = len(dts)
        status = 'safe'
        if n_detections:
            status = 'unsafe'
        else:
            to_be_tagged.append(device_id)
        table.append([status, n_detections, first_seen, hostname, device_id])
    headers = ['Status', 'Detections', 'First Seen', 'Hostname', 'Device ID']
    print(tabulate(table, headers))

    # apply tag
    tags = [generate_tag()]
    if not args.dry_run:
        commons.update_device_tags(api, to_be_tagged, 'add', tags)
    print(f'(*) You can safely move hosts with tags: {",".join(tags)}')
