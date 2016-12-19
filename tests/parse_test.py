# stdlib
import logging
from unittest import TestCase

from generic_utils.parse import split_by_size
from generic_utils.parse import versiontuple

log = logging.getLogger(__name__)


class TestSplitByIndex(TestCase):

    def test_empty(self):
        v1 = split_by_size('', [1, 5, 3])
        self.assertEquals(v1, ('', '', ''))

        v1 = split_by_size('', [1, 5, 3], return_remainder=True)
        self.assertEquals(v1, ('', '', '', ''))

        v1, v2, v3, v4 = split_by_size('', [1, 5, 3], return_remainder=True)
        self.assertEquals(v1, '')
        self.assertEquals(v2, '')
        self.assertEquals(v3, '')
        self.assertEquals(v4, '')

    def test_too_many_values(self):
        with self.assertRaises(ValueError):
            v1, v2 = split_by_size('', [1, 5, 3])

    def test_basic_usage(self):
        v1, v2, v3 = split_by_size('abcdefghijklmnop', [1, 5, 3])
        self.assertEquals(v1, 'a')
        self.assertEquals(v2, 'bcdef')
        self.assertEquals(v3, 'ghi')

        v1, v2, v3, rem = split_by_size('abcdefghijklmnop', [1, 5, 3], return_remainder=True)
        self.assertEquals(v1, 'a')
        self.assertEquals(v2, 'bcdef')
        self.assertEquals(v3, 'ghi')
        self.assertEquals(rem, 'jklmnop')

    def test_non_iterator(self):
        v1, v2, v3, v4, v5 = split_by_size('abcdefghijklmnop', 3)
        self.assertEquals(v1, 'abc')
        self.assertEquals(v2, 'def')
        self.assertEquals(v3, 'ghi')
        self.assertEquals(v4, 'jkl')
        self.assertEquals(v5, 'mno')

        v1, v2, v3, v4, v5, rem = split_by_size('abcdefghijklmnop', 3, return_remainder=True)
        self.assertEquals(v1, 'abc')
        self.assertEquals(v2, 'def')
        self.assertEquals(v3, 'ghi')
        self.assertEquals(v4, 'jkl')
        self.assertEquals(v5, 'mno')
        self.assertEquals(rem, 'p')


class VersiontupleTestCase(TestCase):
    def test_basic_usage(self):
        version_string = "1.6.2"
        expected_version = (1, 6, 2)

        parsed_version = versiontuple(version_string)
        self.assertEquals(parsed_version, expected_version)

    def test_raises_value_error(self):
        bad_version = "1.6.final.2"
        self.assertRaises(ValueError, versiontuple, bad_version)
