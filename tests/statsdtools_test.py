from unittest import TestCase

from generic_utils import loggingtools
from generic_utils.config.test_utils import override_config
from generic_utils.statsdtools import STATSD_NULL_CLIENT_TYPE, _get_statsd_from_config, NullStatsClient, \
    TestCaseStatsClient, STATSD_TESTCASE_CLIENT_TYPE

log = loggingtools.getLogger()


class StatsConfigTestCase(TestCase):
    """Test cases which validate the various configuration driven options for the statsd client
    """
    def test_null_client(self):
        """Validates that we can configure and get the null statsd client as expected
        """
        statsd_client = _get_statsd_from_config()
        self.assertIsInstance(statsd_client, TestCaseStatsClient)

        with override_config(STATSD_CLIENT_TYPE=STATSD_NULL_CLIENT_TYPE):
            statsd_client = _get_statsd_from_config()
            self.assertIsInstance(statsd_client, NullStatsClient)

        # Validate that outside of the override we get the expected client
        statsd_client = _get_statsd_from_config()
        self.assertIsInstance(statsd_client, TestCaseStatsClient)


class NullStatsClientTestCase(TestCase):

    def test_basic_behavior(self):
        """Validates that the NullStatsClient works as expected
        """
        with override_config(STATSD_CLIENT_TYPE=STATSD_NULL_CLIENT_TYPE):
            statsd_client = _get_statsd_from_config()
            self.assertIsInstance(statsd_client, NullStatsClient)
            clients = [statsd_client, statsd_client.pipeline()]
            # Validate that these do nothing...aka they dont fail
            for client in clients:
                client.incr("incr")
                client.set("setval", 12)
                client.decr("decr")
                client.gauge("gauge", 10)
                client.timer("timer")


class CacheStatsClientTestCase(TestCase):
    def test_basic_behavior(self):
        """Validates TestCaseStatsClient works as expected
        """
        with override_config(STATSD_CLIENT_TYPE=STATSD_TESTCASE_CLIENT_TYPE):
            statsd_client = _get_statsd_from_config()
            self.assertIsInstance(statsd_client, TestCaseStatsClient)
            clients = [statsd_client, statsd_client.pipeline()]

            ### EXECUTION
            for client in clients:
                client.incr("incr")
                client.set("setval", 12)
                client.decr("decr")
                client.gauge("gauge", 10)
                client.timer("timer")

            ### VALIDATION
            self.assertEqual(statsd_client.cache['incr|count'], [[1, 1]])
            self.assertEqual(statsd_client.cache['setval|set'], [[12, 1]])
            self.assertEqual(statsd_client.cache['decr|count'], [[-1, 1]])
            self.assertEqual(statsd_client.cache['gauge|gauge'], [[10, 1]])



