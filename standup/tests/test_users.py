import json

from mock import patch
from nose.tools import eq_
from standup.apps.users.models import User
from standup.database import get_session
from standup.tests import BaseTestCase, status, team, user


class ModelsTestCase(BaseTestCase):
    def test_user_repr(self):
        """Test the __repr__ function of the User model."""
        with self.app.app_context():
            u = user(username='testuser', name='Testy Testerson', save=True)

        eq_(repr(u), '<User: [testuser] Testy Testerson>')

    def test_user_recent_statuses(self):
        """Test loading of recent statuses for a project."""
        with self.app.app_context():
            u = user(save=True)

            # Create 30 statuses
            for i in range(30):
                s = status(project=None, user=u, save=True)

            # Create 30 replies
            for i in range(30):
                status(project=None, user=u, reply_to=s, save=True)

            # Should not include replies
            page = u.recent_statuses()
            eq_(page.pages, 2)

    def test_team_repr(self):
        """Test the __repr__ function of the Team model."""
        with self.app.app_context():
            t = team(name='A-Team')

        eq_(repr(t), '<Team: A-Team>')

    def test_team_recent_statuses(self):
        """Test loading of recent statuses for a project."""
        with self.app.app_context():
            t = team(save=True)
            u = user(teams=[t], save=True)
            u2 = user(username='troll', slug='troll', email='s@dav.com',
                      save=True)

            # Create 30 statuses
            for i in range(30):
                s = status(project=None, user=u, save=True)

            # Create 30 replies
            for i in range(30):
                status(project=None, user=u, reply_to=s, save=True)

            # Create 30 statuses for user not in team
            for i in range(10):
                status(project=None, user=u2, save=True)

            # Should not include replies
            page = t.recent_statuses()
            eq_(page.pages, 2)


class ViewsTestCase(BaseTestCase):
    def test_authenticate(self):
        """Test that the authentication view works."""
        with self.app.app_context():
            u = user(save=True)

        with patch('browserid.verify') as mocked:
            mocked.return_value = {'email': u.email}
            eq_(mocked()['email'], u.email)

            response = self.client.post('/authenticate',
                                        data={'assertion': ''})
            eq_(response.status_code, 200)
            data = json.loads(response.data)
            assert 'email' in data
            eq_(data['email'], u.email)

        with self.client.session_transaction() as sess:
            eq_(sess['email'], u.email)

    def test_authenticate_create_user(self):
        """Test that a new user is created by the authentication view"""
        with patch('browserid.verify') as mocked:
            mocked.return_value = {'email': 'john@doe.com'}
            eq_(mocked()['email'], 'john@doe.com')

            response = self.client.post('/authenticate',
                                        data={'assertion': ''})
            eq_(response.status_code, 200)
            data = json.loads(response.data)
            assert 'email' in data

        db = get_session(self.app)
        u = db.query(User).filter_by(email=data['email'])
        eq_(u.count(), 1)

    def test_login(self):
        """Test the login view."""
        with self.app.app_context():
            u = user(save=True)

        with self.client.session_transaction() as sess:
            sess['email'] = u.email

        response = self.client.post('/logout')
        eq_(response.status_code, 200)
        assert 'logout successful' in response.data

        with self.client.session_transaction() as sess:
            assert 'email' not in sess
