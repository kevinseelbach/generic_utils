""" Test settings functions
"""
# stdlib
import os
from unittest import TestCase

from generic_utils.celery import BrokerTypes
from generic_utils.celery import get_broker_url
from generic_utils.loggingtools import getLogger

LOG = getLogger()


class BaseSettingsTests(TestCase):
    """ Tests for functions in base_settings
    """
    def setUp(self):
        self.old_environ = os.environ

    def tearDown(self):
        os.environ = self.old_environ

    def test_get_broker_url_redis(self):
        """
        Test function that returns the broker url for celery.
        :return:
        """
        os.environ["TEST_CELERY_BROKER_TYPE"] = BrokerTypes.REDIS
        os.environ["TEST_CELERY_REDIS_HOST"] = "somehost"
        os.environ["TEST_CELERY_REDIS_PORT"] = "888"
        os.environ["TEST_CELERY_REDIS_DB"] = "123"
        os.environ["TEST_CELERY_REDIS_PREFIX"] = "someprefix"
        os.environ["TEST_CELERY_REDIS_PASSWORD"] = "somepassword"

        broker_url = get_broker_url("TEST_CELERY")

        self.assertEqual(broker_url, "redis://nouser:somepassword@somehost:888/123")

        del os.environ["TEST_CELERY_BROKER_TYPE"]

        broker_url = get_broker_url("TEST_CELERY")

        self.assertEqual(broker_url, "redis://nouser:somepassword@somehost:888/123")

    def test_get_broker_url_rabbitmq(self):
        """
        Test function using rabbitmq connection details.
        :return:
        """
        os.environ["TEST_CELERY_BROKER_TYPE"] = BrokerTypes.RABBITMQ
        os.environ["TEST_CELERY_RABBITMQ_HOST"] = "somehost"
        os.environ["TEST_CELERY_RABBITMQ_PORT"] = "889"
        os.environ["TEST_CELERY_RABBITMQ_USERNAME"] = "someusername"
        os.environ["TEST_CELERY_RABBITMQ_PASSWORD"] = "somepassword"

        broker_url = get_broker_url("TEST_CELERY")

        self.assertEqual(broker_url, "amqp://someusername:somepassword@somehost:889//")
