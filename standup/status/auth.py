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
