from flask import current_app
from sqlalchemy import (Boolean, Column, desc, ForeignKey, Integer, String,
                        Table)
from sqlalchemy.orm import backref, relationship
from standup import OrderedDict
from standup.apps.status.models import Status
from standup.apps.status.helpers import paginate
from standup.database import get_session
from standup.database.classes import Model


class Team(Model):
    """A team of users in the organization."""
    __tablename__ = 'team'

    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    slug = Column(String(100), unique=True)

    def __repr__(self):
        return '<Team: %s>' % self.name

    def recent_statuses(self, page=1, startdate=None, enddate=None):
        """Return a single page of the most recent statuses from this team."""
        statuses = self.statuses().filter_by(reply_to=None)\
            .order_by(desc(Status.created))
        return paginate(statuses, page, startdate, enddate)

    def statuses(self):
        """Return all statuses from this team."""
        db = get_session(current_app)
        user_ids = [u.id for u in self.users]
        return db.query(Status).filter(Status.user_id.in_(user_ids))


class User(Model):
    """A standup participant."""
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    username = Column(String(100), unique=True)
    name = Column(String(100))
    slug = Column(String(100), unique=True)
    email = Column(String(100), unique=True)
    github_handle = Column(String(100), unique=True)
    is_admin = Column(Boolean, default=False)
    team_users = Table('team_users', Model.metadata,
                       Column('team_id', Integer, ForeignKey('team.id')),
                       Column('user_id', Integer, ForeignKey('user.id')))
    teams = relationship('Team', secondary=team_users,
                         backref=backref('users', lazy='dynamic'))

    def __repr__(self):
        return '<User: [%s] %s>' % (self.username, self.name)

    def recent_statuses(self, page=1, startdate=None, enddate=None):
        """Return a single page of the most recent statuses from this user."""
        statuses = self.statuses.filter_by(reply_to=None)\
            .order_by(desc(Status.created))
        return paginate(statuses, page, startdate, enddate)

    def export(self):
        data = OrderedDict()
        data['id'] = self.id
        data['username'] = self.username
        data['name'] = self.name
        data['slug'] = self.slug
        data['email'] = self.email
        data['github_handle'] = self.github_handle
        data['is_admin'] = self.is_admin
        return data
