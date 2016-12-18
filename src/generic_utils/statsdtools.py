"""
Module which loads the appropriate statsd client to be used and makes that available via the statsd attribute of the
module.  This abstracts away the issues related to using the correct statsd client based on your execution environment
such as using the Django statsd client within a django environment or just a plain statsd client if in a plain
environment
"""
from __future__ import absolute_import

from collections import defaultdict
from time import time
import socket
from generic_utils import loggingtools
from generic_utils.config import config
try:
    from statsd.client import StatsClient
except ImportError:
    import statsd
    StatsClient = statsd.Stat
    from statsd import StatsClient

log = loggingtools.getLogger()

statsd = None


#: Configuration keys for STATSD configuration
STATSD_CLIENT_TYPE_CONFIG = "STATSD_CLIENT_TYPE"

#: Client type for use within TestCase's which captures the metric counts and outputs them at the end of a test run
STATSD_TESTCASE_CLIENT_TYPE = "TESTCASE"
STATSD_NULL_CLIENT_TYPE = "NULL"

#: Client type which sends messages to a remote server.  This is the default and is the standard Statsd client
STATSD_REMOTE_CLIENT_TYPE = "REMOTE"
STATSD_HOSTNAME_CONFIG = "STATSD_HOST"
STATSD_PORT_CONFIG = "STATSD_PORT"
STATSD_PREFIX_CONFIG = "STATSD_PREFIX"


def _get_statsd():
    """
    :rtype: StatsClient
    """
    statsd_client = _get_statsd_from_config()

    return statsd_client


def _get_statsd_from_config():
    """
    :return: A StatsClient driven from configuration
    :rtype: StatsClient
    """
    client_type = config.get_conf_value(STATSD_CLIENT_TYPE_CONFIG, STATSD_REMOTE_CLIENT_TYPE)

    if client_type is STATSD_REMOTE_CLIENT_TYPE:
        host = config.get_conf_value(STATSD_HOSTNAME_CONFIG, "localhost", str)
        port = config.get_conf_value(STATSD_PORT_CONFIG, 8125, int)
        prefix = config.get_conf_value(STATSD_PREFIX_CONFIG, None)
        try:
            return StatsClient(host, port, prefix)
        except (socket.error, socket.gaierror, KeyError):
            log.warn("Unable to connect to remote statsd service with config host='%s'; port='%s'; prefix='%s'",
                     host, port, prefix)
            return None
    elif client_type is STATSD_NULL_CLIENT_TYPE:
        return NullStatsClient()
    elif client_type is STATSD_TESTCASE_CLIENT_TYPE:
        return TestCaseStatsClient()
    raise ValueError("Unknown client type '%s'" % client_type)


class NullStatsClient(StatsClient):
    """A null client that does nothing."""

    def _after(self, data):
        pass


class CacheStatsClient(NullStatsClient):
    """A client that pushes things into a local cache.
    Borrowed from django-statsd-mozilla library (https://github.com/andymckay/django-statsd) which has a BSD license.

Copyright (c) 2010, Mozilla Foundation
All rights reserved.

Redistribution and use in source and binary forms, with or without modification,
are permitted provided that the following conditions are met:

    1. Redistributions of source code must retain the above copyright notice,
       this list of conditions and the following disclaimer.

    2. Redistributions in binary form must reproduce the above copyright
       notice, this list of conditions and the following disclaimer in the
       documentation and/or other materials provided with the distribution.

    3. Neither the name of commonware nor the names of its contributors may
       be used to endorse or promote products derived from this software
       without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
    """

    cache = None
    timings = None

    def __init__(self, *args, **kw):
        super(CacheStatsClient, self).__init__(*args, **kw)
        self.cache = defaultdict(list)
        self.timings = []

    def reset(self):
        """Reset the caches
        """
        self.cache = defaultdict(list)
        self.timings = []

    def timing(self, stat, delta, rate=1):
        """Send new timing information. `delta` is in milliseconds."""
        stat = '%s|timing' % stat
        now = time() * 1000
        self.timings.append([stat, now - delta, delta, now])

    def incr(self, stat, count=1, rate=1):
        """Increment a stat by `count`."""
        stat = '%s|count' % stat
        self.cache[stat].append([count, rate])

    def decr(self, stat, count=1, rate=1):
        """Decrement a stat by `count`."""
        stat = '%s|count' % stat
        self.cache[stat].append([-count, rate])

    def gauge(self, stat, value, rate=1, delta=False):
        """Set a gauge value."""
        stat = '%s|gauge' % stat
        self.cache[stat] = [[value, rate]]

    def set(self, stat, value, rate=1):
        stat = '%s|set' % stat
        self.cache[stat].append([value, rate])


class TestCaseStatsClient(CacheStatsClient):
    """StatsClient to be used when running unit tests which will capture all of the statsd metrics that occurred during
    a test case run and provide assertion capabilities so that tests can be performed and verified around the statsd
    coverage.

    For now this doesn't really do anything as it is a stub for the future for someone who wants to actually implement
    the hook into TestCase to listen for test setup and teardown and then also provide assertion helpers
    """


statsd = _get_statsd()
