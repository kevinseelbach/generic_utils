"""
Utilities for redis
"""
# future/compat
from builtins import str

from redis.client import StrictRedis

from generic_utils.config import get_config_value

DEFAULT_URL_PATTERN = "redis://{user_info}{host}:{port}/{db}"
USER_PATTERN = "{username}{password}@"

CONFIG_REDIS_SUFFIX = "_REDIS_"
CONFIG_HOST_SUFFIX = CONFIG_REDIS_SUFFIX + "HOST"
CONFIG_PORT_SUFFIX = CONFIG_REDIS_SUFFIX + "PORT"
CONFIG_DB_SUFFIX = CONFIG_REDIS_SUFFIX + "DB"
CONFIG_PASSWORD_SUFFIX = CONFIG_REDIS_SUFFIX + "PASSWORD"
CONFIG_PREFIX_SUFFIX = CONFIG_REDIS_SUFFIX + "PREFIX"
CONFIG_TIMEOUT_SUFFIX = CONFIG_REDIS_SUFFIX + "TIMEOUT"


class RedisConfigComponents(object):
    """ Configuration object for RabbitMQ.
    """
    def __init__(self, host, port, db, password, timeout, prefix):
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self.timeout = timeout
        self.prefix = prefix

    def to_connection_url(self):
        """Returns a connection url suitable for creation of a redis client through the StrictRedis.from_url() method
        based on a `RedisConfigComponents` instance.

        :return: A connection URL suitable for a redis client
        :rtype: str
        """
        return get_connection_url(host=self.host,
                                  port=self.port,
                                  db=self.db,
                                  password=self.password)



def get_client_url(redis_client, include_userinfo=False, include_password=False):
    """
    Returns a url which identifies the server that the provided redis client is addressed to.

    :param redis_client: A StrictRedisClient instance.
    :param include_userinfo: Whether or not to include the user information(username/password) in the returned URL
    :param include_password: If `include_userinfo` is specified, then this indicates whether or not to include the
                                password in the returned URL
    :return: A redis url for the provided `redis_client`
    """
    connection_kwargs = dict(redis_client.connection_pool.connection_kwargs)
    user_info = ""
    if include_userinfo and "username" in connection_kwargs:
        password = ":%s" % connection_kwargs.get("password", "") if include_password else ""
        user_info = USER_PATTERN.format(username=connection_kwargs["username"],
                                        password=password)

    connection_kwargs["user_info"] = user_info
    return DEFAULT_URL_PATTERN.format(**connection_kwargs)


def get_connection_url(host="localhost", port=6379, db=0, password=None):
    user_info = ""
    if password:
        password = ":%s" % password
        user_info = USER_PATTERN.format(username="nouser",
                                        password=password)

    return DEFAULT_URL_PATTERN.format(user_info=user_info,
                                      host=host,
                                      port=port,
                                      db=db)


def get_connection_url_from_config_value(prefix,
                                         default_host='localhost',
                                         default_port=6379,
                                         default_db=0,
                                         default_password=None):
    """Returns a redis connection url based on standard redis configuration values(see `get_redis_config_values`) based
    on the provided `prefix`

    :return: A connection URL which can be provided to Redis as configuration
    """
    config_values = get_redis_config_values(prefix,
                                            default_host,
                                            default_port,
                                            default_db,
                                            default_password)

    return config_values.to_connection_url()


def get_redis_config_values(prefix,
                            default_host='localhost',
                            default_port=6379,
                            default_db=0,
                            default_password=None,
                            default_timeout=None,
                            default_prefix=None):
    """ Returns the configuration components for a redis instance which follows a standard config key naming convention
    as well as sane default values.

    The name of the config value that is used to retrieve each component of the redis configuration is derived from
    the pattern:

    {prefix}_REDIS_{component_suffix}

    Where the {component_suffix} is based on the connection component that is being retrieved.  The possible suffixes
    are:

        host : HOST
        port : PORT
        db : DB
        password : PASSWORD
        prefix : PREFIX
        timeout : TIMEOUT

    :param prefix: The prefix to prefix all of the standard config names for the various components of the redis config.
        For instance, a prefix of "MYPREFIX" would look for the configuration of the host using the key
            "MYPREFIX_REDIS_HOST"
    :return: A namedtuple RedisConfigComponents which contains all of the values of the requested Redis configuration
    :rtype: RedisConfigComponents
    """
    host = get_config_value(prefix + CONFIG_HOST_SUFFIX, default_host)
    port = get_config_value(prefix + CONFIG_PORT_SUFFIX, default_port)
    db = get_config_value(prefix + CONFIG_DB_SUFFIX, default_db)
    password = get_config_value(prefix + CONFIG_PASSWORD_SUFFIX, default_password, secure=True)
    timeout = get_config_value(prefix + CONFIG_TIMEOUT_SUFFIX, default_timeout, val_type=int)
    prefix_val = get_config_value(prefix + CONFIG_PREFIX_SUFFIX, default_prefix)

    return RedisConfigComponents(host, port, db, password, timeout, prefix_val)


class RedisBackedServiceMixin(object):
    """Mixin which provides common functionality for a class which leverages redis as a backing service.  Primary goals
    of this are to provide a common configuration mechanism in order to provide redis in a consistent, simple way.
    """

    redis_client = None
    redis_key_prefix = None
    redis_key_separator = ":"

    def __init__(self, client=None, key_prefix=None, *args, **kwargs):
        self.set_redis_client(client, key_prefix)
        super(RedisBackedServiceMixin, self).__init__(*args, **kwargs)

    def set_redis_client(self, client, key_prefix=None):
        if isinstance(client, StrictRedis):
            self.redis_client = client
        elif isinstance(client, RedisConfigComponents):
            self.redis_client = StrictRedis.from_url(client.to_connection_url())
            if key_prefix is None:
                key_prefix = client.prefix
        self.key_prefix = key_prefix

    def _get_full_redis_key(self, key):
        key = str(key)
        if self.key_prefix:
            key = self.key_prefix + self.redis_key_separator + key

        return key
