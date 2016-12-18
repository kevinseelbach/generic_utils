from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from future import standard_library
standard_library.install_aliases()

from generic_utils.cassandra_utils.cqlengine_tools.connection import ConfigKey
from generic_utils.config import get_config_value

EXPLICTLY_NOT_10_SECONDS_TIMEOUT = 15.0

CQLENGINE = {
    "TEST_CLUSTER": {
        ConfigKey.CONTACT_POINTS: get_config_value("TEST_CASSANDRA_CONTACT_POINTS", default=["localhost"]),
        ConfigKey.KEYSPACE: get_config_value("TEST_CASSANDRA_KEYSPACE", "python_utils_test"),
        ConfigKey.PORT: get_config_value("TEST_CASSANDRA_PORT", default=9042),
        ConfigKey.USERNAME: get_config_value("TEST_CASSANDRA_USERNAME", default=""),
        ConfigKey.PASSWORD: get_config_value("TEST_CASSANDRA_PASSWORD", default=""),
        ConfigKey.DEFAULT_TIMEOUT: EXPLICTLY_NOT_10_SECONDS_TIMEOUT
    }
}

