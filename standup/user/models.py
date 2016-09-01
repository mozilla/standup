from collections import OrderedDict

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db import models


class LegacyUser(models.Model):
    """A model for the old users in the Flask-based instance.

    For use with the initial data migration. After the new standup
    is in production this can be deleted.
    """
    username = models.CharField(max_length=100)
    name = models.CharField(max_length=100)
    slug = models.CharField(max_length=100)
    email = models.CharField(max_length=100, blank=True)
    github_handle = models.CharField(max_length=100, blank=True)
    is_admin = models.BooleanField(default=False)

    class Meta:
        db_table = 'user'


class StandupUser(models.Model):
    """A standup participant--tied to Django's User model."""
    # Note: User provides "username", "name", "is_superuser", "is_staff" and
    # "email"
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')

    slug = models.SlugField(unique=True)
    github_handle = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ('user__username',)

    def __str__(self):
        return self.user.get_full_name()

    def __repr__(self):
        return '<StandupUser: [{}]>'.format(self.user.username)

    def get_absolute_url(self):
        return reverse('status.user', kwargs={'slug': self.slug})

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
