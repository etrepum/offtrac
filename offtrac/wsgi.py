# -*- coding: utf-8 -*-
import os
import re
import csv
import time
import datetime
from cStringIO import StringIO

from .etl import Report, Ticket, TicketChange, Milestone, Enum, get_engine_url

from sqlalchemy.exc import ResourceClosedError
from sqlalchemy.sql import func, case
from sqlalchemy.sql.expression import and_, desc
from flask import Flask, jsonify, send_from_directory, abort, request, send_file
from flaskext.sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = get_engine_url()
app.config['SQLALCHEMY_ECHO'] = True
db = SQLAlchemy(app)


def msec(dt):
    return int(1000 * time.mktime(dt.timetuple()))


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


def orm_dict(o, *args, **kw):
    return dict(((k, v) for (k, v) in o.__dict__.iteritems()
                if not k.startswith('_')),
                *args, **kw)


@app.route('/')
def index():
    fmt = get_format(request)
    if fmt == 'html':
        return send_file(root_path('static', 'index.html'),
                         mimetype='text/html')
    user = get_user(request)
    if fmt == 'json':
        return jsonify({
            'template': 'index',
            'title': 'Index',
            'user': user,
        })
    abort(404)

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


@app.route('/roadmap')
def milestone_list():
    fmt = get_format(request)
    if fmt == 'html':
        return send_file(root_path('static', 'index.html'),
                         mimetype='text/html')
    user = get_user(request)
    session = db.session
    q = session.query(
        Ticket.milestone,
        func.SUM(1).label("total"),
        func.SUM(case([(u'closed', 1)], Ticket.status, 0)).label("closed"),
        func.SUM(case([(u'closed', 0)], Ticket.status, 1)).label("open"),
    ).group_by(Ticket.milestone).subquery()
    rows = session.query(Milestone, q.c.total, q.c.closed, q.c.open).\
           filter(Milestone.completed == 0).\
           join((q, Milestone.name == q.c.milestone)).\
           order_by(Milestone.due == 0,
                    Milestone.due,
                    func.UPPER(Milestone.name)).\
           all()
    if fmt == 'json':
        return jsonify({
            'template': 'milestone_list',
            'milestones': [orm_dict(r.Milestone,
                                    total=r.total,
                                    closed=r.closed,
                                    open=r.open) for r in rows],
            'user': user,
            'title': 'Roadmap',
        })
    abort(404)


def parse_custom_query(session, args, group, order):
    table = Ticket.__table__
    cols = table.columns
    if group not in cols:
        group = 'status'
    if order not in cols:
        order = 'priority'
    groupcol = cols[group]
    ordercol = cols[order]
    preds = [cols[key].in_(values)
             for (key, values) in args.iterlists()
             if key in cols]
    q = session.query(Ticket.id.label('ticket'),
                      Ticket.summary,
                      Ticket.owner,
                      Ticket.type,
                      Ticket.priority,
                      Ticket.component,
                      Ticket.time.label('created'),
                      Enum.value.label('__color__'),
                      groupcol.label('__group__')
                      ).filter(and_(Enum.type == 'priority',
                                    Ticket.priority == Enum.name,
                                    *preds))
    return q.order_by([
        desc(groupcol) if args.get('groupdesc') == '1' else groupcol,
        desc(ordercol) if args.get('desc') == '1' else ordercol,
        ])


@app.route('/query')
def custom_query():
    fmt = get_format(request)
    if fmt == 'html':
        return send_file(root_path('static', 'index.html'),
                         mimetype='text/html')
    user = get_user(request)
    session = db.session
    group = request.args.get('group', '')
    order = request.args.get('order', '')
    q = parse_custom_query(session, request.args, group, order)
    resultproxy = q.all()
    return run_report(fmt, user, resultproxy,
                      order=order,
                      group=group,
                      title='Custom Query')


@app.route('/timeline')
def timeline():
    fmt = get_format(request)
    if fmt == 'html':
        return send_file(root_path('static', 'index.html'),
                         mimetype='text/html')
    today = datetime.date.today()
    user = get_user(request)
    session = db.session
    daysback = 14
    changes = map(orm_dict,
        session.query(TicketChange).filter(
            TicketChange.time >= msec(today - datetime.timedelta(days=daysback))
        ).order_by(TicketChange.time))
    # sqlite3 has a limit to the number of variables in a query
    # http://www.sqlite.org/limits.html
    i = 0
    chunk_size = 500
    ticket_ids = sorted(set(c['ticket'] for c in changes))
    tickets = {}
    while i < len(ticket_ids):
        tickets.update(
            (ticket.id, orm_dict(ticket))
            for ticket in session.query(Ticket).filter(
                Ticket.id.in_(ticket_ids[i:i+chunk_size])))
        i += chunk_size
    if fmt == 'json':
        return jsonify({
            'template': 'timeline',
            'tickets': tickets,
            'changes': changes,
            'title': 'Timeline',
            'user': user,
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
    ticket_dict = orm_dict(ticket)
    ticket_dict['changes'] = map(
        orm_dict,
        session.query(TicketChange).filter(
            TicketChange.ticket == ticket_id).order_by(
            TicketChange.time).all())
    if fmt == 'json':
        return jsonify({
            'template': 'ticket',
            'ticket': ticket_dict,
            'user': user,
        })
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
    return run_report(fmt, user, resultproxy, report_id=report_id, title=report.title)


def run_report(fmt, user, resultproxy, **kw):
    try:
        res = list(resultproxy)
    except ResourceClosedError:
        res = []
    report_id = kw.get('report_id', 'custom')
    if fmt == 'json':
        d = kw
        cols = res[0].keys() if res else []
        d.update({
            'template': 'report',
            'columns': cols,
            'results': [dict(zip(cols, row)) for row in res],
            'user': user,
        })
        return jsonify(d)
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
