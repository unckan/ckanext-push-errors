import logging
from ckanext.push_errors.redis import get_cache

log = logging.getLogger(__name__)


def push_errors_enable(self, context, data_dict):
    """Enable the sending of notifications"""
    cache = get_cache()
    cache.set('push_errors:enabled', '1')
    log.info("push-errors: Notifications enabled.")
    return {'status': 'enabled'}


def push_errors_disable(self, context, data_dict):
    """Disable the sending of notifications"""
    cache = get_cache()
    cache.set('push_errors:enabled', '0')
    log.info("push-errors: Notifications disabled.")
    return {'status': 'disabled'}
