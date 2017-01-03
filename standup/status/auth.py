from django.db import IntegrityError

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


def create_profile(user, is_new, **kwargs):
    """Creates a profile if the user is new

    :arg User user: a User instance
    :arg bool is_new: whether or not the user instance is new

    :returns: ``{'profile': StandupUser}``

    """
    if not is_new:
        return

    try:
        # If we can access .profile, then it has a profile and we can return here.
        user.profile
        return
    except StandupUser.DoesNotExist:
        pass

    for slug in unique_string_generator(user.username):
        # FIXME: run slugify on slug
        try:
            return {
                'profile': StandupUser.objects.create(
                    user=user,
                    slug=slug
                )
            }
        except IntegrityError:
            pass
