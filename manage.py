#!/usr/bin/env python
import os

from flask.ext.script import Manager
from migrate.exceptions import DatabaseAlreadyControlledError
from migrate.versioning import api as migrate_api

from standup.app import db
from standup.run import app
from standup.apps.status.models import Project, Status
from standup.apps.users.models import Team, User
from standup.utils import slugify


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
    """Create a new migration"""
    migrate_api.script(description, db_repo)
    print 'New migration script created.'


@manager.command
def add_team(name, slug=None):
    """Creates a team."""
    if slug == None:
        slug = slugify(name)

    team = Team.query.filter_by(slug=slug).first()
    if team:
        print 'Team "%s" (%s) already exists.' % (team.name, team.slug)
        return

    team = Team(name=name, slug=slug)
    db.session.add(team)
    db.session.commit()

    print 'Team "%s" created!' % team.name


@manager.command
def add_project(name, slug=None, repo_url=None, color=None):
    """Creates a project."""
    if slug == None:
        slug = slugify(name)

    if repo_url == None:
        repo_url = ''

    if color == None:
        color = 'FF0000'

    project = Project.query.filter_by(slug=slug).first()
    if project:
        print 'Project "%s" (%s) already exists.' % (project.name, project.slug)
        return

    project = Project(name=name, slug=slug, repo_url=repo_url, color=color)
    db.session.add(project)
    db.session.commit()

    print 'Project "%s" created!' % project.name


@manager.command
def stats():
    """Tells you stats about your standup instance."""
    print 'STATS'
    print ''

    print 'DB version: %s' % get_db_version()
    print 'Users:      %d' % len(User.query.all())
    print 'Statuses:   %d' % len(Status.query.all())
    print ''

    teams = Team.query.all()
    print 'Teams:      %d' % len(teams)
    for team in teams:
        print '  %s: %s' % (team.name, team.slug)

    print ''

    projects = Project.query.all()
    print 'Projects:   %d' % len(projects)
    for project in projects:
        print '  %s: %s, %s, %s' % (project.name, project.slug,
                                    project.repo_url, project.color)


if __name__ == '__main__':
    manager.run()
