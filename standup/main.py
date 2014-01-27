from datetime import date, timedelta
from types import FunctionType, ModuleType

from flask import Flask, redirect, request, session, url_for
from flask.ext.funnel import Funnel
from flask.ext.markdown import Markdown
from flask.ext.seasurf import SeaSurf
from standup.apps.status.helpers import get_weeks
from standup.apps.status.models import Project
from standup.apps.users.models import Team, User
from standup.database import get_session
from standup.errors import register_error_handlers
from standup.filters import register_filters
from standup.mdext import nixheaders


csrf = SeaSurf()


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

    # Markdown
    md = Markdown(app)
    # TODO: We might want to expose Markdown extensions to the config
    # file.
    md.register_extension(nixheaders.makeExtension)

    # Flask-Funnel
    Funnel(app)

    # SeaSurf
    csrf.init_app(app)

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

    @app.context_processor
    def globals():
        db = get_session(app)

        ctx = dict()

        # Projects, teams and current user
        ctx['projects'] = db.query(Project).order_by(Project.name)
        ctx['teams'] = db.query(Team).order_by(Team.name)
        ctx['weeks'] = get_weeks()
        ctx['current_user'] = None
        if session and 'user_id' in session:
            user = db.query(User).get(session['user_id'])
            if user:
                ctx['current_user'] = user

        # Time stuff
        ctx['today'] = date.today()
        ctx['yesterday'] = date.today() - timedelta(1)

        # CSRF
        def csrf_field():
            return ('<div style="display: none;">'
                    '<input type="hidden" name="_csrf_token" value="%s">'
                    '</div>' % csrf._get_token())
        ctx['csrf'] = csrf_field

        return ctx

    @app.before_request
    def validate_user():
        db = get_session(app)

        if session and 'email' in session and not 'user_id' in session:
            user = db.query(User).filter_by(email=session['email']).first()

            if not user:
                if request.endpoint not in ('users.new_profile',
                                            'users.authenticate',
                                            'users.logout',
                                            'static'):
                    return redirect(url_for('users.new_profile'))

    @app.teardown_request
    def teardown_request(exception=None):
        # Remove the database session if it exists
        if hasattr(app, 'db_session'):
            app.db_session.close()

    return app
