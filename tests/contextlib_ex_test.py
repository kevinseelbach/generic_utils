# stdlib
import logging
from unittest import TestCase

from generic_utils.contextlib_ex import ExplicitContextDecorator

log = logging.getLogger(__name__)


context_manager_test_dict = {}  # pylint: disable=invalid-name


class DummyContextManager(ExplicitContextDecorator):
    dict_key = None

    def __enter__(self):
        context_manager_test_dict[self.dict_key] = True

    def __exit__(self, *exc_info):
        del context_manager_test_dict[self.dict_key]


class ClassDummyContextManager(DummyContextManager):
    dict_key = "class"


class FuncDummyContextManager(DummyContextManager):
    dict_key = "func"


@ClassDummyContextManager()
class ContextDecoratorTestCase(TestCase):
    """Validates that context managers which subclass `ContextDecorator` can also be used as decorators
    """

    @FuncDummyContextManager()
    def test_context_manager_decorator_enablement(self):
        """Validates that the target test context managers are active when being used as decorators
        """
        self.assertTrue(context_manager_test_dict["class"])
        self.assertTrue(context_manager_test_dict["func"])

        context_manager_test_dict["context_decorator_testcase_ran"] = True


class DidContextDecoratorTestCaseRun(TestCase):
    """Validates that the ContextDecoratorTestCase actually ran.  The reason for doing this is that if the class
    based ContextDecorator is not working as expected then it can modify the test class such that the test runner
    doesn't properly identify as a test and then doesnt run so we get a silent skip of the test.

    Note that this runs after ContextDecoratorTestCase ONLY because it is named alphabetically after it which enforces
    test execution order, at least by nose standards
    """

    def test_did_it_run(self):
        self.assertTrue(context_manager_test_dict["context_decorator_testcase_ran"])
