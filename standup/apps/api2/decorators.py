from flask import jsonify, make_response, request
from functools import wraps
from standup import settings
from standup.apps.api2.helpers import api_error

def api_key_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        api_key = request.json.get('api_key', '')
        if api_key != settings.API_KEY:
            return api_error(403, 'Forbidden: invalid API key.')
        return view(*args, **kwargs)

    return wrapper
