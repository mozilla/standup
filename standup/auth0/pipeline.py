import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.utils.module_loading import import_string


logger = logging.getLogger(__name__)


def run_pipeline(pipeline, **kwargs):
    """Takes a pipeline (list of python path strings) and runs it against kwargs

    :arg list-of-str pipeline: list of python path strings
    :arg dict kwargs: kwargs

    :returns: new kwargs or non-dict return

    """
    # NOTE(willkg): this is a shallow copy, so it doesn't prevent deep mutations.
    kwargs = kwargs.copy()

    for i, path in enumerate(pipeline):
        func = import_string(path)
        result = func(**kwargs) or {}
        if not isinstance(result, dict):
            return result

        kwargs.update(result)
    return kwargs


def log_user_info(user_info, **kwargs):
    """Logs user_info

    Don't use this if you're not debugging!

    """
    logger.info('auth0 user_info: %s', user_info)


def get_user_by_username(user_info, **kwargs):
    """Retrieves the user if there is one available matching on username

    :arg user_info: the ``user_info`` data from auth0

    :returns: ``{'user': User, 'is_new': False}`` or ``{'is_new': True}``

    """
    User = get_user_model()
    try:
        return {
            'user': User.objects.get(username__iexact=user_info['nickname']),
            'is_new': False
        }
    except User.DoesNotExist:
        return {'is_new': True}


def get_user_by_email(user_info, **kwargs):
    """Retrieves the user if there is one available matching on email

    :arg user_info: the ``user_info`` data from auth0

    """
    User = get_user_model()
    try:
        return {
            'user': User.objects.get(email__iexact=user_info['email']),
            'is_new': False
        }
    except User.DoesNotExist:
        return {'is_new': True}


def create_user(user_info, is_new, **kwargs):
    """Creates a new User using nickname and email from user_info"""
    if not is_new:
        return

    User = get_user_model()

    password = User.objects.make_random_password()
    user = User.objects.create_user(
        username=user_info['nickname'],
        password=password,
        email=user_info['email'],
    )
    return {'user': user}


def reject_inactive_user(request, user, **kwargs):
    """Rejects inactive users"""
    if not user.is_active:
        # If inactive, add message and redirect to login page
        messages.error(
            request,
            'This user account is inactive.',
            fail_silently=True
        )
        return HttpResponseRedirect(reverse(settings.AUTH0_SIGNIN_VIEW))


def login_user(request, user, **kwargs):
    """Logs in the user"""
    # FIXME(willkg): This is sort of a lie--should we have our own backend?
    user.backend = 'django.contrib.auth.backends.ModelBackend'
    login(request, user)
