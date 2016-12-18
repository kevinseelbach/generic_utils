"""
https://s-media-cache-ak0.pinimg.com/736x/0e/68/a3/0e68a3e94b3357905707e1b4918abdfd.jpg


A Kombu transport which is backed by shared memory across processes to allow for process based Celery workers without
any other external dependencies such as Redis or a database or AMQ.

This is pretty ugly and does some nasty things and I have not invested in making it cleaner because this is


  PURELY FOR TESTING AND NOT PRODUCTION USE !!!!!!!!!!!


So, forgive some of the absolutely lazy things that I am doing here.  Hopefully noone ever has to look at this again
as it just works for now.


To use this you have to do the following:

  1> You must import this module in order for it to register with Kombu
  2> Configure celery to use this transport by specifying the BROKER_URL as "multiprocessmemory://" which will cause
    celery to use the Transport class in this module
  3> Before starting celery up you must call the init() method in this module.  This will start up a Multiprocessing
    Manager _KombuManager which facilitates the memory sharing.  The manager dynamically attaches to a port on localhost
    to make sure the port is available and will return the address that is used from the init() method and sets the
    address to the global mgr_server_address.  This value must then be set to the "multiprocessmemory.address" value
    in the BROKER_TRANSPORT_OPTIONS celery config value before starting celery.
  4> At this point you should be able to use celery and all should work as long as the workers are run within processes
    on the same host.
  5> Once the test run is complete you must call the shutdown() method so it can shutdown the Manager and do any other
    state cleanup.  At this point you can call init() again and run a clean set of tests again.


NOTE:  This is not thread safe such that you cannot run multiple tests in parallel as the management and setup aspects
    of this do not protect itself and leverages global state.  This is thread safe internally in its management of its
    internal responsibilities and as a Kombu service.
"""
import os
import sys
import signal
from multiprocessing.managers import SyncManager, DictProxy, ListProxy, RemoteError
from multiprocessing import Process
import multiprocessing
from kombu.exceptions import InconsistencyError
from kombu.transport import TRANSPORT_ALIASES
from kombu.transport.memory import Channel as MemoryChannel, Transport as MemoryTransport
from kombu.transport.redis import NO_ROUTE_ERROR
from kombu.utils.encoding import bytes_to_str
from generic_utils import loggingtools

# pylint: disable=global-statement

LOG = loggingtools.getLogger()

# Because this is using multiprocessing and all kinds of pain, it can be difficult to debug with break points, etc.
# So if this is set to True then it turns on print messages and whatever else is needed to work through the madness.
_ENABLE_HACKY_DEBUG = False

_AUTH_KEY = "magic_auth_key"  # shh, dont tell

class _KombuManager(SyncManager):
    """Process Manager which manages shared state for the multiprocessing based Kombu transport
    """
    _client_defined = False

    @classmethod
    def get_client(cls, *args, **kwargs):
        """Return a client suitable for talking to a KombuManager server
        """
        client_type = type("KombuManagerClient", (cls, ), {})
        _debug("Client not defined.  Defining client proxy methods")
        client_type.register('get_queue_dict', proxytype=DictProxy)
        client_type.register('create_new_queue')
        client_type.register('get_queue')
        client_type.register('add_queue_exchange')
        client_type.register('delete_queue_exchange')
        client_type.register('get_exchange_members', proxytype=ListProxy)

        return client_type(*args, **kwargs)

# pylint: disable=invalid-name
_queue_dict = None
_mgr_server = None

# The address that the Manager is bound to
mgr_server_address = None
# pylint: enable=invalid-name


