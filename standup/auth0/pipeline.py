from collections import OrderedDict
from datetime import timedelta
import logging

from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.core.urlresolvers import reverse
from django.db import IntegrityError
from django.http import HttpResponseRedirect
from django.utils import timezone
from django.utils.module_loading import import_string

from standup.auth0.models import IdToken
from standup.auth0.settings import app_settings


logger = logging.getLogger(__name__)


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


def log_info(**kwargs):
    """Logs all kwargs at this point

    Don't use this if you're not debugging!

    """
    # First, sort it so things aren't jumping around from call to call
    new_kwargs = OrderedDict(sorted(kwargs.items()))
    # Log it--doing keys first and separately to make debugging pipeline func args easier
    logger.debug('LOG_INFO KEYS: %r', new_kwargs.keys())
    logger.debug('LOG_INFO: %r', new_kwargs)


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

    .. Warning::

       Be careful using this. The email field in the Django User model is not required to be filled
       in or unique. If you let your users edit their email address and don't notify the email
       address that it's changed and don't verify the new email address, then anyone can use someone
       else's email address and potentially log in as them.

    :arg user_info: the ``user_info`` data from auth0

    :returns: ``{'user': User, 'is_new': False}`` or ``{'is_new': True}``

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
    """Creates a new User using nickname and email from user_info

    :arg user_info: the ``user_info`` data from auth0

    :returns: ``{'user': User}`` of the created user

    """
    if not is_new:
        return

    User = get_user_model()

    password = User.objects.make_random_password()
    # Auth0 returns nicknames that may not be unique across identities, so we add a sequence to the
    # end where necessary.
    for username in unique_string_generator(user_info['nickname']):
        try:
            user = User.objects.create_user(
                username=username,
                password=password,
                email=user_info['email'],
            )
            break
        except IntegrityError:
            pass
    return {'user': user}


def reject_unverified_email(request, user_info, **kwargs):
    """Rejects users with unverified email addresses

    :arg request: the HTTP request
    :arg user_info: the ``user_info`` data from auth0

    :returns: ``HttpResponseRedirect`` or None

    """
    if not user_info['email_verified']:
        # If inactive, add message and redirect to login page
        messages.error(
            request,
            'The email address associated with this account is not verified.',
            fail_silently=True
        )
        return HttpResponseRedirect(reverse(app_settings.AUTH0_SIGNIN_VIEW))


def reject_inactive_user(request, user, is_new, **kwargs):
    """Rejects existing but inactive users

    :arg request: the HTTP request
    :arg user: the User associated with the Auth0 identity
    :arg is_new: whether or not the User is new

    :returns: ``HttpResponseRedirect`` or None

    """
    if not is_new and user and not user.is_active:
        # If inactive, add message and redirect to login page
        messages.error(
            request,
            'This user account is inactive.',
            fail_silently=True
        )
        return HttpResponseRedirect(reverse(app_settings.AUTH0_SIGNIN_VIEW))


def login_user(request, user, **kwargs):
    """Logs in the user

    :arg request: the HTTP request
    :arg user: the User associated with the Auth0 identity

    :returns: None

    """
    # FIXME(willkg): This is sort of a lie--should we have our own backend?
    user.backend = 'django.contrib.auth.backends.ModelBackend'
    login(request, user)


def require_id_token(request, user, user_info, token_info, **kwargs):
    """Handles domains that require id tokens

    For example, if a user logs in with a mozilla.com email address, they must do so using the LDAP
    provider. Otherwise we log them out.

    If they logged in using the correct provider, then we capture the ``id_token`` so we can
    periodically renew it and log them out if it goes bad.

    :arg request: the HTTP request
    :arg user: the User associated with this auth0 identity
    :arg user_info: the ``user_info`` data from auth0
    :arg token_info: the ``token_info`` data from auth0

    :returns: ``HttpResponseRedirect`` or None

    """
    # Pull the domain and if it's in the list of domains we need an id_token for, do the id_token
    # work.
    domain = user_info['email'].lower().split('@', 1)[1]
    logger.debug('require_id_token: %r %r %r', user_info['email'], domain, app_settings.AUTH0_ID_TOKEN_DOMAINS)
    if domain in app_settings.AUTH0_ID_TOKEN_DOMAINS:
        if token_info.get('id_token'):
            # We have an id_token, so persist it.
            try:
                token = IdToken.objects.get(user=user)
            except IdToken.DoesNotExist:
                token = IdToken(user=user)

            token.id_token = token_info['id_token']
            token.expire = timezone.now() + timedelta(seconds=app_settings.AUTH0_ID_TOKEN_EXPIRY)
            token.save()

        else:
            # We don't have an id_token, but should, so return a message and eject.
            messages.error(
                request,
                # FIXME(willkg): This is Mozilla-specific.
                'You can\'t log in with that email address using the provider you '
                'used. Please log in with the Mozilla LDAP provider.',
                fail_silently=True
            )
            return HttpResponseRedirect(reverse(app_settings.AUTH0_SIGNIN_VIEW))


def mozilla_auth0_pipeline(**kwargs):
    """This is a meta-pipeline that runs all the things that Mozilla sites should run"""
    pipeline = [
        'standup.auth0.pipeline.reject_unverified_email',
        'standup.auth0.pipeline.get_user_by_email',
        'standup.auth0.pipeline.create_user',
        'standup.auth0.pipeline.reject_inactive_user',
        'standup.auth0.pipeline.require_id_token',
        'standup.auth0.pipeline.login_user',
    ]
    return run_pipeline(pipeline, **kwargs)
