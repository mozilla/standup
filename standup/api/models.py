from uuid import uuid4

from django.db import models


def generate_token():
    return str(uuid4())


class SystemToken(models.Model):
    """These are tokens given to things like the standup-irc bot which gives it
    access to post status messages on behalf of **all** users.

    These are for systems--not individual users.

    """
    token = models.CharField(
        max_length=36, default=generate_token,
        help_text='API token for authentication.'
    )
    summary = models.CharField(
        max_length=200,
        help_text='System that uses this token.'
    )
    # SystemToken starts off disabled by default until we've explicitly enabled it because of the
    # access they have.
    enabled = models.BooleanField(default=False)
    disabled_reason = models.TextField(
        blank=True, default='',
        help_text='Reason this token was disabled/revoked.'
    )
    contact = models.CharField(
        max_length=200, blank=True, default='',
        help_text='Contact information for what uses this token. Email address, etc.'
    )
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return '<SystemToken "{}">'.format(self.summary)
