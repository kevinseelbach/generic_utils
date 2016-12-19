# stdlib
import logging
import types
from unittest import TestCase

from mock import patch

from generic_utils.classtools import get_class_attributes
from generic_utils.classtools import get_class_from_fqn
from generic_utils.classtools import get_classfqn
from generic_utils.classtools import get_from_fqn
from generic_utils.classtools import get_instance_from_fqn

log = logging.getLogger(__name__)


class DummyClass(object):
    """Dummy test class"""
    pass


class FQNameTestCase(TestCase):
    """Validates `get_fq_classname`, `get_class_from_fqn`, `get_instance_from_fqn`
    """
    EXPECTED_PACKAGE = "tests.classtools_test"

    def test_class_based_function(self):
        """Validates the basic behavior of the `get_fq_classname` method when providing a class to it
        """
        self.assertEqual(get_classfqn(DummyClass), self.EXPECTED_PACKAGE + ".DummyClass")

    def test_instance_based_function(self):
        """Validates the basic behavior of the `get_fq_classname` method when providing an instance to it
        """
        self.assertEqual(get_classfqn(DummyClass()), self.EXPECTED_PACKAGE + ".DummyClass")

    def test_get_class_from_fqn(self):
        """Validates that a class is returned from the get_class_from_fqn function.
        """
        class_fqn = get_classfqn(DummyClass)
        self.assertEqual(DummyClass, get_class_from_fqn(class_fqn))

    def test_get_from_fqn(self):
        """Validate get_from_fqn works as expected"""
        TEST_FQN = "os.path.abspath"  # just a stdlib function.
        result = get_from_fqn(TEST_FQN)
        self.assertIsNotNone(result)
        self.assertEqual(type(result), types.FunctionType)

    def test_get_instance_from_fqn(self):
        """Validates that a instance is returned from the get_instance_from_fqn function
        """
        class_fqn = get_classfqn(DummyClass)
        test_unnamed_arg = "test unnamed arg"
        test_named_arg = "test named arg"
        with patch.object(DummyClass, '__init__') as mock_init:
            mock_init.return_value = None
            self.assertIsInstance(get_instance_from_fqn(class_fqn, test_unnamed_arg, named_arg=test_named_arg),
                                  DummyClass)
            mock_init.assert_called_once_with(test_unnamed_arg, named_arg=test_named_arg)

    def test_get_from_fqn_relative(self):
        """Validate that we can get from a relative FQN for a class defined in the same module as caller."""
        test_names = ['DummyClass', '.DummyClass']
        for name in test_names:
            test_class = get_class_from_fqn(name)
            self.assertEqual(test_class, DummyClass, "should be able to get a class from a relative import name.")


class GetClassAttributesTestCase(TestCase):
    """
    Validates `get_class_attributes` utility method
    """

    ### BEGIN TEST CLASSES ###

    class RootClass(object):
        ROOT_1 = "RootClass"
        OVERRIDE_PROP = "RootClass"
        ROOT_CLASS_PROP = "RootClass"

    class RootClass2(object):
        ROOT_2 = "RootClass2"
        ROOT_1 = "RootClass2"

        @property
        def prop(self):
            return "Some prop"

        args = property(lambda self: tuple())

        def some_method(self):
            pass

    class ChildClass(RootClass, RootClass2):
        OVERRIDE_PROP = "ChildClass"

    ### END TEST CLASSES ###

    def test_only_attrs(self):
        """Validates that only attributes are returned from `get_class_attributes`
        """
        class_attrs = get_class_attributes(self.ChildClass)

        self.assertNotIn("args", class_attrs)
        self.assertNotIn("prop", class_attrs)
        self.assertNotIn("some_method", class_attrs)

    def test_expected_attrs(self):
        ChildClass = self.ChildClass

        EXPECTED_ATTRS = {
            "ROOT_1": ChildClass.ROOT_1,
            "ROOT_2": ChildClass.ROOT_2,
            "ROOT_CLASS_PROP": ChildClass.ROOT_CLASS_PROP,
            "OVERRIDE_PROP": ChildClass.OVERRIDE_PROP
        }
        class_attrs = get_class_attributes(ChildClass)

        self.assertDictEqual(class_attrs, EXPECTED_ATTRS)
