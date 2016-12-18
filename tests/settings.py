"""Settings required for driving the python utils test suite
"""
from generic_utils.cassandra_utils.cqlengine_tools.connection import ConfigKey as CQLEngineConfigKey
from generic_utils.config import get_config_value

#: A timeout that is not the same as the standard default to facilitate testing of the ability to set the timeout
#: via configuration.  This can be changed if needed because of a real timeout need, but just don't set to 10.0
#: This is being used to validate core functionality within the test case
# cassandra_utils.cqlengine_tools.connection_tests.ConnectionTimeoutTestCase
EXPLICTLY_NOT_10_SECONDS_TIMEOUT = 15.0

# Settings for cassandra
CQLENGINE = {
    "TEST_CLUSTER": {
        CQLEngineConfigKey.CONTACT_POINTS: get_config_value("TEST_CASSANDRA_CONTACT_POINTS", default=["localhost"]),
        CQLEngineConfigKey.KEYSPACE: get_config_value("TEST_CASSANDRA_KEYSPACE", "python_utils_test"),
        CQLEngineConfigKey.PORT: get_config_value("TEST_CASSANDRA_PORT", default=9042),
        CQLEngineConfigKey.USERNAME: get_config_value("TEST_CASSANDRA_USERNAME", default=""),
        CQLEngineConfigKey.PASSWORD: get_config_value("TEST_CASSANDRA_PASSWORD", default=""),
        CQLEngineConfigKey.DEFAULT_TIMEOUT: EXPLICTLY_NOT_10_SECONDS_TIMEOUT
    }
}

STATSD_CLIENT_TYPE = "TESTCASE"

# Just adding something in here to verify config exceptions are suppressed
SAFE_EXCEPTION_CLASSES = ["generic_utils.exceptions.GenUtilsValueError"]

try:
    from .local_settings import *
except ImportError:
    pass
