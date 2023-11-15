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
