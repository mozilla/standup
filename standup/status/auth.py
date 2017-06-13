from django.db import IntegrityError
from django.utils.text import slugify

from mozilla_django_oidc.auth import OIDCAuthenticationBackend

from standup.status.models import StandupUser


class Exhausted(Exception):
    pass


def unique_string_generator(base, max_count=50):
    """Generates strings using a base plus some count"""
    yield base

    count = 2
    while count < max_count:
        yield '%s%d' % (base, count)
        count += 1

    raise Exhausted('No more slots available for generation. Base was "%s"' % base)


class StandupOIDCAuthBackend(OIDCAuthenticationBackend):
    """Override the OIDCAuthenticationBackend to also create a StandupUser"""
    def create_user(self, claims):
        user = super().create_user(claims)
        self.create_profile(user)
        return user

    def create_profile(self, user):
        email_name = user.email.split('@', 1)[0]
        for possible_slug in unique_string_generator(email_name):
            try:
                return StandupUser.objects.create(
                    user=user,
                    slug=slugify(possible_slug)
                )
            except IntegrityError:
                pass
