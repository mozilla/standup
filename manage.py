#!/usr/bin/env python
from flask import Flask
from flask.ext.script import Manager

from standup.app import app, db

manager = Manager(app)

@manager.command
def createdb():
    """Create the database."""
    db.create_all()


if __name__ == '__main__':
    manager.run()
