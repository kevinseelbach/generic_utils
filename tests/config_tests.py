# stdlib
import logging
import os
from contextlib import contextmanager
from unittest import TestCase

from generic_utils.config import get_config_value
from generic_utils.ostools import environment_var

log = logging.getLogger(__name__)


class GetConfigValueTestCase(TestCase):
    def test_type_casting_based_on_default(self):
        """Verifies that the return value of get_config_value is casted correctly based on the default value
        """
        PROP = "test_prop"
        with environment_var(PROP, "12"):
            val = get_config_value(PROP, default=10)

            self.assertTrue(isinstance(val, int))
            self.assertEquals(val, 12)

    def test_explicit_type_casting(self):
        """Verifies that the return value of `get_config_value` is casted correctly based on explicitly provided types
        """
        PROP = "test_prop"
        candidates = [
            ("12", [dict, int], 12),
            ("{\"bleh\": 10}", [int, dict], {"bleh": 10}),
            ("[10, 20, 30]", [int, dict, list], [10, 20, 30]),
            ("(10, 20, \"test\")", [int, dict, tuple, list], (10, 20, "test")),
        ]

        for candidate in candidates:
            log.debug("Testing candidate %s", candidate)
            with environment_var(PROP, candidate[0]):
                val = get_config_value(PROP, val_type=candidate[1])

                self.assertTrue(isinstance(val, type(candidate[2])))
                self.assertEquals(val, candidate[2])

    def test_default(self):
        """Validates default behavior of `get_config_value`"""
        default_val = "DEFAULT VALUE"
        self.assertEquals(get_config_value("BOGUS_DOES_NOT_EXIST", default=default_val), default_val)

    def test_no_type_info(self):
        """Validates that the value of `get_config_value` returns a string when no type value is provided"""
        PROP = "test_prop"
        VAL = "12"
        with environment_var(PROP, VAL):
            self.assertEquals(get_config_value(PROP), VAL)
