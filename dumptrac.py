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
FIELDS = ('component', 'priority', 'resolution', 'severity', 'type', 'version')
DIRS = ('ticket', 'changelog') + FIELDS
VERSION = 1
MIN_RECENT = "2000-01-01T00:00:00"

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


def jsondatetime(s):
    return {"__jsonclass__": ["datetime", s]}


def normalize_in_place(o):
    if not isinstance(o, dict):
        return o
    elif '__jsonclass__' in o:
        v = o['__jsonclass__']
        assert v[0] == 'datetime'
        return v[1]
    for k, v in o.iteritems():
        v1 = normalize_in_place(v)
        if v1 is not v:
            o[k] = v1
    return o


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
        res = normalize_in_place(self.raw_call(method, params))
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
        return self.call('ticket.getRecentChanges', [jsondatetime(recent)])

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


def ticket_changed(lst):
    _ticket_id, _created, changed, _props = lst
    return changed


def most_recent(tickets, default=None):
    if default is None:
        default = MIN_RECENT
    return max(
        itertools.chain(
            [default],
            itertools.imap(ticket_changed, tickets)))


class DB(object):
    def __init__(self, root='.'):
        self.root = root
        self.metadata = {}

    def init(self):
        for dirname in DIRS:
            if not os.path.exists(dirname):
                os.mkdir(dirname)
        self.read_metadata()
        self.upgrade()

    def read_metadata(self):
        try:
            with open('db.json', 'rb') as f:
                self.metadata = json.load(f)
        except IOError:
            pass

    def write_metadata(self):
        with open('.db.json', 'wb') as f:
            json.dump(self.metadata, f)
        os.rename('.db.json', 'db.json')

    def upgrade(self):
        while True:
            dbver = self.metadata.get('version', VERSION)
            if dbver == VERSION:
                return
            if dbver == 0:
                self.upgrade_0_1(self)
            assert self.metadata['version'] > dbver
            self.write_metadata()

    def upgrade_0_1(self):
        tickets = []
        for dirname in DIRS:
            for fn, data in self.iter_jsondir(dirname):
                s = json.dumps(normalize_in_place(data))
                if dirname == 'ticket':
                    tickets.append(data)
                with open(fn, 'wb') as f:
                    f.write(s)
        self.metadata['recent'] = most_recent(tickets)
        self.metadata['version'] = 1

    def path_join(self, *args):
        return os.path.join(self.root, *args)

    def json_glob(self, dirname):
        return glob.glob(self.path_join(dirname, '*.json'))

    def iter_jsondir(self, dirname):
        for fn in self.json_glob(dirname):
            with open(fn, 'rb') as f:
                data = json.load(f)
            yield fn, data

    def read_tickets(self):
        for _fn, data in self.iter_jsondir('ticket'):
            yield data


def main():
    user, password = sys.argv[1:]
    t = Trac(user, password)
    db = DB('.')
    db.init()
    recent = most_recent(read_tickets())
    print 'most recent:', recent
    recent_tickets = t.recent_tickets(recent)
    print 'tickets:', len(recent_tickets)
    with open('tickets.json', 'wb') as f:
        f.write(json.dumps(recent))
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
