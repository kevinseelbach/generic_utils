import logging
from unittest import TestCase
from generic_utils.typetools import is_iterable

log = logging.getLogger(__name__)


class GeneralTestCase(TestCase):
    def test_is_iterable(self):
        """Validates the behavior of the `is_iterable` method
        """
        iterables = [
            (1, 2),
            [1, 2],
            [x for x in range(2)],
            {"test": 1}
        ]

        non_iterables = [
            "is_a_string",
            1,
            3.2,
            True,
            None
        ]

        for iterable in iterables:
            log.debug("Testing iterable %s", iterable)
            self.assertTrue(is_iterable(iterable))

        for non_iterable in non_iterables:
            log.debug("Testing non_iterable %s", non_iterable)
            self.assertFalse(is_iterable(non_iterable))
