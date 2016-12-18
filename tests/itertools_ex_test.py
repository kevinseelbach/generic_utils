import logging
import sys
import types
from inspect import getmembers
from unittest import TestCase

from generic_utils.itertools_ex import ibatch, iiterex, reverse_enumerate, index_of, IteratorProxy

log = logging.getLogger(__name__)


def _inner_transform(val):
    """For testing only"""
    log.debug("inner transform to x=%s", val)
    return val + 1


def _outer_transform(x):  # pylint: disable=invalid-name
    """Produces x, x+1 per `x`"""
    log.debug("outer transform to x=%s", x)
    data = [x, x + 1]
    return IteratorProxy(data, item_processor=_inner_transform)


class IteratorProxyTestCase(TestCase):
    """Validate behavior of IteratorProxy class"""

    def test_iterator_basic(self):
        test_data = [1, 2, 3]
        expected = [x + 1 for x in test_data]

        def _add_one(x):  # pylint: disable=invalid-name
            """For testing only"""
            log.debug("Add to x=%s", x)
            return x + 1

        proxy = IteratorProxy(test_data, item_processor=_add_one)
        results = list(proxy)
        self.assertListEqual(results, expected)

    def test_iterator_nested(self):
        """Validate behavior of nested IteratorProxy usage
        """
        # SETUP
        test_data = [1, 10, 20]
        expected = [2, 3, 11, 12, 21, 22]

        proxy = IteratorProxy(test_data, item_processor=_outer_transform)
        results = list(proxy)
        self.assertListEqual(results, expected)


class ReverseEnumerateTestCase(TestCase):
    def test_basic_usage(self):
        my_list = [x for x in reversed(range(10))]
        expected_idx = len(my_list) - 1
        count = 0

        for idx, val in reverse_enumerate(my_list):
            self.assertEqual(expected_idx, idx)
            self.assertEqual(count, val)
            expected_idx -= 1
            count += 1

        self.assertEqual(count, len(my_list))


class TestIIterEx(TestCase):

    def test_callback_true_false(self):
        """ Validates iiterex yields values correctly depending on whether or not the callback returns a True or False.
        :return:
        """
        def callback(obj):
            """
            only iterate over even values.
            :param obj:
            :return:
            """
            return obj % 2 == 0

        new_list = [i for i in range(1, 100)]
        for idx, item in enumerate(iiterex(new_list, callback=callback)):
            self.assertTrue(item % 2 == 0)

    def test_callback_modifyobject(self):
        """
        Validates that you can modify an object pass into the callback function before being yielded.  The object must
        be mutable to begin with of course.
        :return:
        """
        class dummy(object):
            """ Dummy class
            """
            def __init__(self, a, b):
                self.a = a
                self.b = b

        def callback(obj):
            obj.a = 0
            obj.b = 0
            return True

        new_list = [dummy(i, i) for i in range(1, 100)]
        for idx, item in enumerate(iiterex(new_list, callback=callback)):
            self.assertTrue(item.a == 0 and item.b == 0)

    def test_declaritive_callback(self):
        """ Validate that specifying an object attribute specific callback in kwargs is handled similarly to the
         primary callback functionality, only that it allows
        :return:
        """
        class dummy(object):
            """ Dummy class
            """
            def __init__(self, a, b):
                self.a = a
                self.b = b

        def callback_for_a(obj):
            return obj % 5 == 0
        def callback_for_b(obj):
            return obj % 3 == 0

        new_list = [dummy(i, i) for i in range(1, 100)]
        count = 0
        for idx, item in enumerate(iiterex(new_list,
                                           a_callback=callback_for_a,
                                           b_callback=callback_for_b)):
            self.assertEqual(item.a % 5, 0)
            self.assertEqual(item.b % 3, 0)
            count += 1

        self.assertEqual(count, len(new_list) / 15)

    def test_wrapping_object_attr_in_interable(self):
        """ Validates and documents method for wrapping an object's attribute so that it becomes iterable.
        :return:
        """
        class dummychild(object):
            def all(self):
                return [i for i in range(0, 10)]

        class dummy(object):
            """ Dummy class
            """
            def __init__(self, a, b):
                self.a = a
                self.b = b
                self.dummychild = dummychild()

        def make_iterable(self):
            return iter(self.all())

        def dummychild_callback(obj):
            if not hasattr(obj.__class__, '__iter__'):
                obj.__class__.__iter__ = make_iterable
            return True

        new_list = [dummy(i, i) for i in range(1, 2)]
        for idx, item in enumerate(iiterex(new_list, dummychild_callback=dummychild_callback)):
            for idx2, item2 in enumerate(item.dummychild):
                pass


