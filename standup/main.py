from datetime import date, timedelta
from types import FunctionType, ModuleType

from flask import Flask, request, session
from flask.ext.funnel import Funnel
from flask.ext.markdown import Markdown
from flask.ext.sqlalchemy import SQLAlchemy

from standup.errors import register_error_handlers
from standup.filters import register_filters
from standup.mdext import nixheaders


db = SQLAlchemy()


def create_app(settings):
    app = Flask(__name__)

    # Import settings from file
    for name in dir(settings):
        value = getattr(settings, name)
        if not (name.startswith('_') or isinstance(value, ModuleType)
                or isinstance(value, FunctionType)):
            app.config[name] = value

    # Additional settings
    app.config['SQLALCHEMY_DATABASE_URI'] = app.config.get('DATABASE_URL')
    app.secret_key = app.config.get('SESSION_SECRET')

    md = Markdown(app)
    # TODO: We might want to expose Markdown extensions to the config
    # file.
    md.register_extension(nixheaders.makeExtension)

    db.app = app
    db.init_app(app)

    Funnel(app)

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
