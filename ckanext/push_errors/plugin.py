import logging
import traceback
from werkzeug.exceptions import Forbidden, Unauthorized, NotFound
from ckan import plugins
from ckan.common import current_user
from ckan.plugins import toolkit
from ckanext.push_errors.logging import PushErrorHandler, push_message
from ckanext.push_errors.cli import push_errors as push_errors_commands
from ckanext.push_errors.error_logger import log_error

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

            if not current_user:
                # ignore 401, 403 and 404 errors if no user is logged in
                skip_types_if_anon = (
                    Unauthorized, Forbidden, NotFound,
                    toolkit.NotAuthorized, toolkit.ObjectNotFound,
                )

                if type(exception) in skip_types_if_anon:
                    return

            # Registrar usando log_error (deduplicación y silenciado)
            try:
                log_error(exception)
            except Exception as log_err:
                log.warning(f'push-errors: log_error failed: {log_err}')

            exception_str = f'{exception} [({type(exception).__name__})]'
            # get the stacktrace
            trace = traceback.format_exc()
            # Limit the max trace length based on configuration
            max_trace_length = int(toolkit.config.get('ckanext.push_errors.traceback_length', 4000))
            trace = trace[:max_trace_length]
            params = toolkit.request.args if toolkit.request else '-'
            path = toolkit.request.path if toolkit.request else '-'
            user = current_user.name if current_user else '-'

            error_message = (
                f'INTERNAL_ERROR `{exception_str}` \n\t'
                f'TRACE\n```{trace}```\n\t'
                f'on page {path}\n\t'
                f'params: {params}\n\t'
                f'by user *{user}*'
            )
            push_message(error_message)
            # Continue to raise the error
            raise exception

        app.register_error_handler(Exception, error_handler)

        return app

    def make_error_log_middleware(self, app, config):
        """ Capture all log.critical messages """

        # Prepare and add the PushErrorHandler
        push_error_handler = PushErrorHandler()
        push_error_handler.setLevel(logging.ERROR)

        # Add to the ckan logger
        ckan_log = logging.getLogger('ckan')
        ckan_log.addHandler(push_error_handler)
        # Add to the ckanext logger for all extensions
        ckanext_log = logging.getLogger('ckanext')
        ckanext_log.addHandler(push_error_handler)

        if not hasattr(app, 'logger'):
            log.info(f'PUSH_ERRORS The app {app} has no logger')
        else:
            # Add to the app. TODO.Investigate if this is needed
            app.logger.addHandler(push_error_handler)

        return app

    # IClick

    def get_commands(self):
        return [push_errors_commands]

    # IBlueprint

    def get_blueprint(self):
        return [push_error_bp]
