import simplejson as json
from flask import render_template_string
from nose.tools import eq_
from standup.apps.api2.decorators import api_key_required
from standup.tests import BaseTestCase, project, status, user


class DecoratorsTestCase(BaseTestCase):
    def __init__(self, *args, **kwargs):
        super(DecoratorsTestCase, self).__init__(*args, **kwargs)

        @self.app.route('/_tests/_api/_protected', methods=['POST'])
        @api_key_required
        def protected():
            return render_template_string('Success!')

    def test_api_key_required(self):
        """Test the API key required decorator"""

        # Test with API key
        data = json.dumps({
            'api_key': self.app.config.get('API_KEY')})
        response = self.client.post('/_tests/_api/_protected', data=data,
                                    content_type='application/json')

        eq_(response.status_code, 200)

        # Test without API key
        data = json.dumps({})
        response = self.client.post('/_tests/_api/_protected', data=data,
                                    content_type='application/json')

        eq_(response.status_code, 403)


class TimelinesTestCase(BaseTestCase):
    def test_home_timeline(self):
        """Test the home_timeline endpoint"""
        response = self.client.get('/api/v2/statuses/home_timeline.json')
        eq_(response.status_code, 200)
        eq_(response.content_type, 'application/json')

    def test_home_timeline_count(self):
        """Test the count parameter of home_timeline"""
        self.app.config['API2_TIMELINE_MAX_RESULTS'] = 50
        with self.app.app_context():
            u = user(save=True)
            for i in range(60):
                status(project=None, user=u, save=True)

        response = self.client.get('/api/v2/statuses/home_timeline.json')
        data = json.loads(response.data)
        eq_(len(data), 20)

        # Test with an acceptable count
        response = self.client.get('/api/v2/statuses/home_timeline.json'
                                   '?count=50')
        data = json.loads(response.data)
        eq_(len(data), 50)

        # Test with a count that is too large
        response = self.client.get('/api/v2/statuses/home_timeline.json'
                                   '?count=60')
        eq_(response.status_code, 400)

        # Test with a count that is too small
        response = self.client.get('/api/v2/statuses/home_timeline.json'
                                   '?count=0')
        eq_(response.status_code, 400)

        # Test with an invalid count
        response = self.client.get('/api/v2/statuses/home_timeline.json'
                                   '?count=a')
        eq_(response.status_code, 400)

    def test_home_timeline_since_id(self):
        """Test the since_id parameter of home_timeline"""
        with self.app.app_context():
            u = user(save=True)
            for i in range(30):
                status(project=None, user=u, save=True)

        response = self.client.get('/api/v2/statuses/home_timeline.json'
                                   '?since_id=10&count=20')
        data = json.loads(response.data)
        eq_(data[19]['id'], 11)

        response = self.client.get('/api/v2/statuses/home_timeline.json'
                                   '?since_id=10&count=10')
        data = json.loads(response.data)
        eq_(data[9]['id'], 21)

        response = self.client.get('/api/v2/statuses/home_timeline.json'
                                   '?since_id=10&count=30')
        data = json.loads(response.data)
        eq_(len(data), 20)
        eq_(data[19]['id'], 11)

        response = self.client.get('/api/v2/statuses/home_timeline.json'
                                   '?since_id=0')
        eq_(response.status_code, 400)

        response = self.client.get('/api/v2/statuses/home_timeline.json'
                                   '?since_id=a')
        eq_(response.status_code, 400)

    def test_home_timeline_max_id(self):
        """Test the max_id parameter of home_timeline"""
        with self.app.app_context():
            for i in range(30):
                status(project=None, user=None, save=True)

        response = self.client.get('/api/v2/statuses/home_timeline.json'
                                   '?max_id=10&count=20')
        data = json.loads(response.data)
        eq_(len(data), 10)
        eq_(data[0]['id'], 10)

        response = self.client.get('/api/v2/statuses/home_timeline.json'
                                   '?max_id=10&since_id=5')
        data = json.loads(response.data)
        eq_(len(data), 5)

        response = self.client.get('/api/v2/statuses/home_timeline.json'
                                   '?max_id=0')
        eq_(response.status_code, 400)

        response = self.client.get('/api/v2/statuses/home_timeline.json'
                                   '?max_id=a')
        eq_(response.status_code, 400)

    def test_home_timeline_trim_user(self):
        """Test the trim_user parameter of home_timeline"""
        with self.app.app_context():
            u = user(save=True)
            status(user=u, project=None, save=True)

        response = self.client.get('/api/v2/statuses/home_timeline.json')
        data = json.loads(response.data)
        eq_(data[0]['user'], u.dictify())

        response = self.client.get('/api/v2/statuses/home_timeline.json'
                                   '?trim_user=1')
        data = json.loads(response.data)
        eq_(data[0]['user'], u.id)

    def test_home_timeline_trim_project(self):
        """Test the trim_project parameter of home_timeline"""
        with self.app.app_context():
            p = project(save=True)
            status(project=p, save=True)

        response = self.client.get('/api/v2/statuses/home_timeline.json')
        data = json.loads(response.data)
        eq_(data[0]['project'], p.dictify())

        response = self.client.get('/api/v2/statuses/home_timeline.json'
                                   '?trim_project=1')
        data = json.loads(response.data)
        eq_(data[0]['project'], p.id)

    def test_home_timeline_include_replies(self):
        """Test the include_replies parameter of home_timeline"""
        with self.app.app_context():
            u = user(save=True)
            for i in range(10):
                s = status(project=None, user=u, save=True)
            for i in range(10):
                status(project=None, user=u, reply_to=s, save=True)

        response = self.client.get('/api/v2/statuses/home_timeline.json')
        data = json.loads(response.data)
        eq_(len(data), 10)

        response = self.client.get('/api/v2/statuses/home_timeline.json'
                                   '?include_replies=1')
        data = json.loads(response.data)
        eq_(len(data), 20)
