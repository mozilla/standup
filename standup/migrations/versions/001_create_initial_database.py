from datetime import datetime
from sqlalchemy import *

meta = MetaData()

team = Table('team', meta,
             Column('id', Integer, primary_key=True),
             Column('name', String(100)),
             Column('slug', String(100), unique=True))

user = Table('user', meta,
             Column('id', Integer, primary_key=True),
             Column('username', String(100), unique=True),
             Column('name', String(100)),
             Column('slug', String(100), unique=True),
             Column('email', String(100), unique=True),
             Column('github_handle', String(100), unique=True),
             Column('is_admin', Boolean, default=False),
             Column('team_id', Integer, ForeignKey('team.id')))

project = Table('project', meta,
                Column('id', Integer, primary_key=True),
                Column('name', String(100)),
                Column('slug', String(100), unique=True),
                Column('color', String(6)),
                Column('repo_url', String(100)))

status = Table('status', meta,
               Column('id', Integer, primary_key=True),
               Column('created', DateTime, default=datetime.utcnow()),
               Column('user_id', Integer, ForeignKey('user.id')),
               Column('project_id', Integer, ForeignKey('project.id'),
                      nullable=False),
               Column('content', Text),
               Column('content_html', Text))


def upgrade(migrate_engine):
    """Add the color and repo_url fields to the project table """
    meta.bind = migrate_engine
    team.create()
    user.create()
    project.create()
    status.create()


def downgrade(migrate_engine):
    """Remove the color and repo_url fields from the project table"""
    meta.bind = migrate_engine
    status.drop()
    project.drop()
    user.drop()
    team.drop()
