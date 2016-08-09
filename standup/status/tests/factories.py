import factory

from django.template.defaultfilters import slugify


class ProjectFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'status.Project'

    name = factory.Faker('name')
    slug = factory.LazyAttribute(lambda obj: slugify(obj))
    color = 'ffffff'  # white
    repo_url = factory.Faker('repo_url')


class StatusFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'status.Status'

    created = factory.Faker('created')
    user = factory.SubFactory('user.StandupUser')
    project = factory.SubFactory(ProjectFactory)
    content = factory.Faker('content')
    # FIXME: content_html
    reply_to = None
