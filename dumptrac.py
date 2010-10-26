#!/usr/bin/env python
import os
import sys
import httplib
import urlparse
import itertools

import simplejson as json

TRAC_URL = 'https://trac.mochimedia.net/login/jsonrpc'


def get_http_connection(scheme, host):
    """Get a request scoped httplib.HTTPConnection for host

    """
    if scheme == 'http':
        cls = httplib.HTTPConnection
    elif scheme == 'https':
        cls = httplib.HTTPSConnection
    else:
        raise ValueError("scheme must be http or https, not %r" % (scheme,))

    return cls(host)


def auth_header(user, password):
    return ('Authorization', 'Basic ' + (user + ':' + password).encode('base64').strip())


def raw_http_request(method, url, body=None, headers={}):
    """Make a HTTP ``method`` request to ``url``
    with optional body and headers.

    Returns a dict with::

        {
            'status': int,
            'reason': str,
            'version': str,
            'headers': dict, # keys are all lowercase
            'raw_headers': [(key, value)],
            'body': str,
        }

    """
    scheme, netloc, path, query, fragment = urlparse.urlsplit(url)
    if query:
        path = '%s?%s' % (path, query)
    conn = get_http_connection(scheme, netloc)
    conn.request(method, path, body, headers)
    try:
        response = conn.getresponse()
        body = response.read()
        headers = response.getheaders()
    except:
        conn.close()
        raise
    return body


class Trac(object):
    def __init__(self, user, password, url=TRAC_URL):
        self.url = url
        self.headers = dict([auth_header(user, password)])
        self.headers['Content-Type'] = 'application/json'

    def raw_call(self, method, params):
        body = json.dumps({'method': method, 'params': params})
        res = raw_http_request('POST', self.url, body, self.headers)
        return json.loads(res)

    def call(self, method, params):
        res = self.raw_call(method, params)
        if res['error']:
            raise ValueError(res['error'])
        return res['result']

    def imulticall(self, calls, size=100):
        for i in xrange(0, len(calls), size):
            for val in self.multicall(calls[i:i+size]):
                yield val

    def multicall(self, calls):
        calls = [{'method': method, 'params': params, 'id': 1 + i}
                 for i, (method, params) in enumerate(calls)]
        rval = [None] * len(calls)
        for res in self.call('system.multicall', calls):
            if res['error']:
                raise ValueError(res['error'])
            rval[res['id'] - 1] = res['result']
        return rval


def dumps(val):
    return json.dumps(val, sort_keys=True, indent=4)


def main():
    user, password = sys.argv[1:]
    t = Trac(user, password)
    recent = t.call('ticket.getRecentChanges', [{"__jsonclass__": ["datetime", "2000-01-01T00:00:00"]}])
    print 'tickets:', len(recent)
    with open('tickets.json', 'wb') as f:
        f.write(json.dumps(recent))
    for dirname in ('ticket', 'changelog'):
        if not os.path.exists(dirname):
            os.mkdir(dirname)
    for ticket_id, info in itertools.izip(recent, t.imulticall([('ticket.get', [ticket_id]) for ticket_id in recent])):
        print 'ticket', ticket_id
        with open('ticket/%s.json' % (ticket_id,), 'wb') as f:
            f.write(json.dumps(info))
    for ticket_id, changelog in itertools.izip(recent, t.imulticall([('ticket.changeLog', [ticket_id, 0]) for ticket_id in recent])):
        print 'changelog', ticket_id
        with open('changelog/%s.json' % (ticket_id,), 'wb') as f:
            f.write(json.dumps(changelog))


if __name__ == '__main__':
    main()
