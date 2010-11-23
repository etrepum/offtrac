from sqlalchemy import MetaData, Table, Column, TEXT, Index, INTEGER
# In sqlite3 this does not matter, it supports 64-bit natively.
# In PostgreSQL we would care about the native type.
BIGINT = INTEGER

metadata = MetaData()

system =  Table('system', metadata,
    Column(u'name', TEXT(length=None, convert_unicode=False, assert_unicode=None, unicode_error=None, _warn_on_bytestring=False), primary_key=True, nullable=False),
    Column(u'value', TEXT(length=None, convert_unicode=False, assert_unicode=None, unicode_error=None, _warn_on_bytestring=False), primary_key=False),
)
Index('system_pkey', system.c.name, unique=True)


permission =  Table('permission', metadata,
    Column(u'username', TEXT(length=None, convert_unicode=False, assert_unicode=None, unicode_error=None, _warn_on_bytestring=False), primary_key=True, nullable=False),
    Column(u'action', TEXT(length=None, convert_unicode=False, assert_unicode=None, unicode_error=None, _warn_on_bytestring=False), primary_key=True, nullable=False),
)
Index('permission_pk', permission.c.username, permission.c.action, unique=True)


node_change =  Table('node_change', metadata,
    Column(u'repos', INTEGER(), primary_key=True, nullable=False),
    Column(u'rev', TEXT(length=None, convert_unicode=False, assert_unicode=None, unicode_error=None, _warn_on_bytestring=False), primary_key=True, nullable=False),
    Column(u'path', TEXT(length=None, convert_unicode=False, assert_unicode=None, unicode_error=None, _warn_on_bytestring=False), primary_key=True, nullable=False),
    Column(u'node_type', TEXT(length=None, convert_unicode=False, assert_unicode=None, unicode_error=None, _warn_on_bytestring=False), primary_key=False),
    Column(u'change_type', TEXT(length=None, convert_unicode=False, assert_unicode=None, unicode_error=None, _warn_on_bytestring=False), primary_key=True, nullable=False),
    Column(u'base_path', TEXT(length=None, convert_unicode=False, assert_unicode=None, unicode_error=None, _warn_on_bytestring=False), primary_key=False),
    Column(u'base_rev', TEXT(length=None, convert_unicode=False, assert_unicode=None, unicode_error=None, _warn_on_bytestring=False), primary_key=False),
)
Index(u'node_change_repos_rev_idx', node_change.c.repos, node_change.c.rev, unique=False)


auth_cookie =  Table('auth_cookie', metadata,
    Column(u'cookie', TEXT(length=None, convert_unicode=False, assert_unicode=None, unicode_error=None, _warn_on_bytestring=False), primary_key=True, nullable=False),
    Column(u'name', TEXT(length=None, convert_unicode=False, assert_unicode=None, unicode_error=None, _warn_on_bytestring=False), primary_key=True, nullable=False),
    Column(u'ipnr', TEXT(length=None, convert_unicode=False, assert_unicode=None, unicode_error=None, _warn_on_bytestring=False), primary_key=True, nullable=False),
    Column(u'time', INTEGER(), primary_key=False),
)
Index('auth_cookie_pk', auth_cookie.c.cookie, auth_cookie.c.ipnr, auth_cookie.c.name, unique=True)


session =  Table('session', metadata,
    Column(u'sid', TEXT(length=None, convert_unicode=False, assert_unicode=None, unicode_error=None, _warn_on_bytestring=False), primary_key=True, nullable=False),
    Column(u'authenticated', INTEGER(), primary_key=True, nullable=False),
    Column(u'last_visit', INTEGER(), primary_key=False),
)
Index(u'session_authenticated_idx', session.c.authenticated, unique=False)
Index(u'session_last_visit_idx', session.c.last_visit, unique=False)


