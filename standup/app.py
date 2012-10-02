import browserid
import hashlib
import os, re
from bleach import clean, linkify
from datetime import datetime, date, timedelta
from flask import (Flask, render_template, request, redirect, url_for,
                   jsonify, make_response, session)
from flask.ext.sqlalchemy import SQLAlchemy
from functools import wraps
from urllib import urlencode

import settings

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL', 'sqlite:///standup_app.db')
app.secret_key = settings.SESSION_SECRET
db = SQLAlchemy(app)


# Models:

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
            Status.user_id.in_(user_ids)).order_by(db.desc(Status.created))
        return _paginate(statuses, page, startdate, enddate)


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

    def recent_statuses(self, page=1, startdate=None, enddate=None):
        """Return the statuses for the user."""
        statuses = self.statuses.order_by(db.desc(Status.created))
        return _paginate(statuses, page, startdate, enddate)


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
        statuses = self.statuses.order_by(db.desc(Status.created))
        return _paginate(statuses, page, startdate, enddate)


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
        replies = Status.query.filter(Status.reply_to_id==self.id).order_by(
            db.desc(Status.created))
        return _paginate(replies, page)

# TODO: M2M Users <-> Projects

# Views:
def api_key_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        api_key = request.json.get('api_key', '')
        if api_key != settings.API_KEY:
            return make_response(jsonify({'error': 'Invalid API key.'}), 403)
        return view(*args, **kwargs)

    return wrapper


@app.route('/authenticate', methods=['POST'])
def authenticate():
    """Authenticate user with Persona."""
    data = browserid.verify(request.form['assertion'],
                            settings.SITE_URL)
    session['email'] = data['email']
    response = jsonify({'message':'login successful'})
    response.status_code = 200
    return response


@app.route('/logout', methods=['POST'])
def logout():
    """Log user out of app."""
    session.pop('email', None)
    response = jsonify({'message':'logout successful'})
    response.status_code = 200
    return response


@app.route('/')
def index():
    """The home page."""
    return render_template(
        'index.html',
        statuses=_paginate(
            Status.query.order_by(db.desc(Status.created)),
            request.args.get('page', 1),
            _startdate(request),
            _enddate(request)),)


@app.route('/help')
def help():
    """The help page."""
    return render_template('help.html')


@app.route('/user/<slug>', methods=['GET'])
def user(slug):
    """The user page. Shows a user's statuses."""
    user = User.query.filter_by(slug=slug).first()
    if not user:
        return page_not_found('User not found.')
    return render_template(
        'user.html',
        user=user,
        statuses=user.recent_statuses(
            request.args.get('page', 1),
            _startdate(request),
            _enddate(request)))


@app.route('/project/<slug>', methods=['GET'])
def project(slug):
    """The project page. Shows a project's statuses."""
    project = Project.query.filter_by(slug=slug).first()
    if not project:
        return page_not_found('Project not found.')

    return render_template(
        'project.html',
        project=project,
        projects=Project.query.order_by(Project.name).filter(
            Project.statuses.any()),
        statuses=project.recent_statuses(
            request.args.get('page', 1),
            _startdate(request),
            _enddate(request)))


@app.route('/team/<slug>', methods=['GET'])
def team(slug):
    """The team page. Shows a statuses for all users in the team."""
    team = Team.query.filter_by(slug=slug).first()
    if not team:
        return page_not_found('Team not found.')

    return render_template(
        'team.html',
        team=team,
        users=team.users,
        teams=Team.query.order_by(Team.name).all(),
        statuses=team.recent_statuses(
            request.args.get('page', 1),
            _startdate(request),
            _enddate(request)))


@app.route('/status/<id>', methods=['GET'])
def status(id):
    """The status page. Shows a single status."""
    statuses = Status.query.filter_by(id=id)

    if not statuses.count():
        return page_not_found(404)

    status = statuses[0]

    return render_template(
        'status.html',
        user=status.user,
        statuses=_paginate(statuses),
        replies=status.replies(request.args.get('page', 1))
    )


