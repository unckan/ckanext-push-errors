import json
import logging
from datetime import datetime
from logging import Handler, CRITICAL
import requests
from ckan import __version__ as ckan_version
from ckan.common import current_user
from ckan.plugins import toolkit
from ckanext.push_errors import __VERSION__ as push_errors_version
from ckanext.push_errors.redis import get_cache

log = logging.getLogger(__name__)


def can_send_message():
    """
    Verifica si se puede enviar una nueva notificación según los límites definidos.
    """
    cache = get_cache()
    limit_minute = int(toolkit.config.get('ckanext.push_errors.max_messages_minute', 3))  # Default: 3
    limit_hour = int(toolkit.config.get('ckanext.push_errors.max_messages_hour', 10))    # Default: 10

    current_minute = datetime.now().strftime('%Y%m%d%H%M')
    current_hour = datetime.now().strftime('%Y%m%d%H')

    # Claves para Redis
    minute_key = f'push_errors:minute:{current_minute}'
    hour_key = f'push_errors:hour:{current_hour}'

    # Incrementar contadores
    minute_count = cache.incr(minute_key)
    hour_count = cache.incr(hour_key)

    # Define expire in the last call
    if minute_count == 1:
        cache.expire(minute_key, 60)  # Expira en 60 segundos
    if hour_count == 1:
        cache.expire(hour_key, 3600)  # Expira en 1 hora

    # Verify limits
    if minute_count > limit_minute:
        log.warning(f'push-errors: Push error minute limit exceeded ({minute_count}/{limit_minute})')
        return False

    # Solo aplicar límite por minuto si también estamos cerca del límite por hora
    if hour_count > limit_hour:
        log.warning(f'push-errors: Push error hour limit exceeded ({hour_count}/{limit_hour})')
        return False

    return True


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
     - {user}: The current user name (or "-")
    You can add more context vars in extra_context
    Expected CKAN config values:
     - ckanext.push_errors.url: The URL to push the message
     - ckanext.push_errors.method: The method to use (POST or GET)
     - ckanext.push_errors.headers: A JSON string with the headers to send
     - ckanext.push_errors.data: A JSON string with the data to send
    """

    if not can_send_message():
        log.info('push-errors: Message not sent due to notification limit.')
        return None

    url = toolkit.config.get('ckanext.push_errors.url')

    # Context vars
    ctx = {
        'site_url': toolkit.config.get('ckan.site_url'),  # For user to know the environment (if multiple)
        'ckan_version': ckan_version,
        'push_errors_version': push_errors_version,
        'now': datetime.now().isoformat(),
        'user': current_user.name if current_user else '-',
    }
    # Add extra context vars
    ctx.update(extra_context)

    # Set the title for the message
    default_title = 'PUSH_ERROR *{site_url}* \nv{push_errors_version} - CKAN {ckan_version}\n{now} user: {user}\n'
    title = toolkit.config.get('ckanext.push_errors.title') or default_title

    formated_message = title.format(**ctx) + "\n" + message
    ctx['message'] = formated_message

    if not url:
        log.warning('push-errors: No URL configured, logging message locally.')
    else:
        log.debug(f'push-errors Sending message to {url}')

    # Allow multiple headers in config
    # Decoding headers
    headers_str = toolkit.config.get('ckanext.push_errors.headers', '{}') or '{}'
    try:
        headers = json.loads(headers_str)
    except json.JSONDecodeError:
        log.error('push-errors Invalid headers')
        return

    # Override each header value with the context
    for key, value in headers.items():
        headers[key] = value.format(**ctx)

    # Decoding data
    data = toolkit.config.get('ckanext.push_errors.data', '{}') or '{}'
    try:
        data = json.loads(data)
    except json.JSONDecodeError:
        log.error(f'push-errors Invalid data: {data}')
        return
    # Override each data value with the context
    for key, value in data.items():
        data[key] = value.format(**ctx)

    # Sending request
    method = toolkit.config.get('ckanext.push_errors.method', 'POST')
    try:
        response = send_message_to_url(url, headers, data, method)
    except requests.RequestException as e:
        log.error(f'push-errors: Failed to send message to {url}. Exception: {str(e)}')
        return

    if not response:
        return

    # Validating response
    if response.status_code not in (200, 201):
        e = (
            f'push-errors message NOT sent{response.status_code} {response.text}\n\t'
            f'DATA: {data}\n\tHEADERS: {headers}'
        )
        log.error(e)
    else:
        log.info(f'push-errors message sent {response.status_code} {response.text}')

    return response


def send_message_to_url(url, headers={}, data={}, method='POST'):
    """
    Send a message to a URL (if any)
    """
    if not url:
        # Emulate and log the message
        msg = (
            'push-errors message not sent: No URL configured'
            f'\n\tDATA: {data}\n\tHEADERS: {headers}'
        )
        log.error(msg)
        return

    if method == 'POST':
        response = requests.post(url, json=data, headers=headers)
    elif method == 'GET':
        response = requests.get(url, params=data, headers=headers)
    else:
        log.error('push-errors: Invalid method')
        return

    return response
