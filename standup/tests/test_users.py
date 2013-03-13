import simplejson as json
from mock import patch
from nose.tools import eq_
from standup.apps.users.models import User
from standup.database import get_session
from standup.tests import BaseTestCase, login, status, team, user


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

    def test_login(self):
        """Test the login view."""
        with self.app.app_context():
            u = user(save=True)

        login(self.client, u)

        response = self.client.post('/logout')
        eq_(response.status_code, 200)
        assert 'logout successful' in response.data

        with self.client.session_transaction() as sess:
            assert 'email' not in sess
            assert 'user_id' not in sess

    def test_new_profile_redirect(self):
        """Test that non existant users get redirected to profile creation."""
        with self.client.session_transaction() as sess:
            sess['email'] = 'new.user@test.com'

        response = self.client.get('/')
        eq_(response.status_code, 302)
        eq_(response.location, 'http://localhost/profile/new/')

    def test_new_profile(self):
        """Test the new profile page."""
        response = self.client.get('/profile/new/')
        eq_(response.status_code, 302)

        with self.client.session_transaction() as sess:
            sess['email'] = 'new.user@test.com'

        response = self.client.get('/profile/new/')
        eq_(response.status_code, 200)

        with self.app.app_context():
            u = user(save=True)

        login(self.client, u)

        response = self.client.get('/profile/new/')
        eq_(response.status_code, 302)

    def test_new_profile_create(self):
        """Test new profile creation."""
        data = {'email': 'test@test.com', 'username': 'new-username',
                'github_handle': 'test-handle', 'name': 'Test User'}

        response = self.client.post('/profile/new/', data=data)
        eq_(response.status_code, 302)

        db = get_session(self.app)
        u = db.query(User).filter_by(email='test@test.com')
        eq_(u.count(), 1)

        u = u.first()
        eq_(u.username, 'new-username')
        eq_(u.github_handle, 'test-handle')
        eq_(u.name, 'Test User')

    def test_new_profile_create_missing_data(self):
        """Test profile creation attempts with missing data."""
        db = get_session(self.app)
        u = db.query(User)

        # No email
        data = {'email': '', 'username': 'new-username',
                'github_handle': 'test-handle', 'name': 'Test User'}
        response = self.client.post('/profile/new/', data=data)
        eq_(response.status_code, 200)
        eq_(u.count(), 0)

        # No username
        data = {'email': 'test@test.com', 'username': '',
                'github_handle': 'test-handle', 'name': 'Test User'}
        response = self.client.post('/profile/new/', data=data)
        eq_(response.status_code, 200)
        eq_(u.count(), 0)

        # No name
        data = {'email': 'test@test.com', 'username': 'new-username',
                'github_handle': 'test-handle', 'name': ''}
        response = self.client.post('/profile/new/', data=data)
        eq_(response.status_code, 200)
        eq_(u.count(), 0)

        # No GitHub handle
        data = {'email': 'test@test.com', 'username': 'new-username',
                'github_handle': '', 'name': 'Test User'}
        response = self.client.post('/profile/new/', data=data)
        eq_(response.status_code, 302)
        eq_(u.count(), 1)


class ProfileTestCase(BaseTestCase):
    def test_profile_unauthenticated(self):
        """Test that you can't see profile page if you're not logged in."""
        response = self.client.get('/profile/')
        eq_(response.status_code, 403)

    def test_profile_authenticated(self):
        """Test that you can see profile page if you are logged in."""
        with self.app.app_context():
            u = user(email='joe@example.com', save=True)

        login(self.client, u)

        response = self.client.get('/profile/')
        eq_(response.status_code, 200)

    def test_profile_update(self):
        """Test that you can update your profile."""
        with self.app.app_context():
            u = user(save=True)

        login(self.client, u)

        data = {'email': u.email, 'username': 'new-username',
                'github_handle': 'test-handle', 'name': 'Test User'}

        response = self.client.post('/profile/', data=data)
        eq_(response.status_code, 200)

        db = get_session(self.app)
        u = db.query(User).get(u.id)

        eq_(u.username, 'new-username')
        eq_(u.github_handle, 'test-handle')
        eq_(u.name, 'Test User')
