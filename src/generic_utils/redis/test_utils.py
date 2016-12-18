import new
from generic_utils import loggingtools
from generic_utils.test import TestCaseMixinMetaClass
import os
from functools import update_wrapper
from unittest import SkipTest
from redis import ConnectionError

from .utils import get_client_url


log = loggingtools.getLogger(__name__)

REDIS_TEST_KEY = "__THIS_IS_A_TEST_INSTANCE__"
REDIS_TEST_INSTANCE_ENV_VAR = "REDIS_TEST_INSTANCES"

_declared_test_instances = None


class RedisTestCaseMixin(object):
    __metaclass__ = TestCaseMixinMetaClass
    # Either a redis client instance or a function which takes no arguments which returns a redis client to use for the
    # test case.  This must be provided otherwise the test will be skipped
    redis_client = None

    # Whether or not this Mixin should be enabled.  It is possible that based on the dynamic configuration of the system
    # that the test case does not actually use redis, in which case the mixin should not perform its duties.  If this is
    # False then the mixin is disabled and all operations are a noop
    redis_mixin_enabled = True

    def _custom_teardown(self):
        self.do_redis_cleanup()
        try:
            super(RedisTestCaseMixin, self)._custom_teardown()
        except AttributeError:
            pass

    @classmethod
    def _enable_test_method_override(cls):
        return cls.redis_mixin_enabled

    @classmethod
    def setUpClass(cls):
        if cls.redis_mixin_enabled:
            cls.redis_client = cls.validate_redis_client()
        super(RedisTestCaseMixin, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        if cls.redis_mixin_enabled:
            cls.do_redis_cleanup()
        super(RedisTestCaseMixin, cls).tearDownClass()

    @classmethod
    def do_redis_cleanup(cls):
        """Cleans up the current redis instance either after a test execution or before in order to prepare for a new
        clean test run.
        """
        if cls.redis_client:
            if is_test_redis_instance(cls.redis_client):
                log.debug("Flushing redis DB")
                record_needed = is_recorded_as_test_instance(cls.redis_client)
                cls.redis_client.flushdb()
                if record_needed:
                    # After we flush the db, we need to reapply the record of it being a test instance
                    record_as_test_instance(cls.redis_client)
        else:
            log.error("No redis_client defined on the test class therefore cannot do any cleanup")

    @classmethod
    def validate_redis_client(cls):
        """
        Verifies that the provided client is a valid working test redis server otherwise throw a SkipTest exception
        """
        client = cls.redis_client
        if client is None:
            log.error("No redis client provided, so skipping test case which depends on it")
            raise SkipTest("No redis client provided")

        if hasattr(client, "__call__"):
            try:
                client = client.__func__()
            except ValueError:
                log.exception("Redis is not properly configured, so skipping test case which depends on it")
                raise SkipTest("Redis is not configured or is unavailable")

        client_url = get_client_url(client)

        try:
            client.ping()
        except ConnectionError:
            log.warn("Redis instance %s is not configured or is unavailable.  Skipping tests which depend on it", client_url)
            raise SkipTest("Redis instance %s is not configured or is unavailable" % client_url)

        if not is_test_redis_instance(client):
            log.warn("Redis instance %s is not a test instance.  Skipping tests which depend on it", client_url)
            raise SkipTest("Redis instance %s is not a test instance" % client_url)

        return client


def is_test_redis_instance(redis_client):
    """Returns whether or not the redis instance `redis_client` is a test redis instance or not.  This is currently
        determined by the presence of a particular key within the redis instance or the presence of the host string
        within the semi-colon separated environment variable "REDIS_TEST_INSTANCES"
    """
    if redis_client is None:
        return False

    client_url = get_client_url(redis_client)

    if redis_client.exists(REDIS_TEST_KEY):
        log.debug("Redis client '%s' is explictly marked as a test instance", client_url)
        return True

    if client_url in get_declared_redis_test_instances():
        log.debug("Redis client '%s' is declared as a test instance", client_url)
        return True

    return False


def get_declared_redis_test_instances():
    """Returns a list of the urls for the declared redis test instances

    :return: A list of the urls for the declared redis test instances
    """
    global _declared_test_instances
    if _declared_test_instances is None:
        if REDIS_TEST_INSTANCE_ENV_VAR in os.environ:
            _declared_test_instances = os.environ[REDIS_TEST_INSTANCE_ENV_VAR].split(";")
        else:
            _declared_test_instances = []

    return _declared_test_instances


def is_recorded_as_test_instance(redis_client):
    """Returns whether or not the redis instance `redis_client` has been explicitly marked as a test instance or not

    :rtype: bool
    """
    if redis_client is None:
        return False

    return redis_client.exists(REDIS_TEST_KEY)


def record_as_test_instance(redis_client):
    """
    Records the server that the provided `redis_client` refers to as a test instance and can therefore be wiped clean
    during test executions.

    Currently this just means to set a known Key within the instance.

    :param redis_client: A redis client instance which can be used to communicate with a redis server
    """
    redis_client.set(REDIS_TEST_KEY, True)
    log.info("Recorded redis instance '%s' as a test instance", get_client_url(redis_client))
