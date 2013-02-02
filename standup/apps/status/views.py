from flask import (Blueprint, redirect, render_template, request, session,
                   url_for)
from standup.app import db
from standup.errors import forbidden, page_not_found
from standup.apps.status.helpers import enddate, paginate, startdate
from standup.apps.status.models import Project, Status
from standup.apps.users.models import Team, User

blueprint = Blueprint('status', __name__)

@blueprint.route('/')
def index():
    """The home page."""
    return render_template(
        'index.html',
        statuses=paginate(
            Status.query.filter(Status.reply_to==None).order_by(
                db.desc(Status.created)),
            request.args.get('page', 1),
            startdate(request),
            enddate(request)),)

@blueprint.route('/user/<slug>', methods=['GET'])
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
            startdate(request),
            enddate(request)))

@blueprint.route('/project/<slug>', methods=['GET'])
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
            startdate(request),
            enddate(request)))


@blueprint.route('/team/<slug>', methods=['GET'])
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
            startdate(request),
            enddate(request)))


@blueprint.route('/status/<id>', methods=['GET'])
def status(id):
    """The status page. Shows a single status."""
    statuses = Status.query.filter_by(id=id)

    if not statuses.count():
        return page_not_found('Status not found.')

    status = statuses[0]

    return render_template(
        'status.html',
        user=status.user,
        statuses=paginate(statuses),
        replies=status.replies(request.args.get('page', 1))
    )


@blueprint.route('/statusize/', methods=['POST'])
def statusize():
    """Posts a status from the web."""
    email = session.get('email')
    if not email:
        return forbidden('You must be logged in to statusize!')

    user = User.query.filter(User.email == email).first()

    if not user:
        return forbidden('You must have a user account to statusize!')

    message = request.form.get('message', '')

    if not message:
        return page_not_found('You cannot statusize nothing!')

    status = Status(user_id=user.id, content=message, content_html=message)

    project = request.form.get('project', '')
    if project:
        project = Project.query.filter_by(id=project).first()
        if project:
            status.project_id = project.id

    # TODO: reply handling

    db.session.add(status)
    db.session.commit()

    # Try to go back from where we came.
    redirect_url = request.form.get('redirect_to',
        request.headers.get('referer',
            url_for('status.index')))
    return redirect(redirect_url)


@blueprint.route('/profile/', methods=['GET'])
def profile():
    """Shows the user's profile page."""
    email = session.get('email')
    if not email:
        return forbidden('You must be logged in to see a profile!')

    user = User.query.filter(User.email == email).first()

    if not user:
        return forbidden('You must have a user account to see your profile!')

    return render_template(
        'profile.html',
        user=user,
        statuses=user.recent_statuses())
