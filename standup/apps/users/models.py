from standup.app import db
from standup.apps.status.models import Status
from standup.apps.status.helpers import paginate

class Team(db.Model):
    """A team of users in the organization."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    slug = db.Column(db.String(100), unique=True)

    def __repr__(self):
        return '<Team: %s>' % self.name

    def recent_statuses(self, page=1, startdate=None, enddate=None):
        """Return the statuses for the team."""
        user_ids = [u.id for u in self.users]
        statuses = Status.query.filter(
            Status.user_id.in_(user_ids), Status.reply_to==None).order_by(
            db.desc(Status.created))
        return paginate(statuses, page, startdate, enddate)


class User(db.Model):
    """A standup participant."""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    name = db.Column(db.String(100))
    slug = db.Column(db.String(100), unique=True)
    email = db.Column(db.String(100), unique=True)
    github_handle = db.Column(db.String(100), unique=True)
    is_admin = db.Column(db.Boolean, default=False)
    team_users = db.Table('team_users',
        db.Column('team_id', db.Integer, db.ForeignKey('team.id')),
        db.Column('user_id', db.Integer, db.ForeignKey('user.id')))
    team = db.relationship('Team', secondary=team_users,
                           backref=db.backref('users', lazy='dynamic'))

    def __repr__(self):
        return '<User: [%s] %s>' % (self.username, self.name)

    def recent_statuses(self, page=1, startdate=None, enddate=None):
        """Return the statuses for the user."""
        statuses = self.statuses.filter(Status.reply_to==None).order_by(
            db.desc(Status.created))
        return paginate(statuses, page, startdate, enddate)
