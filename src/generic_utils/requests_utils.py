"""Additional HTTPAdapter subclasses for python `requests` module."""
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.poolmanager import PoolManager


class SSLAdapter(HTTPAdapter):
    """An adapter that allows passing in an arbitrary ssl_version.
    Useful because OpenSSL bugs can create situations where Python urllib2 requests can't complete successful
     handshakes.
    """
    __attrs__ = HTTPAdapter.__attrs__ + ['ssl_version']

    def __init__(self, ssl_version=None, **kwargs):
        """Set SSL version on init.

        :param ssl_version: one of the ssl constants from stdlib `ssl` module, e.g. ssl.PROTOCOL_TLSv1
        :type ssl_version: int
        :param kwargs:
        """
        self.ssl_version = ssl_version

        super(SSLAdapter, self).__init__(**kwargs)

    def init_poolmanager(self, connections, maxsize, *args, **kwargs):
        """Force the pool to use this instance's SSL version.
          This is a method used internally by HTTPAdapter, don't use it directly.

        :param connections:
        :param maxsize:
        """
        # pylint: disable=unused-argument, attribute-defined-outside-init
        self._pool_connections = connections
        self._pool_maxsize = maxsize

        self.poolmanager = PoolManager(num_pools=connections,
                                       maxsize=maxsize,
                                       ssl_version=self.ssl_version)
