from datetime import datetime

from django.db.models.signals import post_save
from django.template.defaultfilters import slugify

import factory
from factory import fuzzy
import pytz


class ProjectFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'status.Project'

    name = factory.Faker('name')
    slug = factory.LazyAttribute(lambda obj: slugify(obj.name))
    color = 'ffffff'  # white
    repo_url = 'https://github.com/dude/whatnot/'


class TeamFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'status.Team'
    name = factory.Faker('name')
    slug = factory.LazyAttribute(lambda obj: slugify(obj))


@factory.django.mute_signals(post_save)
class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'auth.User'

    username = factory.Faker('user_name')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    email = factory.Faker('email')
    password = factory.PostGenerationMethodCall('set_password', 'nopassword')

    is_active = True
    is_staff = False
    is_superuser = False


class StandupUserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'status.StandupUser'

    user = factory.SubFactory(UserFactory)
    slug = factory.LazyAttribute(lambda obj: slugify(obj.user.username))
    irc_nick = factory.Faker('user_name')
    github_handle = factory.LazyAttribute(lambda obj: obj.user.username)
    # FIXME: teams


class StatusFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'status.Status'

    created = fuzzy.FuzzyDateTime(
        start_dt=datetime(2011, 9, 6, 0, 0, 0, tzinfo=pytz.utc)
    )
    user = factory.SubFactory(StandupUserFactory)
    project = factory.SubFactory(ProjectFactory)
    content = factory.Faker('sentence')
    reply_to = None
