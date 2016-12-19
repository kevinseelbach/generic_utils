"""Various utilities for dealing with logging within tests
"""
# future/compat
from builtins import str

# stdlib
import logging
import re
from logging.handlers import MemoryHandler

from generic_utils.contextlib_ex import ExplicitContextDecorator
from generic_utils.typetools import as_iterable


class LogBufferHandler(object):
    """Log handler which stores LogRecords in a local buffer and also allows for definition of the types of log records
    to allow
    """

    records = None
    """ :type: list of logging.LogRecord """

    def __init__(self, log_level=logging.NOTSET, *loggers):
        self.log_level = log_level
        if loggers:
            self.loggers = set(loggers)
        else:
            self.loggers = None
        self.records = []
        """ :type: list of logging.LogRecord """

    def reset(self):
        """Resets the log record buffer
        """
        self.records = []

    def handle(self, log_record):
        """

        :param log_record:
        :type log_record: logging.LogRecord
        :return:
        :rtype:
        """
        if not (self.log_level == logging.NOTSET or log_record.levelno >= self.log_level):
            return

        if not self._is_approved_logger(log_record):
            return

        self.records.append(log_record)

    def _is_approved_logger(self, log_record):
        """
        :param log_record: The log record to check if the logger is an approved logger
        :type log_record: logging.LogRecord
        :return: Whether or not the log_record is for an approved logger as defined by this log handler
        :rtype: bool
        """
        if self.loggers is None:
            return True

        log_name = log_record.name
        while log_name:
            if log_name in self.loggers:
                return True
            log_comps = log_name.rsplit(".", 1)
            if len(log_comps) == 1:
                log_name = ""
            else:
                log_name = log_comps[0]
        return False


class LoggingSpy(ExplicitContextDecorator):
    """Decorator/context manager which captures all logs sent to the python logging mechanism while within the context
    of this context manager so that the messages that are logged during that time can be asserted on for test/validation
    purposes.

    This is used as such:

    >>> with LoggingSpy() as log_spy:
    >>>     logging.getLogger("dummy.log").debug("Test")
    >>> log_spy.assert_log("Test", level=logging.DEBUG, logger="dummy.log")

    """
    log_level = None
    loggers = None

    _memory_handler = None
    _log_buffer = None

    def __init__(self, log_level=logging.NOTSET, loggers=None):
        """
        :param log_level: Only capture logs that are of this level or higher.  Default is NOTSET
        :param loggers: Explicit loggers to only capture messages for.  If this is not provided than all loggers are
            captured
        """
        if loggers:
            self.loggers = set()
            for logger in as_iterable(loggers):
                if isinstance(logger, logging.Logger):
                    logger = logger.name
                self.loggers.add(logger)
        else:
            self.loggers = None
        self.log_level = log_level
        self._log_buffer = LogBufferHandler(log_level, *(self.loggers or []))
        self._memory_handler = MemoryHandler(1, target=self._log_buffer)
        self._memory_handler.setLevel(logging.NOTSET)

    def __enter__(self):
        self.reset()
        self._process_handler_on_loggers(logging.Logger.addHandler)
        super(LoggingSpy, self).__enter__()
        return self

    def __exit__(self, *exc_info):
        self._process_handler_on_loggers(logging.Logger.removeHandler)
        super(LoggingSpy, self).__exit__(*exc_info)

    def reset(self):
        """Resets the captured log records.
        """
        self._memory_handler.flush()
        self._log_buffer.reset()

    def _process_handler_on_loggers(self, handler_meth):
        """Applies Logger method `handler_meth` on all of the loggers.  `handler_meth` should either be `addHandler` or
        `removeHandler` depending on the behavior desired to be applied to the loggers.
        """
        loggers = []
        if self.loggers is None:
            loggers.append(None)
        else:
            loggers.extend(self.loggers)

        for logger_name in loggers:
            log_obj = logging.getLogger(logger_name)
            handler_meth(log_obj, self._memory_handler)

    def assert_log(self, message_pattern, level=logging.NOTSET, logger=None, expected_count=1,
                   expect_exact_count=False):
        """Test helper method which asserts that a specific log message exists within the log records.  If the
        requested log message was not logged than an assertion will be raised

        :param message_pattern: A regular expression to use to match against the log messages to find a matching log
            message.
        :type message_pattern: str
        :param level: The log level to expect the message to be logged at.  If this is NOTSET then the log level is not
            considered.  Default is to not consider it.
        :type level: int
        :param logger: The name of a logger to expect the message to be logged to.  If this is None, then the logger
            name is not considered.  Default is to not consider it.
        :type logger: str
        :param expected_count: The number of times a log which meets the provided criteria is expected to be seen.
            Default is 1.
        :type expected_count: int
        :param expect_exact_count: Whether or not the count of matched log entries must exactly match
            `expected_count` (True) or if there can be more (False).  Default is `False`
        :type expect_exact_count: bool
        """
        message_re = re.compile(message_pattern)
        count = 0
        for log_record in self.log_records:
            if level is not logging.NOTSET and log_record.levelno != level:
                continue
            if logger is not None and log_record.name != logger:
                continue
            if not message_re.match(log_record.getMessage()):
                continue
            count += 1

        if count >= expected_count:
            if expect_exact_count and count > expected_count:
                raise AssertionError(
                    "Expected exactly %d log messages with message '%s', level '%s' and logger '%s', but it occurred "
                    "%d times\n%s" % (expected_count, message_pattern, logging.getLevelName(level), str(logger),
                                      count, self._records_to_str(self._log_buffer.records))
                )
        else:
            raise AssertionError(
                "Expected %d log messages with message '%s', level '%s' and logger '%s', "
                "but it occurred %d times\n%s" % (expected_count, message_pattern, logging.getLevelName(level),
                                                  str(logger), count, self._records_to_str(self._log_buffer.records))
            )

    @property
    def log_records(self):
        """Returns all log records which have been captured.  This can be called at any time, however when the context
        is first entered the log records will be cleared/reset.

        :return: The log records that have been captured while the context was active.
        :rtype: list of logging.LogRecord
        """
        return self._log_buffer.records

    @classmethod
    def _records_to_str(cls, log_records):
        """Convert a log records iterable to a string for display purposes
        """
        return_str = "["
        for record in log_records:
            return_str += "\n\t\"" + cls._log_record_to_str(record) + "\","
        return_str += "\n]"
        return return_str

    @staticmethod
    def _log_record_to_str(log_record):
        """
        Converts a LogRecord to a string for display purposes

        :type log_record: logging.LogRecord
        :return: String representation of `log_record`
        :rtype: str
        """
        return "{log_level} {log_name} {func} - {message}".format(log_name=log_record.name,
                                                                  log_level=log_record.levelname,
                                                                  func=log_record.funcName,
                                                                  message=log_record.getMessage())
