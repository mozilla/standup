#!/usr/bin/env python
import os
from flask.ext.script import Manager
from migrate.exceptions import DatabaseAlreadyControlledError
from migrate.versioning import api as migrate_api
from standup.app import app

manager = Manager(app)

app_path = os.path.join(os.path.relpath(os.path.dirname(
    os.path.abspath(__file__)), os.getcwd()), 'standup')
sqlite = os.path.join(app_path, 'standup_app.db')

db_repo = os.path.join(app_path, 'migrations')
db_url = os.environ.get('DATABASE_URL', 'sqlite:///%s' % sqlite)

def get_db_version():
    return migrate_api.db_version(url=db_url, repository=db_repo)

@manager.command
def db_create():
    """Create the database"""
    try:
        migrate_api.version_control(url=db_url, repository=db_repo)
        db_upgrade()
    except DatabaseAlreadyControlledError:
        print 'ERROR: Database is already version controlled.'

@manager.command
def db_downgrade(version):
    """Downgrade the database"""
    v1 = get_db_version()
    migrate_api.downgrade(url=db_url, repository=db_repo, version=version)
    v2 = get_db_version()

    if v1 == v2:
        print 'No changes made.'
    else:
        print 'Downgraded: %s ... %s' % (v1, v2)

@manager.command
def db_upgrade():
    """Upgrade the database"""
    v1 = get_db_version()
    migrate_api.upgrade(url=db_url, repository=db_repo)
    v2 = get_db_version()

    if v1 == v2:
        print 'Database already up-to-date.'
    else:
        print 'Upgraded: %s ... %s' % (v1, v2)

@manager.command
def db_version():
    """Get the current version of the database"""
    print get_db_version()

@manager.command
def new_migration(description):
    migrate_api.script(description, db_repo)
    print 'New migration script created.'

if __name__ == '__main__':
    manager.run()
