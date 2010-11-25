from sqlalchemy import *
from migrate import *

from migrate.changeset import schema
meta = MetaData()
session_attribute = Table('session_attribute', meta,
  Column('sid', Text(length=None, convert_unicode=False, assert_unicode=None, unicode_error=None, _warn_on_bytestring=False),  primary_key=True, nullable=False),
  Column('authenticated', Integer(),  primary_key=True, nullable=False),
  Column('name', Text(length=None, convert_unicode=False, assert_unicode=None, unicode_error=None, _warn_on_bytestring=False),  primary_key=True, nullable=False),
  Column('value', Text(length=None, convert_unicode=False, assert_unicode=None, unicode_error=None, _warn_on_bytestring=False)),
)
auth_cookie = Table('auth_cookie', meta,
  Column('cookie', Text(length=None, convert_unicode=False, assert_unicode=None, unicode_error=None, _warn_on_bytestring=False),  primary_key=True, nullable=False),
  Column('name', Text(length=None, convert_unicode=False, assert_unicode=None, unicode_error=None, _warn_on_bytestring=False),  primary_key=True, nullable=False),
  Column('ipnr', Text(length=None, convert_unicode=False, assert_unicode=None, unicode_error=None, _warn_on_bytestring=False),  primary_key=True, nullable=False),
  Column('time', Integer()),
)
permission = Table('permission', meta,
  Column('username', Text(length=None, convert_unicode=False, assert_unicode=None, unicode_error=None, _warn_on_bytestring=False),  primary_key=True, nullable=False),
  Column('action', Text(length=None, convert_unicode=False, assert_unicode=None, unicode_error=None, _warn_on_bytestring=False),  primary_key=True, nullable=False),
)
node_change = Table('node_change', meta,
  Column('repos', Integer(),  primary_key=True, nullable=False),
  Column('rev', Text(length=None, convert_unicode=False, assert_unicode=None, unicode_error=None, _warn_on_bytestring=False),  primary_key=True, nullable=False),
  Column('path', Text(length=None, convert_unicode=False, assert_unicode=None, unicode_error=None, _warn_on_bytestring=False),  primary_key=True, nullable=False),
  Column('node_type', Text(length=None, convert_unicode=False, assert_unicode=None, unicode_error=None, _warn_on_bytestring=False)),
  Column('change_type', Text(length=None, convert_unicode=False, assert_unicode=None, unicode_error=None, _warn_on_bytestring=False),  primary_key=True, nullable=False),
  Column('base_path', Text(length=None, convert_unicode=False, assert_unicode=None, unicode_error=None, _warn_on_bytestring=False)),
  Column('base_rev', Text(length=None, convert_unicode=False, assert_unicode=None, unicode_error=None, _warn_on_bytestring=False)),
)
cache = Table('cache', meta,
  Column('id', Text(length=None, convert_unicode=False, assert_unicode=None, unicode_error=None, _warn_on_bytestring=False),  primary_key=True, nullable=False),
  Column('generation', Integer()),
)
system = Table('system', meta,
  Column('name', Text(length=None, convert_unicode=False, assert_unicode=None, unicode_error=None, _warn_on_bytestring=False),  primary_key=True, nullable=False),
  Column('value', Text(length=None, convert_unicode=False, assert_unicode=None, unicode_error=None, _warn_on_bytestring=False)),
)
session = Table('session', meta,
  Column('sid', Text(length=None, convert_unicode=False, assert_unicode=None, unicode_error=None, _warn_on_bytestring=False),  primary_key=True, nullable=False),
  Column('authenticated', Integer(),  primary_key=True, nullable=False),
  Column('last_visit', Integer()),
)

def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind migrate_engine
    # to your metadata
    meta.bind = migrate_engine
    session_attribute.drop()
    auth_cookie.drop()
    permission.drop()
    node_change.drop()
    cache.drop()
    system.drop()
    session.drop()

def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    meta.bind = migrate_engine
    session_attribute.create()
    auth_cookie.create()
    permission.create()
    node_change.create()
    cache.create()
    system.create()
    session.create()

