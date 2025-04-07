import logging
from redis import Redis, ConnectionPool
from ckan.plugins import toolkit


log = logging.getLogger(__name__)


def get_cache():
    """ Get the Redis cache connection """
    log.debug('Getting Redis cache connection')

    redis_url = toolkit.config.get('ckan.redis.url', 'redis://localhost:6379/0')
    redis_pool = ConnectionPool.from_url(redis_url)
    cache = Redis(connection_pool=redis_pool)
    log.info(f'Connected to Redis cache at {redis_url}')
    return cache
