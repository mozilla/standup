import json

from nose.tools import ok_, eq_
from standup.apps.status.models import Project, Status
from standup.apps.users.models import User
from standup.database import get_session
from standup.filters import format_update

from standup.tests import BaseTestCase, load_json, project, status, user


class APITestCase(BaseTestCase):
    def test_create_first_status(self):
        """Test creating the very first status for a project and user."""
        db = get_session(self.app)

        data = json.dumps({
            'api_key': self.app.config.get('API_KEY'),
            'user': 'r1cky',
            'project': 'sumodev',
            'content': 'bug 123456'})
        response = self.client.post('/api/v1/status/', data=data,
                                    content_type='application/json')
        eq_(response.status_code, 200)
        assert 'bug 123456' in response.data

        # Verify the user was created.
        eq_(db.query(User).first().username, 'r1cky')
        # Verify the project was created.
        eq_(db.query(Project).first().slug, 'sumodev')
        # Verify the status was created.
        eq_(db.query(Status).first().content, 'bug 123456')

    def test_format_update(self):
        db = get_session(self.app)

        p = Project(name='mdndev', slug='mdndev',
                    repo_url='https://github.com/mozilla/kuma')
        db.add(p)
        db.commit()
        content = "#merge pull #1 and pR 2 to fix bug #3 and BUg 4"
        formatted_update = format_update(content, project=p)
        ok_('tag-merge' in formatted_update)
        ok_('pull/1' in formatted_update)
        ok_('pull/2' in formatted_update)
        ok_('show_bug.cgi?id=3' in formatted_update)
        ok_('show_bug.cgi?id=4' in formatted_update)

    def test_create_status_validation(self):
        """Verify validation of required fields when creating a status"""
        # Missing user
        data = json.dumps({
            'api_key': self.app.config.get('API_KEY'),
            'project': 'sumodev',
            'content': 'bug 123456'})
        response = self.client.post('/api/v1/status/', data=data,
                                    content_type='application/json')
        eq_(response.status_code, 400)

        # Missing content
        data = json.dumps({
            'api_key': self.app.config.get('API_KEY'),
            'user': 'r1cky',
            'project': 'sumodev'})
        response = self.client.post('/api/v1/status/', data=data,
                                    content_type='application/json')
        eq_(response.status_code, 400)

    def test_create_status_invalid_api_key(self):
        """Request with invalid API key should return 403."""
        data = json.dumps({
            'api_key': self.app.config.get('API_KEY') + '123',
            'user': 'r1cky',
            'project': 'sumodev',
            'content': 'bug 123456'})
        response = self.client.post('/api/v1/status/', data=data,
                                    content_type='application/json')
        eq_(response.status_code, 403)

    def test_create_status_missing_api_key(self):
        """Request without an API key should return 403."""
        data = json.dumps({
            'user': 'r1cky',
            'project': 'sumodev',
            'content': 'bug 123456'})
        response = self.client.post('/api/v1/status/', data=data,
                                    content_type='application/json')
        eq_(response.status_code, 403)

    def test_create_status_no_project(self):
        """Statuses can be created without a project"""
        db = get_session(self.app)

        data = json.dumps({
            'api_key': self.app.config.get('API_KEY'),
            'user': 'r1cky',
            'content': 'test update'})
        response = self.client.post('/api/v1/status/', data=data,
                                    content_type='application/json')
        eq_(response.status_code, 200)

        # Verify the status was created
        eq_(db.query(Status).first().content, 'test update')

    def test_create_reply(self):
        """Test creation of replies"""
        db = get_session(self.app)

        with self.app.app_context():
            s = status(save=True)
            sid = s.id

            data = json.dumps({
                'api_key': self.app.config.get('API_KEY'),
                'user': 'r1cky',
                'content': 'reply to status',
                'reply_to': sid})
            response = self.client.post('/api/v1/status/', data=data,
                                        content_type='application/json')
            eq_(response.status_code, 200)

            # Verify that the status is actually a reply
            r = db.query(Status).filter(Status.reply_to_id == sid).first()
            eq_(r.content, 'reply to status')

            # Verify that the reply is included in the list of replies
            s = db.query(Status).get(sid)
            assert r in s.replies().items

            # You should not be able to reply to the reply
            data = json.dumps({
                'api_key': self.app.config.get('API_KEY'),
                'user': 'r1cky',
                'content': 'should not work',
                'reply_to': r.id})
            response = self.client.post('/api/v1/status/', data=data,
                                        content_type='application/json')
            eq_(response.status_code, 400)

            # You should not be able to reply to a status that does not exist
            data = json.dumps({
                'api_key': self.app.config.get('API_KEY'),
                'user': 'r1cky',
                'content': 'reply to status',
                'reply_to': 9999})
            response = self.client.post('/api/v1/status/', data=data,
                                        content_type='application/json')
            eq_(response.status_code, 400)

    def test_delete_status(self):
        """Test deletion of a status"""
        db = get_session(self.app)

        with self.app.app_context():
            s = status(save=True)

        id = s.id

        data = json.dumps({
            'api_key': self.app.config.get('API_KEY'),
            'user': s.user.username})
        response = self.client.delete('/api/v1/status/%s/' % s.id, data=data,
                                      content_type='application/json')
        eq_(response.status_code, 200)

        # Verify the status was deleted
        eq_(db.query(Status).get(id), None)

    def test_delete_status_validation(self):
        """Verify validation of required fields when deleting a status"""
        with self.app.app_context():
            s = status(save=True)

        # Missing user
        data = json.dumps({'api_key': self.app.config.get('API_KEY')})
        response = self.client.delete('/api/v1/status/%s/' % s.id, data=data,
                                      content_type='application/json')
        eq_(response.status_code, 400)

    def test_delete_status_unauthorized(self):
        """Test that only user who created the status can delete it"""
        with self.app.app_context():
            s = status(save=True)

        data = json.dumps({
            'api_key': self.app.config.get('API_KEY'),
            'user': s.user.username + '123'})
        response = self.client.delete('/api/v1/status/%s/' % s.id, data=data,
                                      content_type='application/json')
        eq_(response.status_code, 403)

    def test_delete_status_invalid_api_key(self):
        """Request with invalid API key should return 403"""
        with self.app.app_context():
            s = status(save=True)

        data = json.dumps({
            'api_key': self.app.config.get('API_KEY') + '123',
            'user': s.user.username})
        response = self.client.delete('/api/v1/status/%s/' % s.id, data=data,
                                      content_type='application/json')
        eq_(response.status_code, 403)

    def test_delete_status_missing_api_key(self):
        """Request with missing API key should return 403"""
        with self.app.app_context():
            s = status(save=True)

        data = json.dumps({'user': s.user.username})
        response = self.client.delete('/api/v1/status/%s/' % s.id, data=data,
                                      content_type='application/json')
        eq_(response.status_code, 403)

    def test_delete_status_does_not_exist(self):
        """Request to delete a non existent status should return 400"""
        with self.app.app_context():
            u = user(save=True)

        data = json.dumps({
            'api_key': self.app.config.get('API_KEY'),
            'user': u.username})
        response = self.client.delete('/api/v1/status/%s/' % 9999, data=data,
                                      content_type='application/json')
        eq_(response.status_code, 400)

    def test_update_user(self):
        """Test that a user can update their own settings"""
        db = get_session(self.app)

        with self.app.app_context():
            u = user(save=True)

        id = u.id

        data = json.dumps({
            'api_key': self.app.config.get('API_KEY'),
            'user': u.username,
            'email': 'test@test.com',
            'github_handle': 'test',
            'name': 'Test'})
        response = self.client.post('/api/v1/user/%s/' % u.username, data=data,
                                    content_type='application/json')
        eq_(response.status_code, 200)

        u = db.query(User).get(id)

        eq_(u.email, 'test@test.com')
        eq_(u.github_handle, 'test')
        eq_(u.name, 'Test')

    def test_update_user_by_admins(self):
        """Test that an admin can update another users settings and
        non-admins cannot update other users settings
        """
        db = get_session(self.app)

        with self.app.app_context():
            u = user(save=True)
            a = user(username='admin', slug='admin', email='admin@mail.com',
                     is_admin=True, save=True)

        uid = u.id
        aid = a.id
        username = u.username

        data = json.dumps({
            'api_key': self.app.config.get('API_KEY'),
            'user': a.username,
            'email': 'test@test.com',
            'github_handle': 'test',
            'name': 'Test'})
        response = self.client.post('/api/v1/user/%s/' % username, data=data,
                                    content_type='application/json')
        eq_(response.status_code, 200)

        u = db.query(User).get(uid)

        eq_(u.email, 'test@test.com')
        eq_(u.github_handle, 'test')
        eq_(u.name, 'Test')

        data = json.dumps({
            'api_key': self.app.config.get('API_KEY'),
            'user': username,
            'email': 'test@test.com'})
        response = self.client.post('/api/v1/user/%s/' % aid, data=data,
                                    content_type='application/json')
        eq_(response.status_code, 403)

    def test_update_user_validation(self):
        """Verify validation of required fields when updating a user"""
        with self.app.app_context():
            u = user(save=True)

        # Missing user
        data = json.dumps({'api_key': self.app.config.get('API_KEY')})
        response = self.client.post('/api/v1/user/%s/' % u.id, data=data,
                                    content_type='application/json')
        eq_(response.status_code, 400)

    def test_update_user_invalid_api_key(self):
        """Request with invalid API key should return 403"""
        with self.app.app_context():
            u = user(save=True)

        data = json.dumps({
            'api_key': self.app.config.get('API_KEY') + '123',
            'user': u.username})
        response = self.client.post('/api/v1/user/%s/' % u.id, data=data,
                                    content_type='application/json')
        eq_(response.status_code, 403)

    def test_udate_user_invalid_api_key(self):
        """Request with invalid API key should return 403"""
        with self.app.app_context():
            u = user(save=True)

        data = json.dumps({'user': u.username})
        response = self.client.post(
            '/api/v1/user/%s/' % u.id, data=data,
            content_type='application/json')
        eq_(response.status_code, 403)

    def test_get_statuses(self):
        """Test getting statuses from API"""
        statuses = []

        with self.app.app_context():
            u = user(save=True)
            p = project(save=True)

            # Create 30 dummy statuses
            for i in range(30):
                if i > 25:
                    p = None
                statuses.append(status(user=u, project=p, save=True))

        # Test with no limit
        response = self.client.get('api/v1/feed/')
        eq_(response.status_code, 200)
        feed = load_json(response.data)

        # Ensure that the default limit works
        eq_(len(feed), 20)

        # Ensure that the correct item are first and last
        eq_(feed.keys()[0], '30', 'First item incorrect')
        eq_(feed.keys()[19], '11', 'Last item incorrect')

        # Test with no limit
        response = self.client.get('api/v1/feed/', query_string={'limit': 5})
        eq_(response.status_code, 200)
        feed = load_json(response.data)

        # Ensure that the default limit works
        eq_(len(feed), 5)

        # Test with no limit
        eq_(feed.keys()[0], '30', 'First item incorrect')
        eq_(feed.keys()[4], '26', 'Last item incorrect')
