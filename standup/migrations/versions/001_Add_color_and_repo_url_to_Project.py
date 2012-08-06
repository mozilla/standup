from sqlalchemy import *
from migrate import *

def upgrade(migrate_engine):
    """Add the color and repo_url fields to the project table """
    meta = MetaData(bind=migrate_engine)
    project = Table('project', meta, autoload=True)
    color = Column('color', String(6))
    repo_url = Column('repo_url', String(100))
    color.create(project)
    repo_url.create(project)

def downgrade(migrate_engine):
    """Remove the color and repo_url fields from the project table"""
    meta = MetaData(bind=migrate_engine)
    project = Table('project', meta, autoload=True)
    project.c.color.drop()
    project.c.repo_url.drop()