session_attribute =  Table('session_attribute', metadata,
    Column(u'sid', TEXT(length=None, convert_unicode=False, assert_unicode=None, unicode_error=None, _warn_on_bytestring=False), primary_key=True, nullable=False),
    Column(u'authenticated', INTEGER(), primary_key=True, nullable=False),
    Column(u'name', TEXT(length=None, convert_unicode=False, assert_unicode=None, unicode_error=None, _warn_on_bytestring=False), primary_key=True, nullable=False),
    Column(u'value', TEXT(length=None, convert_unicode=False, assert_unicode=None, unicode_error=None, _warn_on_bytestring=False), primary_key=False),
)
Index('session_attribute_pk', session_attribute.c.sid, session_attribute.c.authenticated, session_attribute.c.name, unique=True)


attachment =  Table('attachment', metadata,
    Column(u'type', TEXT(length=None, convert_unicode=False, assert_unicode=None, unicode_error=None, _warn_on_bytestring=False), primary_key=True, nullable=False),
    Column(u'id', TEXT(length=None, convert_unicode=False, assert_unicode=None, unicode_error=None, _warn_on_bytestring=False), primary_key=True, nullable=False),
    Column(u'filename', TEXT(length=None, convert_unicode=False, assert_unicode=None, unicode_error=None, _warn_on_bytestring=False), primary_key=True, nullable=False),
    Column(u'size', INTEGER(), primary_key=False),
    Column(u'time', BIGINT(), primary_key=False),
    Column(u'description', TEXT(length=None, convert_unicode=False, assert_unicode=None, unicode_error=None, _warn_on_bytestring=False), primary_key=False),
    Column(u'author', TEXT(length=None, convert_unicode=False, assert_unicode=None, unicode_error=None, _warn_on_bytestring=False), primary_key=False),
    Column(u'ipnr', TEXT(length=None, convert_unicode=False, assert_unicode=None, unicode_error=None, _warn_on_bytestring=False), primary_key=False),
)
Index('attachment_pk', attachment.c.type, attachment.c.id, attachment.c.filename, unique=True)


wiki =  Table('wiki', metadata,
    Column(u'name', TEXT(length=None, convert_unicode=False, assert_unicode=None, unicode_error=None, _warn_on_bytestring=False), primary_key=True, nullable=False),
    Column(u'version', INTEGER(), primary_key=True, nullable=False),
    Column(u'time', BIGINT(), primary_key=False),
    Column(u'author', TEXT(length=None, convert_unicode=False, assert_unicode=None, unicode_error=None, _warn_on_bytestring=False), primary_key=False),
    Column(u'ipnr', TEXT(length=None, convert_unicode=False, assert_unicode=None, unicode_error=None, _warn_on_bytestring=False), primary_key=False),
    Column(u'text', TEXT(length=None, convert_unicode=False, assert_unicode=None, unicode_error=None, _warn_on_bytestring=False), primary_key=False),
    Column(u'comment', TEXT(length=None, convert_unicode=False, assert_unicode=None, unicode_error=None, _warn_on_bytestring=False), primary_key=False),
    Column(u'readonly', INTEGER(), primary_key=False),
)
Index(u'wiki_time_idx', wiki.c.time, unique=False)


