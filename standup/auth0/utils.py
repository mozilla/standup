from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import IntegrityError

from standup.status.models import StandupUser


def is_auth0_configured():
    return (
        settings.AUTH0_CLIENT_ID and
        settings.AUTH0_CLIENT_SECRET and
        settings.AUTH0_DOMAIN and
        settings.AUTH0_CALLBACK_URL
    )


class Exhausted(Exception):
    pass


def username_generator(base):
    """Generates usernames using a base plus some count"""
    yield base

    count = 2
    while count < 50:
        yield '%s%d' % (base, count)
        count += 1

    raise Exhausted('No more slots available for generation. Base was "%s"' % base)


def get_or_create_user(email, name=None):
    """Retrieves or creates a User instance

    :arg str email: the email of the user
    :arg str name: the name of the user (or none)

    :returns: User instance

    """
    User = get_user_model()
    try:
        # Try matching on email first--that's our canonical lookup.
        return User.objects.get(email__iexact=email)

    except User.DoesNotExist:
        try:
            # Didn't match on email, so this might be an older account that's never had a profile.
            # So try to match on username, but only if the email field is empty.
            return User.objects.get(email='', username__iexact=email.split('@', 1)[0])

        except User.DoesNotExist:
            # Didn't match email or username, so this is probably a new user.
            username_base = name or email.split('@', 1)[0]
            password = User.objects.make_random_password()

            for username in username_generator(username_base):
                try:
                    user = User.objects.create(
                        username=username,
                        email=email,
                        password=password,
                    )
                    user.save()
                    return user

                except IntegrityError:
                    pass


def get_or_create_profile(user):
    """Retrieves or creates a StandupUser instance

    If this creates a new StandupUser, it makes sure that the StandupUser has a unique slug.

    :arg user User: a User instance

    :returns: StandupUser instance

    """
    try:
        profile = user.profile
    except StandupUser.DoesNotExist:
        profile = StandupUser.objects.create(
            user=user
        )

    if not profile.slug:
        for slug in username_generator(user.username):
            try:
                profile.slug = slug
                profile.save()
            except IntegrityError:
                pass
    return profile
