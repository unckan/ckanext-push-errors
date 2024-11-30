"""
We want to receive notification on Slack when an error occurs in the application.
"""
import json
import logging
from datetime import datetime
from logging import Handler, CRITICAL
import requests
from ckan import __version__ as ckan_version
from ckan.plugins import toolkit
from ckanext.push_errors import __VERSION__ as push_errors_version


log = logging.getLogger(__name__)


class PushErrorHandler(Handler):

    def emit(self, record):
        """ Check the record level and send the message to the external URL """
        self.format(record)
        if record.levelno >= CRITICAL:
            # Get all info about the log record
            extras = record.__dict__
            msg = (
                f'{extras["message"]}\n'
                f'[{extras.get("name")}]::{extras.get("levelname")}::'
                f'{extras.get("asctime")}'
            )
            push_message(msg)


def push_message(message, extra_context={}):
    """
    Push a message to a URL
    Some params can be formated with these context vars
     - {site_url}: The site_url from the CKAN config
     - {message}: The message itself. It could include tracebacks and long log messages
     - {ckan_version}: The CKAN version
     - {push_errors_version}: The push_errors extension version
     - {now}: The current datetime
    You can add more context vars in extra_context
    Expected CKAN config values:
     - ckanext.push_errors.url: The URL to push the message
     - ckanext.push_errors.method: The method to use (POST or GET)
     - ckanext.push_errors.headers: A JSON string with the headers to send
     - ckanext.push_errors.data: A JSON string with the data to send
    """

    url = toolkit.config.get('ckanext.push_errors.url')

    if not url:
        log.error('No push-errors defined')
        return

    # Context vars
    ctx = {
        'site_url': toolkit.config.get('ckan.site_url'),  # For user to know the environment (if multiple)
        'message': message,  # The message itself, it could include tracebacks
        'ckan_version': ckan_version,
        'push_errors_version': push_errors_version,
        'now': datetime.now().isoformat(),
    }
    # Add extra context vars
    ctx.update(extra_context)

    # Set the title for the message
    default_title = 'PUSH_ERROR v{push_errors_version} - CKAN {ckan_version}\n{now}\n\n'
    title = toolkit.config.get('ckanext.push_errors.title', default_title)

    message = title.format(**ctx) + message

    method = toolkit.config.get('ckanext.push_errors.method', 'POST')
    # Allow multiple headers in config
    headers_str = toolkit.config.get('ckanext.push_errors.headers', '{}')
    try:
        headers = json.loads(headers_str)
    except json.JSONDecodeError:
        log.error('push-errors Invalid headers')
        return
    # Override each header value with the context
    for key, value in headers.items():
        headers[key] = value.format(**ctx)

    data = toolkit.config.get('ckanext.push_errors.data', '{}')
    try:
        data = json.loads(data)
    except json.JSONDecodeError:
        log.error('push-errors Invalid data')
        return
    # Override each data value with the context
    for key, value in data.items():
        data[key] = value.format(**ctx)

    if method == 'POST':
        response = requests.post(url, json=data, headers=headers)
    elif method == 'GET':
        response = requests.get(url, params=data, headers=headers)
    else:
        log.error('push-errors Invalid method')
        return

    return response