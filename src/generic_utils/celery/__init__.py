"""
Python Utils for Celery Job Framework
"""

from generic_utils.redis.utils import get_redis_config_values
from generic_utils.rabbitmq.utils import get_rabbitmq_config_values
from generic_utils.config import get_config_value
from generic_utils.loggingtools import getLogger

log = getLogger()


class BrokerTypes(object):
    """ Broker Type vars
    """
    REDIS = "REDIS"
    RABBITMQ = "RABBITMQ"


BROKER_URL_FUNCS = {
    BrokerTypes.REDIS: get_redis_config_values,
    BrokerTypes.RABBITMQ: get_rabbitmq_config_values
}


def get_broker_url(prefix):
    """
    Return the appropriate broker URL.
    :return:
    """
    broker_type = get_config_value("_".join([prefix, "BROKER_TYPE"]), default=BrokerTypes.REDIS)

    try:
        fnc = BROKER_URL_FUNCS[broker_type]

        log.debug("calling %s to get broker url.", fnc)
        broker_url = BROKER_URL_FUNCS[broker_type](prefix).to_connection_url()
    except KeyError:
        log.warn("Attempted to get broker url for broker type %s, but no connection url func defined in "
                 "BROKER_URL_FUNCS")
        return None
    except TypeError as exc:
        log.warn("Error calling %s to get broker_url (%s)", fnc, exc)
        return None

    log.debug("get_broker_url from celery.utils returning %s", broker_url)

    return broker_url


def get_result_backend(prefix):
    """
    Return the appropriate result backend URL.
    :return:
    """
    result_backend_url = get_redis_config_values(prefix).to_connection_url()

    log.debug("get_result_backend from celery.utils returning %s", result_backend_url)

    return result_backend_url
