from datetime import datetime

from flask import Blueprint, current_app, request
from sqlalchemy import desc
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound
from standup.apps.api2.decorators import api_key_required
from standup.apps.status.models import Project, Status, WeekColumnClause
from standup.apps.users.models import Team, User
from standup.database import get_session
from standup.errors import ApiError, api_error
from standup.main import csrf
from standup.utils import jsonify, numerify, truthify


blueprint = Blueprint('api_v2', __name__, url_prefix='/api/v2')

TIMELINE_MAX_RESULTS = 800


def _get_timeline_params():
    params = {}
    try:
        params['count'] = numerify(request.args.get('count'), default=20)
    except (TypeError, ValueError):
        raise ApiError('Error in `count` parameter: invalid count.')
    params['since_id'] = request.args.get('since_id')
    params['max_id'] = request.args.get('max_id')
    params['trim_user'] = truthify(request.args.get('trim_user'))
    params['trim_project'] = truthify(request.args.get('trim_project'))
    params['include_replies'] = request.args.get('include_replies')
    params['weekly'] = truthify(request.args.get('weekly'))

    return params


def _get_team():
    db = get_session(current_app)

    data = request.args if request.method == 'GET' else request.form

    team_id = data.get('team_id')
    slug = data.get('slug')

    try:
        if slug:
            team = db.query(Team).filter_by(slug=slug).one()
        elif team_id:
            team = db.query(Team).filter_by(id=team_id).one()
        else:
            raise ApiError('The `team_id` or `slug` parameter must be '
                           'provided.')
    except NoResultFound:
        raise ApiError('Team not found.', code=404)

    return team


def _get_user():
    db = get_session(current_app)

    data = request.args if request.method == 'GET' else request.form

    user_id = data.get('user_id')
    screen_name = data.get('screen_name')

    try:
        if user_id:
            user = db.query(User).filter_by(id=user_id).one()
        elif screen_name:
            user = db.query(User).filter_by(username=screen_name).one()
        else:
            raise ApiError('The `user_id` or `screen_name` parameter must be '
                           'provided.')
    except NoResultFound:
        raise ApiError('User not found.', code=404)

    return user


def _handle_since(qs, params):
    if params['since_id'] is not None:
        try:
            since_id = numerify(params['since_id'])
            if since_id < 1:
                raise ApiError('Error in `since_id` parameter: invalid id.')
        except (TypeError, ValueError):
            raise ApiError('Error in `since_id` parameter: invalid id.')
        return qs.filter(Status.id > since_id)
    return qs


def _handle_max(qs, params):
    if params['max_id'] is not None:
        try:
            max_id = numerify(params['max_id'])
            if max_id < 1:
                raise ApiError('Error in `max_id` parameter: invalid id.')
        except (TypeError, ValueError):
            raise ApiError('Error in `max_id` parameter: invalid id.')
        return qs.filter(Status.id <= max_id)
    return qs


def _handle_include_replies(qs, params):
    if not truthify(params['include_replies']):
        return qs.filter_by(reply_to_id=None)
    return qs


def _handle_count(qs, max, params):
    if params['count'] > max:
        raise ApiError('Error in `count` parameter: must not be more than %s'
                       % max)
    elif params['count'] < 1:
        raise ApiError('Error in `count` parameter: must not be less than 1')
    else:
        return qs.order_by(desc(Status.created)).limit(params['count'])

def _handle_weekly(qs, params):
    if params['weekly']:
        return qs.order_by(
                desc(WeekColumnClause("created")),
                Status.user_id,
                desc(Status.created))
    return qs

def _get_data(statuses, params):
    data = []
    for status in statuses:
        data.append(status.dictify(trim_user=params['trim_user'],
                                   trim_project=params['trim_project'],
                                   include_week=params['weekly']))
    return data

@blueprint.route('/statuses/home_timeline.json', methods=['GET'])
def home_timeline():
    """Get a collection of the most recent status updates."""
    db = get_session(current_app)
    MAX = current_app.config.get('API2_TIMELINE_MAX_RESULTS',
                                 TIMELINE_MAX_RESULTS)

    try:
        params = _get_timeline_params()

        statuses = db.query(Status)
        statuses = _handle_weekly(statuses, params)
        statuses = _handle_since(statuses, params)
        statuses = _handle_max(statuses, params)
        statuses = _handle_include_replies(statuses, params)
        statuses = _handle_count(statuses, MAX, params)
    except ApiError, e:
        return api_error(e.code, str(e))

    data = _get_data(statuses, params)
    return jsonify(data)


@blueprint.route('/statuses/user_timeline.json', methods=['GET'])
def user_timeline():
    """Get a collection of the user's recent status updates."""
    db = get_session(current_app)
    MAX = current_app.config.get('API2_TIMELINE_MAX_RESULTS',
                                 TIMELINE_MAX_RESULTS)

    try:
        params = _get_timeline_params()
    except ApiError, e:
        return api_error(e.code, str(e))

    try:
        user = _get_user()
    except ApiError, e:
        return api_error(e.code, str(e))

    try:
        statuses = db.query(Status).filter_by(user=user)
        statuses = _handle_weekly(statuses, params)
        statuses = _handle_since(statuses, params)
        statuses = _handle_max(statuses, params)
        statuses = _handle_include_replies(statuses, params)
        statuses = _handle_count(statuses, MAX, params)
    except ApiError, e:
        return api_error(e.code, str(e))

    data = _get_data(statuses, params)
    return jsonify(data)


