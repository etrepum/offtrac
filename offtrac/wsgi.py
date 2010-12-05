# -*- coding: utf-8 -*-
import os
import re
import csv
from cStringIO import StringIO

from .etl import Report

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


@app.route('/report/<int:report_id>')
def report_json(report_id):
    fmt = request.args.get('format', 'json')
    user = request.args.get('USER', 'bob')
    session = db.session
    report = session.query(Report).get(report_id)
    if report is None:
        abort(404)
    if fmt == 'sql':
        return send_file(StringIO(report.query),
                         mimetype='text/plain',
                         as_attachment=True,
                         attachment_filename='report_{0}.sql'.format(report_id))
    resultproxy = session.execute(clean_sql(report.query, user=user))
    try:
        res = list(resultproxy)
    except ResourceClosedError:
        res = []
    if fmt == 'json':
        return jsonify({'results': map(dict, res)})
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
    elif fmt == 'html':
        return send_file(root_path('static', 'index.html'),
                         mimetype='text/html')
    abort(404)


@app.route('/json')
def json():
    return jsonify({'status': 'ok'})


@app.route('/<path:filename>')
def default_file(filename):
    return send_from_directory(root_path('static'), filename)
