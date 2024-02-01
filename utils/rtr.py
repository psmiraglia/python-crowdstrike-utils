#!/usr/bin/env python
'''
Copyright 2024 Paolo Smiraglia <paolo.smiraglia@gmail.com>

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

import json
import logging
import os
import sys
import time
from argparse import ArgumentParser

from falconpy import APIHarnessV2

import commons
from creds import CLIENT_ID, CLIENT_SECRET

logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s',
                    level=logging.DEBUG,
                    filename='sup.log')


def cmd_line():
    parser = ArgumentParser()
    parser.add_argument('--debug', action='store_true', required=False)
    parser.add_argument('--dry-run', action='store_true', required=False)
    parser.add_argument('-s', '--script', required=True)
    parser.add_argument('-p', '--script-params', required=False, default='')
    parser.add_argument('-d', '--devices', required=True)
    return parser.parse_args()


if __name__ == '__main__':
    args = cmd_line()

    if not os.path.isfile(args.devices):
        print(f'(!) File does not exist: {args.devices}')
        sys.exit(1)

    custom_script = args.script
    custom_script_params = args.script_params

    # init the Falcon api
    api = APIHarnessV2(client_id=CLIENT_ID,
                       client_secret=CLIENT_SECRET,
                       debug=args.debug)

    ids = []
    with open(args.devices, 'r') as fp:
        ids = [line.strip() for line in fp.readlines()]
        fp.close()

    for device_id in ids:
        print(f'(*) Device ID: {device_id}')
        # init the RTR session
        resp = commons.rtr_init_session(api, device_id)
        session_id = resp[0].get('session_id')
        print(f'(*) RTR Session ID: {session_id}')

        # run command
        cmd = 'runscript'
        cmd_line = f'{cmd} -CloudFile="{custom_script}"  -CommandLine="{custom_script_params}"'  # noqa
        resp = commons.rtr_exec_ar_command(api, session_id, cmd, cmd_line)

        # check status
        cloud_request_id = resp[0].get('cloud_request_id')
        commons.rtr_check_ar_command_status(api, cloud_request_id)

        # delete session
        resp = commons.rtr_delete_session(api, session_id)
        status_code = resp.get('status_code')
        if status_code >= 200 and status_code < 300:
            print(f'(*) RTR sessions successfully deleted ({status_code})')
        else:
            print('(!) RTR session not deleted ({status_code})')
            print(json.dumps(resp, indent=2))

        # take a rest...
        time.sleep(2)
