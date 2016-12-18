"""Utilities for writing tests
"""
import threading

import unittest
import new
from unittest.case import expectedFailure
import types
from generic_utils import loggingtools

try:
    from ddt import ddt, mk_test_name, add_test, data as ddt_data, UNPACK_ATTR, DATA_ATTR, FILE_ATTR, process_file_data
except ImportError:
    # pylint: disable=invalid-name
    ddt = None
    ddt_data = None
    DATA_ATTR = None

    def ddt_data(*_):
        """
        Dummy ddt data decorator
        """
        raise RuntimeError("In order to use the data decorator you must install python-utils with the "
                           "'test_utils' extras package; eg python-utils['test_utils']")

from nose.plugins import attrib
from nose.tools import nottest

JIRA_ATTR_NAME = "jira"

LOG = loggingtools.getLogger()


__all__ = ["jira", "TestCase", "test_generator", "data", "bad_data"]

data = ddt_data  # pylint: disable=invalid-name


def jira(*args, **kwargs):
    """Decorator to use for linking a jira ticket against a test.  This is just a wrapper around the Nose Attr
    decorator which creates a "jira" attribute on the method which is a list of all of the provided jira tickets

    Positional Arguments:
        A variable list of strings which are the id's of the jira tickets

    Arguments:
        'resolved' - If the issue is resolved.  If this is set to True(default) then the test is run with no added
                     behavior from this decorator.  If it is set to False then that indicates that the issue is not yet
                        fixed and therefore it is expected that the test decorated with this decorator is supposed to
                        fail.  In this case if the test fails then this decorator treats it as a success case, otherwise
                        an assertion is thrown.
        'skip'     - Whether or not to skip execution of the test if the issue is not resolved.  This value only matters
                        if the `resolved` parameter is True.  This flag is used primarily if the negative effects of
                        the Jira are detrimental such as a infinite recursion.  This is just a convenience around the
                        unittest @skip decorator, but is more explicit and self documenting in that you are tying the
                        skip behavior to a Jira

    Examples:

    @jira("STIK-101", "STIK-102")
    def my_test():
        pass

    # This test will pass because resolved is False even though the test body fails
    @jira("STIK-101", "STIK-102", resolved=False)
    def my_test():
        self.fail("Issue not resolved yet")

    # This test will be skipped because resolved is False and skip is True
    @jira("STIK-101", "STIK-102", resolved=False, skip=True)
    def my_test():
        pass
    """
    def wrap(func):
        """Function wrapper
        """
        resolved = kwargs.pop('resolved', True)
        skip_val = kwargs.pop('skip', False)
        attrs = {
            JIRA_ATTR_NAME: args
        }

        if not resolved:
            if skip_val:
                func = unittest.skip("Jira(s) %s are not resolved yet" % str(args))(func)
            else:
                # Currently nose does not support expected failures, but we use it anyway in hopes PYUTILS-2 will be
                # fixed
                func = unittest.expectedFailure(func)

        attr_wrapped = attrib.attr(**attrs)
        return attr_wrapped(func)

    return wrap

_TEST_GENERATOR_PARAMS_ATTR = "_TEST_GENERATOR_PARAMS_ATTR"
_BAD_DATA_ATTR = "_BAD_DATA_ATTR"

