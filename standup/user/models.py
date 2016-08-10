from collections import OrderedDict

from django.contrib.auth.models import User
from django.db import models


class Team(models.Model):
    """A team of users in the organization."""
    name = models.CharField(
        max_length=100,
        help_text='Name of the team'
    )
    slug = models.SlugField(unique=True)

    def __repr__(self):
        return '<Team: [%s]>' % (self.name,)

    def dictify(self):
        data = OrderedDict()
        data['id'] = self.id
        data['name'] = self.name
        data['slug'] = self.slug
        return data


class StandupUser(models.Model):
    """A standup participant--tied to Django's User model."""
    # Note: User provides "username", "name", "is_superuser", "is_staff" and
    # "email"
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    slug = models.SlugField(unique=True)
    github_handle = models.CharField(max_length=100, unique=True)
    teams = models.ManyToManyField(Team)

    class Meta:
        # FIXME: can we order by self.user.username ?
        pass

    def __repr__(self):
        return '<User: [%s] %s>' % (self.user.username, self.user.name)

    @property
    def name(self):
        return self.user.get_full_name()

    @property
    def username(self):
        return self.user.username

    @property
    def email(self):
        return self.user.email

    def dictify(self):
        """Returns an OrderedDict of model attributes"""
        data = OrderedDict()
        data['id'] = self.id
        data['username'] = self.username
        data['name'] = self.name
        data['slug'] = self.slug
        # FIXME: Should we be providing email addresses publicly via the api?
        # data['email'] = self.user.email
        data['github_handle'] = self.github_handle
        data['is_staff'] = self.user.is_staff
        return data
