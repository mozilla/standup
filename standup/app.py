from datetime import datetime
import os

from flask import (Flask, render_template, request, redirect, url_for,
                   jsonify, make_response)
from flask.ext.sqlalchemy import SQLAlchemy

import settings


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL', 'sqlite:///standup_app.db')
db = SQLAlchemy(app)


# Models:

class Team(db.Model):
    """A team of users in the organization."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    slug = db.Column(db.String(100), unique=True)

    def __repr__(self):
        return '<Team: %s>' % self.name

    def recent_statuses(self, daterange='all'):
        """Return the statuses for the team."""
        # TODO: filter on dates
        return self.statuses


class User(db.Model):
    """A standup participant."""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    name = db.Column(db.String(100))
    slug = db.Column(db.String(100), unique=True)
    email = db.Column(db.String(100), unique=True)
    github_handle = db.Column(db.String(100), unique=True)
    is_admin = db.Column(db.Boolean, default=False)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'))
    team = db.relationship(
        'Team', backref=db.backref('users', lazy='dynamic'))

    def __repr__(self):
        return '<User: [%s] %s>' % (self.username, self.name)

    def recent_statuses(self, daterange='all'):
        """Return the statuses for the user."""
        # TODO: filter on dates
        return self.statuses


class Project(db.Model):
    """A project that does standups."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    slug = db.Column(db.String(100), unique=True)

    def __repr__(self):
        return '<Project: [%s] %s>' % (self.slug, self.name)

    def recent_statuses(self, daterange='all'):
        """Return the statuses for the project."""
        # TODO: filter on dates
        return self.statuses


class Status(db.Model):
    """A standup update for a user on a given project."""
    id = db.Column(db.Integer, primary_key=True)
    created = db.Column(db.DateTime, default=datetime.now)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship(
        'User', backref=db.backref('statuses', lazy='dynamic'))
    project_id = db.Column(
        db.Integer, db.ForeignKey('project.id'), nullable=False)
    project = db.relationship(
        'Project', backref=db.backref('statuses', lazy='dynamic'))
    content = db.Column(db.Text)
    content_html = db.Column(db.Text)

    def __repr__(self):
        return '<Status: %s: %s>' % (self.user.username, self.content)

# TODO: M2M Users <-> Projects

# Views:
@app.route('/')
def index():
    """The home page."""
    return render_template(
        'index.html',
        statuses=Status.query.order_by(db.desc(Status.created)),
        projects=Project.query.all(),
        teams=Team.query.all())


@app.route('/user/<slug>', methods=['GET'])
def user(slug):
    """The user page. Shows a user's statuses."""
    user = User.query.filter_by(slug=slug).first()
    if not user:
        return page_not_found('User not found.')

    statuses = Status.query.filter_by(
        user=user).order_by(db.desc(Status.created))

    return render_template('user.html', user=user, statuses=statuses)


@app.route('/project/<slug>', methods=['GET'])
def project(slug):
    """The project page. Shows a project's statuses."""
    project = Project.query.filter_by(slug=slug).first()
    if not project:
        return page_not_found('Project not found.')

    statuses = Status.query.filter_by(
        project=project).order_by(db.desc(Status.created))

    return render_template('project.html', project=project, statuses=statuses)


@app.route('/team/<slug>', methods=['GET'])
def team(slug):
    """The team page. Shows a statuses for all users in the team."""
    team = Team.query.filter_by(slug=slug).first()
    if not team:
        return page_not_found('Team not found.')

    return render_template('team.html', team=team, users=team.users)


@app.route('/api/v1/status/', methods=['POST'])
def create_status():
    """Post a new status.

    The status should be posted as json using 'application/json' as the
    content type. The posted JSON needs to have 4 required fields:
        * user (the username)
        * project (the slug)
        * content
        * api_key

    An example of the JSON::

        {
            "user": "r1cky",
            "project": "sumodev",
            "content": "working on bug 123456",
            "api_key": "qwertyuiopasdfghjklzxcvbnm1234567890"
        }
    """
    # Check that api_key is valid.
    api_key = request.json.get('api_key')
    if api_key != settings.API_KEY:
        return make_response(jsonify(dict(error='Invalid API key.')), 403)

    # The data we need
    username = request.json.get('user')
    project_slug = request.json.get('project')
    content = request.json.get('content')

    # Validate we have the required fields.
    if not (username and project_slug and content):
        return make_response(
            jsonify(dict(error='Missing required fields.')), 400)

    # Get or create the user
    # TODO: People change their nicks sometimes, figure out what to do.
    user = User.query.filter_by(username=username).first()
    if not user:
        user = User(username=username, name=username,
                    slug=username, github_handle=username)
        db.session.add(user)
        db.session.commit()

    # Get or create the project
    project = Project.query.filter_by(slug=project_slug).first()
    if not project:
        project = Project(slug=project_slug, name=project_slug)
        db.session.add(project)
        db.session.commit()

    # Create the status
    status = Status(project_id=project.id, user_id=user.id, content=content,
                    content_html=content)
    db.session.add(status)
    db.session.commit()

    return jsonify(dict(id=status.id, content=content))


@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404


@app.errorhandler(500)
def something_broke(error):
    return render_template('500.html'), 500


if __name__ == '__main__':
    db.create_all()
    # Bind to PORT if defined, otherwise default to 5000.
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
