"""Tests for exceptions utils"""
# stdlib
from unittest import TestCase

from generic_utils import loggingtools
from generic_utils.exceptions import GenUtilsTypeError
from generic_utils.exceptions import GenUtilsValueError
from generic_utils.exceptions.utils import suppress_safe_exceptions

LOG = loggingtools.getLogger()



class SuppressSafeExceptionsTestCase(TestCase):
    """Validate behavior of SuppressSafeExceptions decorator / context manager"""

    def test_basic(self):
        suppressed_defaults = [
            ArithmeticError(), AttributeError(), LookupError(), TypeError(), ValueError()
        ]
        should_raise = [
            BufferError(), EnvironmentError(), EOFError(), ImportError(), MemoryError(), NameError(), ReferenceError(),
            RuntimeError(), SyntaxError()
        ]
        for exc in suppressed_defaults:
            self._suppress_as_context_mgr(exc)
            self._suppress_as_decorator(exc)

        for exc in should_raise:
            with self.assertRaises(exc.__class__):
                self._suppress_as_context_mgr(exc)
            with self.assertRaises(exc.__class__):
                self._suppress_as_decorator(exc)

    def test_suppress_configured_types(self):
        """Validate types listed in config SAFE_EXCEPTION_CLASSES are suppressed"""
        safe_exception = GenUtilsValueError("Blah")
        self._suppress_as_context_mgr(safe_exception)
        self._suppress_as_decorator(safe_exception)

        bad_exception = MemoryError()
        # Validate a type that is not in the SAFE_EXCEPTION_CLASSES or defaults raises
        with self.assertRaises(MemoryError):
            self._suppress_as_context_mgr(bad_exception)
        with self.assertRaises(MemoryError):
            self._suppress_as_decorator(bad_exception)

    def test_explicit_only(self):
        """Validate when called with explicit only defaults are ignored"""
        suppressed = GenUtilsTypeError("Test", "Test")
        raises = ValueError()

        # Validate decorator suppresses GenUtilsTypeError
        self._suppress_explicit(suppressed)
        # Validate that ValueError is raises for contextmgr or decorator
        with self.assertRaises(ValueError):
            self._suppress_explicit(raises)
        with self.assertRaises(ValueError):
            with suppress_safe_exceptions(exception_whitelist=[GenUtilsTypeError], no_defaults=True):
                raise raises
        #     Should pass
        with suppress_safe_exceptions(exception_whitelist=[GenUtilsTypeError], no_defaults=True):
            raise suppressed

    @staticmethod
    def _suppress_as_context_mgr(exc):
        """
        :param exc:
        :type exc: Exception
        :return:
        :rtype:
        """
        with suppress_safe_exceptions():
            raise exc

    @staticmethod
    @suppress_safe_exceptions(exception_whitelist=[GenUtilsTypeError], no_defaults=True)
    def _suppress_explicit(exc):
        """For testing only"""
        raise exc

    @staticmethod
    @suppress_safe_exceptions()
    def _suppress_as_decorator(exc):
        """For Testing only"""
        raise exc
