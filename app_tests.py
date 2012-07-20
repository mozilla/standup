import json
import os
import tempfile
import unittest

import app


class AppTestCase(unittest.TestCase):

    def setUp(self):
        self.db_fd, app.app.config['DATABASE'] = tempfile.mkstemp()
        app.app.config['TESTING'] = True
        self.app = app.app.test_client()
        app.db.create_all()

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(app.app.config['DATABASE'])

    def test_create_status(self):
        data = json.dumps(dict(content="working on Bug 123456"))
        response = self.app.post(
            '/status', data=data, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        

if __name__ == '__main__':
    unittest.main()
