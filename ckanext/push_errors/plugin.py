import logging
import traceback
from werkzeug.exceptions import Forbidden, Unauthorized, NotFound
from ckan import plugins
from ckan.common import current_user
from ckan.plugins import toolkit
from ckanext.push_errors.logging import PushErrorHandler, push_message
from ckanext.push_errors.cli import push_errors as push_errors_commands
from ckanext.push_errors.utils import get_error_trace_id

from ckanext.push_errors.blueprints.push_errors import push_error_bp

log = logging.getLogger(__name__)


class PushErrorsPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IClick)
    plugins.implements(plugins.IMiddleware)
    plugins.implements(plugins.IBlueprint)

    # IMiddleware

    def make_middleware(self, app, config):
        """ Allow this extension to capture request errors and push them to an external URL """

        if not hasattr(app, 'register_error_handler'):
            log.info(f'PUSH_ERRORS The app {app} has no register_error_handler')
            return app

        def error_handler(exception):
            """ Capture all errors from the application """
            if not current_user:
                # If no user is logged in, ignore certain exceptions that represent expected scenarios,
                # such as 401 (Unauthorized), 403 (Forbidden), and 404 (Not Found). These are not system
                # failures but access-related or missing resource errors.

                # List of known exception types to skip for anonymous users.
                skip_types_if_anon = (
                    Unauthorized, Forbidden, NotFound,
                    toolkit.NotAuthorized, toolkit.ObjectNotFound,
                )

                # Check if the exception matches any known types and skip processing if so.
                if isinstance(exception, skip_types_if_anon):
                    return None

            exception_str = f'{exception} [({type(exception).__name__})]'
            # get the stacktrace
            trace = traceback.format_exc()
            # Limit the max trace length based on configuration
            max_trace_length = int(toolkit.config.get('ckanext.push_errors.traceback_length', 4000))
            trace = trace[:max_trace_length]
            params = toolkit.request.args if toolkit.request else '-'
            path = toolkit.request.path if toolkit.request else '-'
            user = current_user.name if current_user else '-'
            error_id = get_error_trace_id(exception)

            error_message = (
                f'INTERNAL_ERROR `{exception_str}`\n'
                f'TRACE\n'
                f'```{trace}```\n'
                f'on page {path}\n'
                f'params: {params}\n'
                f'by user *{user}*'
            )
            push_message(error_message, extra_context={'error_id': error_id})
            raise exception

        app.register_error_handler(Exception, error_handler)

        return app

    def make_error_log_middleware(self, app, config):
        """ Capture all log.critical messages """

        # Prepare and add the PushErrorHandler
        push_error_handler = PushErrorHandler()
        push_error_handler.setLevel(logging.ERROR)
        logging.getLogger('ckan').addHandler(push_error_handler)
        logging.getLogger('ckanext').addHandler(push_error_handler)
        return app

    # IClick

    def get_commands(self):
        return [push_errors_commands]

    # IBlueprint

    def get_blueprint(self):
        return [push_error_bp]
