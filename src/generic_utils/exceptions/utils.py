"""Utilities for working with Exceptions"""
# future/compat
from builtins import next

# stdlib
from generic_utils import loggingtools
from generic_utils.classtools import cached_property
from generic_utils.classtools import get_class_from_fqn
from generic_utils.config import config
from generic_utils.contextlib_ex import ExplicitContextDecorator

LOG = loggingtools.getLogger()

_SAFE_EXCEPTION_TYPES = None


def _get_configured_exceptions():
    """Set the _CONFIGURED_EXCEPTIONS cache
    :return:
    :rtype:
    """
    global _SAFE_EXCEPTION_TYPES  # pylint: disable=global-statement
    if _SAFE_EXCEPTION_TYPES is None:
        exception_classes = set()
        configured_exceptions = config.get_conf_value('SAFE_EXCEPTION_CLASSES', default_value=set(),
                                                      value_type_func=set)
        for val in configured_exceptions:
            if isinstance(val, str):
                # Try to get class from FQN
                exception_classes.add(get_class_from_fqn(val))
            elif isinstance(val, type) and issubclass(val, BaseException):
                exception_classes.add(val)
            else:
                raise TypeError(
                    "Received value of unexpected type_name=%s in configuration property=SAFE_EXCEPTION_CLASSES",
                    type(val))
        _SAFE_EXCEPTION_TYPES = exception_classes
    return _SAFE_EXCEPTION_TYPES


class SuppressSafeExceptions(ExplicitContextDecorator):
    """
    A context-manager / decorator that allows suppressing exceptions from a configurable whitelist
    """
    _DEFAULT_SAFE_EXCEPTIONS = frozenset([ArithmeticError, AttributeError, LookupError, TypeError, ValueError])

    def __init__(self, on_suppression_handler=None, exception_whitelist=None, no_defaults=False):
        """

        :param on_suppression_handler: Callable which should accept one parameter, the exception instance, which will be
         called if a "safe" exception is hit
        :type on_suppression_handler: func
        :param exception_whitelist: An iterable of exception classes to suppress
        :type exception_whitelist: None | [Exception]
        :param no_defaults: Whether to use include any configured defaults in the whitelist. By default, it looks to the
         defined _DEFAULT_SAFE_EXCEPTIONS and any configured application-level safe exceptions
        :type no_defaults: bool
        """
        self.on_suppression_handler = on_suppression_handler
        self._exception_whitelist = exception_whitelist
        self._no_defaults = no_defaults

    def __enter__(self):
        """Enter the context manager."""
        LOG.debug("Entering suppress_safe_exceptions block - safe exception types are %r.",
                  self._safe_exception_types)

    def __exit__(self, exc_type, exc_value, traceback):  # pylint: disable=arguments-differ
        """Exit context manager."""
        if exc_type and self.is_safe_exception(exc_type):
            LOG.debug("Suppressing safe exception of type=%s", exc_type)
            if callable(self.on_suppression_handler):
                LOG.debug('Calling on_suppression_handler=%r for exc_value=%r', self.on_suppression_handler, exc_value)
                self.on_suppression_handler(exc_value)
            return True
        LOG.debug("Exiting suppress_safe_exceptions block exc_type=%r exc_value=%r.", exc_type, exc_value)

    @cached_property
    def _safe_exception_types(self):
        """
        :return:
        :rtype: set
        """
        if self._no_defaults is False:
            safe_types = self._DEFAULT_SAFE_EXCEPTIONS | _get_configured_exceptions()
        else:
            safe_types = set()
        if self._exception_whitelist is not None:
            safe_types |= set(self._exception_whitelist)
        return safe_types

    def is_safe_exception(self, exc):
        """Returns whether or not an exception `exc` is considered a 'safe' exception which means it is a subclass of
        any of the defined safe exceptions.
        :rtype: bool
        """
        safe_types = self._safe_exception_types
        safe_base_types = (safe_base_type for safe_base_type in safe_types if issubclass(exc, safe_base_type))
        try:
            matched_type = next(safe_base_types)
            return matched_type != None
        except StopIteration:
            return False



suppress_safe_exceptions = SuppressSafeExceptions  # pylint: disable=invalid-name
