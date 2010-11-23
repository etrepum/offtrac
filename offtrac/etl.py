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


def get_engine():
    return create_engine('sqlite:///offtrac.db')


def get_session_class(engine):
    Session = sessionmaker(autocommit=True)
    Session.configure(bind=engine)
    return Session


def iso8601_to_trac_time(isodatetime):
    utc_tuple = time.strptime(isodatetime, '%Y-%m-%dT%H:%M:%S')
    return int(calendar.timegm(utc_tuple) * 1000)


class ETL(object):
    def __init__(self, filedb, Session):
        self.filedb = filedb
        self.Session = Session

    def reindex(self):
        session = self.Session()
        with session.begin():
            session.add_all(self.ormify_fields())
            session.add_all(self.ormify_enum())
            session.add_all(self.ormify_ticket())
            session.add_all(self.ormify_report())
            session.add_all(self.ormify_changelog())


    def ormify_enum(self):
        Enum = make_orm_class(model.enum)
        for enum_type in ('priority', 'resolution', 'severity', 'type'):
            for fn, data in self.filedb.iter_jsondir('field/' + enum_type):
                name = urllib.unquote_plus(fn.rpartition('.')[0])
                yield Enum(type=enum_type, name=name, value=data)


    def ormify_fields(self):
        for table in (model.component, model.version, model.milestone):
            FieldClass = make_orm_class(table)
            for _fn, data in self.filedb.iter_jsondir('field/' + table.name):
                yield FieldClass(**data)

    def ormify_ticket(self):
        Ticket = make_orm_class(model.ticket)
        for _fn, data in self.filedb.iter_jsondir('ticket'):
            ticket_id, created, changed, props = data
            props = dict(props,
                id=ticket_id,
                time=iso8601_to_trac_time(created),
                changetime=iso8601_to_trac_time(changed))
            yield Ticket(**props)

    def ormify_changelog(self):
        TicketChange = make_orm_class(model.ticket_change)
        for fn, data in self.filedb.iter_jsondir('changelog'):
            ticket_id = fn.rpartition('.')[0]
            for isotime, author, field, oldvalue, newvalue, _permanent in data:
                yield TicketChange(
                    ticket=ticket_id,
                    time=iso8601_to_trac_time(isotime),
                    author=author,
                    field=field,
                    oldvalue=oldvalue,
                    newvalue=newvalue)

    def ormify_report(self):
        Report = make_orm_class(model.report)
        for fn, props in self.filedb.iter_jsondir('report'):
            report_id = fn.rpartition('.')[0]
            yield Report(
                id=report_id,
                title=props['title'],
                query=props['sql'],
                author='',
                description='')

def main():
    filedb = dumptrac.DB()
    filedb.init()
    imp = ETL(filedb, get_session_class(engine=get_engine()))
    imp.reindex()


if __name__ == '__main__':
    main()
