from flask import render_template_string
from nose.tools import eq_

from standup.tests import BaseTestCase, testing_app


TMPL = '{{ text|markdown }}'


class MarkdownTestCase(BaseTestCase):
    def rts(self, text_value):
        return render_template_string(TMPL, text=text_value)

    def test_basic_markdown(self):
        with testing_app.test_request_context():
            eq_(self.rts('text'), '<p>text</p>')
            eq_(self.rts('*text*'), '<p><em>text</em></p>')
            eq_(self.rts('**text**'), '<p><strong>text</strong></p>')
            eq_(self.rts('*wow* http://example.com/'),
                '<p><em>wow</em> http://example.com/</p>')

    def test_nixheaders(self):
        with testing_app.test_request_context():
            eq_(self.rts('# foo'), '<p>foo</p>')
            eq_(self.rts('#foo'), '<p>foo</p>')
            eq_(self.rts('## foo'), '<p>foo</p>')
            eq_(self.rts('i\'m at #work'), '<p>i\'m at #work</p>')
