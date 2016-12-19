"""
Utilities for rabbitmq
"""
# stdlib
from generic_utils.config import get_config_value
from generic_utils.loggingtools import getLogger

LOG = getLogger()

DEFAULT_URL_PATTERN = "amqp://{user_info}{host}:{port}/{vhost}"
USER_PATTERN = "{username}:{password}@"

CONFIG_RABBITMQ_SUFFIX = "_RABBITMQ_"
CONFIG_HOST_SUFFIX = CONFIG_RABBITMQ_SUFFIX + "HOST"
CONFIG_PORT_SUFFIX = CONFIG_RABBITMQ_SUFFIX + "PORT"
CONFIG_VHOST_SUFFIX = CONFIG_RABBITMQ_SUFFIX + "VHOST"
CONFIG_USERNAME_SUFFIX = CONFIG_RABBITMQ_SUFFIX + "USERNAME"
CONFIG_PASSWORD_SUFFIX = CONFIG_RABBITMQ_SUFFIX + "PASSWORD"


class RabbitMQConfigComponents(object):
    """ Configuration object for RabbitMQ.
    """
    def __init__(self, host, port, vhost, username, password):
        self.host = host
        self.port = port
        self.vhost = vhost
        self.username = username
        self.password = password

    def to_connection_url(self):
        """Returns a connection url suitable for rabbitmq and celery.

        :return: A rabbitmq connection URL
        :rtype: str
        """
        user_info = USER_PATTERN.format(username=self.username,
                                        password=self.password)
        connection_url = DEFAULT_URL_PATTERN.format(user_info=user_info,
                                                    host=self.host,
                                                    port=self.port,
                                                    vhost=self.vhost)

        return connection_url


def get_rabbitmq_config_values(prefix,
                               default_host='localhost',
                               default_port=5672,
                               default_vhost='/',
                               default_user=None,
                               default_password=None):
    """
    Lookup configuration for RabbitMQ details and return a RabbitMQConfigComponents object.
    :param prefix:
    :param default_host:
    :param default_port:
    :param default_user:
    :param default_password:
    :return:
    """
    host = get_config_value(prefix + CONFIG_HOST_SUFFIX, default_host)
    port = get_config_value(prefix + CONFIG_PORT_SUFFIX, default_port, val_type=int)
    vhost = get_config_value(prefix + CONFIG_VHOST_SUFFIX, default_vhost)
    username = get_config_value(prefix + CONFIG_USERNAME_SUFFIX, default_user)
    password = get_config_value(prefix + CONFIG_PASSWORD_SUFFIX, default_password, secure=True)

    return RabbitMQConfigComponents(host, port, vhost, username, password)
