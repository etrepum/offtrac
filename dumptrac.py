#!/usr/bin/env python
"""
# TODO: real syncing
# TODO: attachments
# TODO: wiki
# TODO: trac compatible report db

"""
from __future__ import with_statement

import os
import sys
import glob
import urllib
import getpass
import httplib
import urlparse
import itertools
import subprocess

import simplejson as json


TRAC_URL = 'https://trac.mochimedia.net'
FIELDS = (
    'component',
    'priority',
    'resolution',
    'severity',
    'type',
    'version',
    'milestone',
)
DIRS = ('report', 'ticket', 'changelog') + tuple('field/' + f for f in FIELDS)
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


def ticket_changed(lst):
    _ticket_id, _created, changed, _props = lst
    return changed


def url_safe_id(ident):
    s = unicode(ident)
    return urllib.quote_plus(s.encode('utf8'))


class Trac(object):
    def __init__(self, user, password, url=TRAC_URL):
        self.url = url
        self.headers = dict([auth_header(user, password)])
        self.conn = None

    def http_request(self, method, path, body=None, headers={}):
        """Make a HTTP ``method`` request to ``self.url + path``
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
        (scheme, netloc, path,
         query, fragment) = urlparse.urlsplit(self.url + path)
        if query:
            path = '%s?%s' % (path, query)
        if self.conn is None:
            self.conn = get_http_connection(scheme, netloc)
        self.conn.request(method, path, body, headers)
        try:
            response = self.conn.getresponse()
            body = response.read()
            headers = response.getheaders()
        except:
            self.conn.close()
            self.conn = None
            raise
        return body

    def http_get(self, path):
        res = self.http_request('GET',
                               path,
                               '',
                               self.headers)
        return res

    def raw_call(self, method, params):
        body = json.dumps({'method': method, 'params': params})
        headers = dict(self.headers)
        headers['Content-Type'] = 'application/json'
        res = self.http_request('POST',
                               '/login/jsonrpc',
                               body,
                               headers)
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

    def report_list(self):
        raw = self.http_get('/report?asc=1&format=tab')
        for line in raw.decode('utf8').splitlines()[1:]:
            report, delim, title = line.partition('\t')
            if not delim:
                continue
            yield report, title

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

    def yield_reports(self, reports):
        for report_id, title in reports:
            sql = self.http_get('/report?id=%s&format=sql' % (report_id,))
            yield report_id, {'title': title, 'sql': sql.decode('utf8')}


class DB(object):
    def __init__(self, root='.'):
        self.root = root
        self.metadata = {}

    def init(self):
        for dirname in DIRS:
            if not os.path.exists(dirname):
                os.makedirs(dirname)
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
        print 'syncing reports'
        reports = t.report_list()
        for report_id, info in t.yield_reports(reports):
            safe_id = url_safe_id(report_id)
            write_json(self.path_join('report', '%s.json' % (safe_id,)), info)
        for field_name in FIELDS:
            print 'syncing', field_name
            ## TODO: This is a bad sync, we do not
            ##       garbage collect field values that were deleted
            for field_id, info in t.yield_field(field_name):
                safe_id = url_safe_id(field_id)
                write_json(self.path_join('field',
                                          field_name,
                                          '%s.json' % (safe_id,)),
                           info)
        print 'fetching changed ticket ids since', self.recent
        recent_tickets = t.recent_tickets(self.recent)
        print 'fetching metadata for %d tickets' % (len(recent_tickets),)
        new_recent = self.recent
        for ticket_id, info in t.yield_tickets(recent_tickets):
            new_recent = max(new_recent, ticket_changed(info))
            write_json(self.path_join('ticket', '%s.json' % (ticket_id,)),
                       info)
        print 'fetching changelog for %d tickets' % (len(recent_tickets),)
        for ticket_id, info in t.yield_changelogs(recent_tickets):
            write_json(self.path_join('changelog', '%s.json' % (ticket_id,)),
                       info)
        self.metadata['recent'] = new_recent
        self.write_metadata()
        print 'synced up to', self.recent


def keychain_auth(url):
    (_scheme, netloc, _path,
     _query, _fragment) = urlparse.urlsplit(url)
    username = getpass.getuser()
    (_stdout, stderr) = subprocess.Popen(
        ["security", "find-internet-password", "-g", "-s", netloc],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE).communicate()
    password = stderr.split('"')[1]
    return username, password


def main():
    user, password = keychain_auth(TRAC_URL)
    t = Trac(user, password, TRAC_URL)
    db = DB('.')
    db.init()
    db.pull(t)


if __name__ == '__main__':
    main()
