# -*- coding: utf-8 -*-
import os
import re
import csv
from cStringIO import StringIO

from .etl import Report, Ticket

from sqlalchemy.exc import ResourceClosedError
from flask import Flask, jsonify, send_from_directory, abort, request, send_file
from flaskext.sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///offtrac.db'
#app.config['SQLALCHEMY_ECHO'] = True
db = SQLAlchemy(app)


def root_path(*args):
    return os.path.join(app.config.root_path, *args)


def clean_sql(sql,
              user='bob',
              TYPE_RE=re.compile(r'(::\w+)')):
    return TYPE_RE.sub('', sql).replace('$USER', user)


def csv_safe_row(row):
    return [unicode(v).encode('utf-8') for v in row]


def get_format(request):
    if 'application/json' in request.headers.get('Accept', ''):
        return 'json'
    return request.args.get('format', 'html')


def get_user(request):
    return request.args.get('USER', 'bob')


def csvify(results, dialect):
    sio = StringIO()
    if not results:
        return sio
    out = csv.writer(sio, dialect=dialect)
    keys = results[0].keys()
    out.writerow(csv_safe_row(keys))
    out.writerows(csv_safe_row(row[k] for k in keys) for row in results)
    sio.seek(0)
    return sio


def orm_dict(o):
    return dict((k, v) for (k, v) in o.__dict__.iteritems()
                if not k.startswith('_'))


@app.route('/report')
def report_list():
    fmt = get_format(request)
    if fmt == 'html':
        return send_file(root_path('static', 'index.html'),
                         mimetype='text/html')
    user = get_user(request)
    session = db.session
    reports = session.query(Report).order_by(Report.id).all()
    if fmt == 'json':
        return jsonify({
            'template': 'report_list',
            'reports': map(orm_dict, reports),
            'user': user,
            'title': 'Available Reports',
        })
    abort(404)


@app.route('/ticket/<int:ticket_id>')
def ticket(ticket_id):
    fmt = get_format(request)
    if fmt == 'html':
        return send_file(root_path('static', 'index.html'),
                         mimetype='text/html')
    user = get_user(request)
    session = db.session
    ticket = session.query(Ticket).get(ticket_id)
    if ticket is None:
        abort(404)
    if fmt == 'json':
        return jsonify({
            'template': 'ticket',
            'ticket': orm_dict(ticket),
            'user': user,
        })
    """
    elif fmt == 'csv':
        return send_file(csvify(res, dialect='excel'),
                         mimetype='text/csv',
                         as_attachment=True,
                         attachment_filename='ticket_{0}.csv'.format(ticket_id))
    elif fmt == 'tab':
        return send_file(csvify(res, dialect='excel-tab'),
                         mimetype='text/tab-separated-values',
                         as_attachment=True,
                         attachment_filename='ticket_{0}.tsv'.format(ticket_id))
    """
    abort(404)


@app.route('/report/<int:report_id>')
def report(report_id):
    fmt = get_format(request)
    if fmt == 'html':
        return send_file(root_path('static', 'index.html'),
                         mimetype='text/html')
    user = get_user(request)
    session = db.session
    report = session.query(Report).get(report_id)
    if report is None:
        abort(404)
    if fmt == 'sql':
        return send_file(StringIO(report.query.encode('utf-8')),
                         mimetype='text/plain',
                         as_attachment=True,
                         attachment_filename='report_{0}.sql'.format(report_id))
    resultproxy = session.execute(clean_sql(report.query, user=user))
    try:
        res = list(resultproxy)
    except ResourceClosedError:
        res = []
    if fmt == 'json':
        return jsonify({
            'template': 'report',
            'columns': res[0].keys() if res else [],
            'results': map(dict, res),
            'title': report.title,
            'user': user,
            'report_id': report_id,
        })
    elif fmt == 'csv':
        return send_file(csvify(res, dialect='excel'),
                         mimetype='text/csv',
                         as_attachment=True,
                         attachment_filename='report_{0}.csv'.format(report_id))
    elif fmt == 'tab':
        return send_file(csvify(res, dialect='excel-tab'),
                         mimetype='text/tab-separated-values',
                         as_attachment=True,
                         attachment_filename='report_{0}.tsv'.format(report_id))
    abort(404)


@app.route('/json/<path:blah>')
def json(blah):
    print request.headers
    return jsonify({'status': 'ok'})


@app.route('/<path:filename>')
def default_file(filename):
    return send_from_directory(root_path('static'), filename)
