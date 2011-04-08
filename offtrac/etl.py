import os
import time
import calendar

from sqlalchemy import create_engine, and_
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from . import model
from . import dumptrac
from .dumptrac import path_id

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
OfftracMeta = make_orm_class(model.offtrac_meta)

MODEL_CLASSES = (
    Component,
    Version,
    Milestone,
    Enum,
    Report,
    TicketChange,
    Ticket,
    OfftracMeta,
)

FIELD_CLASSES = (Component, Version, Milestone)

TABLE_CLASS_MAP = dict((t.__table__.name, t) for t in MODEL_CLASSES)

def get_engine_url(filedb=None):
    if filedb is None:
        filedb = dumptrac.DB()
        filedb.init()
    return 'sqlite:///{}'.format(filedb.path_join('offtrac.db'))


def get_engine(filedb):
    return create_engine(get_engine_url(filedb))


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

    def reindex(self):
        session = self.Session()
        git_head = None
        with session.begin():
            pair = session.query(OfftracMeta).get('git_head')
            if pair is not None:
                git_head = pair.value
        if git_head:
            self.incremental_reindex(git_head)
        else:
            self.full_reindex()

    def incremental_reindex(self, git_head):
        print 'Starting incremental_reindex({!r})'.format(git_head)
        session = self.Session()
        with session.begin():
            for modes, fn in self.filedb.changed_files(git_head):
                cls = self.lookup_class(fn)
                if cls is None:
                    continue
                if 'D' in modes:
                    if cls is Enum:
                        typ = path_id(os.path.dirname(fn))
                        name = path_id(fn)
                        session.query(Enum).filter(and_(
                            Enum.type == path_id(os.path.dirname(fn)),
                            Enum.name == path_id(fn))).delete()
                    else:
                        pk = list(cls.__table__.primary_key.columns)[0]
                        session.query(cls).filter(pk == path_id(fn)).delete()
                else:
                    lst = self.from_disk(cls, fn)
                    if 'A' in modes:
                        session.add_all(lst)
                    else:
                        for obj in lst:
                            session.merge(obj)
            session.query(OfftracMeta).delete()
            session.add_all(self.ormify_offtrac_meta())

    def full_reindex(self):
        print 'Starting full_reindex()'
        session = self.Session()
        with session.begin():
            for Class in MODEL_CLASSES:
                session.query(Class).delete()
            session.add_all(self.ormify_fields())
            session.add_all(self.ormify_enum())
            session.add_all(self.ormify_ticket())
            session.add_all(self.ormify_report())
            session.add_all(self.ormify_changelog())
            session.add_all(self.ormify_offtrac_meta())

    def lookup_class(self, fn):
        parts = fn.split('/')
        if not (1 < len(parts) < 3):
            return None
        first = parts[0]
        if first == 'field':
            if parts[1] in self.ENUM_TYPES:
                return Enum
            return TABLE_CLASS_MAP.get(parts[1])
        elif first == 'changelog':
            return TicketChange
        return TABLE_CLASS_MAP.get(first)

    def from_disk(self, cls, fn):
        data = self.filedb.load_json(fn)
        if cls is Enum:
            data = dict(
                type=path_id(os.path.dirname(fn)),
                name=path_id(fn),
                value=data)
        elif cls is Milestone:
            data = dict(
                data,
                due=iso8601_to_trac_time(data['due']),
                completed=iso8601_to_trac_time(data['completed']))
        elif cls is Ticket:
            ticket_id, created, changed, props = data
            data = dict(props,
                id=ticket_id,
                time=iso8601_to_trac_time(created),
                changetime=iso8601_to_trac_time(changed))
        elif cls is TicketChange:
            return self._ticket_changes(path_id(fn), data)
        elif cls is Report:
            data = dict(
                id=path_id(fn),
                title=data['title'],
                query=data['sql'],
                author='',
                description='')
        return [cls(**data)]

    def _ticket_changes(self, ticket_id, data):
        bigtime = None
        for isotime, author, field, oldvalue, newvalue, _permanent in data:
            bigtime = new_bigtime(isotime, bigtime)
            yield TicketChange(
                ticket=ticket_id,
                time=bigtime,
                author=author,
                field=field,
                oldvalue=oldvalue,
                newvalue=newvalue)

    def ormify_offtrac_meta(self):
        yield OfftracMeta(key='git_head', value=self.filedb.git_head)
        for k, v in self.filedb.metadata.iteritems():
            yield OfftracMeta(key=k, value=v)

    def ormify_enum(self):
        for enum_type in self.ENUM_TYPES:
            for fn, data in self.filedb.iter_jsondir('field/' + enum_type):
                yield Enum(type=enum_type, name=path_id(fn), value=data)

    def ormify_fields(self):
        for FieldClass in FIELD_CLASSES:
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
            for obj in self._ticket_changes(path_id(fn), data):
                yield obj

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
    engine = get_engine(filedb)
    # model.metadata.create_all(engine)
    imp = ETL(filedb, get_session_class(engine=engine))
    imp.reindex()


if __name__ == '__main__':
    main()
