from sqlalchemy import *
from migrate import *


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    meta = MetaData(bind=migrate_engine)
    status = Table('status', meta, autoload=True)
    reply = Column('reply_to_id', Integer, ForeignKey('status.id'))
    reply.create(status)


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    meta = MetaData(bind=migrate_engine)
    status = Table('status', meta, autoload=True)
    status.c.reply_to_id.drop()