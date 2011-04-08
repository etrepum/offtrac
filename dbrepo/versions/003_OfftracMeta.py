from sqlalchemy import *
from migrate import *

from migrate.changeset import schema
meta = MetaData()
offtrac_meta = Table('offtrac_meta', meta,
    Column(u'key', TEXT(), primary_key=True),
    Column(u'value', TEXT()))


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind migrate_engine
    # to your metadata
    meta.bind = migrate_engine
    offtrac_meta.create()

def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    meta.bind = migrate_engine
    offtrac_meta.drop()