import browserid
from flask import (Blueprint, current_app, flash, redirect, render_template,
                   request, session, url_for)
from standup import csrf
from standup.apps.users.forms import ProfileForm
from standup.apps.users.models import User
from standup.database import get_session
from standup.errors import forbidden
from standup.utils import jsonify
from werkzeug.datastructures import MultiDict


blueprint = Blueprint('users', __name__)


@blueprint.route('/authenticate', methods=['POST'])
@csrf.exempt
def authenticate():
    """Authenticate user with Persona."""
    app = current_app
    db = get_session(app)

    data = browserid.verify(request.form['assertion'],
                            app.config.get('SITE_URL'))
    email = data['email']
    session['email'] = email

    # Create a user if one does not already exist for this email
    # address.
    user = db.query(User).filter_by(email=email).first()
    if user:
        session['user_id'] = user.id

    return jsonify({'email': email})


@blueprint.route('/logout', methods=['POST'])
@csrf.exempt
def logout():
    """Log user out of app."""
    session.pop('email')
    session.pop('user_id')
    return jsonify({'message': 'logout successful'})


@blueprint.route('/profile/', methods=['GET', 'POST'])
def profile():
    """Shows the user's profile page."""
    db = get_session(current_app)

    user_id = session.get('user_id')
    if not user_id:
        return forbidden('You must be logged in to see a profile!')

    user = db.query(User).get(user_id)

    if request.method == 'POST':
        data = request.form
    else:
        data = MultiDict(user.dictify())

    form = ProfileForm(data)

    if request.method == 'POST' and form.validate():
        user.name = data['name']
        user.username = data['username']
        user.slug = data['username']
        user.github_handle = data['github_handle']
        db.add(user)
        db.commit()
        flash('Your profile was updated.', 'success')

    return render_template('users/profile.html', form=form)


@blueprint.route('/profile/new/', methods=['GET', 'POST'])
def new_profile():
    """Create a new user profile"""
    if (not (session or request.method == 'POST') or 'user_id' in session
            or not ('email' in session or 'email' in request.form)):
        return redirect(url_for('status.index'))

    data = MultiDict()
    try:
        data['email'] = session['email']
        session.pop('email')
    except KeyError:
        pass

    if request.method == 'POST':
        data = request.form

    form = ProfileForm(data)

    if request.method == 'POST' and form.validate():
        db = get_session(current_app)
        u = User(name=data['name'], email=data['email'],
                 username=data['username'], slug=data['username'],
                 github_handle=data['github_handle'])
        db.add(u)
        db.commit()

        session['email'] = u.email
        session['user_id'] = u.id

        flash('Your profile was created.', 'success')

        return redirect(url_for('status.index'))

    return render_template('users/new_profile.html', form=form)
