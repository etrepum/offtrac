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
    if isinstance(o, dict):
        if '__jsonclass__' in o:
            v = o['__jsonclass__']
            assert v[0] == 'datetime'
            return v[1]
        for k, v in o.iteritems():
            v1 = normalize_in_place(v)
            if v1 is not v:
                o[k] = v1
    elif isinstance(o, list):
        for i, v in enumerate(o):
            v1 = normalize_in_place(v)
            if v1 is not v:
                o[i] = v1
    return o


def write_json(fn, data):
    dirname, basename = os.path.split(fn)
    tmpfn = os.path.join(dirname, '.' + basename)
    with open(tmpfn, 'wb') as f:
        json.dump(data, f)
    os.rename(tmpfn, fn)

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
        write_json(self.path_join('db.json'), self.metadata)

    def upgrade(self):
        while True:
            dbver = self.metadata.get('version', VERSION)
            if dbver == VERSION:
                return
            if dbver == 0:
                self.upgrade_0_1()
            assert self.metadata['version'] > dbver
            self.write_metadata()

    def upgrade_0_1(self):
        # First version didn't cache recent or de-jsonclass datetime
        print 'upgrading version 0 db to version 1'
        recent = MIN_RECENT
        for dirname in DIRS:
            for fn, data in self.iter_jsondir(dirname):
                data = normalize_in_place(data)
                if dirname == 'ticket':
                    recent = max(recent, ticket_changed(data))
                write_json(fn, data)
        self.metadata['recent'] = recent
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

    @property
    def recent(self):
        return self.metadata['recent']

    def pull(self, t):
        for field_name in FIELDS:
            print 'syncing', field_name
            ## TODO: This is a bad sync, we do not
            ##       garbage collect field values that were deleted
            for field_id, info in t.yield_field(field_name):
                write_json(self.path_join(field_name, '%s.json' % (field_id,)),
                           info)

        print 'fetching changed ticket ids since', self.recent
        recent_tickets = t.recent_tickets(self.recent)
        print 'fetching metadata for %d tickets' % (len(recent_tickets),)
        for ticket_id, info in t.yield_tickets(recent_tickets):
            write_json(self.path_join('ticket', '%s.json' % (ticket_id,)),
                       info)
        print 'fetching changelog for %d tickets' % (len(recent_tickets),)
        for ticket_id, info in t.yield_changelogs(recent_tickets):
            write_json(self.path_join('changelog', '%s.json' % (ticket_id,)),
                       info)


def main():
    user, password = sys.argv[1:]
    t = Trac(user, password)
    db = DB('.')
    db.init()
    db.pull(t)


if __name__ == '__main__':
    main()
