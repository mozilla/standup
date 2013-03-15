from flask import render_template, request

from standup.utils import json_requested, jsonify


def register_error_handlers(app):
    app.register_error_handler(403, forbidden)
    app.register_error_handler(404, page_not_found)
    app.register_error_handler(500, something_broke)


def api_error(code, message):
    error = dict(request=request.path, message=message)
    return jsonify(error), code


def error(code, message, template):
    if json_requested():
        return api_error(code, str(message))
    else:
        return render_template(template, error=message), code


def forbidden(message=None):
    message = message or 'You shall not pass!'
    return error(403, message, 'errors/403.html')


def page_not_found(message=None):
    message = message or 'Oops! The page you are looking for does not exist.'
    return error(404, message, 'errors/404.html')


def something_broke(message=None):
    message = message or 'Oops! Stood up too fast and feeling woozy.'
    return error(500, message, 'errors/500.html')


class ApiError(Exception):
    pass
