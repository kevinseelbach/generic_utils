import logging
from unittest import TestCase
from generic_utils.base_utils import ImmutableMixin, ImmutableDelay, ImmutableObjectException


log = logging.getLogger(__name__)


class MyImmutableClass(ImmutableMixin):
    some_prop = None

    def __init__(self):
        self.some_prop = "Default Value"
        super(MyImmutableClass, self).__init__()


class ImmutableTest(TestCase):

    def test_immutability(self):
        """
        Verifies that immutability works and a class that subclasses ImmutableMixin is actually immutable
        """
        instance = MyImmutableClass()
        with self.assertRaises(TypeError):
            instance.some_prop = "New Value"

    def test_delayed_immutability(self):
        """Verifies that we can use the `ImmutableDelay` context manager to delay immutability of an Immtuable object
        """
        NEW_VALUE = "New Value"
        with ImmutableDelay():
            instance = MyImmutableClass()
            old_value = instance.some_prop
            self.assertNotEqual(old_value, NEW_VALUE)
            instance.some_prop = NEW_VALUE

        self.assertEqual(instance.some_prop, NEW_VALUE)
        with self.assertRaises(ImmutableObjectException):
            instance.some_prop = NEW_VALUE + "even newer"
