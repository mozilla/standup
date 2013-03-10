from datetime import date, timedelta
from types import FunctionType, ModuleType

from flask import Flask, request, session
from flask.ext.funnel import Funnel
from flask.ext.markdown import Markdown

from standup.apps.status.models import Project
from standup.apps.users.models import Team, User
from standup.database import get_session
from standup.errors import register_error_handlers
from standup.filters import register_filters
from standup.mdext import nixheaders


def _get_apps_full_names(apps):
    names = []
    for app in apps:
        parts = []
        if not __name__ == '__main__':
            parts = __name__.split('.')
            parts.pop()
        parts.append('apps')
        parts.append(app)

        names.append('.'.join(parts))
    return names


def create_app(settings):
    app = Flask(__name__)

    # Import settings from file
    for name in dir(settings):
        value = getattr(settings, name)
        if not (name.startswith('_') or isinstance(value, ModuleType)
                or isinstance(value, FunctionType)):
            app.config[name] = value

    # Additional settings
    app.installed_apps = _get_apps_full_names(settings.INSTALLED_APPS)
    app.secret_key = app.config.get('SESSION_SECRET')

    #Markdown
    md = Markdown(app)
    # TODO: We might want to expose Markdown extensions to the config
    # file.
    md.register_extension(nixheaders.makeExtension)

    #Flask-Funnel
    Funnel(app)

    # Register error handlers
    register_error_handlers(app)

    # Register template filters
    register_filters(app)

    for a in app.installed_apps:
        # Register blueprints
        app.register_blueprint(
            getattr(__import__('%s.views' % a, fromlist=['blueprint']),
                    'blueprint'))

    @app.context_processor
    def inject_page():
        return dict(page=int(request.args.get('page', 1)))

    @app.before_request
    def bootstrap():
        # Jinja global variables
        db = get_session(app)
        projects = db.query(Project).order_by(Project.name).all()
        teams = db.query(Team).order_by(Team.name).all()

        if session:
            user = db.query(User).filter_by(email=session['email']).first()
        else:
            user = None

        app.jinja_env.globals.update(projects=list(projects), teams=teams,
                                     current_user=user, today=date.today(),
                                     yesterday=date.today() - timedelta(1))

    @app.teardown_request
    def teardown_request(exception=None):
        # Remove the database session if it exists
        if hasattr(app, 'db_session'):
            app.db_session.close()

    return app
