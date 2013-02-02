from flask import render_template

def register_error_handlers(app):
    app.register_error_handler(403, forbidden)
    app.register_error_handler(404, page_not_found)
    app.register_error_handler(500, something_broke)


def forbidden(error=None):
    error = error or 'You shall not pass!'
    return render_template('403.html', error=error), 403


def page_not_found(error=None):
    error = error or 'Oops! The page you are looking for does not exist.'
    return render_template('404.html', error=error), 404


def something_broke(error=None):
    error = error or 'Oops! Stood up too fast and feeling woozy.'
    return render_template('500.html', error=error), 500
