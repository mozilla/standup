from datetime import datetime

import factory
from factory import fuzzy
import pytz

from django.template.defaultfilters import slugify


class ProjectFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'status.Project'

    name = factory.Faker('name')
    slug = factory.LazyAttribute(lambda obj: slugify(obj.name))
    color = 'ffffff'  # white
    repo_url = factory.Faker('uri')


class StatusFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'status.Status'

    created = fuzzy.FuzzyDateTime(
        start_dt=datetime(2011, 9, 6, 0, 0, 0, tzinfo=pytz.utc)
    )
    user = factory.SubFactory(
        'standup.user.tests.factories.StandupUserFactory'
    )
    project = factory.SubFactory(ProjectFactory)
    content = factory.Faker('sentence')
    # FIXME: content_html
    reply_to = None
