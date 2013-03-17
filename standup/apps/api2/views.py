from flask import Blueprint, current_app, request
from sqlalchemy import desc
from sqlalchemy.orm.exc import NoResultFound
from standup.apps.status.models import Project, Status
from standup.apps.users.models import Team, User
from standup.database import get_session
from standup.errors import ApiError, api_error
from standup.utils import jsonify, numerify, truthify


blueprint = Blueprint('api_v2', __name__, url_prefix='/api/v2')

TIMELINE_MAX_RESULTS = 800


def _get_params(request):
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

    return params


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


@blueprint.route('/statuses/home_timeline.json', methods=['GET'])
def home_timeline():
    """Get a collection of the most recent status updates."""
    app = current_app
    db = get_session(app)
    MAX = app.config.get('API2_TIMELINE_MAX_RESULTS', TIMELINE_MAX_RESULTS)

    try:
        params = _get_params(request)

        statuses = db.query(Status)
        statuses = _handle_since(statuses, params)
        statuses = _handle_max(statuses, params)
        statuses = _handle_include_replies(statuses, params)
        statuses = _handle_count(statuses, MAX, params)
    except ApiError, e:
        return api_error(400, str(e))

    data = []
    for status in statuses:
        data.append(status.dictify(trim_user=params['trim_user'],
                                   trim_project=params['trim_project']))

    return jsonify(data)


@blueprint.route('/statuses/user_timeline.json', methods=['GET'])
def user_timeline():
    """Get a collection of the user's recent status updates."""
    app = current_app
    db = get_session(app)
    MAX = app.config.get('API2_TIMELINE_MAX_RESULTS', TIMELINE_MAX_RESULTS)

    try:
        params = _get_params(request)
    except ApiError, e:
        return api_error(400, str(e))

    user_id = request.args.get('user_id')
    screen_name = request.args.get('screen_name')

    try:
        if user_id:
            user = db.query(User).filter_by(id=user_id).one()
        elif screen_name:
            user = db.query(User).filter_by(username=screen_name).one()
        else:
            return api_error(400, 'The `user_id` or `screen_name` parameter '
                                  'must be provided.')
    except NoResultFound:
        return api_error(404, 'User not found.')

    try:
        statuses = db.query(Status).filter_by(user=user)
        statuses = _handle_since(statuses, params)
        statuses = _handle_max(statuses, params)
        statuses = _handle_include_replies(statuses, params)
        statuses = _handle_count(statuses, MAX, params)
    except ApiError, e:
        return api_error(400, str(e))

    data = []
    for status in statuses:
        data.append(status.dictify(trim_user=params['trim_user'],
                                   trim_project=params['trim_project']))

    return jsonify(data)


@blueprint.route('/statuses/project_timeline.json', methods=['GET'])
def project_timeline():
    """Get a collection of the project's recent status updates."""
    app = current_app
    db = get_session(app)
    MAX = app.config.get('API2_TIMELINE_MAX_RESULTS', TIMELINE_MAX_RESULTS)

    try:
        params = _get_params(request)
    except ApiError, e:
        return api_error(400, str(e))

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
        statuses = _handle_since(statuses, params)
        statuses = _handle_max(statuses, params)
        statuses = _handle_include_replies(statuses, params)
        statuses = _handle_count(statuses, MAX, params)
    except ApiError, e:
        return api_error(400, str(e))

    data = []
    for status in statuses:
        data.append(status.dictify(trim_user=params['trim_user'],
                                   trim_project=params['trim_project']))

    return jsonify(data)


@blueprint.route('/statuses/team_timeline.json', methods=['GET'])
def team_timeline():
    """Get a collection of the team's recent status updates."""
    app = current_app
    db = get_session(app)
    MAX = app.config.get('API2_TIMELINE_MAX_RESULTS', TIMELINE_MAX_RESULTS)

    try:
        params = _get_params(request)
    except ApiError, e:
        return api_error(400, str(e))

    team_id = request.args.get('team_id')
    slug = request.args.get('slug')

    try:
        if slug:
            team = db.query(Team).filter_by(slug=slug).one()
        elif team_id:
            team = db.query(Team).filter_by(id=team_id).one()
        else:
            return api_error(400, 'The `team_id` or `slug` parameter must '
                                  'be provided.')
    except NoResultFound:
        return api_error(404, 'Team not found.')

    try:
        statuses = team.statuses().order_by(desc(Status.created))
        statuses = _handle_since(statuses, params)
        statuses = _handle_max(statuses, params)
        statuses = _handle_include_replies(statuses, params)
        statuses = _handle_count(statuses, MAX, params)
    except ApiError, e:
        return api_error(400, str(e))

    data = []
    for status in statuses:
        data.append(status.dictify(trim_user=params['trim_user'],
                                   trim_project=params['trim_project']))

    return jsonify(data)
