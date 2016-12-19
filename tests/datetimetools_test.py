""" Tests for datetimetools module.
"""
# stdlib
import logging
from datetime import datetime
from datetime import timedelta
from unittest import TestCase

from freezegun import freeze_time
from pytz import timezone

from generic_utils.datetimetools import EPOCH
from generic_utils.datetimetools import datetime_from_milliseconds
from generic_utils.datetimetools import get_timezone_offset_string
from generic_utils.datetimetools import milliseconds_since_epoch
from generic_utils.datetimetools import timezone_supports_dst

LOG = logging.getLogger(__name__)


pacific = timezone("US/Pacific")
US_EASTERN = timezone("US/Eastern")
AUSTRALIA_SYDNEY = timezone("Australia/Sydney")


class MillisecondsConversionTestCase(TestCase):
    """
    Test Case for conversions to and from milliseconds.
    """
    def setUp(self):
        self.one_hour_in_ms = 60 * 60 * 1000

    def test_milliseconds_since_epoch(self):
        """
        Test the milliseconds_since_epoch to ensure we can get from milliseconds utc since epoch TO a datetime object.
        :return:
        """
        test_cases = [
            (EPOCH, 0),
            (EPOCH + timedelta(days=1), 86400000),
            (EPOCH + timedelta(weeks=1), 604800000),
            (pacific.localize(datetime(1970, 1, 1)),   # confirm timezone conversion.
             self.one_hour_in_ms * 8),
        ]
        for convert_from, expected_milliseconds in test_cases:
            self.assertEqual(milliseconds_since_epoch(convert_from), expected_milliseconds)

        with self.assertRaises(ValueError):
            # no timezone information.
            milliseconds_since_epoch(datetime(1970, 1, 1))

    def test_datetime_from_milliseconds(self):
        """
        Test the datetime_from_milliseconds_utc method to ensure we can get to milliseconds utc since epoch FROM a
        datetime object.
        :return:
        """
        test_cases = [
            (0, EPOCH),
            (86400000, EPOCH + timedelta(days=1)),
            (604800000, EPOCH + timedelta(weeks=1)),
        ]
        for convert_from, expected_datetime in test_cases:
            self.assertEqual(datetime_from_milliseconds(convert_from), expected_datetime)


class TimezoneOffsetUseCases(TestCase):

    def test_get_timezone_offset_string(self):
        """
        Validate the expected offset is returned.
        :return:
        """
        test_cases = [
            ("+1000", AUSTRALIA_SYDNEY, datetime(2015, 8, 1)),
            ("+1100", AUSTRALIA_SYDNEY, datetime(2015, 1, 1)),
            ("-0400", US_EASTERN, datetime(2015, 8, 1)),
            ("-0500", US_EASTERN, datetime(2015, 1, 1)),
        ]

        for expected_offset, tz, frozen_now in test_cases:
            with freeze_time(frozen_now):
                offset = get_timezone_offset_string(tz)
                self.assertEqual(expected_offset, offset,
                                 "Offset is different from expected.  %s != %s" % (offset, expected_offset))

    def test_supports_dst(self):
        """
        Validate supports_dst method.

        Australia: Daylight Saving Time begins at 2am on the first Sunday in October, when clocks are put forward one
        hour.

        Chicago: Leaves DST Sunday, November 1, 2015

        There is a gap when Australia and Chicago are both on DST.  Oct 15th will be chosen for this test.
        :return:
        """
        with freeze_time(datetime(year=2015, month=10, day=31)):
            timezones_tests = [
                (timezone("Australia/Sydney"), (True, True)),
                (timezone("America/Chicago"), (True, True)),
                (timezone("Europe/Paris"), (True, False)),
                (timezone("America/Grenada"), (False, False))
            ]

            for tz, expected_result in timezones_tests:
                self.assertEqual(timezone_supports_dst(tz), expected_result)

        with freeze_time(datetime(year=2015, month=11, day=1, hour=12)):
            self.assertEqual(timezone_supports_dst(timezone("America/Chicago")),
                             (True, False))
        with freeze_time(datetime(year=2015, month=10, day=25)):
            self.assertEqual(timezone_supports_dst(timezone("Europe/Paris")),
                             (True, True))
