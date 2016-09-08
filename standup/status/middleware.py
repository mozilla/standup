from django.http import HttpResponseRedirect


class NewUserProfileMiddleware(object):
    def process_response(self, request, response):
        user = getattr(request, 'user', None)
        if user and 'profile' not in request.path and user.is_authenticated() \
                and not user.profile.name:
            return HttpResponseRedirect('/new-profile/')

        return response
