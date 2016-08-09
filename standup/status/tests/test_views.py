from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.client import Client
from django.test.utils import override_settings

import pytest


class HomeViewTestCase(TestCase):
    client_class = Client

    def test_home_view(self):
        resp = self.client.get(reverse('home-view'))
        assert resp.status_code == 200
