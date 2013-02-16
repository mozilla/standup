from flask import Blueprint, jsonify

from standup.apps.status.models import Status
from standup.main import db


blueprint = Blueprint('api_v2', __name__, url_prefix='/api/v2')


@blueprint.route('/', methods=['GET'])
@blueprint.route('/feed/', methods=['GET'])
def feed(request):
    """Get all status updates.

    Returns id, user (the name), project name and timestamp of statuses.

    The amount of items to return is determined by the limit argument
    (defaults to 20)::

        /api/v2/feed/?limit=20

    An example of the JSON::

        {
            "1": {
                "user": "r1cky",
                "content": "working on bug 123456",
                "project": "sumodev",
                "timestamp": "2013-01-11T21:13:30.806236"
            }
        }

    """
    limit = request.args.get('limit', 20)

    statuses = (Status.query.filter(Status.reply_to == None)
                      .order_by(db.desc(Status.created)).limit(limit))

    data={}
    for row in statuses:
        id = row.id
        created = row.created.isoformat()
        try:
            project_name = row.project.name
        except:
            project_name = None
        data[id] = (dict(author=row.user.name, content=row.content,
            timestamp=created, project=project_name))

    return jsonify(data)