class TestCaseMixinMetaClass(type):
    """Meta class for the base TestCase which provides core hooks and test case modifications which are beneficial
    for all test cases.

    Specifically this meta class enables the following:

      1> Automatic hook into the core setUp and tearDown methods which guarantee a call to _custom_setup and
        _custom_teardown independent of what the final TestCase class does which enables utility code to have
        guarantees about setup and teardown lifecycle.
    """

    _core_test_methods_overridden = False
    _thread_locals = threading.local()

    def __init__(cls, name, bases, dct):
        cls._expand_generators()

        super(TestCaseMixinMetaClass, cls).__init__(name, bases, dct)

    def __call__(cls, *args, **kwargs):
        if not getattr(cls, "_core_test_methods_overridden", False) and \
                (not hasattr(cls, "_enable_test_method_override") or cls._enable_test_method_override()):
            current_setup = cls.setUp
            current_teardown = cls.tearDown

            def cb_wrapped_setUp(self, *args, **kwargs):  # pylint: disable=invalid-name
                """Wrapper which wraps the core setUp and calls the _custom_setup
                """
                cls._thread_locals.__setattr__("current_test", self)
                try:
                    self._custom_setup()
                except AttributeError:
                    pass
                current_setup(self)

            def cb_wrapped_tearDown(self):  # pylint: disable=invalid-name
                """Wrapper which wraps the core tearDown and calls the _custom_teardown
                """
                try:
                    self._custom_teardown()
                except AttributeError:
                    pass
                current_teardown(self)
                cls._thread_locals.__delattr__("current_test")

            # pylint: disable=attribute-defined-outside-init, invalid-name
            cls.setUp = new.instancemethod(cb_wrapped_setUp, None, cls)
            cls.tearDown = new.instancemethod(cb_wrapped_tearDown, None, cls)

            cls._core_test_methods_overridden = True

        return super(TestCaseMixinMetaClass, cls).__call__(*args, **kwargs)

    def _expand_generators(cls):
        """Discovers all test generator attributes on tests within this test case and expands them out as test
        generators
        """
        if ddt is None:
            LOG.warn("Python-utils test dependency 'ddt' is not available in the python path which means that "
                     "data driven test capabilities as well as test generator capabilities on TestCase's will "
                     "not be available.  When using the python-utils TestCase it is recommended to add the "
                     "dependency \"python-utils['test_utils']\" to your projects dependencies.")
            return

        for name, func in list(cls.__dict__.items()):
            if not isinstance(func, types.FunctionType):
                continue
            remove_test = False
            if hasattr(func, _TEST_GENERATOR_PARAMS_ATTR):
                generator_params = getattr(func, _TEST_GENERATOR_PARAMS_ATTR)
                cls._expand_test_generator(name, func, generator_params)
                remove_test = True
            if hasattr(func, _BAD_DATA_ATTR):
                bd_arg_list = getattr(func, _BAD_DATA_ATTR)
                cls._expand_bad_data_tests(name, func, bd_arg_list)
                remove_test = True

            # Process DDT decorators so we do it all in one loop
            if hasattr(func, DATA_ATTR):
                for i, value in enumerate(getattr(func, DATA_ATTR)):
                    test_name = mk_test_name(name, getattr(value, "__name__", value), i)
                    if hasattr(func, UNPACK_ATTR):
                        if isinstance(value, tuple) or isinstance(value, list):
                            add_test(cls, test_name, func, *value)
                        else:
                            # unpack dictionary
                            add_test(cls, test_name, func, **value)
                    else:
                        add_test(cls, test_name, func, value)
                remove_test = True
            if hasattr(func, FILE_ATTR):
                file_attr = getattr(func, FILE_ATTR)
                process_file_data(cls, name, func, file_attr)
                remove_test = True

            # End DDT Decorators

            if remove_test:
                delattr(cls, name)

    def _expand_bad_data_tests(cls, name, member, bd_arg_list):
        """Processes bad_data test generator information to generate new tests
        """
        exp_failure_method = expectedFailure(member)
        idx = 0
        for bd_args, bd_kwargs in bd_arg_list:
            unpack = bd_kwargs.get("unpack", False) or hasattr(member, UNPACK_ATTR)

            for val in bd_args:
                test_name = mk_test_name(name, getattr(val, "__name__", val), idx)
                idx += 1
                if unpack:
                    if isinstance(val, tuple) or isinstance(val, list):
                        add_test(cls, test_name, exp_failure_method, *val)
                    else:
                        # unpack dictionary
                        add_test(cls, test_name, exp_failure_method, **val)
                else:
                    add_test(cls, test_name, exp_failure_method, val)

    def _expand_test_generator(cls, name, member, test_gen_params):
        """Processes test_generator test generator information to generate new tests from a decorated original test
        method
        """
        generator_params = getattr(member, _TEST_GENERATOR_PARAMS_ATTR)
        if "func" in test_gen_params:
            for i, test_func in enumerate(generator_params["func"](member)):
                try:
                    # Generators can optionally return the function name as the second item of a tuple, otherwise
                    # it is just the function
                    test_func, suffix_data = test_func
                except TypeError:
                    # This just needs to be something that is not "trivial" so that it is ignored in the name
                    # generation within mk_test_name
                    suffix_data = cls

                test_name = mk_test_name(name, suffix_data, i)
                add_test(cls, test_name, test_func)


