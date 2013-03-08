from datetime import datetime

from flask import current_app
from sqlalchemy import (asc, Column, DateTime, desc, ForeignKey, Integer,
                        String, Text)
from sqlalchemy.orm import backref, relationship
from standup.apps.status.helpers import paginate
from standup.database import get_session
from standup.database.classes import Model


class Project(Model):
    """A project that does standups."""
    __tablename__ = 'project'

    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    slug = Column(String(100), unique=True)
    color = Column('color', String(6))
    repo_url = Column('repo_url', String(100))

    def __repr__(self):
        return '<Project: [%s] %s>' % (self.slug, self.name)

    def recent_statuses(self, page=1, startdate=None, enddate=None):
        """Return the statuses for the project."""
        statuses = self.statuses.filter(Status.reply_to == None).order_by(
            desc(Status.created))
        return paginate(statuses, page, startdate, enddate)


class Status(Model):
    """A standup update for a user on a given project."""
    __tablename__ = 'status'

    id = Column(Integer, primary_key=True)
    created = Column(DateTime, default=datetime.utcnow)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(
        'User', backref=backref('statuses', lazy='dynamic'))
    project_id = Column(Integer, ForeignKey('project.id'))
    project = relationship(
        'Project', backref=backref('statuses', lazy='dynamic'))
    content = Column(Text)
    content_html = Column(Text)
    reply_to_id = Column(Integer, ForeignKey('status.id'))
    reply_to = relationship('Status', remote_side=[id])

    def __repr__(self):
        return '<Status: %s: %s>' % (self.user.username, self.content)

    def replies(self, page=1):
        db = get_session(current_app)
        replies = db.query(Status).filter(Status.reply_to_id == self.id).order_by(
            asc(Status.created))
        return paginate(replies, page)
