import json
import os
import tempfile
import unittest

from standup import app
from standup.app import User, Project, Status
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

        # Missing project
        data = json.dumps({
            'api_key': settings.API_KEY,
            'user': 'r1cky',
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
            '/api/v1/user/%s/' % u.id, data=data,
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
            '/api/v1/user/%s/' % uid, data=data,
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
