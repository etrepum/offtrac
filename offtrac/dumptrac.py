#!/usr/bin/env python
"""
# TODO: real syncing
# TODO: attachments
# TODO: wiki
# TODO: trac compatible report db

"""
from __future__ import with_statement

import os
import glob
import time
import urllib
import getpass
import httplib
import urlparse
import itertools
from subprocess import Popen, PIPE

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
IGNORES = ('*.db',)
VERSION = 2
MIN_RECENT = "2000-01-01T00:00:00"
GIT = 'git'
DEFAULT_PATH = './db'


class ProcessError(Exception):
    pass


class DBError(Exception):
    pass


def call(args, **kw):
    p = Popen(args, stdout=PIPE, stderr=PIPE, **kw)
    (stdout, stderr) = p.communicate()
    return (p.returncode, stdout, stderr)


def check_call(args, **kw):
    (rc, stdout, stderr) = call(args, **kw)
    if rc:
        raise ProcessError("{!r} returned {}".format(args, rc))
    return (rc, stdout, stderr)


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
        json.dump(data, f, sort_keys=True, indent=1, separators=(',', ':'))
    os.rename(tmpfn, fn)


def ticket_changed(lst):
    _ticket_id, _created, changed, _props = lst
    return changed


def url_safe_id(ident):
    s = unicode(ident)
    return urllib.quote_plus(s.encode('utf8'))


def parse_git_status(stdout):
    results = []
    for line in stdout.splitlines():
        if not line.endswith('.json'):
            continue
        modes, _, rest = line.partition('\t')
        results.append((modes, rest))
    return results


def path_id(path):
    return urllib.unquote_plus(os.path.basename(path).rpartition('.')[0])


class Trac(object):
    def __init__(self, user, password, url=TRAC_URL):
        self.url = url
        self.headers = dict([auth_header(user, password)])
        self.conn = None

    def http_request(self, method, path, body=None, headers={}, retries=3):
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
        while True:
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
            except Exception, e:
                self.conn.close()
                self.conn = None
                if retries > 0 and isinstance(e, httplib.BadStatusLine):
                    retries -= 1
                    time.sleep(0.01)
                    continue
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
    def __init__(self, root=DEFAULT_PATH):
        self.root = root
        self.metadata = {}
        self._git_head = None

    def init(self):
        for dirname in map(self.path_join, DIRS):
            if not os.path.exists(dirname):
                os.makedirs(dirname)
        self.gitinit()
        self.cleanup()
        self.gitignore()
        self.read_metadata()
        self.upgrade()
        self.checkpoint()

    def git(self, *args):
        return check_call([GIT] + list(args), cwd=self.root)

    def gitinit(self):
        self.git('init')

    def checkpoint(self):
        self._git_head = None
        self.git('add', '-A')
        # This will fail if there is nothing to commit
        # TODO: handle this gracefully
        try:
            self.git('commit', '-am', '{}'.format(self.recent))
        except ProcessError:
            pass

    def cleanup(self):
        # This will fail if the repo has no commits
        try:
            self.git('reset', '--hard', 'HEAD')
        except ProcessError:
            pass
        # Remove unknown files
        for line in self.git('status', '-s')[2].splitlines():
            if line.startswith('?? '):
                os.remove(self.path_join(line[3:]))

    def gitignore(self):
        fn = self.path_join('.gitignore')
        ignores = set([ignore + '\n' for ignore in IGNORES])
        try:
            with open(fn, 'rb') as f:
                for l in f:
                    ignores.discard(l)
        except IOError:
            pass
        if not ignores:
            return
        with open(fn, 'ab') as f:
            for ignore in sorted(ignores):
                f.write(ignore)

    def read_metadata(self):
        try:
            with open(self.path_join('db.json'), 'rb') as f:
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
            elif dbver < 2:
                raise DBError(
                    "Version {} no longer supported".format(dbver))
            assert self.metadata['version'] > dbver
            self.write_metadata()

    def path_join(self, *args):
        return os.path.join(self.root, *args)

    def json_glob(self, *args):
        return glob.glob(self.path_join(*(args + ('*.json',))))

    def load_json(self, fn):
        with open(self.path_join(fn), 'rb') as f:
            return json.load(f)

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
        return self.metadata.get('recent', MIN_RECENT)
    
    @property
    def git_head(self):
        if self._git_head is not None:
            return self._git_head
        self._git_head = self.git('rev-parse', 'HEAD')[1].rstrip()
        return self._git_head

    def changed_files(self, ver):
        return parse_git_status(
            self.git('diff', '--name-status', '{}...HEAD'.format(ver))[1])

    def nuke(self, *args):
        for fn in self.json_glob(*args):
            os.remove(fn)

    def pull(self, t):
        # Reports
        print 'syncing reports'
        self.nuke('report')
        reports = t.report_list()
        for report_id, info in t.yield_reports(reports):
            safe_id = url_safe_id(report_id)
            write_json(self.path_join('report', '%s.json' % (safe_id,)), info)
        # Fields
        for field_name in FIELDS:
            print 'syncing', field_name
            self.nuke('field', field_name)
            for field_id, info in t.yield_field(field_name):
                safe_id = url_safe_id(field_id)
                write_json(self.path_join('field',
                                          field_name,
                                          '%s.json' % (safe_id,)),
                           info)
        # Changed tickets
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
        self.checkpoint()


def keychain_auth(url):
    (_scheme, netloc, _path,
     _query, _fragment) = urlparse.urlsplit(url)
    username = getpass.getuser()
    (_ret, _stdout, stderr) = call(
        ["security", "find-internet-password", "-g", "-s", netloc])
    password = stderr.split('"')[1]
    return username, password


def main():
    user, password = keychain_auth(TRAC_URL)
    t = Trac(user, password, TRAC_URL)
    db = DB()
    db.init()
    db.pull(t)


if __name__ == '__main__':
    main()