ticket =  Table('ticket', metadata,
    Column(u'id', INTEGER(), primary_key=True, nullable=False),
    Column(u'type', TEXT(length=None, convert_unicode=False, assert_unicode=None, unicode_error=None, _warn_on_bytestring=False), primary_key=False),
    Column(u'time', BIGINT(), primary_key=False),
    Column(u'changetime', BIGINT(), primary_key=False),
    Column(u'component', TEXT(length=None, convert_unicode=False, assert_unicode=None, unicode_error=None, _warn_on_bytestring=False), primary_key=False),
    Column(u'severity', TEXT(length=None, convert_unicode=False, assert_unicode=None, unicode_error=None, _warn_on_bytestring=False), primary_key=False),
    Column(u'priority', TEXT(length=None, convert_unicode=False, assert_unicode=None, unicode_error=None, _warn_on_bytestring=False), primary_key=False),
    Column(u'owner', TEXT(length=None, convert_unicode=False, assert_unicode=None, unicode_error=None, _warn_on_bytestring=False), primary_key=False),
    Column(u'reporter', TEXT(length=None, convert_unicode=False, assert_unicode=None, unicode_error=None, _warn_on_bytestring=False), primary_key=False),
    Column(u'cc', TEXT(length=None, convert_unicode=False, assert_unicode=None, unicode_error=None, _warn_on_bytestring=False), primary_key=False),
    Column(u'version', TEXT(length=None, convert_unicode=False, assert_unicode=None, unicode_error=None, _warn_on_bytestring=False), primary_key=False),
    Column(u'milestone', TEXT(length=None, convert_unicode=False, assert_unicode=None, unicode_error=None, _warn_on_bytestring=False), primary_key=False),
    Column(u'status', TEXT(length=None, convert_unicode=False, assert_unicode=None, unicode_error=None, _warn_on_bytestring=False), primary_key=False),
    Column(u'resolution', TEXT(length=None, convert_unicode=False, assert_unicode=None, unicode_error=None, _warn_on_bytestring=False), primary_key=False),
    Column(u'summary', TEXT(length=None, convert_unicode=False, assert_unicode=None, unicode_error=None, _warn_on_bytestring=False), primary_key=False),
    Column(u'description', TEXT(length=None, convert_unicode=False, assert_unicode=None, unicode_error=None, _warn_on_bytestring=False), primary_key=False),
    Column(u'keywords', TEXT(length=None, convert_unicode=False, assert_unicode=None, unicode_error=None, _warn_on_bytestring=False), primary_key=False),
)
Index(u'ticket_time_idx', ticket.c.time, unique=False)
Index(u'ticket_status_idx', ticket.c.status, unique=False)


version =  Table('version', metadata,
    Column(u'name', TEXT(length=None, convert_unicode=False, assert_unicode=None, unicode_error=None, _warn_on_bytestring=False), primary_key=True, nullable=False),
    Column(u'time', BIGINT(), primary_key=False),
    Column(u'description', TEXT(length=None, convert_unicode=False, assert_unicode=None, unicode_error=None, _warn_on_bytestring=False), primary_key=False),
)
Index('version_pkey', version.c.name, unique=True)


report =  Table('report', metadata,
    Column(u'id', INTEGER(), primary_key=True, nullable=False),
    Column(u'author', TEXT(length=None, convert_unicode=False, assert_unicode=None, unicode_error=None, _warn_on_bytestring=False), primary_key=False),
    Column(u'title', TEXT(length=None, convert_unicode=False, assert_unicode=None, unicode_error=None, _warn_on_bytestring=False), primary_key=False),
    Column(u'query', TEXT(length=None, convert_unicode=False, assert_unicode=None, unicode_error=None, _warn_on_bytestring=False), primary_key=False),
    Column(u'description', TEXT(length=None, convert_unicode=False, assert_unicode=None, unicode_error=None, _warn_on_bytestring=False), primary_key=False),
)
Index('report_pkey', report.c.id, unique=True)


ticket_change =  Table('ticket_change', metadata,
    Column(u'ticket', INTEGER(), primary_key=True, nullable=False),
    Column(u'time', BIGINT(), primary_key=True, nullable=False),
    Column(u'author', TEXT(length=None, convert_unicode=False, assert_unicode=None, unicode_error=None, _warn_on_bytestring=False), primary_key=False),
    Column(u'field', TEXT(length=None, convert_unicode=False, assert_unicode=None, unicode_error=None, _warn_on_bytestring=False), primary_key=True, nullable=False),
    Column(u'oldvalue', TEXT(length=None, convert_unicode=False, assert_unicode=None, unicode_error=None, _warn_on_bytestring=False), primary_key=False),
    Column(u'newvalue', TEXT(length=None, convert_unicode=False, assert_unicode=None, unicode_error=None, _warn_on_bytestring=False), primary_key=False),
)
Index(u'ticket_change_ticket_idx', ticket_change.c.ticket, unique=False)
Index(u'ticket_change_time_idx', ticket_change.c.time, unique=False)


