from django.conf import settings
from django.db import models


class IdToken(models.Model):
    """Associates a user with their id token

    These tokens need to be renewed on a periodic basis and if they fail, they force Django logout.

    """
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    id_token = models.TextField(help_text='The id token for this user.')
    expire = models.DateTimeField()
