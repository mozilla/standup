from flask import Blueprint, jsonify, make_response, request

from standup.apps.api.decorators import api_key_required
from standup.apps.status.models import Project, Status
from standup.apps.users.models import User
from standup.main import db
from standup.utils import slugify


blueprint = Blueprint('api_v1', __name__, url_prefix='/api/v1')


@blueprint.route('/feed/', methods=['GET'])
def get_statuses():
    """Get all status updates.

    Returns id, user (the name), project name and timestamp of statuses.

    The amount of items to return is determined by the limit argument
    (defaults to 20)::

        /api/v1/feed/?limit=20

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

    statuses = Status.query.filter(Status.reply_to == None).\
    order_by(db.desc(Status.created)).limit(limit)

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


@blueprint.route('/status/', methods=['POST'])
@api_key_required
def create_status():
    """Post a new status.

    The status should be posted as JSON using 'application/json' as
    the content type. The posted JSON needs to have 3 required fields:

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

    # If this is a reply make sure that the status being replied to
    # exists and is not itself a reply
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
            slug=slugify(username), github_handle=username)
        db.session.add(user)
        db.session.commit()

    # Get or create the project (but not if this is a reply)
    if project_slug and not replied:
        # This forces the slug to be slug-like.
        project_slug = slugify(project_slug)
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


@blueprint.route('/status/<id>/', methods=['DELETE'])
@api_key_required
def delete_status(id):
    """Delete an existing status

    The status to be deleted should be posted as JSON using
    'application/json as the content type. The posted JSON needs to
    have 2 required fields:

    * user (the username)
    * api_key

    An example of the JSON::

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
        return make_response(jsonify(dict(error='Status does not exist.')),
            400)

    if not status[0].user.username == user:
        return make_response(
            jsonify(dict(error='You cannot delete this status.')), 403)

    status.delete()
    db.session.commit()

    return make_response(jsonify(dict(id=id)))


@blueprint.route('/user/<username>/', methods=['POST'])
@api_key_required
def update_user(username):
    """Update settings for an existing user.

    The settings to be deleted should be posted as JSON using
    'application/json as the content type. The posted JSON needs to
    have 2 required fields:

    * user (the username of the IRC user)
    * api_key

    You may optionally supply the following settings to overwrite
    their values:

    * name
    * email
    * github_handle

    An example of the JSON::

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
        user = User(username=username, slug=slugify(username))
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
