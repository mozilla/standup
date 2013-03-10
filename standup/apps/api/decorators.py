from functools import wraps

from flask import current_app, jsonify, make_response, request


def api_key_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        api_key = request.json.get('api_key', '')
        if api_key != current_app.config.get('API_KEY'):
            return make_response(jsonify({'error': 'Invalid API key.'}), 403)
        return view(*args, **kwargs)

    return wrapper
