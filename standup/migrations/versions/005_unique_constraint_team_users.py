from migrate.changeset.constraint import UniqueConstraint
from sqlalchemy import Column, ForeignKey, Integer, MetaData, Table, String, Boolean


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

team_users = Table('team_users', meta,
                   Column('team_id', Integer, ForeignKey('team.id')),
                   Column('user_id', Integer, ForeignKey('user.id')))
constraint = UniqueConstraint('team_id', 'user_id', table=team_users)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    meta.bind = migrate_engine
    constraint.create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    meta.bind = migrate_engine
    constraint.drop()
