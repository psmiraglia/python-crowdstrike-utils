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

import csv
import logging
import sys
from argparse import ArgumentParser

from falconpy import APIHarnessV2

try:
    import sup_cfg as cfg

    import commons
    from creds import CLIENT_ID, CLIENT_SECRET
except Exception as e:
    print(f'(!) Error: {e}')
    sys.exit(1)


logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s',
                    level=logging.DEBUG,
                    filename='sup.log')


def cmd_line():
    parser = ArgumentParser()
    parser.add_argument('--debug', action='store_true', required=False)
    parser.add_argument('--dry-run', action='store_true', required=False)
    parser.add_argument('-u', '--user', required=False)
    parser.add_argument('-p', '--profile', required=False, choices=cfg.PROFILES, default=cfg.DEFAULT_PROFILE)  # noqa
    parser.add_argument('-f', '--csv-file', required=False, default='')
    return parser.parse_args()


def set_user_profile(api, user, profile, dry_run):
    # get the user's uuid
    print(f'(*) Username: {user}')
    user_uuid = commons.retrieve_user_uuid(api, user)[0]
    print(f'(*) UUID: {user_uuid}')

    # get the current user's roles... and revoke them
    roles = commons.get_user_role_ids(api, user_uuid)
    if roles:
        print(f'(*) Current roles: {", ".join(roles)}')
        if not dry_run:
            commons.revoke_user_role_ids(api, user_uuid, roles)

    # grant new permissions
    print(f'(*) Profile: {profile}')
    if not dry_run:
        commons.grant_user_role_ids(api, user_uuid, cfg.ROLES[profile])
        roles = commons.get_user_role_ids(api, user_uuid)
        print(f'(*) New roles: {", ".join(roles)}')


if __name__ == '__main__':
    args = cmd_line()
    dry_run = args.dry_run
    debug = args.debug

    # init the Falcon api
    api = APIHarnessV2(client_id=CLIENT_ID,
                       client_secret=CLIENT_SECRET,
                       debug=debug)

    if args.csv_file:
        with open(args.csv_file) as csv_file:
            rows = csv.reader(csv_file, delimiter=',')
            for row in rows:
                user = row[0]
                profile = row[1]
                set_user_profile(api, user, profile, dry_run)
                print('---')
            csv_file.close()
    elif args.user:
        user = args.user
        profile = args.profile
        set_user_profile(api, user, profile, dry_run)
    else:
        print('Error: bad arguments')
