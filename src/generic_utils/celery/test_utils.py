"""Celery test case mixin."""
from multiprocessing import Process, Manager
from celery.worker import state
from celery.beat import EmbeddedService
from celery.result import allow_join_result
from celery_testutils import CELERY_TEST_CONFIG_MEMORY, setup_celery_worker, CeleryWorkerThread
from kombu.transport.memory import Transport
from nose.tools import nottest
from generic_utils import loggingtools

from generic_utils.test import TestCaseMixinMetaClass


LOG = loggingtools.getLogger()

# Constants which indicate what type of Celery worker to use for running a test.  The default is a THREAD_WORKER
PROCESS_WORKER = "process_worker"
THREAD_WORKER = "thread_worker"

class CeleryWorkerProcess(Process):
    """A process based celery worker which just wraps the CeleryWorkerThread in a Process.

    In the majority of cases the thread based worker is the right one to use as this one just adds additional
    complexity, however if you want more true isolation or need to test a task in a more real world type scenario then
    you could benefit from using the Process based worker.

    """

    _worker_thread = None
    _app = None
    _manager = None

    def __init__(self, app):
        self._app = app
        self._manager = Manager()
        self._ready_event = self._manager.Event()  # pylint: disable=no-member
        self._idle_event = self._manager.Event()  # pylint: disable=no-member
        self._stop_signal = self._manager.Event()  # pylint: disable=no-member
        super(CeleryWorkerProcess, self).__init__(kwargs={
            "ready_event": self._ready_event,
            "idle_event": self._idle_event,
            "stop_signal": self._stop_signal
        })

    def run(self):
        LOG.debug("Starting Process based worker")
        super(CeleryWorkerProcess, self).run()
        self._worker_thread = worker_thread = CeleryWorkerThread(self._app)

        # Shadow the worker's events with our multiprocess based events instead of the single process events.  This is
        # so that any external consumer of the worker and the worker itself can properly synchronize across processes
        # instead of just threads
        worker_thread.ready = self._kwargs["ready_event"]
        worker_thread.monitor.idle = self._kwargs["idle_event"]
        worker_thread.idle = self._kwargs["idle_event"]

        # Start up the thread based worker within our new worker process
        worker_thread.daemon = True
        worker_thread.start()
        worker_thread.ready.wait()
        LOG.debug("Process based worker is ready")

        while worker_thread.is_alive():
            if self._kwargs["stop_signal"].wait(0.5):
                self._worker_thread.stop()

        LOG.debug("Stopping Process based worker")

    def stop(self):
        """Request the worker to stop at it's first convenience.  The alive state of the process should be consulted
        or join() should be called on the process to determine when the process has actually stopped.
        """
        self._stop_signal.set()
        LOG.debug("Process based worker signalled to stop execution")

    @property
    def ready(self):
        """An Event which is set when the worker is ready
        """
        return self._kwargs["ready_event"]

    @property
    def idle(self):
        """An Event which is set when the worker is idle
        """
        return self._kwargs["idle_event"]



