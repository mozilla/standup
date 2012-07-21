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

class User(db.Model):
    """A standup participant."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    irc_handle = db.Column(db.String(100), unique=True)
    github_handle = db.Column(db.String(100), unique=True)
    is_admin = db.Column(db.Boolean, default=False)


class Project(db.Model):
    """A project that does standups."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    irc_channel = db.Column(db.String(100), unique=True)


class Status(db.Model):
    """A standup update for a user on a given project."""
    id = db.Column(db.Integer, primary_key=True)
    created = db.Column(db.DateTime, default=datetime.now)
    irc_handle = db.Column(db.String(100))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship(
        'User', backref=db.backref('statuses', lazy='dynamic'))
    project_id = db.Column(
        db.Integer, db.ForeignKey('project.id'), nullable=False)
    project = db.relationship(
        'Project', backref=db.backref('statuses', lazy='dynamic'))
    content = db.Column(db.Text)
    content_html = db.Column(db.Text)

# TODO: M2M Users <-> Projects


# Views:
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/status', methods=['POST'])
def create_status():
    """Post a new status.

    The status should be posted as json using 'application/json' as the
    content type. The posted JSON needs to have 4 required fields:
        * irc_handle
        * irc_channel
        * content
        * api_key

    An example of the JSON::

        {
            "irc_handle": "r1cky",
            "irc_channel": "sumodev",
            "content": "working on bug 123456",
            "api_key": "qwertyuiopasdfghjklzxcvbnm1234567890"
        }
    """
    # Check that api_key is valid.
    api_key = request.json.get('api_key')
    if api_key != settings.API_KEY:
        return make_response(jsonify(dict(error='Invalid API key.')), 403)

    # The data we need
    irc_handle = request.json.get('irc_handle')
    irc_channel = request.json.get('irc_channel')
    content = request.json.get('content')

    # Validate we have the required fields.
    if not (irc_handle and irc_channel and content):
        return make_response(
            jsonify(dict(error='Missing required fields.')), 400)

    # Get or create the user
    # TODO: People change their nicks sometimes, figure out what to do.
    user = User.query.filter_by(irc_handle=irc_handle).first()
    if not user:
        user = User(irc_handle=irc_handle)
        db.session.add(user)
        db.session.commit()

    # Get or create the project
    project = Project.query.filter_by(irc_channel=irc_channel).first()
    if not project:
        project = Project(irc_channel=irc_channel, name=irc_channel)
        db.session.add(project)
        db.session.commit()

    # Create the status
    status = Status(irc_handle=irc_handle, project_id=project.id,
                    user_id=user.id, content=content, content_html=content)
    db.session.add(status)
    db.session.commit()

    return jsonify(dict(id=status.id, content=content))


if __name__ == '__main__':
    db.create_all()
    # Bind to PORT if defined, otherwise default to 5000.
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
