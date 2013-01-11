import json
import os
import tempfile
import unittest

from nose.tools import ok_, eq_

from standup import app
from standup.app import User, Project, Status, format_update, TAG_TMPL
from standup import settings
from standup.tests import status, user


class AppTestCase(unittest.TestCase):

    def setUp(self):
        self.db_fd, app.app.config['DATABASE'] = tempfile.mkstemp()
        app.app.config['SQLALCHEMY_DATABASE_URI'] = ('sqlite:///%s' %
            app.app.config['DATABASE'])
        app.app.config['TESTING'] = True
        self.app = app.app.test_client()
        app.db.create_all()

    def tearDown(self):
        app.db.session.remove()
        os.close(self.db_fd)
        os.unlink(app.app.config['DATABASE'])


class KungFuActionGripProfileTestCase(AppTestCase):
    def test_profile_unauthenticated(self):
        with app.app.test_client() as tc:
            rv = tc.get('/profile/')
            eq_(rv.status_code, 403)

    def test_profile_authenticationified(self):
        with app.app.test_client() as tc:
            with tc.session_transaction() as sess:
                sess['email'] = 'joe@example.com'

            rv = tc.get('/profile/')
            eq_(rv.status_code, 200)


class StatusizerTestCase(AppTestCase):
    def test_status_unauthenticated(self):
        """Test that you get a 403 if you're not authenticated."""
        with app.app.test_client() as tc:
            rv = tc.post('/statusize/',
                         data={'message': 'foo'},
                         follow_redirects=True)
            eq_(rv.status_code, 403)

    def test_status(self):
        """Test posting a status."""
        with app.app.test_client() as tc:
            with tc.session_transaction() as sess:
                sess['email'] = 'joe@example.com'

            rv = tc.post('/statusize/',
                         data={'message': 'foo'},
                         follow_redirects=True)
            eq_(rv.status_code, 200)

    def test_status_no_message(self):
        """Test posting a status with no message."""
        with app.app.test_client() as tc:
            with tc.session_transaction() as sess:
                sess['email'] = 'joe@example.com'

            rv = tc.post('/statusize/',
                         data={'message': ''},
                         follow_redirects=True)
            # This kicks up a 404, but that's lame.
            eq_(rv.status_code, 404)

    def test_status_with_project(self):
        """Test posting a status with no message."""
        p = Project(name='blackhole', slug='blackhole')
        app.db.session.add(p)
        app.db.session.commit()
        pid = p.id

        with app.app.test_client() as tc:
            with tc.session_transaction() as sess:
                sess['email'] = 'joe@example.com'

            rv = tc.post('/statusize/',
                         data={'message': 'r1cky rocks!', 'project': pid},
                         follow_redirects=True)
            eq_(rv.status_code, 200)


