from sqlalchemy import *


meta = MetaData()


team_users = Table('team_users', meta,
                   Column('team_id', Integer, ForeignKey('team.id')),
                   Column('user_id', Integer, ForeignKey('user.id')))


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    meta.bind = migrate_engine

    team = Table('team', meta, autoload=True)
    user = Table('user', meta, autoload=True)

    try:
        team_users.drop()
    except:
        pass
    team_users.create()

    result = user.select().execute().fetchall()

    for row in result:
        if row.team_id:
            values = {'team_id': row.team_id, 'user_id': row.id}
            team_users.insert(values=values).execute()

    user.c.team_id.drop()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    meta.bind = migrate_engine

    team = Table('team', meta, autoload=True)
    user = Table('user', meta, autoload=True)

    team_id = Column('team_id', Integer, ForeignKey('team.id'))
    team_id.create(user)

    result = team_users.select().execute().fetchall()

    for row in result:
        values = {'team_id': row.team_id}
        user.update(values=values).where(user.c.id == row.user_id).execute()

    team_users.drop()
