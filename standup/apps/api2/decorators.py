from datetime import timedelta
from functools import wraps, update_wrapper

from flask import current_app, request, make_response
from standup.errors import api_error

def api_key_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        data = request.args if request.method == 'GET' else request.form
        api_key = data.get('api_key', '')
        if api_key != current_app.config.get('API_KEY'):
            return api_error(403, 'Forbidden: Invalid API key.')
        return view(*args, **kwargs)

    return wrapper

# CORS Decorator from http://flask.pocoo.org/snippets/56/
# -------------------------------------------------------------------------
# Cross-site HTTP requests are HTTP requests for resources from a different
# domain than the domain of the resource making the request. For instance, a
# resource loaded from Domain A makes a request for a resource on Domain B.
# The way this is implemented in modern browsers is by using HTTP Access
# Control headers. Documentation on developer.mozilla.org:
#   https://developer.mozilla.org/en/HTTP_access_control
def crossdomain(origin=None, methods=None, headers=None,
                max_age=21600, attach_to_all=True,
                automatic_options=True):
    if methods is not None:
        methods = ', '.join(sorted(x.upper() for x in methods))
    if headers is not None and not isinstance(headers, basestring):
        headers = ', '.join(x.upper() for x in headers)
    if not isinstance(origin, basestring):
        origin = ', '.join(origin)
    if isinstance(max_age, timedelta):
        max_age = max_age.total_seconds()

    def get_methods():
        if methods is not None:
            return methods

        options_resp = current_app.make_default_options_response()
        return options_resp.headers['allow']

    def decorator(f):
        def wrapped_function(*args, **kwargs):
            if automatic_options and request.method == 'OPTIONS':
                resp = current_app.make_default_options_response()
            else:
                resp = make_response(f(*args, **kwargs))
            if not attach_to_all and request.method != 'OPTIONS':
                return resp

            h = resp.headers

            h['Access-Control-Allow-Origin'] = origin
            h['Access-Control-Allow-Methods'] = get_methods()
            h['Access-Control-Max-Age'] = str(max_age)
            if headers is not None:
                h['Access-Control-Allow-Headers'] = headers
            return resp

        f.provide_automatic_options = False
        return update_wrapper(wrapped_function, f)
    return decorator