@blueprint.route('/statuses/project_timeline.json', methods=['GET'])
def project_timeline():
    """Get a collection of the project's recent status updates."""
    db = get_session(current_app)
    MAX = current_app.config.get('API2_TIMELINE_MAX_RESULTS',
                                 TIMELINE_MAX_RESULTS)

    try:
        params = _get_timeline_params()
    except ApiError, e:
        return api_error(e.code, str(e))

    project_id = request.args.get('project_id')
    slug = request.args.get('slug')

    try:
        if slug:
            project = db.query(Project).filter_by(slug=slug).one()
        elif project_id:
            project = db.query(Project).filter_by(id=project_id).one()
        else:
            return api_error(400, 'The `project_id` or `slug` parameter must '
                                  'be provided.')
    except NoResultFound:
        return api_error(404, 'Project not found.')

    try:
        statuses = db.query(Status).filter_by(project=project)
        statuses = _handle_weekly(statuses, params)
        statuses = _handle_since(statuses, params)
        statuses = _handle_max(statuses, params)
        statuses = _handle_include_replies(statuses, params)
        statuses = _handle_count(statuses, MAX, params)
    except ApiError, e:
        return api_error(e.code, str(e))

    data = _get_data(statuses, params)
    return jsonify(data)


@blueprint.route('/statuses/team_timeline.json', methods=['GET'])
def team_timeline():
    """Get a collection of the team's recent status updates."""
    MAX = current_app.config.get('API2_TIMELINE_MAX_RESULTS',
                                 TIMELINE_MAX_RESULTS)

    try:
        params = _get_timeline_params()
    except ApiError, e:
        return api_error(e.code, str(e))

    try:
        team = _get_team()
    except ApiError, e:
        return api_error(e.code, str(e))

    try:
        statuses = team.statuses().order_by(desc(Status.created))
        statuses = _handle_weekly(statuses, params)
        statuses = _handle_since(statuses, params)
        statuses = _handle_max(statuses, params)
        statuses = _handle_include_replies(statuses, params)
        statuses = _handle_count(statuses, MAX, params)
    except ApiError, e:
        return api_error(e.code, str(e))

    data = _get_data(statuses, params)
    return jsonify(data)


@csrf.exempt
@blueprint.route('/teams/create.json', methods=['POST'])
@api_key_required
def create_team():
    """Creates a new team."""
    db = get_session(current_app)
    team = Team()

    team.slug = request.form.get('slug')

    if not team.slug:
        return api_error(400, 'No slug provided.')

    team.name = request.form.get('name', team.slug)

    db.add(team)

    try:
        db.commit()
    except IntegrityError:
        return api_error(400, 'Slug is already in use.')

    return jsonify(team.dictify())


@csrf.exempt
@blueprint.route('/teams/destroy.json', methods=['POST'])
@api_key_required
def destroy_team():
    """Removes a team."""
    db = get_session(current_app)

    try:
        team = _get_team()
    except ApiError, e:
        return api_error(e.code, str(e))

    data = team.dictify()

    db.delete(team)
    db.commit()

    return jsonify(data)


@csrf.exempt
@blueprint.route('/teams/update.json', methods=['POST'])
@api_key_required
def update_team():
    """Update a team's info."""
    db = get_session(current_app)

    try:
        team = _get_team()
    except ApiError, e:
        return api_error(e.code, str(e))

    team.name = request.form.get('name', team.slug)
    db.commit()

    return jsonify(team.dictify())


@blueprint.route('/teams/members.json', methods=['GET'])
def team_members():
    """Get a list of members of the team."""
    try:
        team = _get_team()
    except ApiError, e:
        return api_error(e.code, str(e))

    members = []
    for user in team.users.all():
        members.append(user.dictify())

    return jsonify({'users': members})


@csrf.exempt
@blueprint.route('/teams/members/create.json', methods=['POST'])
@api_key_required
def create_team_member():
    """Add a user to the team."""
    db = get_session(current_app)

    try:
        team = _get_team()
        user = _get_user()
    except ApiError, e:
        return api_error(e.code, str(e))

    team.users.append(user)

    try:
        db.commit()
    except IntegrityError:
        return api_error(400, 'User is already in that team.')

    return jsonify(team.dictify())


@csrf.exempt
@blueprint.route('/teams/members/destroy.json', methods=['POST'])
@api_key_required
def destroy_team_member():
    """Remove a user from the team."""
    db = get_session(current_app)

    try:
        team = _get_team()
        user = _get_user()
    except ApiError, e:
        return api_error(e.code, str(e))

    team.users.remove(user)
    db.commit()

    return jsonify(team.dictify())


@blueprint.route('/info/timesince_last_update.json', methods=['GET'])
def timesince_last_update():
    """Get the time since the users last update in seconds"""
    db = get_session(current_app)

    try:
        user = _get_user()
    except ApiError, e:
        return api_error(e.code, str(e))

    try:
        status = db.query(Status).filter_by(user=user)
        status = status.order_by(desc(Status.created)).one()
    except NoResultFound:
        return jsonify({'timesince': None})

    td = datetime.utcnow() - status.created
    ts = (td.microseconds + (td.seconds + td.days * 24 * 3600) * 10**6) / 10**6

    return jsonify({'timesince': int(ts)})