cache =  Table('cache', metadata,
    Column(u'id', TEXT(length=None, convert_unicode=False, assert_unicode=None, unicode_error=None, _warn_on_bytestring=False), primary_key=True, nullable=False),
    Column(u'generation', INTEGER(), primary_key=False),
)
Index('cache_pkey', cache.c.id, unique=True)


ticket_custom =  Table('ticket_custom', metadata,
    Column(u'ticket', INTEGER(), primary_key=True, nullable=False),
    Column(u'name', TEXT(length=None, convert_unicode=False, assert_unicode=None, unicode_error=None, _warn_on_bytestring=False), primary_key=True, nullable=False),
    Column(u'value', TEXT(length=None, convert_unicode=False, assert_unicode=None, unicode_error=None, _warn_on_bytestring=False), primary_key=False),
)
Index('ticket_custom_pk', ticket_custom.c.ticket, ticket_custom.c.name, unique=True)


enum =  Table('enum', metadata,
    Column(u'type', TEXT(length=None, convert_unicode=False, assert_unicode=None, unicode_error=None, _warn_on_bytestring=False), primary_key=True, nullable=False),
    Column(u'name', TEXT(length=None, convert_unicode=False, assert_unicode=None, unicode_error=None, _warn_on_bytestring=False), primary_key=True, nullable=False),
    Column(u'value', TEXT(length=None, convert_unicode=False, assert_unicode=None, unicode_error=None, _warn_on_bytestring=False), primary_key=False),
)
Index('enum_pk', enum.c.type, enum.c.name, unique=True)


component =  Table('component', metadata,
    Column(u'name', TEXT(length=None, convert_unicode=False, assert_unicode=None, unicode_error=None, _warn_on_bytestring=False), primary_key=True, nullable=False),
    Column(u'owner', TEXT(length=None, convert_unicode=False, assert_unicode=None, unicode_error=None, _warn_on_bytestring=False), primary_key=False),
    Column(u'description', TEXT(length=None, convert_unicode=False, assert_unicode=None, unicode_error=None, _warn_on_bytestring=False), primary_key=False),
)
Index('component_pkey', component.c.name, unique=True)


repository =  Table('repository', metadata,
    Column(u'id', INTEGER(), primary_key=True, nullable=False),
    Column(u'name', TEXT(length=None, convert_unicode=False, assert_unicode=None, unicode_error=None, _warn_on_bytestring=False), primary_key=True, nullable=False),
    Column(u'value', TEXT(length=None, convert_unicode=False, assert_unicode=None, unicode_error=None, _warn_on_bytestring=False), primary_key=False),
)
Index('repository_pk', repository.c.id, repository.c.name, unique=True)


milestone =  Table('milestone', metadata,
    Column(u'name', TEXT(length=None, convert_unicode=False, assert_unicode=None, unicode_error=None, _warn_on_bytestring=False), primary_key=True, nullable=False),
    Column(u'due', BIGINT(), primary_key=False),
    Column(u'completed', BIGINT(), primary_key=False),
    Column(u'description', TEXT(length=None, convert_unicode=False, assert_unicode=None, unicode_error=None, _warn_on_bytestring=False), primary_key=False),
)
Index('milestone_pkey', milestone.c.name, unique=True)


revision =  Table('revision', metadata,
    Column(u'repos', INTEGER(), primary_key=True, nullable=False),
    Column(u'rev', TEXT(length=None, convert_unicode=False, assert_unicode=None, unicode_error=None, _warn_on_bytestring=False), primary_key=True, nullable=False),
    Column(u'time', BIGINT(), primary_key=False),
    Column(u'author', TEXT(length=None, convert_unicode=False, assert_unicode=None, unicode_error=None, _warn_on_bytestring=False), primary_key=False),
    Column(u'message', TEXT(length=None, convert_unicode=False, assert_unicode=None, unicode_error=None, _warn_on_bytestring=False), primary_key=False),
)
Index(u'revision_repos_time_idx', revision.c.repos, revision.c.time, unique=False)

