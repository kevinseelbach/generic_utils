"""Tests for
"""
# stdlib
from unittest import TestCase

from generic_utils.dict_utils import lower_keys


class DictUtilsTestCase(TestCase):
    def test_lower_keys(self):
        input_dict = {
            "TestKey": [{
                "NestedTestKey": 1
            }],
            "TestKeyTwo": {"NestedTestKeyTwo": 2}
        }
        EXPECTED_NON_RECURSIVE = {
            "testkey": [{
                "NestedTestKey": 1
            }],
            "testkeytwo": {"NestedTestKeyTwo": 2}
        }
        EXPECTED_RECURSIVE = {
            "testkey": [{
                "nestedtestkey": 1
            }],
            "testkeytwo": {"nestedtestkeytwo": 2}
        }
        self.assertEqual(lower_keys(input_dict, True), EXPECTED_RECURSIVE)
        self.assertEqual(lower_keys(input_dict), EXPECTED_NON_RECURSIVE)