class TestIBatch(TestCase):

    def test_yields_items(self):
        """Validates that ibatch returns expected items when given an iterable
        """
        new_list = [i for i in range(100)]
        x = 0
        for idx, item in enumerate(ibatch(new_list)):
            self.assertEquals(idx, x)
            self.assertEquals(item, x)
            x += 1

        self.assertEquals(x, len(new_list))

    def test_yields_items_chunk_size(self):
        """Validates that ibatch returns expected items when given an iterable
        """
        new_list = [i for i in range(100)]
        x = 0

        for idx, item in enumerate(ibatch(new_list, chunk_size=5)):
            self.assertEquals(x, idx)
            self.assertEquals(x, item)
            x += 1
        self.assertEquals(x, len(new_list))

        x = 0
        for idx, item in enumerate(ibatch(new_list, chunk_size=3)):
            self.assertEquals(x, idx)
            self.assertEquals(x, item)
            x += 1
        self.assertEquals(x, len(new_list))


class IndexOfTestCase(TestCase):
    """Tests for the index_of method
    """
    def test_index_of_first_only_true(self):
        """Validates the behavior of index_of when matching for only the first index within an iterable
        """
        ### SETUP
        TEST_CASES = [
            # (iterable, predicate function, expected_idx)
            ([0, 1, 2, 1], lambda x: x == 1, 1),
            ([{"a": 0}, {"a": 1}, {"a": 2}, {"a": 1}], lambda x: x["a"] == 1, 1),

            # Validate the correct behavior if the predicate matches nothing
            ([0, 1, 2, 1], lambda x: x == 3, None),
            ([{"a": 0}, {"a": 1}, {"a": 2}, {"a": 1}], lambda x: x["a"] == 3, None),

            # Validate it works with a generator as well
            (xrange(3), lambda x: x == 1, 1),
        ]

        self._do_index_of_test_cases(TEST_CASES, True)

    def test_index_of_first_only_false(self):
        """Validates the behavior of index_of when matching for multiple indices within an iterable
        """
        ### SETUP
        TEST_CASES = [
            # (iterable, predicate function, expected_idx)
            ([0, 1, 2, 1], lambda x: x == 1, [1, 3]),
            ([0, 1, 2, 1], lambda x: x == 2, [2]),
            ([{"a": 0}, {"a": 1}, {"a": 2}, {"a": 1}], lambda x: x["a"] == 1, [1, 3]),

            # Validate the correct behavior if the predicate matches nothing
            ([0, 1, 2, 1], lambda x: x == 3, None),
            ([{"a": 0}, {"a": 1}, {"a": 2}, {"a": 1}], lambda x: x["a"] == 3, None),
        ]

        self._do_index_of_test_cases(TEST_CASES, False)

    def _do_index_of_test_cases(self, test_cases, first_only):
        test_case_idx = 0
        for iterable, predicate, expected_idx in test_cases:
            log.debug("Executing test case %d with iterable %s and expected_idx %s",
                      test_case_idx, iterable, expected_idx)
            try:
                idx = index_of(iterable, predicate, first_only=first_only)
                if isinstance(expected_idx, list):
                    self.assertListEqual(idx, expected_idx)
                else:
                    self.assertEqual(idx, expected_idx)
            except ValueError:
                if expected_idx is not None:
                    raise

            test_case_idx += 1

