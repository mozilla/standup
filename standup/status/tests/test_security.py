from django.urls import reverse
from django.test import TestCase, override_settings


class NoSniffTestCase(TestCase):
    """Tests x-content-type-options == 'nosniff'"""
    @override_settings(SECURE_CONTENT_TYPE_NOSNIFF=False)
    def test_xsniff_off(self):
        resp = self.client.get(reverse('status.index'))
        assert resp.status_code == 200
        assert resp.get('x-content-type-options') is None

    @override_settings(SECURE_CONTENT_TYPE_NOSNIFF=True)
    def test_xsniff_on(self):
        resp = self.client.get(reverse('status.index'))
        assert resp.status_code == 200
        assert resp.get('x-content-type-options') == 'nosniff'


class XFrameOptionsTestCase(TestCase):
    """Verifies xframeoptions == 'SAMEORIGIN'"""
    def test_xframe_options(self):
        resp = self.client.get(reverse('status.index'))
        assert resp.status_code == 200
        assert resp['x-frame-options'] == 'SAMEORIGIN'