class APITestCase(AppTestCase):
    def test_create_first_status(self):
        """Test creating the very first status for a project and user."""
        data = json.dumps({
            'api_key': settings.API_KEY,
            'user': 'r1cky',
            'project': 'sumodev',
            'content': 'bug 123456'})
        response = self.app.post(
            '/api/v1/status/', data=data, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        assert 'bug 123456' in response.data

        # Verify the user was created.
        self.assertEqual(User.query.first().username, 'r1cky')
        # Verify the project was created.
        self.assertEqual(Project.query.first().slug, 'sumodev')
        # Verify the status was created.
        self.assertEqual(Status.query.first().content, 'bug 123456')

    def test_format_update(self):
        p = Project(name='mdndev', slug='mdndev',
                    repo_url='https://github.com/mozilla/kuma')
        app.db.session.add(p)
        app.db.session.commit()
        content = "#merge pull #1 and pR 2 to fix bug #3 and BUg 4"
        formatted_update = format_update(content, project=p)
        ok_('tag-merge' in formatted_update)
        ok_('pull/1' in formatted_update)
        ok_('pull/2' in formatted_update)
        ok_('show_bug.cgi?id=3' in formatted_update)
        ok_('show_bug.cgi?id=4' in formatted_update)

    def test_create_status_validation(self):
        """Verify validation of required fields."""
        # Missing user
        data = json.dumps({
            'api_key': settings.API_KEY,
            'project': 'sumodev',
            'content': 'bug 123456'})
        response = self.app.post(
            '/api/v1/status/', data=data, content_type='application/json')
        self.assertEqual(response.status_code, 400)

        # Missing content
        data = json.dumps({
            'api_key': settings.API_KEY,
            'user': 'r1cky',
            'project': 'sumodev'})
        response = self.app.post(
            '/api/v1/status/', data=data, content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_create_status_invalid_api_key(self):
        """Request with invalid API key should return 403."""
        data = json.dumps({
            'api_key': settings.API_KEY + '123',
            'user': 'r1cky',
            'project': 'sumodev',
            'content': 'bug 123456'})
        response = self.app.post(
            '/api/v1/status/', data=data, content_type='application/json')
        self.assertEqual(response.status_code, 403)

    def test_create_status_missing_api_key(self):
        """Request without an API key should return 403."""
        data = json.dumps({
            'user': 'r1cky',
            'project': 'sumodev',
            'content': 'bug 123456'})
        response = self.app.post(
            '/api/v1/status/', data=data, content_type='application/json')
        self.assertEqual(response.status_code, 403)

    def test_create_status_no_project(self):
        """Statuses can be created without a project"""
        data = json.dumps({
            'api_key': settings.API_KEY,
            'user': 'r1cky',
            'content': 'test update'})
        response = self.app.post(
            '/api/v1/status/', data=data, content_type='application/json')
        self.assertEqual(response.status_code, 200)

        # Verify the status was created
        self.assertEqual(Status.query.first().content, 'test update')

    def test_create_reply(self):
        """Test creation of replies"""
        s = status(save=True)
        sid = s.id

        data = json.dumps({
            'api_key': settings.API_KEY,
            'user': 'r1cky',
            'content': 'reply to status',
            'reply_to': sid})
        response = self.app.post(
            '/api/v1/status/', data=data, content_type='application/json')
        self.assertEqual(response.status_code, 200)

        # Verify that the status is actually a reply
        r = Status.query.filter(Status.reply_to_id==sid).first()
        self.assertEqual(r.content, 'reply to status')

        # Verify that the reply is included in the list of replies
        s = Status.query.get(sid)
        assert r in s.replies().items

        # You should not be able to reply to the reply
        data = json.dumps({
            'api_key': settings.API_KEY,
            'user': 'r1cky',
            'content': 'should not work',
            'reply_to': r.id})
        response = self.app.post(
            '/api/v1/status/', data=data, content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_delete_status(self):
        """Test deletion of a status"""
        s = status(save=True)
        id = s.id

        data = json.dumps({
            'api_key': settings.API_KEY,
            'user': s.user.username})
        response = self.app.delete(
            '/api/v1/status/%s/' % s.id, data=data,
            content_type='application/json')
        self.assertEqual(response.status_code, 200)

        # Verify the status was deleted
        self.assertEqual(Status.query.get(id), None)

    def test_delete_status_validation(self):
        """Verify validation of required fields"""
        s = status(save=True)

        # Missing user
        data = json.dumps({'api_key': settings.API_KEY})
        response = self.app.delete(
            '/api/v1/status/%s/' % s.id, data=data,
            content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_delete_status_unauthorized(self):
        """Test that only user who created the status can delete it"""
        s = status(save=True)
        data = json.dumps({
            'api_key': settings.API_KEY,
            'user': s.user.username + '123'})
        response = self.app.delete(
            '/api/v1/status/%s/' % s.id, data=data,
            content_type='application/json')
        self.assertEqual(response.status_code, 403)

    def test_delete_status_invalid_api_key(self):
        """Request with invalid API key should return 403"""
        s = status(save=True)
        data = json.dumps({
            'api_key': settings.API_KEY + '123',
            'user': s.user.username})
        response = self.app.delete(
            '/api/v1/status/%s/' % s.id, data=data,
            content_type='application/json')
        self.assertEqual(response.status_code, 403)

    def test_delete_status_missing_api_key(self):
        """Request with missing API key should return 403"""
        s = status(save=True)
        data = json.dumps({'user': s.user.username})
        response = self.app.delete(
            '/api/v1/status/%s/' % s.id, data=data,
            content_type='application/json')
        self.assertEqual(response.status_code, 403)

    def test_update_user(self):
        """Test that a user can update their own settings"""
        u = user(save=True)
        id = u.id

        data = json.dumps({
            'api_key': settings.API_KEY,
            'user': u.username,
            'email': 'test@test.com',
            'github_handle': 'test',
            'name': 'Test'})
        response = self.app.post(
            '/api/v1/user/%s/' % u.username, data=data,
            content_type='application/json')
        self.assertEqual(response.status_code, 200)

        u = User.query.get(id)

        self.assertEqual(u.email, 'test@test.com')
        self.assertEqual(u.github_handle, 'test')
        self.assertEqual(u.name, 'Test')

    def test_update_user_by_admins(self):
        """Test that an admin can update another users settings and non-admins
        cannot update other users settings
        """
        u = user(save=True)
        a = user(username='admin', slug='admin', email='admin@mail.com',
                 is_admin=True, save=True)

        uid = u.id
        aid = a.id
        username = u.username

        data = json.dumps({
            'api_key': settings.API_KEY,
            'user': a.username,
            'email': 'test@test.com',
            'github_handle': 'test',
            'name': 'Test'})
        response = self.app.post(
            '/api/v1/user/%s/' % username, data=data,
            content_type='application/json')
        self.assertEqual(response.status_code, 200)

        u = User.query.get(uid)

        self.assertEqual(u.email, 'test@test.com')
        self.assertEqual(u.github_handle, 'test')
        self.assertEqual(u.name, 'Test')

        data = json.dumps({
            'api_key': settings.API_KEY,
            'user': username,
            'email': 'test@test.com'})
        response = self.app.post(
            '/api/v1/user/%s/' % aid, data=data,
            content_type='application/json')
        self.assertEqual(response.status_code, 403)

    def test_update_user_validation(self):
        """Verify validation of required fields"""
        u = user(save=True)

        # Missing user
        data = json.dumps({'api_key': settings.API_KEY})
        response = self.app.post(
            '/api/v1/user/%s/' % u.id, data=data,
            content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_update_user_invalid_api_key(self):
        """Request with invalid API key should return 403"""
        u = user(save=True)
        data = json.dumps({
            'api_key': settings.API_KEY + '123',
            'user': u.username})
        response = self.app.post(
            '/api/v1/user/%s/' % u.id, data=data,
            content_type='application/json')
        self.assertEqual(response.status_code, 403)


    def test_udate_user_invalid_api_key(self):
        """Request with invalid API key should return 403"""
        u = user(save=True)
        data = json.dumps({'user': u.username})
        response = self.app.post(
            '/api/v1/user/%s/' % u.id, data=data,
            content_type='application/json')
        self.assertEqual(response.status_code, 403)


class FormatUpdateTest(unittest.TestCase):
    def test_tags(self):
        # Test valid tags.
        for tag in ('#t', '#tag', '#TAG', '#tag123'):
            expected = '%s <div class="tags">%s</div>' % (tag, TAG_TMPL.format('', tag[1:]),)
            eq_(format_update(tag), expected)

        # Test invalid tags.
        for tag in ('#1', '#.abc', '#?abc'):
            eq_(format_update(tag), tag)
