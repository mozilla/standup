from datetime import date, datetime, timedelta

from nose.tools import eq_
from standup.apps.status.helpers import (enddate, paginate, startdate,
                                         week_start, week_end)
from standup.apps.status.models import Status
from standup.database import get_session
from standup.tests import (authenticate, BaseTestCase, create_request, project,
                           status, team, user)


class HelpersTestCase(BaseTestCase):
    def test_startdate(self):
        """Test the startdate helper function."""
        req = create_request(query_string={'dates': '7d'})
        eq_(startdate(req), date.today() - timedelta(days=7))

        req = create_request(query_string={'dates': 'today'})
        eq_(startdate(req), date.today())

        req = create_request(query_string={'day': '2012-05-24'})
        eq_(startdate(req), datetime(2012, 5, 24))

        req = create_request(query_string={'day': 'today'})
        eq_(startdate(req), None)

        req = create_request()
        eq_(startdate(req), None)

    def test_enddate(self):
        """Test the enddate helper function"""
        req = create_request(query_string={'day': '2012-05-24'})
        eq_(enddate(req), datetime(2012, 5, 25))

        req = create_request(query_string={'day': 'today'})
        eq_(enddate(req), None)

    def test_paginate(self):
        """Test the paginate helper function."""
        db = get_session(self.app)

        statuses = []
        with self.app.app_context():
            p = project(save=True)
            u = user(save=True)

            # Create 100 statuses
            for i in range(30):
                statuses.append(status(project=p, user=u,
                                       created=datetime(2012, 5, 25),
                                       save=True))

            for i in range(30):
                statuses.append(status(project=p, user=u,
                                       created=datetime(2012, 6, 25),
                                       save=True))

            for i in range(40):
                statuses.append(status(project=p, user=u,
                                       created=datetime(2012, 7, 25),
                                       save=True))

        s = db.query(Status).order_by(Status.id)

        # Test simple pagination
        page = paginate(s, page=1)

        eq_(page.pages, 5)

        eq_(page.has_prev, False)
        eq_(page.has_next, True)

        page = paginate(s, page=3)
        eq_(page.has_prev, True)
        eq_(page.has_next, True)

        page = paginate(s, page=5)
        eq_(page.has_prev, True)
        eq_(page.has_next, False)

        # Test date filtered pagination
        page = paginate(s, page=1, startdate=datetime(2012, 5, 28))
        eq_(page.pages, 4)

        page = paginate(s, page=1, startdate=datetime(2012, 5, 28),
                        enddate=datetime(2012, 6, 28))
        eq_(page.pages, 2)

        page = paginate(s, page=1, enddate=datetime(2012, 6, 28))
        eq_(page.pages, 3)

    def test_weeks(self):
        """Test the week start/end helper functions."""
        d = datetime(2014, 1, 29)
        start = week_start(d)
        eq_(start, datetime(2014, 1, 27))
        end = week_end(d)
        eq_(end, datetime(2014, 2, 2))


class ModelsTestCase(BaseTestCase):
    def test_status_repr(self):
        """Test the __repr__ function of the Status model."""
        with self.app.app_context():
            u = user(username='testuser', save=True)
            s = status(content='my status update', user=u, save=True)

        eq_(repr(s), '<Status: testuser: my status update>')

    def test_status_replies(self):
        """Test the loading of replies for a status."""
        with self.app.app_context():
            p = project(save=True)
            u = user(save=True)
            s = status(project=p, user=u, save=True)

            for i in range(30):
                status(project=p, user=u, reply_to=s, save=True)

            page = s.replies()

        eq_(page.pages, 2)

    def test_status_reply_count(self):
        """Test the reply_count property of the Status model."""
        with self.app.app_context():
            u = user(save=True)
            s = status(user=u, project=None, save=True)
            for i in range(5):
                status(user=u, project=None, reply_to=s, save=True)

            eq_(s.reply_count, 5)

    def test_project_repr(self):
        """Test the __repr__ function of the Project model."""
        with self.app.app_context():
            p = project(slug="project", name="Project", save=True)

        eq_(repr(p), '<Project: [project] Project>')

    def test_project_recent_statuses(self):
        """Test loading of recent statuses for a project."""
        with self.app.app_context():
            p = project(save=True)
            u = user(save=True)

            # Create 70 statuses
            for i in range(70):
                status(project=p, user=u, save=True)

            s = status(project=p, user=u, save=True)

            # Create 30 replies
            for i in range(30):
                status(project=p, user=u, reply_to=s, save=True)

        # Should not include replies
        page = p.recent_statuses()
        eq_(page.pages, 4)


