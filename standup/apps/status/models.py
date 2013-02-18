from datetime import datetime

from standup.apps.status.helpers import paginate
from standup.main import db


class Project(db.Model):
    """A project that does standups."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    slug = db.Column(db.String(100), unique=True)
    color = db.Column('color', db.String(6))
    repo_url = db.Column('repo_url', db.String(100))

    def __repr__(self):
        return '<Project: [%s] %s>' % (self.slug, self.name)

    def recent_statuses(self, page=1, startdate=None, enddate=None):
        """Return the statuses for the project."""
        statuses = self.statuses.filter(Status.reply_to == None).order_by(
            db.desc(Status.created))
        return paginate(statuses, page, startdate, enddate)


class Status(db.Model):
    """A standup update for a user on a given project."""
    id = db.Column(db.Integer, primary_key=True)
    created = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship(
        'User', backref=db.backref('statuses', lazy='dynamic'))
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))
    project = db.relationship(
        'Project', backref=db.backref('statuses', lazy='dynamic'))
    content = db.Column(db.Text)
    content_html = db.Column(db.Text)
    reply_to_id = db.Column(db.Integer, db.ForeignKey('status.id'))
    reply_to = db.relationship('Status', remote_side=[id])

    def __repr__(self):
        return '<Status: %s: %s>' % (self.user.username, self.content)

    def replies(self, page=1):
        replies = Status.query.filter(Status.reply_to_id == self.id).order_by(
            db.asc(Status.created))
        return paginate(replies, page)
