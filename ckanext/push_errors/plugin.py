import logging
from werkzeug.exceptions import Forbidden, Unauthorized, NotFound
from ckan import plugins
from ckan.common import current_user
from ckan.plugins import toolkit
from ckanext.push_errors.logging import PushErrorHandler, push_message
from ckanext.push_errors.cli import push_errors as push_errors_commands


log = logging.getLogger(__name__)


class PushErrorsPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IClick)
    plugins.implements(plugins.IMiddleware)

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

            exception_str = f'{exception} [({type(exception).__name__})]'
            # get the stacktrace
            import traceback
            trace = traceback.format_exc()
            # Limit the max trace length
            trace = trace[-4000:]
            path = toolkit.request.path if toolkit.request else '-'
            user = current_user.name if current_user else '-'

            error_message = (
                f'INTERNAL_ERROR `{exception_str}` \n\t'
                f'TRACE\n```{trace}```\n\t'
                f'on page {path}\n\t'
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
