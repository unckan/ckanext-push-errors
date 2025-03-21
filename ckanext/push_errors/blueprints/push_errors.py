import logging
from flask import Blueprint
from ckan.plugins import toolkit

log = logging.getLogger(__name__)

push_error_bp = Blueprint('push_errors', __name__, url_prefix='/push-error')


@push_error_bp.route('/test', methods=["GET"])
def test_push_error():
    """
    A view function that logs a critical error message.
    Only accessible by sysadmins.
    """
    # Check if the current user is a sysadmin
    if not toolkit.g.userobj or not toolkit.g.userobj.sysadmin:
        return toolkit.abort(403, toolkit._('Unauthorized to access this page'))

    # Get the message from the query parameters or use the default
    msg = toolkit.request.params.get('msg', 'Push error test message')

    # Log the critical message
    log.critical(msg)

    # Return a simple confirmation
    return toolkit._('Message logged: {}').format(msg)
