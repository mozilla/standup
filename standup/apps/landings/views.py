from flask import Blueprint, render_template


blueprint = Blueprint('landings', __name__)


@blueprint.route('/help')
def help():
    """The help page."""
    return render_template('landings/help.html')
