import browserid
from flask import Blueprint, current_app, jsonify, request, session

from standup import settings
from standup.apps.users.models import User
from standup.database import get_session
from standup.utils import slugify


blueprint = Blueprint('users', __name__)


@blueprint.route('/authenticate', methods=['POST'])
def authenticate():
    """Authenticate user with Persona."""
    db = get_session(current_app)

    data = browserid.verify(request.form['assertion'],
        settings.SITE_URL)
    email = data['email']
    session['email'] = email

    user = db.query(User).filter(User.email == email).first()

    # Create a user if one does not already exist for this email
    # address.
    user = db.query(User).filter_by(email=email).first()
    if not user:
        # TODO: We assume the user wants the first part of their email
        # address to be their username. Good idea? Probably not.
        username = email.split('@')[0]
        user = User(username=username, name=username, email=email,
            slug=slugify(username), github_handle=username)
        db.add(user)
        db.commit()

    response = jsonify({'email': user.email})
    response.status_code = 200
    return response


@blueprint.route('/logout', methods=['POST'])
def logout():
    """Log user out of app."""
    session.pop('email', None)
    response = jsonify({'message': 'logout successful'})
    response.status_code = 200
    return response