class CeleryTestCaseMixin(object):
    """
    Base Celery test class. It handles setup and teardown Celery test configurations.

    This is mostly taken from celerytest.testcase.CeleryTestCaseMixin with some bugs fixed
    """
    __metaclass__ = TestCaseMixinMetaClass

    celery_config = CELERY_TEST_CONFIG_MEMORY
    celery_app = None
    celery_concurrency = 1
    celery_share_worker = True

    worker = None

    #: The celery scheduler service that is used by the test if scheduling is used.
    schedule_service = None

    #: Whether or not the test needs job scheduling support.  If this is true then a celery scheduler will be launched
    #: in a separate thread in addition to the celery worker
    with_scheduling = False

    #: The scheduler class to use if `with_scheduling` is True.  If this is not specified then the scheduler_class from
    #: celery_app will be used
    scheduler_class = None

    # The type of celery worker to use.  This can be either THREAD_WORKER or PROCESS_WORKER.  In general you should use
    # THREAD_WORKER as it is much more flexible and PROCESS_WORKER should only be used if you absolutely need to
    worker_type = THREAD_WORKER

    _allow_join_result = None

    WORKER_TYPE_CONF_MAP = {
        THREAD_WORKER: {
            "class": CeleryWorkerThread,
        },
        PROCESS_WORKER: {
            "class": CeleryWorkerProcess,
            "config": {
                "BROKER_URL": "multiprocessmemory://",
                "CELERYD_POOL": "celery.concurrency.prefork:TaskPool"
            }
        }
    }

    def _custom_setup(self):  # pylint: disable=invalid-name
        """Perform celery based setup"""
        if not self.celery_share_worker:
            self.worker = self.start_worker()
        else:
            self.ensure_shared_worker()

        self._allow_join_result = allow_join_result()
        self._allow_join_result.__enter__()  # pylint: disable=no-member

        if self.with_scheduling:
            self._do_with_scheduling_setup()

        super_class = super(CeleryTestCaseMixin, self)
        if hasattr(super_class, "_custom_setup"):
            super_class._custom_setup()  # pylint: disable=protected-access

    def _custom_teardown(self):  # pylint: disable=invalid-name
        """Perform celery teardown
        """
        local_worker = self.__class__.worker if hasattr(self, "shared_worker") else self.worker
        if not self.wait_for_worker_idle(local_worker, 5.0):
            LOG.error("Worker did not complete work in a sufficient amount of time.  Test cleanup will likely not "
                      "be complete and there could be additional abnormalities which occur.  To address this problem "
                      "you need to ensure your tests which spawn background Celery tasks complete their execution "
                      "during the test run and dont just leave them hanging around before completion of the test.")
        if not self.celery_share_worker:
            self.stop_worker(local_worker)

        self._do_with_scheduling_teardown()

        self._allow_join_result.__exit__(None, None, None)  # pylint: disable=no-member

        super_class = super(CeleryTestCaseMixin, self)
        if hasattr(super_class, "_custom_teardown"):
            super_class._custom_teardown()  # pylint: disable=protected-access

    @classmethod
    def setUpClass(cls):  # pylint: disable=invalid-name
        """Perform test case setup at class initialization which in this case is for starting the shared worker for the
        class, if `celery_share_worker` is set to True on the class.
        """
        if cls.celery_share_worker:
            cls.ensure_shared_worker()
        super_class = super(CeleryTestCaseMixin, cls)
        if hasattr(super_class, "setUpClass"):
            super_class.setUpClass()

    @classmethod
    def tearDownClass(cls):  # pylint: disable=invalid-name
        """Perform test case cleanup at class tear down
        """
        if cls.worker:
            if not cls.wait_for_worker_idle(cls.worker, 5.0):
                LOG.error("Worker did not complete work in a sufficient amount of time.  Test cleanup will likely not "
                          "be complete and there could be additional abnormalities which occur.  To address this "
                          "problem you need to ensure your tests which spawn background Celery tasks complete their "
                          "execution during the test run and dont just leave them hanging around before completion of "
                          "the test.")
            cls.stop_worker(cls.worker)
        super_class = super(CeleryTestCaseMixin, cls)
        if hasattr(super_class, "tearDownClass"):
            super_class.tearDownClass()

    @classmethod
    @nottest
    def start_worker(cls):
        """Starts the background celery worker for the test case
        """
        cls._clean_celery_environment()
        worker_conf = dict(cls.WORKER_TYPE_CONF_MAP[cls.worker_type])
        if cls.worker_type == PROCESS_WORKER:
            from generic_utils.kombu.transport import multiprocess_memory
            multiprocess_memory.init()

        worker_class = worker_conf["class"]

        return start_celery_worker(worker_class,
                                   cls.celery_app,
                                   config=cls._get_celery_config(),
                                   concurrency=cls.celery_concurrency)

    @classmethod
    @nottest
    def stop_worker(cls, worker):
        """
        Stop the provided worker and do any other necessary operations needed when a worker is stopped.
        """
        if worker.is_alive():
            worker.stop()
            worker.join(10.0)

        if cls.worker_type == PROCESS_WORKER:
            from generic_utils.kombu.transport import multiprocess_memory
            multiprocess_memory.shutdown()

    @classmethod
    def _get_celery_config(cls):
        """Returns the celery config to use for creating celery workers
        """
        # Create a "clone" of the class celery_config so that any local changes we make are not shared across tests.
        config = type("TempConfig", (object,), dict(cls.celery_config.__dict__))
        worker_conf = cls.WORKER_TYPE_CONF_MAP[cls.worker_type]
        if "config" in worker_conf:
            for key, value in worker_conf["config"].items():
                setattr(config, key, value)

        if cls.worker_type == PROCESS_WORKER:
            from generic_utils.kombu.transport import multiprocess_memory

            transport_options = dict(config.BROKER_TRANSPORT_OPTIONS)  # pylint: disable=no-member
            transport_options["multiprocessmemory.address"] = multiprocess_memory.mgr_server_address
            config.BROKER_TRANSPORT_OPTIONS = transport_options

        return config

    @nottest
    def get_async_result(self, async_result, timeout=5.0, **kwargs):  # pylint: disable=no-self-use
        """Helper method for blocking on the result of an async result from a Celery task

        :param async_result: The AsyncResult to block on for a result
        :type async_result: celery.result.AsyncResult
        :param timeout: How long, in seconds, to wait.  In general the default should be fine
        :type timeout: float

        :return: The result of the provided async_result after it has completed, or an exception is raised.
        """
        return async_result.get(timeout, **kwargs)

    def _create_embedded_schedule_srvc(self):
        """Creates an EmbeddedService for task scheduling handling in process
        """
        this = self
        scheduler_class = self.scheduler_class
        if scheduler_class is None:
            scheduler_class = self.celery_app.Beat().scheduler_cls
            LOG.debug("scheduler_class not explicitly set, so got scheduler class %s from the provided celery app",
                      scheduler_class)
        service = EmbeddedService(thread=True, app=self.celery_app, scheduler_cls=scheduler_class)
        old_run = service.run

        def run_monkey_patch(_self):
            """Monkey patch for the service `run` method which injects a hook for doing scheduler setup and teardown
            within the executing thread of the scheduler
            """
            # pylint: disable=protected-access
            try:
                this._on_scheduler_start()
                old_run()
            finally:
                this._on_scheduler_stop()

        service.run = run_monkey_patch.__get__(service)  # pylint: disable=no-member
        return service

    def _on_scheduler_stop(self):
        """Hook method for handling of termination of the embedded scheduler service within the Thread of the scheduler
        """
        pass

    def _on_scheduler_start(self):
        """Hook method for handling of start of the embedded scheduler service within the Thread of the scheduler
        """
        pass

    def _do_with_scheduling_setup(self):
        """Perform setup operations for the scheduling service
        """
        self.schedule_service = self._create_embedded_schedule_srvc()
        LOG.debug("Starting schedule service")
        self.schedule_service.start()

    def _do_with_scheduling_teardown(self):
        """Perform teardown operations for the scheduling service
        """
        if self.schedule_service:
            LOG.debug("Stopping schedule service")
            self.schedule_service.stop()
            self.schedule_service.join()
            LOG.debug("Schedule service stopped")

    @classmethod
    def ensure_shared_worker(cls):
        """Ensures that the shared worker is actually running and if it isn't then it restarts it as it is possible
        that another test killed the worker
        """
        if cls.worker and cls.worker.is_alive():
            LOG.debug("Shared worker is alive, nothing to do")
            return

        cls.worker = cls.start_worker()
        cls.shared_worker = cls.worker

    @classmethod
    def _clean_celery_environment(cls):
        """Cleans up the celery environment from any pollution that may have occurred during a test run
        """
        # Reset the state variables just in case a test caused a worker to stop
        state.should_stop = False
        state.should_terminate = False

        # Clear the in memory global Transport state since this is in memory storage but the transport could be backed
        # by something else.  The transport state caches some of the exchanges which from test to test may be different
        Transport.state.clear()

    @classmethod
    def wait_for_worker_idle(cls, worker, timeout_s=None):
        """Blocks until the worker is idle and no longer processing any tasks.  If timeout_s is specified then this will
        block until timeout_s is reached and if the worker is not idle then False will be returned

        :param worker: The worker to wait on
        :param timeout_s: The amount of time, in seconds, to wait for the worker to go idle before giving up.  If this
            is not specified then no timeout occurs and it will block indefinitely
        :return: Whether or not the worker went idle before any timeout.
        :rtype: bool
        """
        if not worker:
            LOG.debug("There isn't a worker for the current test/environment, so there is nothing to wait on")
            return True
        LOG.debug("Waiting for worker to go idle")
        idle_success = worker.idle.wait(timeout_s)
        if idle_success:
            LOG.debug("Worker is idle")
        else:
            LOG.debug("Worker is still processing tasks")
        return idle_success


def start_celery_worker(worker_cls, app, config=CELERY_TEST_CONFIG_MEMORY, concurrency=1):
    """Starts a celery worker of class worker_cls.

    This is a clone of celerytest.start_celery_worker which allows for specifying the worker class to use
    """
    setup_celery_worker(app, config=config, concurrency=concurrency)

    worker = worker_cls(app)
    worker.daemon = True
    worker.start()
    worker.ready.wait()
    return worker
