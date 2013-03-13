from datetime import datetime

from flask import current_app
from sqlalchemy import (asc, Column, DateTime, desc, ForeignKey, Integer,
                        String, Text)
from sqlalchemy.orm import backref, relationship
from standup import OrderedDict
from standup.apps.status.helpers import paginate
from standup.database import get_session
from standup.database.classes import Model
from standup.filters import format_update


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
        statuses = self.statuses.filter_by(reply_to=None)\
            .order_by(desc(Status.created))
        return paginate(statuses, page, startdate, enddate)

    def dictify(self):
        """Returns an OrderedDict of model attributes"""
        data = OrderedDict()
        data['id'] = self.id
        data['name'] = self.name
        data['slug'] = self.slug
        data['color'] = self.color
        return data


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
        replies = db.query(Status).filter_by(reply_to_id=self.id)\
            .order_by(asc(Status.created))
        return paginate(replies, page)

    @property
    def reply_count(self):
        db = get_session(current_app)
        return db.query(Status).filter(Status.reply_to_id == self.id).count()

    def dictify(self, trim_user=False, trim_project=False):
        """Returns an OrderedDict of model attributes"""
        if self.reply_to:
            reply_to_user_id = self.reply_to.user.id
            reply_to_username = self.reply_to.user.username
        else:
            reply_to_user_id = None
            reply_to_username = None

        data = OrderedDict()
        data['id'] = self.id
        data['created'] = self.created.isoformat()
        if self.user:
            if trim_user:
                data['user'] = self.user.id
            else:
                data['user'] = self.user.dictify()
        else:
            data['user'] = None
        if self.project:
            if trim_project:
                data['project'] = self.project.id
            else:
                data['project'] = self.project.dictify()
        else:
            data['project'] = None
        data['content'] = format_update(self.content_html)
        data['reply_to_id'] = self.reply_to_id
        data['reply_to_user_id'] = reply_to_user_id
        data['reply_to_username'] = reply_to_username
        data['reply_count'] = self.reply_count

        return data
