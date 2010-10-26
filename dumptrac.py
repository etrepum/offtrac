#!/usr/bin/env python
from __future__ import with_statement

import os
import sys
import glob
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

    def recent_tickets(self, recent):
        return self.call('ticket.getRecentChanges', [{"__jsonclass__": ["datetime", recent]}])

    def component_list(self):
        return self.call('ticket.component.getAll', [])

    def yield_components(self, components):
        return itertools.izip(
            components,
            self.imulticall([('ticket.component.get', [component])
                             for component in components]))

    def yield_field(self, field):
        prefix = 'ticket.' + field
        field_ids = self.call(prefix + '.getAll', [])
        return itertools.izip(
            field_ids,
            self.imulticall([(prefix + '.get', [field_id])
                             for field_id in field_ids]))

    def yield_tickets(self, tickets):
        return itertools.izip(
            tickets,
            self.imulticall([('ticket.get', [ticket_id])
                             for ticket_id in tickets]))

    def yield_changelogs(self, tickets):
        return itertools.izip(
            tickets,
            self.imulticall([('ticket.changeLog', [ticket_id, 0])
                             for ticket_id in tickets]))


def read_tickets():
    for fn in glob.glob('ticket/*.json'):
        with open(fn, 'rb') as f:
            data = json.load(f)
        yield data


def ticket_changed(lst):
    _ticket_id, _created, changed, _props = lst
    return changed['__jsonclass__'][1]


def most_recent(tickets):
    return max(
        itertools.chain(
            ["2000-01-01T00:00:00"],
            itertools.imap(ticket_changed, tickets)))


def main():
    user, password = sys.argv[1:]
    t = Trac(user, password)
    recent = most_recent(read_tickets())
    print 'most recent:', recent
    recent_tickets = t.recent_tickets(recent)
    print 'tickets:', len(recent_tickets)
    with open('tickets.json', 'wb') as f:
        f.write(json.dumps(recent))
    FIELDS = ('component', 'priority', 'resolution', 'severity', 'type', 'version')
    for dirname in ('ticket', 'changelog') + FIELDS:
        if not os.path.exists(dirname):
            os.mkdir(dirname)
    for field_name in FIELDS:
        for field_id, info in t.yield_field(field_name):
            print field_name, field_id
            with open('%s/%s.json' % (field_name, field_id), 'wb') as f:
                f.write(json.dumps(info))
    for ticket_id, info in t.yield_tickets(recent_tickets):
        print 'ticket', ticket_id
        with open('ticket/%s.json' % (ticket_id,), 'wb') as f:
            f.write(json.dumps(info))
    for ticket_id, info in t.yield_changelogs(recent_tickets):
        print 'changelog', ticket_id
        with open('changelog/%s.json' % (ticket_id,), 'wb') as f:
            f.write(json.dumps(info))


if __name__ == '__main__':
    main()
