import json
import logging

from django.http import (
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseForbidden,
    HttpResponseNotAllowed,
    HttpResponseServerError,
)
from django.utils.encoding import force_str
from django.utils.text import slugify
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View

from .models import SystemToken
from standup.status.models import Project, Status, StandupUser


logger = logging.getLogger(__name__)


def convert_to_json(resp, cors=False):
    """Converts responses into JSON responses"""
    # If the response is already json-ified, then we skip it.
    if getattr(resp, 'is_json', False):
        return resp

    resp['content_type'] = 'application/json'
    if cors:
        resp['Access-Control-Allow-Origin'] = '*'

    content = resp.content

    if isinstance(resp, (
            HttpResponseBadRequest,
            HttpResponseForbidden,
            HttpResponseServerError
    )):
        # Errors are in the form {'error': 'error string...'}
        content = {'error': content.decode('utf-8')}

    elif isinstance(resp, HttpResponseNotAllowed):
        content = {'error': 'Method not allowed'}

    elif isinstance(resp, HttpResponseJSON):
        return resp

    resp.content = json.dumps(content)
    resp.is_json = True
    return resp


class AuthException(Exception):
    """Authentication exception"""
    pass


class HttpResponseJSON(HttpResponse):
    is_json = True

    def __init__(self, content, status=None, cors=False):
        super(HttpResponseJSON, self).__init__(
            content=json.dumps(content),
            content_type='application/json',
            status=status
        )

        if cors:
            self['Access-Control-Allow-Origin'] = '*'


class APIView(View):
    """API view that looks at the world in JSON"""
    @classmethod
    def as_view(cls, *args, **kwargs):
        # API calls use token authentication and don't need csrf bits
        return csrf_exempt(super(APIView, cls).as_view(*args, **kwargs))

    def authenticate(self, request):
        """Authenticates the request which pulls out the auth token and validates it

        Adds "auth_token" attribute to the request with the token instance.

        :raises AuthError: for authentication errors

        """
        pass

    def dispatch(self, request, *args, **kwargs):
        """Dispatches like View, except always returns JSON responses"""
        try:
            if request.body:
                # FIXME: This assumes the body is utf-8.
                request.json_body = json.loads(force_str(request.body))
                if not isinstance(request.json_body, dict):
                    raise Exception('Unrecognized JSON payload.')
            else:
                request.json_body = None

            self.authenticate(request)

            resp = super(APIView, self).dispatch(request, *args, **kwargs)

        except AuthException as exc:
            resp = HttpResponseForbidden(exc.args[0])

        except Exception as exc:
            resp = HttpResponseServerError('Error occured: %s' % exc)
            logger.exception('Request kicked up exception')

        return convert_to_json(resp)


class AuthenticatedAPIView(APIView):
    def authenticate(self, request):
        # If this request is for a method that's not allowed, we just
        # skip it and dispatch will deal with it.
        if getattr(self, request.method.lower(), None) is None:
            return

        if not request.json_body:
            raise AuthException('No api_key provided.')

        api_key = request.json_body.get('api_key')
        if not api_key:
            raise AuthException('No api_key provided.')

        # Check to see if this is a system token
        try:
            token = SystemToken.objects.get(token=api_key)
        except SystemToken.DoesNotExist:
            raise AuthException('Api key forbidden.')

        # Verify the token is enabled
        if not token.enabled:
            raise AuthException('Api key forbidden.')

        # Add token to request object
        request.auth_token = token


class StatusCreate(AuthenticatedAPIView):
    def post(self, request):
        token = request.auth_token

        # FIXME: Authorize operation.

        username = request.json_body.get('user')
        project_slug = request.json_body.get('project')
        content = request.json_body.get('content')
        reply_to = request.json_body.get('reply_to')
        project = None
        replied = None

        # Validate we have the required fields.
        if not (username and content):
            return HttpResponseBadRequest('Missing required fields.')

        # If this is a reply make sure that the status being replied to
        # exists and is not itself a reply
        if reply_to:
            replied = Status.objects.filter(id=reply_to).first()
            if not replied:
                return HttpResponseBadRequest('Status does not exist.')
            elif replied.reply_to:
                return HttpResponseBadRequest('Cannot reply to a reply.')

        # Get the user
        user = StandupUser.objects.filter(user__username=username).first()
        if not user:
            return HttpResponseBadRequest('User does not exist.')

        # Get or create the project (but not if this is a reply)
        if project_slug and not replied:
            # This forces the slug to be slug-like.
            project_slug = slugify(project_slug)
            project = Project.objects.filter(slug=project_slug).first()
            if not project:
                project = Project(slug=project_slug, name=project_slug)
                project.save()

        # Create the status
        status = Status(user=user, content=content)
        if project_slug and project:
            status.project = project
        if replied:
            status.reply_to = replied

        status.save()

        return HttpResponseJSON({'id': status.id, 'content': content})


class StatusDelete(AuthenticatedAPIView):
    def delete(self, request, pk):
        token = request.auth_token

        # FIXME: Authorize this operation.

        username = request.json_body.get('user')

        if not username:
            return HttpResponseBadRequest('Missing required fields.')

        status = Status.objects.filter(id=pk).first()
        if not status:
            return HttpResponseBadRequest('Status does not exist.')

        if status.user.username != username:
            return HttpResponseForbidden('You cannot delete this status.')

        status_id = status.id
        status.delete()

        return HttpResponseJSON({'id': status_id})


class UpdateUser(AuthenticatedAPIView):
    def post(self, request, username):
        token = request.auth_token

        # FIXME: Authorize this operation.

        user = StandupUser.objects.filter(user__username=username).first()
        if not user:
            return HttpResponseBadRequest('User does not exist.')

        if 'name' in request.json_body:
            user.name = request.json_body['name']
        if 'email' in request.json_body:
            user.user.email = request.json_body['email']
        if 'github_handle' in request.json_body:
            user.github_handle = request.json_body['github_handle']

        user.save()
        user.user.save()

        return HttpResponseJSON({'id': user.id})
