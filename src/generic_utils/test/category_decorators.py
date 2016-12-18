"""Module which provides decorators for labeling of tests with categories for the purpose of filtering based on the
assigned category.

The primary usage is through the short hand decorators such as `slow_test` which would be used as the following

>>> @slow_test
>>> def do_some_test():
>>>     pass

or

>>> @slow_test()
>>> def do_some_test():
>>>     pass

These are just wrappers around the `nose.plugins.attrib` decorator which allows for filtering of tests based on
attribute.  In order to run all tests but exclude the "slow" tests you could then run ::

    > bin/test -a category='not slow' -a '!category'

"""
from generic_utils.decorator_tools import decorator
from generic_utils.test.nose_utils import get_attrib_decorated_func, specialize_attr_decorator

TEST_CATEGORY_ATTR_NAME = "category"

TEST_TYPE_ATTR_NAME = "test_type"


class TestCategory(object):
    """Class which contains constants for standardized test category labels
    """
    # A test which is relatively slow.  Currently this is considered to take longer than 500ms, however that definition
    # may change over time
    SLOW = "slow"


class TestType(object):
    """Class which contains constants for standardized test category labels
    """
    # A test which spans more than a unit and relies on the interaction of multiple units within a single application
    # space.
    INTEGRATION = "integration"

    # A test which relies on external systems with which to operate.  Technically any test which relies on the database
    # is a system test, however currently we are a bit lax on that one as well as things like Redis and any sort of
    # data storage
    SYSTEM = "system"

    # A test which tests a single unit and does not rely on integrations with other components or systems.  All tests
    # are assumed to be unit tests by default unless specified otherwise.
    UNIT = "unit"


@decorator
def test_category(func=None, *category_names):
    """Decorator to use for categorizing/labeling a test with an identifier via a standardized mechanism which can be
    filtered against when running tests via Nose.  This is just a wrapper around the Nose Attr
    decorator which creates a "category" attribute on the method which is a list of all of the provided category names.

    This is a generic implementation of the categorization operation.  In general the more specialized categorization
    decorators should be used such as `slow_test`.

    Multiple categories can be applied to a test.

    Positional Arguments:
        A variable list of strings which are the test categories to apply to the test

    Examples ::

    @test_category("cool_test")
    def my_test():
        pass

    """
    return get_attrib_decorated_func(func, TEST_CATEGORY_ATTR_NAME, values=category_names)


@decorator
def test_type(func=None, *category_names):
    """Decorator to use for categorizing a test by its type, such as an Integration test or a system test which can be
    filtered against when running tests via Nose.  This is just a wrapper around the Nose Attr
    decorator which creates a "test_type" attribute on the method which is a list of all of the provided category names.

    This is a generic implementation of the test type annotating operation.  In general the more specialized
    decorators should be used such as `integration_test` and `system_test`.

    Note that all tests are assumed to be a UNIT TEST unless decorated specifically.

    A test can only have a single type and any other types after the first one will be ignored.

    Positional Arguments:
        A variable list of strings which are the test categories to apply to the test

    Examples ::

        @test_type("custom_type")
        def my_test():
            pass

    In general a more appropriate example using the specialized decorators would be ::

        @integration_test
        def my_test():
            pass

    or ::

        @system_test
        def my_test():
            pass

    """
    return get_attrib_decorated_func(func, TEST_TYPE_ATTR_NAME, values=category_names, allow_multiple_values=False)


# pylint: disable=invalid-name

# Short hand decorators for specific categories
slow_test = specialize_attr_decorator(test_category, TestCategory.SLOW)
"""Test Decorator for the `slow` test category"""

integration_test = specialize_attr_decorator(test_type, TestType.INTEGRATION)
"""Test Decorator for the `integration` test category"""

system_test = specialize_attr_decorator(test_type, TestType.SYSTEM)
"""Test Decorator for the `system` test category"""

# pylint: enable=invalid-name
