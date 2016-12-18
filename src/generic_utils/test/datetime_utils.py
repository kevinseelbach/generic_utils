"""Test utils for dealing with datetimes

"""
import datetime


class EST(datetime.tzinfo):
    """A tzinfo for the EASTERN timezone.  This is NOT to be used in production and is purely for testing purposes
    for environments where pytz doesn't exist and you need a timezone that is not UTC
    """
    def utcoffset(self, dt):  # pylint: disable=unused-argument
        """The utc offset
        """
        return datetime.timedelta(hours=-5)

    def dst(self, dt):  # pylint: disable=unused-argument
        """
        dst
        """
        return datetime.timedelta(0)
