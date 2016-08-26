import factory

from django.template.defaultfilters import slugify


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


class TeamFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'user.Team'
    name = factory.Faker('name')
    slug = factory.LazyAttribute(lambda obj: slugify(obj))


class StandupUserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'user.StandupUser'

    user = factory.SubFactory(UserFactory)
    slug = factory.LazyAttribute(lambda obj: slugify(obj.user.username))
    github_handle = factory.LazyAttribute(lambda obj: obj.user.username)
    # FIXME: teams
