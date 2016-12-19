from generic_utils.test.category_decorators import TEST_CATEGORY_ATTR_NAME
from generic_utils.test.category_decorators import TEST_TYPE_ATTR_NAME
from generic_utils.test.category_decorators import TestCategory
from generic_utils.test.category_decorators import TestType
from generic_utils.test.category_decorators import integration_test
from generic_utils.test.category_decorators import slow_test
from generic_utils.test.category_decorators import system_test
from generic_utils.test.category_decorators import test_category

from .decorators_tests import AttrTestCase


class TestCategoryDecoratorTestCase(AttrTestCase):
    TEST_ATTR = TEST_CATEGORY_ATTR_NAME

    def test_specialized_category(self):
        """Validates that we are able to mark a test via a specific category using a specialized decorator.  In this
        case we are using the slow_test decorator, but in practice it could be any decorator created from the
        `_specialized_category_decorator` method
        """
        @slow_test
        def some_test():
            pass

        @slow_test()
        def some_test_with_args():
            pass

        self.assertEqual(self._get_attr(some_test), (TestCategory.SLOW, ))
        self.assertEqual(self._get_attr(some_test_with_args), (TestCategory.SLOW, ))

    def test_multiple_categories(self):
        """Validates that we can mark a test with multiple categories
        """
        CUSTOM_CATEGORY = "custom"

        @slow_test
        @test_category(CUSTOM_CATEGORY)
        def some_test():
            pass

        self.assertEqual(self._get_attr(some_test), (TestCategory.SLOW, CUSTOM_CATEGORY))


class TestTypeDecoratorTestCase(AttrTestCase):
    TEST_ATTR = TEST_TYPE_ATTR_NAME

    def test_specialized_type(self):
        """Validates that we are able to mark a test via a specific category using a specialized decorator.  In this
        case we are using the slow_test decorator, but in practice it could be any decorator created from the
        `_specialized_category_decorator` method
        """
        @integration_test
        def some_test():
            pass

        @integration_test()
        def some_test_with_args():
            pass

        self.assertEqual(self._get_attr(some_test), (TestType.INTEGRATION, ))
        self.assertEqual(self._get_attr(some_test_with_args), (TestType.INTEGRATION, ))

    def test_multiple_types(self):
        """Validates that if we mark a test with multiple types, only the last one wins
        """
        @integration_test
        @system_test
        def some_test():
            pass

        self.assertEqual(self._get_attr(some_test), (TestType.SYSTEM, ))
