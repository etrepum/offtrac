from sqlalchemy import MetaData, Table, Column, TEXT, Index, INTEGER
# In sqlite3 this does not matter, it supports 64-bit natively.
# In PostgreSQL we would care about the native type.
BIGINT = INTEGER

metadata = MetaData()

def DEFAULT_TEXT():
    return TEXT(
        length=None, convert_unicode=False, assert_unicode=None,
        unicode_error=None, _warn_on_bytestring=False)

offtrac_meta = Table('offtrac_meta', metadata,
    Column(u'key', TEXT(), primary_key=True),
    Column(u'value', TEXT()))

attachment =  Table('attachment', metadata,
    Column(u'type', DEFAULT_TEXT(), primary_key=True, nullable=False),
    Column(u'id', DEFAULT_TEXT(), primary_key=True, nullable=False),
    Column(u'filename', DEFAULT_TEXT(), primary_key=True, nullable=False),
    Column(u'size', INTEGER()),
    Column(u'time', BIGINT()),
    Column(u'description', DEFAULT_TEXT()),
    Column(u'author', DEFAULT_TEXT()),
    Column(u'ipnr', DEFAULT_TEXT()),
)
Index('attachment_pk', attachment.c.type, attachment.c.id, attachment.c.filename, unique=True)


wiki =  Table('wiki', metadata,
    Column(u'name', DEFAULT_TEXT(), primary_key=True, nullable=False),
    Column(u'version', INTEGER(), primary_key=True, nullable=False),
    Column(u'time', BIGINT()),
    Column(u'author', DEFAULT_TEXT()),
    Column(u'ipnr', DEFAULT_TEXT()),
    Column(u'text', DEFAULT_TEXT()),
    Column(u'comment', DEFAULT_TEXT()),
    Column(u'readonly', INTEGER()),
)
Index(u'wiki_time_idx', wiki.c.time, unique=False)


ticket =  Table('ticket', metadata,
    Column(u'id', INTEGER(), primary_key=True, nullable=False),
    Column(u'type', DEFAULT_TEXT()),
    Column(u'time', BIGINT()),
    Column(u'changetime', BIGINT()),
    Column(u'component', DEFAULT_TEXT()),
    Column(u'severity', DEFAULT_TEXT()),
    Column(u'priority', DEFAULT_TEXT()),
    Column(u'owner', DEFAULT_TEXT()),
    Column(u'reporter', DEFAULT_TEXT()),
    Column(u'cc', DEFAULT_TEXT()),
    Column(u'version', DEFAULT_TEXT()),
    Column(u'milestone', DEFAULT_TEXT()),
    Column(u'status', DEFAULT_TEXT()),
    Column(u'resolution', DEFAULT_TEXT()),
    Column(u'summary', DEFAULT_TEXT()),
    Column(u'description', DEFAULT_TEXT()),
    Column(u'keywords', DEFAULT_TEXT()),
)
Index(u'ticket_time_idx', ticket.c.time, unique=False)
Index(u'ticket_status_idx', ticket.c.status, unique=False)


version =  Table('version', metadata,
    Column(u'name', DEFAULT_TEXT(), primary_key=True, nullable=False),
    Column(u'time', BIGINT()),
    Column(u'description', DEFAULT_TEXT()),
)
Index('version_pkey', version.c.name, unique=True)


report =  Table('report', metadata,
    Column(u'id', INTEGER(), primary_key=True, nullable=False),
    Column(u'author', DEFAULT_TEXT()),
    Column(u'title', DEFAULT_TEXT()),
    Column(u'query', DEFAULT_TEXT()),
    Column(u'description', DEFAULT_TEXT()),
)
Index('report_pkey', report.c.id, unique=True)


ticket_change =  Table('ticket_change', metadata,
    Column(u'ticket', INTEGER(), primary_key=True, nullable=False),
    Column(u'time', BIGINT(), primary_key=True, nullable=False),
    Column(u'author', DEFAULT_TEXT()),
    Column(u'field', DEFAULT_TEXT(), primary_key=True, nullable=False),
    Column(u'oldvalue', DEFAULT_TEXT()),
    Column(u'newvalue', DEFAULT_TEXT()),
)
Index(u'ticket_change_ticket_idx', ticket_change.c.ticket, unique=False)
Index(u'ticket_change_time_idx', ticket_change.c.time, unique=False)


ticket_custom =  Table('ticket_custom', metadata,
    Column(u'ticket', INTEGER(), primary_key=True, nullable=False),
    Column(u'name', DEFAULT_TEXT(), primary_key=True, nullable=False),
    Column(u'value', DEFAULT_TEXT()),
)
Index('ticket_custom_pk', ticket_custom.c.ticket, ticket_custom.c.name, unique=True)


enum =  Table('enum', metadata,
    Column(u'type', DEFAULT_TEXT(), primary_key=True, nullable=False),
    Column(u'name', DEFAULT_TEXT(), primary_key=True, nullable=False),
    Column(u'value', DEFAULT_TEXT()),
)
Index('enum_pk', enum.c.type, enum.c.name, unique=True)


component =  Table('component', metadata,
    Column(u'name', DEFAULT_TEXT(), primary_key=True, nullable=False),
    Column(u'owner', DEFAULT_TEXT()),
    Column(u'description', DEFAULT_TEXT()),
)
Index('component_pkey', component.c.name, unique=True)


repository =  Table('repository', metadata,
    Column(u'id', INTEGER(), primary_key=True, nullable=False),
    Column(u'name', DEFAULT_TEXT(), primary_key=True, nullable=False),
    Column(u'value', DEFAULT_TEXT()),
)
Index('repository_pk', repository.c.id, repository.c.name, unique=True)


milestone =  Table('milestone', metadata,
    Column(u'name', DEFAULT_TEXT(), primary_key=True, nullable=False),
    Column(u'due', BIGINT()),
    Column(u'completed', BIGINT()),
    Column(u'description', DEFAULT_TEXT()),
)
Index('milestone_pkey', milestone.c.name, unique=True)


revision =  Table('revision', metadata,
    Column(u'repos', INTEGER(), primary_key=True, nullable=False),
    Column(u'rev', DEFAULT_TEXT(), primary_key=True, nullable=False),
    Column(u'time', BIGINT()),
    Column(u'author', DEFAULT_TEXT()),
    Column(u'message', DEFAULT_TEXT()),
)
Index(u'revision_repos_time_idx', revision.c.repos, revision.c.time, unique=False)