class TestCase(unittest.TestCase):
    """
    Base TestCase class which applies behavior provided by TestCaseMixinMetaClass.
        See docstring of TestCaseMixinMetaClass for more details.
    """
    __metaclass__ = TestCaseMixinMetaClass

    def _custom_setup(self):  # pylint: disable=invalid-name
        """Setup method that should be overridden by utility TestCase subclasses instead of the core test setUp method.
        This is really no different then the core setUp method except that in general a test writer does not ever
        think to call super() when overriding setUp so it is a very redundant task that is often forgotten and with
        so many tests being written this because a problem.  Whereas core base TestCases can be expected to conform
        to the API and call the super method of _custom_setup so it is a much more reliable and safe way to provide base
        setUp behaviors.
        """
        pass

    def _custom_teardown(self):  # pylint: disable=invalid-name
        """TearDown method that should be overridden by utility TestCase subclasses instead of the core test tearDown
        method.  This is really no different then the core setUp method except that in general a test writer does not
        ever think to call super() when overriding setUp so it is a very redundant task that is often forgotten and
        with so many tests being written this because a problem.  Whereas core base TestCases can be expected to conform
        to the API and call the super method of _custom_teardown so it is a much more reliable and safe way to provide base
        tearDown behaviors.
        """
        pass

    @classmethod
    @nottest
    def get_current_test_case(cls):
        """Helper method for returning the current TestCase that is running, if a test case is currently the driver
        for the current thread of execution.

        :return: The current test case that is running within the current thread, or None if a TestCase is not currently
            running.
        :rtype: TestCase
        """
        try:
            return cls._thread_locals.__getattribute__("current_test")  # pylint: disable=no-member
        except AttributeError:
            return None


def test_generator(generator_func=None):
    """Decorator which can be applied to test methods of a TestCase which will leverage the single test method and the
    provided configuration of this decorator in order to generate test methods either through data

    :param generator_func: The function which given the test method as the sole parameter will generate new test methods
    :type generator_func: func
    :return: A decorator capable of decorating a test method for the purpose of generating new tests from the original
        test method.
    :rtype: func
    """
    def test_decorator(test_func):
        """Internal function decorator method
        """
        generator_params = {
            "func": generator_func
        }
        setattr(test_func, _TEST_GENERATOR_PARAMS_ATTR, generator_params)
        return test_func
    return test_decorator


def bad_data(*values, **kwargs):
    """Decorator which can be applied to a test method to generate new tests from it which are expected to fail due to
    the "bad data" provided.  Each data set is provided to the decorated test which then becomes a test itself and if
    the underlying test raises an AssertionError then the test actually passes whereas if it doesn't then the generated
    test will fail.

    This can be used as below which generates 2 separate tests, one for each data input:

    >>> @bad_data(1, 2)
    >>> def test_bad_data(self, val):
    >>>    self.assertTrue(val > 2)  # This will fail, but generated test will pass as it is expected to be bad data

    or with collections of data

    >>> @bad_data(
    >>>   [1, 2],
    >>>   [2, 3]
    >>> )
    >>> def test_bad_data(self, val):
    >>>    self.assertTrue(isinstance(val, list))  # this is true
    >>>    self.assertTrue(val[0] > 2)  # This will fail, but generated test will pass as it is expected to be bad data

    or with multiple parameters

    >>> @bad_data([1, 2], [2, 3], unpack=True)
    >>> def test_bad_data(self, val1, val2):
    >>>    self.assertTrue(val1 < 3)  # This is true
    >>>    self.assertTrue(val2 < 2)  # This will fail, but generated test will pass as it is expected to be bad data
    """
    def wrapper(func):
        """Internal wrapper function for acting as a decorator which sets the bad data attributes onto the target
        function
        """
        bad_data_list = getattr(func, _BAD_DATA_ATTR, [])
        bad_data_list.append((values, kwargs))
        setattr(func, _BAD_DATA_ATTR, bad_data_list)
        return func
    return wrapper