def init():  # pylint: disable=too-many-branches
    """Initialize the Multiprocess Memory transport support systems, etc.  This must be called before using this
    with celery and upon completion of use you must call shutdown to perform the necessary cleanup
    """
    _debug("In multiprocess_memory init")

    # pylint: disable=invalid-name
    global _mgr_server
    global mgr_server_address
    # pylint: enable=invalid-name

    if mgr_server_address:
        return

    # Private shared state
    queue_dict = {}
    exchange_dict = {}

    def _get_queue_dict():  # pylint: disable=missing-docstring
        _debug("IN MEMORY PROCESS get_queue_dict - %s" % str(queue_dict))
        return queue_dict

    def _get_queue(queue_name):  # pylint: disable=missing-docstring
        return queue_dict[queue_name]

    def _create_new_queue(queue_name):  # pylint: disable=missing-docstring
        try:
            return queue_dict[queue_name]
        except KeyError:
            queue_dict[queue_name] = multiprocessing.Queue()
            return queue_dict[queue_name]

    def _add_queue_exchange(exchange_name, value):  # pylint: disable=missing-docstring
        exchange_set = exchange_dict.setdefault(exchange_name, set())
        _debug("_add_queue_exchange(%s, %s) - values = %s"
               % (exchange_name, value, _get_exchange_members(exchange_name)))
        exchange_set.add(value)

    def _delete_queue_exchange(exchange_name, value):  # pylint: disable=missing-docstring
        try:
            exchange_set = exchange_dict[exchange_name]
            """ :type: set"""
            _debug("_delete_queue_exchange(%s)" % value)
            exchange_set.remove(value)
        except KeyError:
            pass

    def _get_exchange_members(exchange_name):  # pylint: disable=missing-docstring
        try:
            exchange_set = exchange_dict[exchange_name]
            """ :type: set"""
            return list(exchange_set)
        except KeyError:
            return []

    _KombuManager.register('get_queue_dict', callable=_get_queue_dict, proxytype=DictProxy)
    _KombuManager.register('create_new_queue', callable=_create_new_queue)
    _KombuManager.register('get_queue', callable=_get_queue)
    _KombuManager.register('add_queue_exchange', callable=_add_queue_exchange)
    _KombuManager.register('delete_queue_exchange', callable=_delete_queue_exchange)
    _KombuManager.register('get_exchange_members', callable=_get_exchange_members, proxytype=ListProxy)

    _mgr_instance = _KombuManager(address=('', 0), authkey=_AUTH_KEY)
    server = _mgr_instance.get_server()
    mgr_server_address = server.address

    def _serve_forever():
        """Wrapper target function for the server.serve_forever method which also supports a more explicit termination
        behavior
        """
        def _sigterm_handler(*_, **__):
            """
            Local sig handler for the SIGTERM signal
            """
            _debug("On SIGTERM")
            sys.exit()

        # Listen for the SIGTERM signal so we can raise a SystemExit which the server handles cleanly for shutting down
        # the socket
        signal.signal(signal.SIGTERM, _sigterm_handler)
        try:
            server.serve_forever()
        finally:
            _debug("DONE SERVING")
    _mgr_server = Process(target=_serve_forever)
    _mgr_server.daemon = True
    _debug("In multiprocess_memory init - Starting Server")
    _mgr_server.start()

    LOG.info("Shared memory process server for Kombu transport has started on address %s", mgr_server_address)
    _debug("SERVER STARTED - %s" % (str(mgr_server_address), ))
    return mgr_server_address

def shutdown():
    """Shutdown the multiprocess memory server and any other support functionality
    """
    _debug("In shutdown()")
    # pylint: disable=invalid-name
    global _mgr_server
    global mgr_server_address
    # pylint: enable=invalid-name
    if _mgr_server:
        _debug("TERMINATING Multiprocess Memory process server")
        try:
            os.kill(_mgr_server.pid, signal.SIGTERM)
            _mgr_server.join(10.0)
            if _mgr_server.is_alive():
                raise RuntimeError("Could not shutdown Multiprocess Memory Manager server in time.")
            _debug("Server terminated")
        finally:
            _mgr_server = None
            mgr_server_address = None

    # Clear the state of the Transport as it is global.
    Transport.state.clear()

