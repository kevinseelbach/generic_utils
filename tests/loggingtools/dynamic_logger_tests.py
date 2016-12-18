import logging

from mock import patch
from generic_utils import loggingtools
from generic_utils.loggingtools.dynamic_logger import DynamicLogLevelLogger
from generic_utils.loggingtools.loggingconfig import LoggingLevelManager, \
    InMemoryLogLevelProvider
from generic_utils.loggingtools import dynamic_logger
from generic_utils.loggingtools.test_utils import LoggingSpy
from generic_utils.test import TestCase


LOG = loggingtools.getLogger()


class DynamicLoggerTestCase(TestCase):

    @classmethod
    def setUpClass(cls):
        old_logger_class = logging.getLoggerClass()
        # Temporarily set the logger class to DynamicLogLevelLogger so our loggers for our test are of the correct type
        logging.setLoggerClass(DynamicLogLevelLogger)
        DynamicLogLevelLogger.enable_dynamic_config()
        try:
            cls.base_log = loggingtools.getLogger()
            cls.base_log.level = logging.ERROR
            cls.logging_spy = LoggingSpy(loggers=[cls.base_log])
            cls.base_log_name = cls.base_log.name
            # Intentionally don't create a concrete logger for intermediate_log as we need it to be a PlaceHolder
            cls.intermediate_log_name = "middle_log"
            cls.intermediate_log_fullname = "{}.{}".format(cls.base_log_name, cls.intermediate_log_name)
            cls.child_log_name = cls.intermediate_log_name + ".child_log"
            cls.child_log_fullname = "{}.{}".format(cls.base_log_name, cls.child_log_name)
            cls.child_log = cls.base_log.getChild(cls.child_log_name)
            cls.child_log.level = logging.NOTSET
        finally:
            # Revert back to original logger class
            logging.setLoggerClass(old_logger_class)

    def setUp(self):
        self.logging_spy.start()
        self.mem_provider = InMemoryLogLevelProvider()

        self.local_logging_manager = LoggingLevelManager()
        self.local_logging_manager.add_providers(self.mem_provider)

        self.mock_get_logging_level_manager = patch.object(dynamic_logger, "_get_logging_level_manager",
                                                           return_value=self.local_logging_manager)
        LOG.debug("Begin patch of '_get_logging_level_manager'")
        self.mock_get_logging_level_manager.start()

    def tearDown(self):
        self.logging_spy.stop()
        self.mock_get_logging_level_manager.stop()
        LOG.debug("End patch of '_get_logging_level_manager'")

    def test_parent_level_override(self):
        """Validates that changes to the log level overrides of a parent logger is properly reflected in the
        DynamicLogger
        """
        # Validate preconditions that the log level is such that debug does nothing
        self._do_test_log(expect_base=False, expect_child=False)

        # Override and validate that debug now works
        self.mem_provider.apply_overrides({self.base_log_name: logging.DEBUG})
        self._do_test_log(expect_base=True, expect_child=True)

    def test_place_holder_override(self):
        """Validates that changes to the log level overrides of a parent logger which has not actually ever been created
        as a logger(aka a PlaceHolder) is properly reflected in the child DynamicLogger
        """
        # Validate preconditions that the log level is such that debug does nothing
        self._do_test_log(expect_base=False, expect_child=False)

        # Override and validate that debug now works
        self.mem_provider.apply_overrides({self.intermediate_log_fullname: logging.DEBUG})
        self._do_test_log(expect_base=False, expect_child=True)

    def test_explicit_logger_level_override(self):
        """Validates that changes to the log level overrides of an explicit logger is properly reflected in the
        DynamicLogger
        """
        # Validate preconditions that the log level is such that debug does nothing
        self._do_test_log(expect_base=False, expect_child=False)

        # Override and validate that debug now works
        self.mem_provider.apply_overrides({self.child_log_fullname: logging.DEBUG})
        self._do_test_log(expect_base=False, expect_child=True)

    def test_child_level_isolation(self):
        """Validates that the overridden log level of a parent logger has no affect on an overridden level of a child
        logger
        """
        # Validate preconditions that the log level is such that debug does nothing
        self._do_test_log(expect_base=False, expect_child=False)

        # Override and validate that debug now works still for the child logger
        self.mem_provider.apply_overrides(
            {
                self.child_log_fullname: logging.DEBUG,
                self.base_log_name: logging.ERROR
            }
        )
        self._do_test_log(expect_base=False, expect_child=True)

    def _do_test_log(self, expect_base, expect_child):
        """Test helper which performs debug logs against base and child loggers and asserts the stated expected behavior

        :param expect_base: Whether or not we should expect the log from the base logger to work
        :param expect_child: Whether or not we should expect the log from the child logger to work
        """
        self.child_log.debug("Test")
        self.base_log.debug("BaseTest")

        expected_count = 0

        if expect_child:
            self.logging_spy.assert_log("^Test$")
            expected_count += 1

        if expect_base:
            self.logging_spy.assert_log("^BaseTest$")
            expected_count += 1

        self.assertEqual(len(self.logging_spy.log_records), expected_count)
