"""Utilities for dealing with Context Managers and the like
"""
from __future__ import absolute_import

# stdlib
import functools
import importlib
from functools import update_wrapper

# Import types using import_module because the relative module "types" is shadowing the global types
types = importlib.import_module('types')  # pylint: disable=invalid-name


class ContextDecorator(object):
    """Base class which enables subclasses to act as both a context manager and a decorator.  When acting as a decorator
      subclasses can decorate a function in which case when the function is called it is executed within the context of
      the context manager.  Certain classes can also be decorated which have defined entry and exit points, such as a
      TestCase where on `setUp` the context manager starts and on `tearDown` it exits.  Not all classes can be decorated
      as there is not an obvious entry and exit point for most classes.

    Subclasses need to implement the __enter__() and __exit__() methods
    """
    def __call__(self, func):
        """Decorator handler
        """
        processed_f = self._on_decorate(func) or func

        if isinstance(func, types.FunctionType):
            processed_f = self._decorate_function(processed_f)

        else:  # Assume it is a class
            processed_f = self._decorate_class(processed_f)
        return processed_f

    # pylint: disable=no-self-use
    def _on_decorate(self, obj):
        """Method called when the class is being used as a decorator at the time an object is being decorated.

        This allows subclasses to provide additional functionality as needed when used as a decorator as opposed to
        being used just as a context manager
        """
        return obj

    def _decorate_function(self, func):
        """Decorate `func` so that it is executed within the context of this context manager
        """
        @functools.wraps(func)
        def decorated(*args, **kwds):
            """Decorator wrapper for context manager
            """
            with self._get_decorator_ctx_mgr(args, kwds):
                return func(*args, **kwds)
        return decorated

    def _decorate_class(self, clazz):
        """Decorate a class `clazz`
        """
        if hasattr(clazz, "setUp"):  # TestCase like class
            return self._decorate_tase_case(clazz)

        return clazz

    def _get_decorator_ctx_mgr(self, func_args, func_kwargs):  # pylint: disable=unused-argument
        """Return a context manager for the call to the decorated method when this class is used as a decorator.

        By default this just returns self, but if a subclass wants to intercept the arguments coming into the decorated
        method in order to provide a different behavior based on those arguments then this method should be overridden.

        When overridding this method, it is recommended to be aware of possible thread safety issues and it may be
        best to return a new context manager different from the current instance of this class as it is not expected to
        the caller that using this as a decorator would mutate the state of the decorator on each call which may lead
        to unexpected behavior.

        :param func_args: A list of the positional arguments being provided to the decorated function.  This list will
            be passed to the function so any modifications to this list will be reflected when passed to the decorated
            func.
        :type func_args: list
        :param func_kwargs: Dictionary of the kwargs being provided to the decorated function.  This dict will be
            used as the kwargs to the decorated function so any changes to this argument will be reflected when passed
            to the decorated func.
        :type func_kwargs: dict
        :return: A context manager to execute the decorated function within
        """
        return self

    def _decorate_tase_case(self, test_case_class):
        """Decorate a `TestCase` class so that tests are run within the context of this context manager
        """
        # In order for TestCase decorating to work the current ContextManager must mixin ExplicitContextManagerMixin
        assert isinstance(self, ExplicitContextManagerMixin)
        context_manager = self

        def _get_setup_wrapper(func):
            """Generates a wrapper for the setUp method which "starts" the current context manager
            """
            def wrapped_setup(self, *a, **kw):
                """Actual setUp wrapper
                """
                context_manager.start()  # pylint: disable=no-member
                return func(self, *a, **kw)
            return wrapped_setup

        def _get_teardown_wrapper(func):
            """Actual tearDown wrapper
            """
            def wrapped_teardown(self, *a, **kw):
                """Actual tearDown wrapper
                """
                context_manager.stop()  # pylint: disable=no-member
                return func(self, *a, **kw)
            return wrapped_teardown

        test_case_class.setUp = update_wrapper(_get_setup_wrapper(test_case_class.setUp), test_case_class.setUp)
        test_case_class.tearDown = update_wrapper(
            _get_teardown_wrapper(test_case_class.tearDown),
            test_case_class.tearDown)
        return test_case_class


class ExplicitContextManagerMixin(object):
    """ContextManager mixin which provides explicit `start` and `stop` methods which allow for the context to be applied
    via direct calls instead of having to be within the `with` statement.
    """

    def __enter__(self):
        pass

    def __exit__(self, *exc_info):
        pass

    def start(self):
        """Start the context for this context manager.  This is an explicit call which does the same thing as using the
        context manager within a `with` block but exposes it in a more explicit/discrete way
        """
        return self.__enter__()

    def stop(self):
        """Exit the context for this context manager.  This is an explicit call which does the same thing as a clean
        exit from a `with` block when using the context manager but exposes it in a more explicit/discrete way
        """
        self.__exit__(None, None, None)


class ExplicitContextDecorator(ExplicitContextManagerMixin, ContextDecorator):
    """Helper class which provides both the `ExplicitContextManagerMixin` and the `ContextDecorator` as base classes
    """
