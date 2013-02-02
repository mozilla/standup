import browserid
from flask import Blueprint, jsonify, request, session
from standup import settings
from standup.utils import slugify
from standup.app import db
from standup.apps.users.models import User

blueprint = Blueprint('users', __name__)

@blueprint.route('/authenticate', methods=['POST'])
def authenticate():
    """Authenticate user with Persona."""
    data = browserid.verify(request.form['assertion'],
        settings.SITE_URL)
    email = data['email']
    session['email'] = email

    user = User.query.filter(User.email == email).first()

    # Create a user if one does not already exist for this email
    # address.
    user = User.query.filter_by(email=email).first()
    if not user:
        # TODO: We assume the user wants the first part of their email
        # address to be their username. Good idea? Probably not.
        username = email.split('@')[0]
        user = User(username=username, name=username, email=email,
            slug=slugify(username), github_handle=username)
        db.session.add(user)
        db.session.commit()

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
