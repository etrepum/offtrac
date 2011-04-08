from sqlalchemy import MetaData, Table, Column, TEXT, Index, INTEGER
# In sqlite3 this does not matter, it supports 64-bit natively.
# In PostgreSQL we would care about the native type.
BIGINT = INTEGER

metadata = MetaData()

offtrac_meta = Table('offtrac_meta', metadata,
    Column(u'key', TEXT(), primary_key=True),
    Column(u'value', TEXT()))

attachment =  Table('attachment', metadata,
    Column(u'type', TEXT(), primary_key=True, nullable=False),
    Column(u'id', TEXT(), primary_key=True, nullable=False),
    Column(u'filename', TEXT(), primary_key=True, nullable=False),
    Column(u'size', INTEGER()),
    Column(u'time', BIGINT()),
    Column(u'description', TEXT()),
    Column(u'author', TEXT()),
    Column(u'ipnr', TEXT()),
)
Index('attachment_pk', attachment.c.type, attachment.c.id, attachment.c.filename, unique=True)


wiki =  Table('wiki', metadata,
    Column(u'name', TEXT(), primary_key=True, nullable=False),
    Column(u'version', INTEGER(), primary_key=True, nullable=False),
    Column(u'time', BIGINT()),
    Column(u'author', TEXT()),
    Column(u'ipnr', TEXT()),
    Column(u'text', TEXT()),
    Column(u'comment', TEXT()),
    Column(u'readonly', INTEGER()),
)
Index(u'wiki_time_idx', wiki.c.time, unique=False)


ticket =  Table('ticket', metadata,
    Column(u'id', INTEGER(), primary_key=True, nullable=False),
    Column(u'type', TEXT()),
    Column(u'time', BIGINT()),
    Column(u'changetime', BIGINT()),
    Column(u'component', TEXT()),
    Column(u'severity', TEXT()),
    Column(u'priority', TEXT()),
    Column(u'owner', TEXT()),
    Column(u'reporter', TEXT()),
    Column(u'cc', TEXT()),
    Column(u'version', TEXT()),
    Column(u'milestone', TEXT()),
    Column(u'status', TEXT()),
    Column(u'resolution', TEXT()),
    Column(u'summary', TEXT()),
    Column(u'description', TEXT()),
    Column(u'keywords', TEXT()),
)
Index(u'ticket_time_idx', ticket.c.time, unique=False)
Index(u'ticket_status_idx', ticket.c.status, unique=False)


version =  Table('version', metadata,
    Column(u'name', TEXT(), primary_key=True, nullable=False),
    Column(u'time', BIGINT()),
    Column(u'description', TEXT()),
)
Index('version_pkey', version.c.name, unique=True)


report =  Table('report', metadata,
    Column(u'id', INTEGER(), primary_key=True, nullable=False),
    Column(u'author', TEXT()),
    Column(u'title', TEXT()),
    Column(u'query', TEXT()),
    Column(u'description', TEXT()),
)
Index('report_pkey', report.c.id, unique=True)


ticket_change =  Table('ticket_change', metadata,
    Column(u'ticket', INTEGER(), primary_key=True, nullable=False),
    Column(u'time', BIGINT(), primary_key=True, nullable=False),
    Column(u'author', TEXT()),
    Column(u'field', TEXT(), primary_key=True, nullable=False),
    Column(u'oldvalue', TEXT()),
    Column(u'newvalue', TEXT()),
)
Index(u'ticket_change_ticket_idx', ticket_change.c.ticket, unique=False)
Index(u'ticket_change_time_idx', ticket_change.c.time, unique=False)


ticket_custom =  Table('ticket_custom', metadata,
    Column(u'ticket', INTEGER(), primary_key=True, nullable=False),
    Column(u'name', TEXT(), primary_key=True, nullable=False),
    Column(u'value', TEXT()),
)
Index('ticket_custom_pk', ticket_custom.c.ticket, ticket_custom.c.name, unique=True)


enum =  Table('enum', metadata,
    Column(u'type', TEXT(), primary_key=True, nullable=False),
    Column(u'name', TEXT(), primary_key=True, nullable=False),
    Column(u'value', TEXT()),
)
Index('enum_pk', enum.c.type, enum.c.name, unique=True)


component =  Table('component', metadata,
    Column(u'name', TEXT(), primary_key=True, nullable=False),
    Column(u'owner', TEXT()),
    Column(u'description', TEXT()),
)
Index('component_pkey', component.c.name, unique=True)


repository =  Table('repository', metadata,
    Column(u'id', INTEGER(), primary_key=True, nullable=False),
    Column(u'name', TEXT(), primary_key=True, nullable=False),
    Column(u'value', TEXT()),
)
Index('repository_pk', repository.c.id, repository.c.name, unique=True)


milestone =  Table('milestone', metadata,
    Column(u'name', TEXT(), primary_key=True, nullable=False),
    Column(u'due', BIGINT()),
    Column(u'completed', BIGINT()),
    Column(u'description', TEXT()),
)
Index('milestone_pkey', milestone.c.name, unique=True)


revision =  Table('revision', metadata,
    Column(u'repos', INTEGER(), primary_key=True, nullable=False),
    Column(u'rev', TEXT(), primary_key=True, nullable=False),
    Column(u'time', BIGINT()),
    Column(u'author', TEXT()),
    Column(u'message', TEXT()),
)
Index(u'revision_repos_time_idx', revision.c.repos, revision.c.time, unique=False)

