from __future__ import absolute_import

from unittest import TestCase
from generic_utils import loggingtools
from generic_utils.exceptions import GenUtilsException, GenUtilsValueError, IllegalArgumentException

log = loggingtools.getLogger()


class MyCustomException(GenUtilsException):
    color = None
    message = "The color is {color}"


class MyCustomSubclassException(MyCustomException):
    shape = None
    message = "The color is {color} and the shape is {shape}"

    _some_private_prop = None

    def some_method(self):
        pass


class MyCustomExceptionWithNoMessage(GenUtilsException):
    pass


class ExceptionTest(TestCase):
    def test_generic_exception(self):
        """Validate we can raise a GenUtilsException with our own message
        """
        MESSAGE = "test message"
        dynamic_exception = GenUtilsException(MESSAGE)

        self.assertEqual(dynamic_exception.message, MESSAGE)

    def test_exception_with_kwarg(self):
        EXPECTED_MESSAGE = "The color is Blue"
        my_exception = MyCustomException(color="Blue")

        self.assertEqual(my_exception.color, "Blue")
        self.assertEqual(my_exception.message, EXPECTED_MESSAGE)

    def test_exception_with_no_kwarg(self):
        EXPECTED_MESSAGE = "The color is None"
        my_exception = MyCustomException()

        self.assertIsNone(my_exception.color)
        self.assertEqual(my_exception.message, EXPECTED_MESSAGE)

    def test_custom_message_no_kwargs(self):
        """Validates that we can provide a custom message for an exception instance
        """
        my_exception = MyCustomException("My custom message")

        self.assertEqual(my_exception.message, "My custom message")
        self.assertIsNone(my_exception.color)

        # Try as a kwarg
        my_exception2 = MyCustomException(message="My custom message")

        self.assertEqual(my_exception2.message, "My custom message")
        self.assertIsNone(my_exception2.color)

    def test_custom_message_with_kwargs(self):
        """Validates that we can provide a custom message for an exception instance with kwargs provided
        """
        my_exception = MyCustomException("My custom message - color = {color}", color="Red")

        self.assertEqual(my_exception.message, "My custom message - color = Red")
        self.assertEqual(my_exception.color, "Red")

    def test_custom_value_error(self):

        value_error = GenUtilsValueError(value_name="test")

        self.assertEqual(value_error.value_name, "test")
        self.assertIsInstance(value_error, ValueError)

    def test_fail_on_invalid_kwarg(self):
        """Validates that if we attempt to provide an invalid kwarg to an exception that it raises an exception
        """
        TEST_CASES = [
            ("no_attr",),
            ("__init__",),
            ("_some_private_prop",),
            ("some_method",)
        ]

        for kwarg_name, in TEST_CASES:
            log.debug("Testing kwarg '%s'", kwarg_name)
            kwargs = {
                kwarg_name: "Some Test Value"
            }

            with self.assertRaises(IllegalArgumentException):
                MyCustomSubclassException(**kwargs)

    def test_exception_no_message(self):
        """Validate that if no message provided to exception then error is not thrown
        :return:
        """
        obj = MyCustomExceptionWithNoMessage()
        self.assertIsNone(obj.message)
