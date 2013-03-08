from flask import abort
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from standup.database.classes import Pagination


def get_session(app):
    if not hasattr(app, 'db_session'):
        # Create the engine
        engine = create_engine(app.config.get('DATABASE_URL'),
                               convert_unicode=True)

        # Create a session
        Session = sessionmaker(bind=engine, autocommit=False, autoflush=False)
        app.db_session = Session()

    return app.db_session


def paginate(query, page, per_page=20, error_out=True):
    """Returns `per_page` items from page `page`."""
    if error_out and page < 1:
        abort(404)
    items = query.limit(per_page).offset((page - 1) * per_page).all()
    if not items and page != 1 and error_out:
        abort(404)
    return Pagination(query, page, per_page, query.count(), items)