class Channel(MemoryChannel):  # pylint: disable=abstract-method
    """A Kombu channel which stores its state in shared memory.  This acts very close to the Redis Transport except
    Redis is simulated in memory with the _KombuManager
    """
    # Pulled from Redis Channel impl
    _fanout_queues = {}
    sep = '\x06\x16'

    def __init__(self, connection, **kwargs):
        _debug("CHANNEL INIT %s" % str(connection.client.transport_options))
        super(Channel, self).__init__(connection, **kwargs)
        try:
            address = connection.client.transport_options["multiprocessmemory.address"]
        except (KeyError, AttributeError):
            raise RuntimeError("You must provide a value for multiprocessmemory.address in the "
                               "BROKER_TRANSPORT_OPTIONS config value for celery")

        self.shared_manager = _KombuManager.get_client(address=address, authkey=_AUTH_KEY)
        self.shared_manager.connect()
        # Workaround for authkey not being present in new spawned process - https://bugs.python.org/issue7503
        multiprocessing.current_process().authkey = _AUTH_KEY

        _debug("Created new channel %s" % self)

    def _has_queue(self, queue, **kwargs):
        _debug("has_queue %s" % queue)
        return self.queues.has_key(queue)

    def _new_queue(self, queue, **kwargs):
        if not self.queues.has_key(queue):
            _debug("Created new channel %s" % queue)
            self._create_new_queue(queue)
        else:
            _debug("Queue already exists - %s" % queue)

    def _queue_for(self, queue):
        if queue not in self.queues:
            _debug("Created new channel %s" % queue)
            return self._create_new_queue(queue)
        _debug("Returning _queue_for(%s)" % queue)
        try:
            return self.shared_manager.get_queue(queue)  # pylint: disable=no-member
        except KeyError:
            return self._create_new_queue(queue)
        except RemoteError as exc:
            remote_exception_str = str(exc.args[0])
            remote_exception_split = remote_exception_str.split("\n")

            if len(remote_exception_split) >= 2:
                exception_line = remote_exception_split[-2]  # Last line is a blank string
                if exception_line.startswith("KeyError"):  # Remote exception was a KeyError
                    _debug("Got KeyError wrapped in a RemoteError exception!!! %s" % repr(exc))
                    return self._create_new_queue(queue)

            _debug("Got exception!!! %s" % repr(exc))
            raise

    def close(self):
        # Intentionally doing super of MemoryChannel to skip MemoryChannels impl
        super(MemoryChannel, self).close()  # pylint: disable=bad-super-call
        _debug("QUEUES = %s" % str(self.queues))
        try:
            for queue in self.queues:
                self.queues[queue].empty()
        except TypeError:
            _debug("Type Error - %s" % str(self.queues))
        except KeyError:
            pass
        self.queues.clear()

    def _size(self, queue):
        try:
            return super(Channel, self)._size(queue)
        except NotImplementedError:
            # Because multiprocessing Queue qsize does not on Mac we have a bit of a hack here.
            # This is obviously not suitable for production use on Mac until qsize works there
            return 1 if not self._queue_for(queue).empty() else 0

    def _queue_bind(self, exchange, routing_key, pattern, queue):  # pylint: disable=arguments-differ
        # This is just the redis implementation ported to shared memory
        if self.typeof(exchange).type == 'fanout':
            # Mark exchange as fanout.
            self._fanout_queues[queue] = (
                exchange, routing_key.replace('#', '*'),
            )

        self.shared_manager.add_queue_exchange(  # pylint: disable=no-member
            exchange,
            self.sep.join([routing_key or '',
                           pattern or '',
                           queue or '']))

    def _delete(self, queue, exchange, routing_key, pattern, *args):
        # This is just the redis implementation ported to shared memory
        _debug("Deleting queue exchange %s" % exchange)
        self.shared_manager.delete_queue_exchange(  # pylint: disable=no-member
            exchange,
            self.sep.join([routing_key or '',
                           pattern or '',
                           queue or ''])
        )

    def get_table(self, exchange):
        # This is just the redis implementation ported to shared memory
        values = self.shared_manager.get_exchange_members(exchange)  # pylint: disable=no-member
        if not values:
            raise InconsistencyError(NO_ROUTE_ERROR.format(exchange, exchange))
        return [tuple(bytes_to_str(val).split(self.sep)) for val in values]

    @property
    def queues(self):
        """
        :rtype: dict
        """
        queue_dict = self.shared_manager.get_queue_dict()  # pylint: disable=no-member
        return queue_dict

    def _create_new_queue(self, queue_name):
        """
        Overridden _create_new_queue
        """
        return self.shared_manager.create_new_queue(queue_name)  # pylint: disable=no-member


class Transport(MemoryTransport):
    """Transport which uses shared process memory for state management
    """
    Channel = Channel

    driver_type = 'multiprocessmemory'
    driver_name = 'multiprocessmemory'

# Register our multiprocess memory transport with Kombu
TRANSPORT_ALIASES["multiprocessmemory"] = "generic_utils.kombu.transport.multiprocess_memory:Transport"


def _debug(msg):
    """
    Log debug message
    """
    if _ENABLE_HACKY_DEBUG:
        # Print because logging doesn't work with multi-processes to a file
        print "(%s) - %s" % (str(os.getpid()), msg)
