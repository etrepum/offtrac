import os
import time
import urllib
import calendar

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from . import model
from . import dumptrac


Base = declarative_base()


def orm_name(name):
    return ''.join([s.capitalize() for s in name.split('_')])


def make_orm_class(table):
    return type(orm_name(table.name), (Base,), {'__table__': table})


Ticket = make_orm_class(model.ticket)
TicketChange = make_orm_class(model.ticket_change)
Enum = make_orm_class(model.enum)
Component = make_orm_class(model.component)
Version = make_orm_class(model.version)
Milestone = make_orm_class(model.milestone)
Report = make_orm_class(model.report)

MODEL_CLASSES = (
    Component,
    Version,
    Milestone,
    Enum,
    Report,
    TicketChange,
    Ticket,
)


def path_id(path):
    return urllib.unquote_plus(os.path.basename(path).rpartition('.')[0])


def get_engine():
    return create_engine('sqlite:///offtrac.db')


def get_session_class(engine):
    Session = sessionmaker(autocommit=True)
    Session.configure(bind=engine)
    return Session


def iso8601_to_trac_time(isodatetime):
    if not isodatetime:
        return isodatetime
    utc_tuple = time.strptime(isodatetime, '%Y-%m-%dT%H:%M:%S')
    return int(calendar.timegm(utc_tuple) * 1000)


def new_bigtime(isodatetime, old_bigtime=None):
    bigtime = iso8601_to_trac_time(isodatetime)
    if old_bigtime is None or bigtime > old_bigtime:
        return bigtime
    return old_bigtime + 1


class ETL(object):
    ENUM_TYPES = ('priority', 'resolution', 'severity', 'type')

    def __init__(self, filedb, Session):
        self.filedb = filedb
        self.Session = Session

    def full_reindex(self):
        session = self.Session()
        with session.begin():
            for Class in MODEL_CLASSES:
                session.query(Class).delete()
            session.add_all(self.ormify_fields())
            session.add_all(self.ormify_enum())
            session.add_all(self.ormify_ticket())
            session.add_all(self.ormify_report())
            session.add_all(self.ormify_changelog())

    def ormify_enum(self):
        for enum_type in self.ENUM_TYPES:
            for fn, data in self.filedb.iter_jsondir('field/' + enum_type):
                yield Enum(type=enum_type, name=path_id(fn), value=data)

    def ormify_fields(self):
        for FieldClass in (Component, Version, Milestone):
            table = FieldClass.__table__
            for _fn, data in self.filedb.iter_jsondir('field/' + table.name):
                if FieldClass is Milestone:
                    data = dict(
                        data,
                        due=iso8601_to_trac_time(data['due']),
                        completed=iso8601_to_trac_time(data['completed']))
                yield FieldClass(**data)

    def ormify_ticket(self):
        for _fn, data in self.filedb.iter_jsondir('ticket'):
            ticket_id, created, changed, props = data
            props = dict(props,
                id=ticket_id,
                time=iso8601_to_trac_time(created),
                changetime=iso8601_to_trac_time(changed))
            yield Ticket(**props)

    def ormify_changelog(self):
        for fn, data in self.filedb.iter_jsondir('changelog'):
            bigtime = None
            for isotime, author, field, oldvalue, newvalue, _permanent in data:
                bigtime = new_bigtime(isotime, bigtime)
                yield TicketChange(
                    ticket=path_id(fn),
                    time=bigtime,
                    author=author,
                    field=field,
                    oldvalue=oldvalue,
                    newvalue=newvalue)

    def ormify_report(self):
        for fn, props in self.filedb.iter_jsondir('report'):
            yield Report(
                id=path_id(fn),
                title=props['title'],
                query=props['sql'],
                author='',
                description='')

def main():
    filedb = dumptrac.DB()
    filedb.init()
    imp = ETL(filedb, get_session_class(engine=get_engine()))
    imp.full_reindex()


if __name__ == '__main__':
    main()
