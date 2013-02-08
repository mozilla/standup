from sqlalchemy import *
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql.expression import ColumnClause
from migrate import *

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

    # Create a session
    Session = sessionmaker(bind=migrate_engine)
    session = Session()

    for u in session.query(user).all():
        if u.team_id:
            values={'team_id': u.team_id, 'user_id': u.id,}
            team_users.insert(values=values).execute()

    user.c.team_id.drop()

def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    meta.bind = migrate_engine

    team = Table('team', meta, autoload=True)
    user = Table('user', meta, autoload=True)

    team_id = Column('team_id', Integer, ForeignKey('team.id'))
    team_id.create(user)

    # Create a session
    Session = sessionmaker(bind=migrate_engine)
    session = Session()

    for team_user in session.query(team_users).all():
        values = {'team_id': team_user.team_id}
        user.update(values=values).where(user.c.id==team_user.user_id).execute()

    session.commit()

    team_users.drop()
