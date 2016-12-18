from generic_utils import loggingtools
from generic_utils.test.mock.tools import SpyObject
from mock import patch
from unittest import TestCase

explicit_log = loggingtools.getLogger(__name__)
implicit_log = loggingtools.getLogger()
child_log = implicit_log.getChild("child")


class LoggerCreationTestCases(TestCase):
    class_logger = loggingtools.getLogger()

    def test_explicit_log(self):
        """Validates that a logger with an explicit name is created with the correct name
        """
        self.assertEqual(explicit_log.name,
                         "{0}.tests.loggingtools.base_tests".format(loggingtools.BASE_NS_LOG_NAME))

    def test_implicit_module_log(self):
        """Validates that a logger with an implicit name created at the module level is given the correct name
        """
        self.assertEqual(implicit_log.name,
                         "{0}.tests.loggingtools.base_tests".format(loggingtools.BASE_NS_LOG_NAME))

    def test_implicit_class_log(self):
        """Validates that a logger with an implicit name created at the class level is given the correct name
        """
        self.assertEqual(self.class_logger.name,
                         "{0}.tests.loggingtools.base_tests.LoggerCreationTestCases".format(
                             loggingtools.BASE_NS_LOG_NAME))

    def test_child_log(self):
        """
        Validates that creating a child logger from an implicit logger works as expected
        """
        self.assertEqual(child_log.name,
                         "{0}.tests.loggingtools.base_tests.child".format(loggingtools.BASE_NS_LOG_NAME))


class SysLogHandlerTestCases(TestCase):
    log = loggingtools.getLogger()

    def setUp(self):
        self.test_log = loggingtools.getLogger()
        self.syslog_address = ("localhost", 514)

    def tearDown(self):
        del self.test_log

    def test_sysloghandler_format(self):
        """
        Test that the tags specified are correctly added to the outbound syslog message.
        :return:
        """
        test_message_configs = (
            (["blah", "yo"], "my message", "blah-yo: my message", "-"),
            (["blah", "yo"], "my message", "blah~yo: my message", "~"),
            (["blah", "yo"], "my message", "blah-yo: my message", None),
            (["blah"], "my message", "blah: my message", None),
            ([], "my message", "my message", None),
            (None, "my message", "my message", None),
            ([None, "yo"], "my message", "yo: my message", None),
            ([None, "yo", None, "blah", "", "arg"], "my message", "yo-blah-arg: my message", None),
        )
        for tags, msg, expected_msg, tag_delimiter in test_message_configs:
            self._test_log_messages_with_tags(msg, expected_msg, tags, tag_delimiter)

    def _test_log_messages_with_tags(self, msg, expected_msg, tags=None, tag_delimiter=None):
        from socket import socket

        # SETUP
        self.log.debug("setting up handler with %s %s.", tags, tag_delimiter)
        handler = loggingtools.SysLogHandler(self.syslog_address, tags=tags if tags else [],
                                             tag_delimiter=tag_delimiter)

        # pylint: disable=unused-argument
        # method call fails if args and kwargs are not defined in the method sig
        def check_format_return(return_value, *args, **kwargs):
            # VALIDATE
            self.assertEquals(return_value, expected_msg)

        # pylint: enable=unused-argument

        # EXECUTE

        self.test_log.addHandler(handler)

        try:
            # patch all socket send methods so that this test message isn't actually logged.
            # Would patch the .emit() fnc, except that it is responsible for calling the format method we are spying.
            with \
                    SpyObject(handler, "format", cb_post_func=check_format_return) as handler_format_fnc, \
                    patch.object(socket, "send", return_value=None), \
                    patch.object(socket, "send", return_value=None), \
                    patch.object(socket, "send", return_value=None):

                self.test_log.warn(msg)

                # VALIDATE
                self.assertTrue(handler_format_fnc.called,
                                "SysLogHandler format should have been called by the log statement.")
        finally:
            self.test_log.removeHandler(handler)
            self.log.debug("handler removed from test_log.")
