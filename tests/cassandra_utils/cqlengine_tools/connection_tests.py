from generic_utils.cassandra_utils.cqlengine_tools.test_utils import CassandraTestCaseMixin
from generic_utils.test import TestCase


class ConnectionTimeoutTestCase(CassandraTestCaseMixin, TestCase):
    """Validates that a default connection timeout can be set as expected via configuration
    """

    def default_timeout_from_config_test(self):
        """Validate that the expected configured default timeout is in fact the timeout that is being used
        """
        from cassandra.cqlengine.connection import session
        from ...settings import EXPLICTLY_NOT_10_SECONDS_TIMEOUT

        self.assertEqual(session.default_timeout, EXPLICTLY_NOT_10_SECONDS_TIMEOUT)
