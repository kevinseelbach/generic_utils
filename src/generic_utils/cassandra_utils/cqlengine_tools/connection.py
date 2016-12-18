"""Module which assists in establishing and configuring Cassandra connections
"""
from cassandra.auth import PlainTextAuthProvider
from cassandra.cluster import NoHostAvailable  # pylint: disable=no-name-in-module
from cassandra.cqlengine import connection as cqlengine_connection
from cassandra.cqlengine.connection import get_session
from cassandra.cqlengine import CQLEngineException
from generic_utils import loggingtools
from generic_utils.config import config

LOG = loggingtools.getLogger()

_connection_setup = False  # pylint: disable=invalid-name

CQL_ENGINE_CONFIG_KEY = "CQLENGINE"


class ConfigKey(object):
    """Enum class which defines standard settings keys for the purpose of cassandra configuration
    """
    CONTACT_POINTS = "contact_points"
    KEYSPACE = "keyspace"
    USERNAME = "username"
    PASSWORD = "password"
    PORT = "port"
    #: The default client timeout to use for any queries to the cluster unless explicitly specified on a given query
    DEFAULT_TIMEOUT = "default_timeout"


def setup_connection_from_config(lazy_connect=True, force_load=False):
    """Sets up the CQLEngine connection from the current configuration.
    :return: Whether or not the connection could be setup
    :rtype: bool
    """
    global _connection_setup  # pylint: disable=invalid-name,global-statement
    if not force_load and _connection_setup:
        return True

    _connection_setup = False

    try:
        root_conf = config.get_conf_value(CQL_ENGINE_CONFIG_KEY)
        for cluster_name in root_conf:
            LOG.debug("Setting up connection for cluster %s", cluster_name)
            cluster_conf = root_conf[cluster_name]
            auth_provider = None
            if cluster_conf.get(ConfigKey.USERNAME):
                auth_provider = PlainTextAuthProvider(cluster_conf[ConfigKey.USERNAME],
                                                      cluster_conf[ConfigKey.PASSWORD])
                LOG.info("Using authentication for accessing DAP Cassandra")
            contact_points = cluster_conf[ConfigKey.CONTACT_POINTS]
            if not contact_points:
                # Currently only support a single connection per process, so we can bail here.  In the future we cannot
                # be so aggressive
                LOG.warn("No Cassandra contact points specified, so unable to setup Cassandra connection")
                return False
            cqlengine_connection.setup(contact_points,
                                       cluster_conf[ConfigKey.KEYSPACE],
                                       lazy_connect=lazy_connect,
                                       auth_provider=auth_provider,
                                       port=cluster_conf[ConfigKey.PORT])

            connection_timeout = cluster_conf.get(ConfigKey.DEFAULT_TIMEOUT, 10.0)
            set_default_timeout(cqlengine_connection.get_connection(), connection_timeout)

        _connection_setup = True
        return True
    except KeyError as exc:
        LOG.debug("Got exception %s with args %s while trying to setup Cassandra connection", exc, exc.args)

    return False


def set_default_timeout(conn=None, default_timeout_in_s=10.0):
    """Sets the default connection timeout that cqlengine uses.

    :param conn: The connection to set default_timeout on.
    :type conn: cassandra.cqlengine.connection.Connection
    :param default_timeout_in_s: The default connection timeout to use in seconds.  This timeout will be used unless
        a different timeout is explicitly used on a specific query
    :type default_timeout_in_s: float
    """
    if conn is None:
        conn = cqlengine_connection.get_connection()
    if not conn.session:
        # Session is being loaded lazily, so need to assign the timeout at first session creation

        # Monkey Patch the handle_lazy_connect method so we can intercept the initial call and do session setup
        old_handle_lazy_connect = conn.handle_lazy_connect

        def cb_handle_lazy_connect():
            """handle_lazy_connect monkey patch interceptor method which assigns the default timeout upon
            lazy session creation of cqlengine
            """
            LOG.debug("Intercepted lazy cqlengine connect call")
            conn.handle_lazy_connect = old_handle_lazy_connect
            old_handle_lazy_connect()
            set_default_timeout(default_timeout_in_s)

            conn.handle_lazy_connect = cb_handle_lazy_connect
    else:
        LOG.debug("Default connection timeout set to %s", default_timeout_in_s)
        conn.session.default_timeout = default_timeout_in_s


def is_cassandra_available():
    """
    :return: Whether or not Cassandra is currently available.
    :rtype: bool
    """
    cass_setup = False
    try:
        cass_setup = setup_connection_from_config()
    except AttributeError:
        pass
    if not cass_setup:
        LOG.error("Cassandra is not configured")
        return False

    try:
        get_session()
        return True
    except (CQLEngineException, NoHostAvailable):
        LOG.error("Unable to establish a Cassandra session")
    return False
