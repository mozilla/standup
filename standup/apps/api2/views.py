from flask import Blueprint, current_app, request
from sqlalchemy import desc
from standup.apps.api2.helpers import numerify
from standup.apps.status.models import Status
from standup.database import get_session
from standup.errors import api_error
from standup.utils import jsonify, truthify


blueprint = Blueprint('api_v2', __name__, url_prefix='/api/v2')

TIMELINE_MAX_RESULTS = 800


@blueprint.route('/statuses/home_timeline.json', methods=['GET'])
def home_timeline():
    """Get a collection of the most recent status updates."""
    app = current_app
    db = get_session(app)

    # Parameteres
    try:
        count = numerify(request.args.get('count'), default=20)
    except (TypeError, ValueError):
        return api_error(400, 'Error in `count` parameter: invalid count.')
    since_id = request.args.get('since_id')
    max_id = request.args.get('max_id')
    trim_user = truthify(request.args.get('trim_user'))
    trim_project = truthify(request.args.get('trim_project'))
    include_replies = request.args.get('include_replies')

    statuses = db.query(Status)

    if since_id:
        try:
            since_id = numerify(since_id)
            if since_id < 1:
                return api_error(400, 'Error in `since_id` parameter: '
                                      'invalid id.')
        except (TypeError, ValueError):
            return api_error(400, 'Error in `since_id` parameter: invalid id.')
        statuses = statuses.filter(Status.id > since_id)

    if max_id:
        try:
            max_id = numerify(max_id)
            if max_id < 1:
                return api_error(400, 'Error in `max_id` parameter: '
                                      'invalid id.')
        except (TypeError, ValueError):
            return api_error(400, 'Error in `max_id` parameter: invalid id.')
        statuses = statuses.filter(Status.id <= max_id)

    if not truthify(include_replies):
        statuses = statuses.filter_by(reply_to_id=None)

    MAX = app.config.get('API2_TIMELINE_MAX_RESULTS', TIMELINE_MAX_RESULTS)
    if count > MAX:
        return api_error(400, 'Error in `count` parameter: must not be more '
                              'than %s' % MAX)
    elif count < 1:
        return api_error(400, 'Error in `count` parameter: must not be less '
                              'than 1')
    else:
        statuses = statuses.order_by(desc(Status.created)).limit(count)

    data = []
    for status in statuses:
        data.append(status.export(trim_user=trim_user,
                                  trim_project=trim_project))

    return jsonify(data)
