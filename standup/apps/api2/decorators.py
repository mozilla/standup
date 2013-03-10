from functools import wraps

from flask import current_app, request
from standup.errors import api_error


def api_key_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        api_key = request.json.get('api_key', '')
        if api_key != current_app.config.get('API_KEY'):
            return api_error(403, 'Forbidden: invalid API key.')
        return view(*args, **kwargs)

    return wrapper