@app.route('/api/v1/status/', methods=['POST'])
@api_key_required
def create_status():
    """Post a new status.

    The status should be posted as JSON using 'application/json' as the
    content type. The posted JSON needs to have 3 required fields:
        * user (the username)
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
    # The data we need
    username = request.json.get('user')
    project_slug = request.json.get('project')
    content = request.json.get('content')
    reply_to = request.json.get('reply_to')

    # Validate we have the required fields.
    if not (username and content):
        return make_response(
            jsonify(dict(error='Missing required fields.')), 400)

    # If this is a reply make sure that the status being replied to exists and
    # is not itself a reply
    if reply_to:
        replied = Status.query.filter_by(id=reply_to).first()
        if not replied:
            return make_response(
                jsonify(dict(error='Status does not exist.')), 400)
        elif replied.reply_to:
            return make_response(
                jsonify(dict(error='Cannot reply to a reply.')), 400)
    else:
        replied = None

    # Get or create the user
    # TODO: People change their nicks sometimes, figure out what to do.
    user = User.query.filter_by(username=username).first()
    if not user:
        user = User(username=username, name=username,
                    slug=username, github_handle=username)
        db.session.add(user)
        db.session.commit()

    # Get or create the project (but not if this is a reply)
    if project_slug and not replied:
        project = Project.query.filter_by(slug=project_slug).first()
        if not project:
            project = Project(slug=project_slug, name=project_slug)
            db.session.add(project)
            db.session.commit()

    # Create the status
    status = Status(user_id=user.id, content=content, content_html=content)
    if project_slug and project:
        status.project_id = project.id
    if replied:
        status.reply_to_id = replied.id
    db.session.add(status)
    db.session.commit()

    return jsonify(dict(id=status.id, content=content))


@app.route('/api/v1/status/<id>/', methods=['DELETE'])
@api_key_required
def delete_status(id):
    """Delete an existing status

    The status to be deleted should be posted as JSON using 'application/json as
    the content type. The posted JSON needs to have 2 required fields:
        * user (the username)
        * api_key

    An example of the JSON:

        {
            "user": "r1cky",
            "api_key": "qwertyuiopasdfghjklzxcvbnm1234567890"
        }
    """
    # The data we need
    user = request.json.get('user')

    if not (id and user):
        return make_response(
            jsonify(dict(error='Missing required fields.')), 400)

    status = Status.query.filter(Status.id==id)

    if not status.count():
        return make_response(jsonify(dict(error='Status does not exist.')), 400)

    if not status[0].user.username == user:
        return make_response(
            jsonify(dict(error='You cannot delete this status.')), 403)

    status.delete()
    db.session.commit()

    return make_response(jsonify(dict(id=id)))


@app.route('/api/v1/user/<username>/', methods=['POST'])
@api_key_required
def update_user(username):
    """Update settings for an existing user.

    The settings to be deleted should be posted as JSON using 'application/json
    as the content type. The posted JSON needs to have 2 required fields:
        * user (the username of the IRC user)
        * api_key

    You may optionally supply the following settings to overwrite their values:
        * name
        * email
        * github_handle

    An example of the JSON:

        {
            "user": "r1cky",
            "email": "ricky@email.com"
            "api_key": "qwertyuiopasdfghjklzxcvbnm1234567890"
        }
    """

    # The data we need
    authorname = request.json.get('user')

    # Optional data
    name = request.json.get('name')
    email = request.json.get('email')
    github_handle = request.json.get('github_handle')

    if not (username and authorname and (name or email or github_handle)):
        return make_response(
            jsonify(dict(error='Missing required fields')), 400)

    author = User.query.filter(User.username==authorname)[0]

    user = User.query.filter(User.username==username)

    if not user.count():
        user = User(username=username, slug=username)
    else:
        user = user[0]

    if author.username != user.username and not author.is_admin:
        return make_response(
            jsonify(dict(error='You cannot modify this user.')), 403)

    if name:
        user.name = name

    if email:
        user.email = email

    if github_handle:
        user.github_handle = github_handle

    db.session.commit()

    return make_response(jsonify(dict(id=user.id)))


@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404


@app.errorhandler(500)
def something_broke(error):
    return render_template('500.html'), 500


@app.template_filter('dateformat')
def dateformat(date, format='%Y-%m-%d'):
    def suffix(d):
        return 'th' if 11<=d<=13 else {1:'st',2:'nd',3:'rd'}.get(d%10, 'th')

    return date.strftime(format).replace('{S}', str(date.day) + suffix(date.day))


@app.template_filter('gravatar_url')
def gravatar_url(email, size=None):
    m = hashlib.md5(email.lower())
    hash = m.hexdigest()
    url = 'http://www.gravatar.com/avatar/' + hash

    qs = {}

    if settings.DEBUG:
        qs['d'] = 'mm'
    else:
        qs['d'] = settings.SITE_URL + url_for('static', filename='img/default-avatar.png')

    if size:
        qs['s'] = size

    url += '?' + urlencode(qs)
    return url


TAG_TMPL = '{0} <span class="tag tag-{1}">{1}</span>'


@app.template_filter('format_update')
def format_update(update, project=None):
    def set_target(attrs, new=False):
        attrs['target'] = '_blank'
        return attrs

    # Remove icky stuff.
    formatted = clean(update, tags=[])

    # Linkify "bug #n" and "bug n" text.
    formatted = re.sub(r'(bug) #?(\d+)',
        r'<a href="http://bugzilla.mozilla.org/show_bug.cgi?id=\2">\1 \2</a>',
        formatted, flags=re.I)

    # Linkify "pull #n" and "pull n" text.
    if project and project.repo_url:
        formatted = re.sub(r'(pull|pr) #?(\d+)',
            r'<a href="%s/pull/\2">\1 \2</a>' % project.repo_url, formatted,
            flags=re.I)

    formatted = linkify(formatted, target='_blank')

    # Search for tags on the original, unformatted string. A tag must start
    # with a letter.
    tags = re.findall(r'(?:^|[^\w\\/])#([a-zA-Z][a-zA-Z0-9_\.-]*)(?:\b|$)',
                      update)
    tags.sort()
    if tags:
        tags_html = ''
        for tag in tags:
            tags_html = TAG_TMPL.format(tags_html, tag)
        formatted = '%s <div class="tags">%s</div>' % (formatted, tags_html)

    return formatted


@app.context_processor
def inject_page():
    return dict(page=int(request.args.get('page', 1)))


def _paginate(statuses, page=1, startdate=None, enddate=None):
    if startdate:
        statuses = statuses.filter(Status.created >= startdate)
    if enddate:
        statuses = statuses.filter(Status.created <= enddate)
    return statuses.paginate(int(page))


def _startdate(request):
    dates = request.args.get('dates')
    day = request.args.get('day')
    if dates == '7d':
        return date.today() - timedelta(days=7)
    elif dates == 'today':
        return date.today()
    elif _isday(day):
        return _day(day)
    return None


def _enddate(request):
    day = request.args.get('day')
    if _isday(day):
        return _day(day) + timedelta(days=1)
    return None


def _isday(day):
    return day and re.match('^\d{4}-\d{2}-\d{2}$', day)


def _day(day):
    return datetime.strptime(day, '%Y-%m-%d')


@app.before_request
def bootstrap():
    # Jinja global variables
    projects = Project.query.order_by(Project.name).filter(Project.statuses.any())
    teams = Team.query.order_by(Team.name).all()

    if session:
        user = User.query.filter(User.email == session['email']).first()
    else:
        user = None

    app.jinja_env.globals.update(projects = list(projects), teams = teams,
                                 current_user = user, today=date.today(),
                                 yesterday=date.today() - timedelta(1))


if __name__ == '__main__':
    db.create_all()
    
    # Bind to PORT if defined, otherwise default to 5000.
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=settings.DEBUG)
