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

import json
import time

#
# Helpers
#


def _api_call(api, command, *args, **kwargs):
    r = api.command(command, **kwargs)
    sc = r.get('status_code')
    if sc < 200 or sc > 299:
        err = [f'{e["message"]} ({e["code"]})' for e in r['body']['errors']]
        raise Exception('\n'.join(err))
    else:
        return r


def _details(api, ids, cb):
    details = []
    offset = 100
    i = 0
    j = offset

    total = len(ids)
    while j < total:
        details.extend(cb(api, ids[i:j]))
        i = j
        j += offset
    details.extend(cb(api, ids[i:total]))

    return details


def _query(api, command, filter=None, sort=None):
    limit = 100
    total = 1
    offset = 0

    items = []
    while offset < total:
        resp = _api_call(api, command,
                         filter=filter,
                         limit=limit,
                         offset=offset,
                         sort=sort)
        items.extend(resp['body']['resources'])
        total = resp['body']['meta']['pagination']['total']
        offset = resp['body']['meta']['pagination']['offset']
        if offset == 0:
            offset = total
    return items

#
# Methods
#


def get_device_details(api, device_ids):
    def cb(api, device_ids):
        body = {'ids': device_ids}
        resp = _api_call(api, 'GetDeviceDetails', body=body)
        return resp['body']['resources']
    return _details(api, device_ids, cb)


def get_detect_summaries(api, detection_ids):
    def cb(api, detection_ids):
        body = {'ids': detection_ids}
        resp = _api_call(api, 'GetDetectSummaries', body=body)
        return resp['body']['resources']
    return _details(api, detection_ids, cb)


def query_detects(api, filter=None, sort=None):
    return _query(api, 'QueryDetects', filter, sort)


def query_devices_by_filter(api, filter=None, sort=None):
    return _query(api, 'QueryDevicesByFilter', filter, sort)


def update_device_tags(api, device_ids, action, tags):
    body = {'action': action, 'device_ids': device_ids, 'tags': tags}
    resp = _api_call(api, 'UpdateDeviceTags', body=body)
    return resp


def query_host_groups(api, filter=None, sort=None):
    return _query(api, 'queryHostGroups', filter, sort)


def get_host_groups(api, group_ids):
    def cb(api, group_ids):
        resp = _api_call(api, 'getHostGroups', ids=group_ids)
        return resp['body']['resources']
    return _details(api, group_ids, cb)


def retrieve_user_uuid(api, user_ids):
    resp = _api_call(api, 'RetrieveUserUUID', uid=user_ids)
    return resp['body']['resources']


def get_user_role_ids(api, user_uuid):
    resp = _api_call(api, 'GetUserRoleIds', user_uuid=user_uuid)
    return resp['body']['resources']


def revoke_user_role_ids(api, user_uuid, role_ids):
    resp = _api_call(api, 'RevokeUserRoleIds',
                     user_uuid=user_uuid, ids=role_ids)
    return resp


def grant_user_role_ids(api, user_uuid, role_ids):
    body = {'roleIds': role_ids}
    resp = _api_call(api, 'GrantUserRoleIds', user_uuid=user_uuid, body=body)
    return resp


def rtr_init_session(api, device_id):
    body = {'device_id': device_id, 'origin': 'api', 'queue_offline': False}
    resp = _api_call(api, 'RTR_InitSession', body=body)
    return resp['body']['resources']


def rtr_delete_session(api, session_id):
    parameters = {'session_id': session_id}
    resp = _api_call(api, 'RTR_DeleteSession', parameters=parameters)
    return resp


def rtr_exec_ar_command(api, session_id, cmd, cmd_line):
    print(f'(*) Running command: {cmd_line}')
    body = {"base_command": cmd, "command_string": cmd_line,
            "persist": False, "session_id": session_id}
    resp = _api_call(api, 'RTR_ExecuteActiveResponderCommand',
                     timeout=10, timeout_duration='s', body=body)
    return resp['body']['resources']


def rtr_check_ar_command_status(api, cloud_request_id):
    complete = False
    attempt = 0
    while not complete:
        resp = _api_call(api, "RTR_CheckActiveResponderCommandStatus",
                         cloud_request_id=cloud_request_id, sequence_id=0)
        complete = resp['body']['resources'][0]['complete']
        stdout = resp['body']['resources'][0]['stdout']
        stderr = resp['body']['resources'][0]['stderr']
        if complete:
            print('(*) Command successfully executed')
            if stdout:
                print('>>> stdout')
                print(stdout)
                print('>>> ------')
            if stderr:
                print('>>> stderr')
                print(stderr)
                print('>>> ------')

        # avoid infinite loop
        attempt += 1
        if attempt > 6:
            print('(!) Reached maximum number of attempts')
            print(json.dumps(resp, indent=2))
            break

        # wait for the next attempt
        time.sleep(2)
