from django.db import IntegrityError
from django.contrib.auth.models import User

from .models import StandupUser


def create_user_profile(backend, user, response, details, *args, **kwargs):
    if backend.name == 'github':
        try:
            profile = user.profile
        except StandupUser.DoesNotExist:
            StandupUser.objects.create(
                user=user,
                name=details['fullname'],
                slug=response['login'],
                github_handle=response['login'],
            )
        else:
            if profile.github_handle != response['login']:
                profile.github_handle = response['login']
                profile.name = details['fullname']
                profile.save()


def browserid_create_user(email, username=None):
    username = username or email.split('@')[0]
    try:
        user = User.objects.create_user(username, email)
    except IntegrityError:
        user = browserid_create_user(email, username + '1')

    return user
