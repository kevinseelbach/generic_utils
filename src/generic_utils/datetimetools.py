"""
Helpful utilities for doing date/time manipulation.
"""
from __future__ import division

# stdlib
from datetime import datetime
from datetime import timedelta
from datetime import tzinfo

from generic_utils import loggingtools

LOG = loggingtools.getLogger()

try:
    import pytz
except ImportError:
    pytz = None


ZERO = timedelta(0)


class UTC(tzinfo):
    """
    UTC implementation taken from Python's docs.

    Used only when pytz isn't available.
    """

    def __repr__(self):
        return "<UTC>"

    def utcoffset(self, dt):
        return ZERO

    def tzname(self, dt):
        return "UTC"

    def dst(self, dt):
        return ZERO


utc = pytz.utc if pytz else UTC()
"""UTC time zone as a tzinfo instance."""


def utcnow():
    """
    :return: a timezone aware UTC datetime representation of `now`
    :rtype: datetime
    """
    # timeit shows that datetime.now(tz=utc) is 24% slower
    return datetime.utcnow().replace(tzinfo=utc)


def now_astimezone(timezone):
    """
    Return now as a function of the timezone passed in.
    :type timezone: pytz.timezone
    :return: a timezone aware datetime in the timezone that is offered.
    :rtype: datetime
    """
    now = utcnow()
    return now.astimezone(timezone)


EPOCH = datetime.fromtimestamp(0, tz=utc)


def milliseconds_since_epoch(datetime_to_convert):
    """
    Return the number of milliseconds since epoch for a given datetime.
    :param datetime_to_convert: Datetime that you want to get milliseconds from epoch for.  If it is naive,
    then a ValueError will be raised.
    :type datetime_to_convert: datetime
    :return: Number of milliseconds since epoch for a given datetime
    :rtype: long
    :raises: ValueError
    """
    if datetime_to_convert.tzinfo is None:
        raise ValueError("datetime_to_convert is naive, aware datetime is required.")
    return (datetime_to_convert - EPOCH).total_seconds() * 1000


def datetime_from_milliseconds(ms_since_epoch):
    """
    Return a datetime object in utc that is a conversion from the ms value passed in.
    :param ms_since_epoch: Time since epoch represented by milliseconds.
    :type ms_since_epoch: float or long
    :return: datetime object conversion of the ms input.
    :rtype: datetime
    """
    return utc.localize(datetime.utcfromtimestamp(ms_since_epoch / 1000))


def get_timezone_offset_string(timezone):
    """
    Returns the UTC offset for a given pytz timezone.
    :type timezone: pytz.timezone
    :return: Offset value.
    :rtype: basestring
    """
    now = now_astimezone(timezone)
    return now.strftime('%z')


def timezone_supports_dst(tz):
    """
    Take a timezone and returns a tuple describing whether it "supports" dst, and if so, if it is currently dst.
    """
    JULY_DATETIME = tz.localize(datetime(year=2000, day=15, month=6))
    DECEMBER_DATETIME = tz.localize(datetime(year=2000, day=15, month=12))
    delta = DECEMBER_DATETIME - JULY_DATETIME

    LOG.debug("delta for TZ %s is %s", tz, delta)

    supports = delta.seconds != 0
    LOG.debug("supports? %s", supports)

    utcnow_dst = utcnow().astimezone(tz).dst()
    LOG.debug("utcnow_dst is %s", utcnow_dst)
    currently_dst = utcnow_dst != timedelta(0)
    LOG.debug("currently_dst? %s", currently_dst)

    return supports, currently_dst


def datetime_xrange(begin, end, step):
    """
    This returns a datetime range generator analogous to the builtin integer function
    range(begin_inclusive, end_exclusive, step)
    :type begin: datetime.datetime
    :type end: datetime.datetime
    :type step: datetime.timedelta
    :return: A list of date time objects.
    :rtype: generator
    """
    current_datetime_var = begin
    while current_datetime_var < end:
        yield current_datetime_var
        current_datetime_var = current_datetime_var + step


def datetime_range(begin, end, step):
    """
    This returns a datetime range list analogous to the builtin integer function
    range(begin_inclusive, end_exclusive, step)
    :type begin: datetime.datetime
    :type end: datetime.datetime
    :type step: datetime.timedelta
    :return: A list of date time objects.
    :rtype: list[datetime.datetime]
    """
    return list(datetime_xrange(begin, end, step))
