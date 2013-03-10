from mock import patch
from nose.tools import eq_
from standup.apps.status.models import Status
from standup.database.helpers import get_session, paginate
from standup.tests import BaseTestCase, status, user


class FakeException(BaseException):
    pass


class HelpersTestCase(BaseTestCase):
    def setUp(self):
        super(HelpersTestCase, self).setUp()
        with self.app.app_context():
            u = user(username='jdoe', save=True)
            for i in range(100):
                status(project=None, user=u, save=True)

        db = get_session(self.app)
        self.query = db.query(Status).order_by(Status.id)

    def test_paginate(self):
        """Test the paginate helper function"""
        with patch('standup.database.classes.abort') as mocked:
            def exceptionify(*args, **kwargs):
                raise FakeException()
            mocked.side_effect = exceptionify

            page = paginate(self.query, 2, per_page=10)
            eq_(page.pages, 10)
            eq_(page.has_prev, True)
            eq_(page.prev_num, 1)

            prev = page.prev()
            eq_(prev.has_prev, False)

            try:
                prev.prev()
            except FakeException:
                pass
            else:
                self.fail('Did not error out')

            page = paginate(self.query, 9, per_page=10)
            eq_(page.has_next, True)
            eq_(page.next_num, 10)

            next = page.next()
            eq_(next.has_next, False)

            try:
                next.next()
            except FakeException:
                pass
            else:
                self.fail('Did not error out')

    def test_paginate_errors(self):
        """Test the paginate function erroring out"""
        with patch('standup.database.helpers.abort') as mocked:
            def exceptionify(*args, **kwargs):
                raise FakeException()
            mocked.side_effect = exceptionify

            try:
                paginate(self.query, 0)
            except FakeException:
                pass
            else:
                self.fail('paginate did not error out')

            try:
                paginate(self.query, 0, error_out=False)
            except FakeException:
                self.fail('paginate errored out')

            try:
                paginate(self.query, 6)
            except FakeException:
                pass
            else:
                self.fail('paginate did not error out')

            try:
                paginate(self.query, 6, error_out=False)
            except FakeException:
                self.fail('paginate errored out')
