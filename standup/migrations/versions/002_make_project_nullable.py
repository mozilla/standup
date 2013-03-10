from sqlalchemy import *


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    meta = MetaData(bind=migrate_engine)
    status = Table('status', meta, autoload=True)
    status.c.project_id.alter(nullable=True)


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    meta = MetaData(bind=migrate_engine)
    status = Table('status', meta, autoload=True)
    status.c.project_id.alter(nullable=False)
