from flask import jsonify, make_response, request
from functools import wraps
from standup import settings

def api_key_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        api_key = request.json.get('api_key', '')
        if api_key != settings.API_KEY:
            return make_response(jsonify({'error': 'Invalid API key.'}), 403)
        return view(*args, **kwargs)

    return wrapper
