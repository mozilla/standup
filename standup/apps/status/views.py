from flask import (Blueprint, current_app, redirect, render_template, request,
                   session, url_for)
from jinja2.filters import urlize
from markdown import markdown
from urlparse import urljoin
from werkzeug.contrib.atom import AtomFeed

from sqlalchemy import desc
from standup.apps.status.helpers import enddate, paginate, startdate
from standup.apps.status.models import Project, Status, WeekColumnClause
from standup.apps.users.models import Team, User
from standup.database import get_session
from standup.errors import forbidden, page_not_found
from standup.filters import format_update


blueprint = Blueprint('status', __name__)


def absolute_url(url):
    """Return a non-relative URL; used in XML feeds."""
    return urljoin(request.url_root, url)


def format_status(status):
    """Format a status update inside an Atom feed with HTML filters."""
    return markdown(urlize(format_update(status.content_html, status.project)))


def render_feed(title, statuses):
    """Create an Atom feed from a title and list of statuses."""
    feed = AtomFeed(title, feed_url=request.url, url=request.url_root)

    for status in statuses:
        title = 'From %s at %s' % (status.user.username,
                                   status.created.strftime('%I:%M%p %Z'))
        content = unicode(format_status(status))

        if status.project:
            content = '<h3>%s</h3>%s' % (status.project.name, content)

        feed.add(title, content, content_type='html', author=status.user.name,
                 url=absolute_url(url_for('status.status', id=status.id)),
                 updated=status.created, published=status.created)
    return feed.get_response()


@blueprint.route('/')
def index():
    """The home page."""
    db = get_session(current_app)

    return render_template(
        'status/index.html',
        statuses=paginate(
            db.query(Status).filter_by(reply_to=None).order_by(
                desc(Status.created)),
            request.args.get('page', 1),
            startdate(request),
            enddate(request)),)

@blueprint.route('/weekly')
def weekly():
    """The weekly status page."""
    db = get_session(current_app)

    #select id, user_id, created, strftime('%Y%W', created), date(created, 'weekday 1'), content from status order by 4, 2, 3;
    return render_template(
        'status/weekly.html',
        week=request.args.get('week', None),
        statuses=paginate(
            db.query(Status).filter_by(reply_to=None).order_by(
                desc(WeekColumnClause("created")),
                Status.user_id,
                desc(Status.created)),
            request.args.get('page', 1),
            startdate(request),
            enddate(request),
            per_page=100),)

@blueprint.route('/statuses.xml')
def index_feed():
    """Output every status in an Atom feed."""
    db = get_session(current_app)

    statuses = db.query(Status).filter_by(reply_to=None)\
        .order_by(desc(Status.created))

    return render_feed('All status updates', statuses)


@blueprint.route('/user/<slug>', methods=['GET'])
def user(slug):
    """The user page. Shows a user's statuses."""
    db = get_session(current_app)

    user = db.query(User).filter_by(slug=slug).first()
    if not user:
        return page_not_found('User not found.')
    return render_template(
        'status/user.html',
        user=user,
        statuses=user.recent_statuses(
            request.args.get('page', 1),
            startdate(request),
            enddate(request)))


@blueprint.route('/user/<slug>.xml', methods=['GET'])
def user_feed(slug):
    """A user's Atom feed. Output every status from this user."""
    db = get_session(current_app)

    user = db.query(User).filter_by(slug=slug).first()
    if not user:
        return page_not_found('User not found.')

    statuses = user.statuses.filter_by(reply_to=None)\
        .order_by(desc(Status.created))

    return render_feed('Updates by %s' % user.username, statuses)


@blueprint.route('/project/<slug>', methods=['GET'])
def project(slug):
    """The project page. Shows a project's statuses."""
    db = get_session(current_app)

    project = db.query(Project).filter_by(slug=slug).first()
    if not project:
        return page_not_found('Project not found.')

    return render_template(
        'status/project.html',
        project=project,
        projects=db.query(Project).order_by(Project.name).filter(
            Project.statuses.any()),
        statuses=project.recent_statuses(
            request.args.get('page', 1),
            startdate(request),
            enddate(request)))


@blueprint.route('/project/<slug>.xml', methods=['GET'])
def project_feed(slug):
    """Project Atom feed. Shows all statuses for a project."""
    db = get_session(current_app)

    project = db.query(Project).filter_by(slug=slug).first()
    if not project:
        return page_not_found('Project not found.')

    statuses = project.statuses.filter_by(reply_to=None)\
        .order_by(desc(Status.created))

    return render_feed('Updates for %s' % project.name, statuses)


@blueprint.route('/team/<slug>', methods=['GET'])
def team(slug):
    """The team page. Shows statuses for all users in the team."""
    db = get_session(current_app)

    team = db.query(Team).filter_by(slug=slug).first()
    if not team:
        return page_not_found('Team not found.')

    return render_template(
        'status/team.html',
        team=team,
        users=team.users,
        teams=db.query(Team).order_by(Team.name).all(),
        statuses=team.recent_statuses(
            request.args.get('page', 1),
            startdate(request),
            enddate(request)))


@blueprint.route('/team/<slug>.xml', methods=['GET'])
def team_feed(slug):
    """The team status feed. Shows all updates from a team in Atom format."""
    db = get_session(current_app)

    team = db.query(Team).filter_by(slug=slug).first()
    if not team:
        return page_not_found('Team not found.')

    statuses = team.statuses().filter_by(reply_to=None)\
        .order_by(desc(Status.created))

    return render_feed('Updates from %s' % team.name, statuses)


@blueprint.route('/status/<id>', methods=['GET'])
def status(id):
    """The status page. Shows a single status."""
    db = get_session(current_app)

    statuses = db.query(Status).filter_by(id=id)

    if not statuses.count():
        return page_not_found('Status not found.')

    status = statuses[0]

    return render_template(
        'status/status.html',
        user=status.user,
        statuses=paginate(statuses),
        replies=status.replies(request.args.get('page', 1))
    )


@blueprint.route('/statusize/', methods=['POST'])
def statusize():
    """Posts a status from the web."""
    db = get_session(current_app)

    user_id = session.get('user_id')
    if not user_id:
        return forbidden('You must be logged in to statusize!')

    user = db.query(User).get(user_id)

    message = request.form.get('message', '')

    if not message:
        return page_not_found('You cannot statusize nothing!')

    status = Status(user_id=user.id, content=message, content_html=message)

    project = request.form.get('project', '')
    if project:
        project = db.query(Project).filter_by(id=project).first()
        if project:
            status.project_id = project.id

    # TODO: reply handling

    db.add(status)
    db.commit()

    # Try to go back from where we came.
    referer = request.headers.get('referer', url_for('status.index'))
    redirect_url = request.form.get('redirect_to', referer)
    return redirect(redirect_url)
