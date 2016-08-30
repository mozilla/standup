from datetime import datetime

import factory
from factory import fuzzy
import pytz

from standup.api import models


class SystemTokenFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.SystemToken

    summary = factory.Faker('sentence')
    enabled = True
    disabled_reason = ''
    contact = factory.Faker('name')
    created = fuzzy.FuzzyDateTime(
        start_dt=datetime(2011, 9, 6, 0, 0, 0, tzinfo=pytz.utc)
    )
