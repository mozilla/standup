from migrate.changeset.constraint import UniqueConstraint
from sqlalchemy import Column, ForeignKey, Integer, MetaData, Table


meta = MetaData()


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
