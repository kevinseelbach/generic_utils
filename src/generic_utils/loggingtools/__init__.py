"""Helper utilities for dealing with python logging
"""
import inspect
import logging
import os
import traceback
from six import StringIO

from logging.handlers import SysLogHandler as python_SysLogHandler
from logging.handlers import SYSLOG_UDP_PORT
from generic_utils.inspecttools import get_calling_frame, is_module_frame

# Namespace logging under a prefix.
# For example a logger should be created by one of either:
#   log = ns_log.getChild("mylogger")
#     or
#   log = getLogger("mylogger")

#: TODO Make this configurable per application, i.e. write function to return a new getLogger function per namespace
BASE_NS_LOG_NAME = os.environ.get('GENERIC_UTILS_LOGGING_PREFIX', 'project_logs')
UNKNOWN_LOGGER_NAME = "UNKNOWN"
FULL_UNKNOWN_LOG_NAME = "{base}.{unknown}".format(base=BASE_NS_LOG_NAME, unknown=UNKNOWN_LOGGER_NAME)


# pylint: disable=invalid-name
ns_log = logging.getLogger(BASE_NS_LOG_NAME)
_log = ns_log.getChild("generic_utils.loggingtools")
# pylint: enable=invalid-name


def getLogger(name=None):  # pylint: disable=invalid-name
    """
    Convenience method for getting a namespaced python logger.  This is a short-hand for just doing:

    >>> log = ns_log.getChild(name)

    :param name: The name of the child logger to create.  This will be a child of the `ns_log` logger
    :return: Requested logger
    :rtype: logging.Logger
    """
    if name is None:
        frame = get_calling_frame()
        caller_frame = frame[0]
        caller_module = inspect.getmodule(caller_frame)
        if caller_module is None:
            string_file = StringIO()
            traceback.print_stack(file=string_file)
            _log.error("getLogger() is unable to determine the name of the calling module.  This is generally do "
                       "to some general import problem that occurred within the module that the logger is trying to be "
                       "created within and therefore that import issue must be resolved which is preventing the module "
                       "from loading.  Other possibilities include creating a logger within an unsupported context.  "
                       "Returning an 'UNKNOWN' logger so that the logging functionality does not get in the way of "
                       "functional operation of the application.  Current call stack is\n: %s", string_file.getvalue())
            return ns_log.getChild(UNKNOWN_LOGGER_NAME)

        name = caller_module.__name__
        if not is_module_frame(caller_frame):
            name = ".".join([name, caller_frame.f_code.co_name])

    return ns_log.getChild(name)


class SysLogHandler(python_SysLogHandler):
    """
    Extension to the python SysLogHandler to support the passing of tag values to be embedded int he messages
    for later filtering.
    """
    DEFAULT_SYSLOG_EXE = "/var/run/syslog"
    TAG_FORMAT_PATTERN = u"{tags}: {msg}"

    def __init__(self,
                 address=('localhost', SYSLOG_UDP_PORT),
                 facility=python_SysLogHandler.LOG_USER,
                 socktype=None, tags=None, tag_delimiter=None):

        self.tags = [t for t in tags if t] if tags else []
        self.tag_delimiter = tag_delimiter or "-"
        super(SysLogHandler, self).__init__(address, facility, socktype)

    def format(self, record):
        """
        Preempt format call with a setting of configured tags.

        Handling this here will of course cause problems if you extend from this Handler and expect .format to return
        the formatted message string.  It will also have the intended syslog tag (obviously).
        :param record:
        :return:
        """
        formatted_msg = super(SysLogHandler, self).format(record)
        return self._add_tags_to_msg(formatted_msg)

    def _add_tags_to_msg(self, msg):
        """
        Given a msg argument and a valid tags argument, add the necessary tag string and return the resulting message.
        :param msg: message to be logged.
        :return: formatted message with tags
        """
        unicode_message = self._get_unicode_msg(msg)
        return SysLogHandler.TAG_FORMAT_PATTERN.format(
            tags=self.tag_delimiter.join(self.tags),
            msg=unicode_message
        ) if self.tags else unicode_message

    @staticmethod
    def _get_unicode_msg(message):
        """Convert the bytestring to unicode
        :param message:
        :type message:
        :return:
        :rtype: unicode
        """
        if isinstance(message, unicode):
            return message
        elif isinstance(message, str):
            return message.decode('utf-8', 'replace')
        else:
            raise TypeError("Received unexpected type=%s for argument message" % type(message))
