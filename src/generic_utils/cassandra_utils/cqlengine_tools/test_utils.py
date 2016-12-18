"""Module which contains utilities for writing tests using Cassandra

"""
from unittest import SkipTest
import warnings
from cassandra.cluster import NoHostAvailable  # pylint: disable=no-name-in-module
from cassandra.cqlengine import management
from cassandra.cqlengine import CQLEngineException
from generic_utils import loggingtools
from generic_utils.cassandra_utils.cqlengine_tools.connection import setup_connection_from_config, \
    is_cassandra_available as prod_is_cassandra_available
from generic_utils.cassandra_utils.cqlengine_tools.schema_tools import truncate_table, create_keyspace_from_model
from generic_utils.test import TestCaseMixinMetaClass, TestCase


log = loggingtools.getLogger()


def is_cassandra_available():
    """
    :return: Whether or not Cassandra is currently available.
    :rtype: bool
    """
    warnings.warn("This method has been moved to "
                  "generic_utils.cassandra_utils.cqlengine_tools.connection.is_cassandra_available and that should "
                  "be used instead as this method is pending deprecation.", DeprecationWarning)
    return prod_is_cassandra_available()


class CassandraTestCaseMixin(TestCase):
    """TestCase mixin which provides helper functionality for dealing with Cassandra within a TestCase such as:

    1> Auto skipping of the whole TestCase if Cassandra is not available
    2> Auto syncing of models which are defined in the class property `test_models`
    3> Truncation of models defined in `test_models` on tearDown to provide post test cleanup
    """
    __metaclass__ = TestCaseMixinMetaClass

    # Whether or not this Mixin should be enabled.  It is possible that based on the dynamic configuration of the system
    # that the test case does not actually use cassandra, in which case the mixin should not perform its duties.
    # If this is False then the mixin is disabled and all operations are a noop
    cass_mixin_enabled = True

    # A list of CQLEngine Model classes which the test relies on and uses.  Models defined here will be synced before
    # test execution and cleaned up after a test execution
    test_models = None

    def _custom_setup(self):  # pylint: disable=invalid-name
        """Overloaded _custom_setup
        """
        if self.cass_mixin_enabled:
            self.validate_cassandra_client()

            try:
                self.sync_models()
            except NoHostAvailable:
                log.debug("No Cassandra host available.  Skipping test")
                raise SkipTest("No Cassandra host available")
            except CQLEngineException:
                log.exception("CQLEngineException occurred while trying to setup Cassandra models and we must assume "
                              "it is a configuration issue and therefore are just going to skip this test")
                raise SkipTest("CQLEngineException occurred which prevents executing a Cassandra test")
            # Perform cleanup before running the test to ensure the test is running in a clean environment
            self.do_cassandra_cleanup()
        try:
            super(CassandraTestCaseMixin, self)._custom_setup()
        except AttributeError:
            pass

    def _custom_teardown(self):  # pylint: disable=invalid-name
        """Overloaded _custom_teardown
        """
        if self.cass_mixin_enabled:
            self.do_cassandra_cleanup()
        try:
            super(CassandraTestCaseMixin, self)._custom_teardown()
        except AttributeError:
            pass

    @classmethod
    def setUpClass(cls):  # pylint: disable=invalid-name
        """Setup functionality on Class creation
        """
        if cls.cass_mixin_enabled:
            cass_setup = False
            try:
                cass_setup = setup_connection_from_config()
            except AttributeError:
                pass
            if not cass_setup:
                raise SkipTest("Cassandra is not configured correctly.")
            cls.validate_cassandra_client()
        super(CassandraTestCaseMixin, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):  # pylint: disable=invalid-name
        """Destruction functionality on Class test execution complete
        """
        if cls.cass_mixin_enabled:
            cls.do_cassandra_cleanup()
        super(CassandraTestCaseMixin, cls).tearDownClass()

    @classmethod
    def do_cassandra_cleanup(cls):
        """Cleans up the current Cassandra instance either after a test execution or before in order to prepare for a
        new clean test run.
        """
        cls.truncate_models()

    @classmethod
    def validate_cassandra_client(cls):
        """
        Verifies that the provided client is a valid working test Cassandra server otherwise throw a SkipTest exception
        """
        if not prod_is_cassandra_available():
            log.warn("Cassandra is not currently available.  Skipping tests which depend on it")
            raise SkipTest("Cassandra is not currently available")

    @classmethod
    def sync_models(cls):
        """Syncs Cassandra against models defined on the class property "test_models"
        """
        test_models = cls.test_models
        if test_models:
            for model in test_models:
                create_keyspace_from_model(model)
                management.sync_table(model)
                log.debug("Cassandra table %s in keyspace %s for model %s created",
                          model.column_family_name(), model._get_keyspace(), model)  # pylint: disable=protected-access

    @classmethod
    def truncate_models(cls):
        """Truncates tables within Cassandra for any models defined on the class property "test_models"
        """
        test_models = cls.test_models
        if test_models:
            for model in test_models:
                truncate_table(model)
                log.debug("Truncated cassandra table %s in keyspace %s for model %s",
                          model.column_family_name(), model._get_keyspace(), model)  # pylint: disable=protected-access
