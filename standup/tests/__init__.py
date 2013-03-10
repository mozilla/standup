import json
import unittest
from collections import OrderedDict
from functools import wraps

from flask import current_app, Request
from standup import test_settings
from standup.apps.status.models import Project, Status
from standup.apps.users.models import Team, User
from standup.database import get_session
from standup.database.classes import Model
from standup.main import create_app
from werkzeug.test import create_environ


testing_app = create_app(test_settings)
testing_app.config['TESTING'] = True


class BaseTestCase(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(BaseTestCase, self).__init__(*args, **kwargs)
        self.app = testing_app

    def setUp(self):
        super(BaseTestCase, self).setUp()
        self.client = self.app.test_client()
        for app in self.app.installed_apps:
            try:
                __import__('%s.models' % app)
            except ImportError:
                pass
        db = get_session(self.app)
        Model.metadata.create_all(db.bind)

    def tearDown(self):
        db = get_session(self.app)
        Model.metadata.drop_all(db.bind)
        db.close()


def with_save(func):
    """Decorate a model maker to add a `save` kwarg.

    If save=True, the model maker will save the object before returning it.

    """
    @wraps(func)
    def saving_func(*args, **kwargs):
        save = kwargs.pop('save', False)
        ret = func(*args, **kwargs)
        if save:
            db = get_session(current_app)
            db.add(ret)
            db.commit()
        return ret

    return saving_func


@with_save
def project(**kwargs):
    """Model maker for Project"""
    defaults = dict(name='Test Project',
                    slug='test-project')
    defaults.update(kwargs)

    return Project(**defaults)


@with_save
def user(**kwargs):
    """Model maker for User"""
    defaults = dict(username='jdoe',
                    name='John Doe',
                    email='john@doe.com',
                    slug='jdoe')
    defaults.update(kwargs)

    return User(**defaults)


@with_save
def status(**kwargs):
    """Model maker for Status"""
    defaults = dict(content='This is a status update.',
                    content_html='This is a status update.')
    defaults.update(kwargs)

    if 'user' not in kwargs and 'user_id' not in kwargs:
        defaults['user'] = user(save=True)

    if 'project' not in kwargs and 'project_id' not in kwargs:
        defaults['project'] = project(save=True)

    return Status(**defaults)


@with_save
def team(**kwargs):
    """Model marker for Team"""
    defaults = dict(name='Test Team', slug='test-team')
    defaults.update(kwargs)

    return Team(**defaults)


def load_json(str):
    """Loads JSON to an ordered dict"""
    return json.JSONDecoder(object_pairs_hook=OrderedDict).decode(str)


def create_request(*args, **kwargs):
    """Creates a test request object"""
    env = create_environ(*args, **kwargs)
    return Request(env)
