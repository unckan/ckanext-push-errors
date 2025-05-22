import traceback
import logging


log = logging.getLogger(__name__)

logged_errors = set()  # To track already logged errors
disabled_notifications = set()  # To track disabled error notifications


def log_error(error, disable_notification=False):
    tb = traceback.extract_tb(error.__traceback__)
    if tb:
        file_path, line_number, _, _ = tb[-1]
        error_id = f"{file_path}:{line_number}"
    else:
        error_id = "unknown"

    if error_id in disabled_notifications:
        return  # Skip logging if notifications are disabled for this error

    if error_id not in logged_errors:
        logged_errors.add(error_id)
        log.critical(error)

    if disable_notification:
        disabled_notifications.add(error_id)