class ViewsTestCase(BaseTestCase):
    def test_index_view(self):
        """Make sure the index view works like it's supposed to."""
        response = self.client.get('/')
        eq_(response.status_code, 200)

    def test_user_view(self):
        """Make sure the user view works like it's supposed to."""
        with self.app.app_context():
            u = user(save=True)

        response = self.client.get('/user/%s' % u.slug)
        eq_(response.status_code, 200)

        response = self.client.get('/user/not-a-real-user')
        eq_(response.status_code, 404)

    def test_project_view(self):
        """Make sure the project view works like it's supposed to."""
        with self.app.app_context():
            p = project(save=True)

        response = self.client.get('/project/%s' % p.slug)
        eq_(response.status_code, 200)

        response = self.client.get('/project/not-a-real-project')
        eq_(response.status_code, 404)

    def test_team_view(self):
        """Make sure the project view works like it's supposed to."""
        with self.app.app_context():
            u = user(save=True)
            t = team(users=[u], save=True)

        response = self.client.get('/team/%s' % t.slug)
        eq_(response.status_code, 200)

        response = self.client.get('/team/not-a-real-team')
        eq_(response.status_code, 404)

    def test_status_view(self):
        with self.app.app_context():
            s = status(content='this works!', content_html='this works!',
                       save=True)

        response = self.client.get('/status/%s' % s.id)
        eq_(response.status_code, 200)
        assert 'this works!' in response.data

        response = self.client.get('/status/9999')
        eq_(response.status_code, 404)

    def test_feeds(self):
        """Test that the site-wise Atom feed appears and functions properly."""
        with self.app.app_context():
            u = user(email='joe@example.com', slug='joe', save=True)
            team(users=[u], slug='a-team', save=True)
            p = project(slug='prjkt', save=True)

            for i in range(20):
                status(user=u, project=p, content='foo', content_html='foo',
                       save=True)

        authenticate(self.client, u)

        site_url = self.app.config.get('SITE_URL')

        # Ensure the Atom link appears in the rendered HTML.
        rv = self.client.get('/')
        assert ('<link rel="alternate" type="application/atom+xml" '
                'href="%s/statuses.xml"') % site_url in rv.data

        # Make sure the Atom feed displays statuses.
        rv = self.client.get('/statuses.xml')
        assert '<entry' in rv.data
        assert ('<content type="html">&lt;h3&gt;Test Project&lt;/h3&gt;&lt;p'
                '&gt;foo&lt;/p&gt;</content>') in rv.data

        rv = self.client.get('/user/joe.xml')
        assert '<entry' in rv.data
        assert ('<content type="html">&lt;h3&gt;Test Project&lt;/h3&gt;&lt;p'
                '&gt;foo&lt;/p&gt;</content>') in rv.data

        rv = self.client.get('/project/prjkt.xml')
        assert '<entry' in rv.data
        assert ('<content type="html">&lt;h3&gt;Test Project&lt;/h3&gt;&lt;p'
                '&gt;foo&lt;/p&gt;</content>') in rv.data

        rv = self.client.get('/team/a-team.xml')
        assert '<entry' in rv.data
        assert ('<content type="html">&lt;h3&gt;Test Project&lt;/h3&gt;&lt;p'
                '&gt;foo&lt;/p&gt;</content>') in rv.data

    def test_feeds_no_statuses(self):
        """Make sure the Atom feed works with no status updates."""
        rv = self.client.get('/statuses.xml')
        eq_(rv.status_code, 200)

    def test_feeds_do_not_exist(self):
        """Test feeds for non existant objects"""
        rv = self.client.get('/user/who.xml')
        eq_(rv.status_code, 404)

        rv = self.client.get('/project/fake.xml')
        eq_(rv.status_code, 404)

        rv = self.client.get('/team/not-real.xml')
        eq_(rv.status_code, 404)

    def test_contextual_feeds(self):
        """Test that team/project/user Atom feeds appear as <link> tags."""

        with self.app.app_context():
            user(email='joe@example.com', save=True)
            u = user(username='buffy', email="buffy@sunnydalehigh.edu",
                     name='Buffy Summers', slug='buffy', save=True)
            team(name='Scooby Gang', slug='scoobies', users=[u], save=True)
            project(name='Kill The Master', slug='master', save=True)

        authenticate(self.client, u)

        site_url = self.app.config.get('SITE_URL')

        rv = self.client.get('/')
        assert ('<link rel="alternate" type="application/atom+xml" '
                'href="%s/statuses.xml"') % site_url in rv.data
        assert ('<link rel="alternate" type="application/atom+xml" '
                'href="%s/project/') % site_url not in rv.data

        rv = self.client.get('/team/scoobies')
        assert ('<link rel="alternate" type="application/atom+xml" '
                'href="%s/team/') % site_url in rv.data

        rv = self.client.get('/project/master')
        assert ('<link rel="alternate" type="application/atom+xml" '
                'href="%s/project/') % site_url in rv.data

        rv = self.client.get('/user/buffy')
        assert ('<link rel="alternate" type="application/atom+xml" '
                'href="%s/user/') % site_url in rv.data


class StatusizerTestCase(BaseTestCase):
    def test_status_unauthenticated(self):
        """Test that you get a 403 if you're not authenticated."""
        rv = self.client.post('/statusize/', data={'message': 'foo'},
                              follow_redirects=True)
        eq_(rv.status_code, 403)

    def test_status(self):
        """Test posting a status."""
        with self.app.app_context():
            u = user(email='joe@example.com', save=True)

        authenticate(self.client, u)

        rv = self.client.post('/statusize/', data={'message': 'foo'},
                              follow_redirects=True)
        eq_(rv.status_code, 200)

    def test_status_no_message(self):
        """Test posting a status with no message."""
        with self.app.app_context():
            u = user(email='joe@example.com', save=True)

        authenticate(self.client, u)

        rv = self.client.post('/statusize/', data={'message': ''},
                              follow_redirects=True)
        # This kicks up a 404, but that's lame.
        eq_(rv.status_code, 404)

    def test_status_with_project(self):
        """Test posting a status with a project."""
        with self.app.app_context():
            u = user(email='joe@example.com', save=True)
            p = project(name='blackhole', slug='blackhole', save=True)
            data = {'message': 'r1cky rocks!', 'project': p.id}

        authenticate(self.client, u)

        rv = self.client.post('/statusize/', follow_redirects=True,
                              data=data)
        eq_(rv.status_code, 200)
