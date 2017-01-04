from django.conf import settings
from django.db import models


class IdToken(models.Model):
    """Relates an ID token to a user

    These tokens need to be renewed on a periodic basis and if they fail, they cause the Django
    session to expire.

    """
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    id_token = models.TextField(max_length=100, null=True)
