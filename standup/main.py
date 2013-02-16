import os
from datetime import date, timedelta

from flask import Flask, request, session
from flask.ext.markdown import Markdown
from flask.ext.sqlalchemy import SQLAlchemy

from standup.errors import register_error_handlers
from standup.filters import register_filters


db = SQLAlchemy()


def create_app(settings):
    app = Flask(__name__)
    app.debug = getattr(settings, 'DEBUG', False)
    app.config['SITE_TITLE'] = getattr(settings, 'SITE_TITLE', 'Standup')
    app.config['SQLALCHEMY_DATABASE_URI'] = getattr(
        settings, 'DATABASE_URL',
        os.environ.get('DATABASE_URL', 'sqlite:///standup_app.db'))
    app.secret_key = settings.SESSION_SECRET
    Markdown(app)
    db.app = app
    db.init_app(app)

    # Register error handlers
    register_error_handlers(app)

    # Register template filters
    register_filters(app)

    # Register blueprints
    for blueprint in settings.BLUEPRINTS:
        app.register_blueprint(
            getattr(
                __import__(blueprint, fromlist=['blueprint']), 'blueprint'))

    @app.context_processor
    def inject_page():
        return dict(page=int(request.args.get('page', 1)))

    @app.before_request
    def bootstrap():
        # Imports happen here to avoid circular import
        from standup.apps.status.models import Project
        from standup.apps.users.models import Team, User

        # Jinja global variables
        projects = Project.query.order_by(Project.name).all()
        teams = Team.query.order_by(Team.name).all()

        if session:
            user = User.query.filter(User.email == session['email']).first()
        else:
            user = None

        app.jinja_env.globals.update(projects=list(projects), teams=teams,
                                     current_user=user, today=date.today(),
                                     yesterday=date.today() - timedelta(1))

    return app
