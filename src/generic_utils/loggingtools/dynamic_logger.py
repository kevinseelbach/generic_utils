"""Module which exposes a custom python Logger, DynamicLogLevelLogger, which consumes its log level dynamically from
a logging level manager which allows for runtime log level changes from any log level provider(whether file based,
database based, etc)
"""
# future/compat
from builtins import str

# stdlib
from logging import NOTSET as logging_NOTSET
from logging import Logger
from logging import getLoggerClass
from logging import setLoggerClass

from generic_utils import NOTSET
from generic_utils.classtools import get_classfqn
from generic_utils.typetools import as_iterable

_logging_level_manager = None  # pylint: disable=invalid-name


def _get_logging_level_manager():
    """Internal helper which returns the LoggingLevelManager instance to use for pulling dynamic log level information
    from

    :rtype: .loggingconfig.LoggingLevelManager
    """
    global _logging_level_manager  # pylint: disable=global-statement, invalid-name
    if not _logging_level_manager:
        try:
            from .loggingconfig import logging_level_manager
        except:  # pylint: disable=bare-except
            # There may be a timing issue which prevents us from doing the import at this moment, so no manager is
            # available just yet.  This could be related to any number of possible exceptions and not just ImportError
            # hence the catch of all exceptions
            return None
        _logging_level_manager = logging_level_manager
    return _logging_level_manager


class DynamicLogLevelLogger(Logger):
    """Custom logger which determines the log level of the logger based on dynamic configuration.

    In order for this to have the most effect this must be set as the logger class as soon as possible as this once
    loggers are created they cannot be changed to a different class.
    """

    _enabled = False

    @classmethod
    def enable_dynamic_config(cls):
        """Enables dynamic config support of log levels.  Once this logger is installed as the logger it will not
        actually provide dynamic log level support until it is enabled in order to provide flexibility around when
        the required dependencies might be available since logging is such a low level thing that comes before all
        other services.
        """
        cls._enabled = True

    @classmethod
    def disable_dynamic_config(cls):
        """
        Disables dynamic log level configuration in the running system.
        """
        cls._enabled = False

    @classmethod
    def install_as_logger(cls, base_logger_classes=NOTSET):
        """Installs this logger as the logger to be used by the python logging facilities.

        In order for this to have the most effect this must be set as the logger class as soon as possible as this once
        loggers are created they cannot be changed to a different class.

        :param base_logger_classes: If the DynamicLogLevelLogger should subclass from other Logger subclasses, then they
            should be provided here as a single class or as a list of classes.  If no value is provided for this then
            any current logger class that is set as the logger class will be used.  If this is None then only `Logger`
            will be the base class.
        :type base_logger_classes: type or list of type
        """
        current_logger_class = getLoggerClass()
        if issubclass(current_logger_class, cls):
            return

        if base_logger_classes is NOTSET:
            current_logger_class = getLoggerClass()
            if current_logger_class is not Logger:
                base_logger_classes = [current_logger_class]

        if base_logger_classes:
            bases = [cls]
            bases.extend(as_iterable(base_logger_classes))
            final_class = type("CustomDynamicLogLevelLogger", tuple(bases), {})
            setLoggerClass(final_class)

            log_args = ("Created custom CustomDynamicLogLevelLogger logger '%s' set as Logger class with bases %s",
                      get_classfqn(final_class), str(bases))
        else:
            final_class = cls
            setLoggerClass(final_class)
            log_args = ("'%s' set as Logger class", get_classfqn(final_class))
        cls.monkey_patch_loggers(final_class)

        # Dont create logger until after we have set the logger class
        from . import getLogger
        getLogger().debug(*log_args)

    @property
    def level(self):
        """
        :return: The level assigned to the logger, which could be the result of a configured log level override
        :rtype: int
        """
        if not self._enabled:
            return self.configured_level

        mgr = _get_logging_level_manager()
        if mgr:
            level = mgr.get_log_level(self.name, True)
            if level == logging_NOTSET:
                level = self._get_placeholder_level_override()
        else:
            level = logging_NOTSET

        return level if level > logging_NOTSET else self.configured_level

    @level.setter
    def level(self, level_val):
        """Setter for level property
        """
        super(DynamicLogLevelLogger, self).__dict__["level"] = level_val

    @property
    def configured_level(self):
        """
        :return: The underlying initially configured level for the logger.
        :rtype: int
        """
        return super(DynamicLogLevelLogger, self).__dict__["level"]

    def _get_placeholder_level_override(self):
        """While log names are hierarchical it doesn't mean that every level in the hierarchy actually has a logger as
        the logging framework only ever creates Logger instances, and therefore child/parent logger relationships,
        when a logger is actually requested of the specific name.  In the case where there is a "virtual" parent
        the logging framework creates `PlaceHolder` instances so that they can be plugged in later should someone
        actually create a logger with that name.

        This method accounts for placeholders in between hierarchical loggers so that level overriding can occur at
        the place holder level in addition to the concrete logger levels.  This method will walk the placeholders
        between this current logger and it's parent and if there is a level override for any of the place holders
        that will be returned.
        """
        if not self.parent or self.parent.name == "root":
            return logging_NOTSET
        mgr = _get_logging_level_manager()
        if not mgr:
            return logging_NOTSET

        parent_name = self.parent.name
        name = self.name
        while True:
            name = name.rsplit(".", 1)[0]
            if name == parent_name:
                return logging_NOTSET
            level = mgr.get_log_level(name, True)
            if level > logging_NOTSET:
                return level

    def getEffectiveLevel(self):
        """
        This does the same thing as the parent version however it is slightly optimized so that the level property of
        a logger is only access one time since our dynamic logger is slightly more expensive on that property
        """
        logger = self
        while logger:
            level = logger.level
            if level:
                return level
            logger = logger.parent
        return logging_NOTSET

    @staticmethod
    def monkey_patch_loggers(logger_cls):
        """Monkey patches all existing loggers to become DynamicLogLevelLogger's
        """
        assert issubclass(logger_cls, Logger)

        for logger in list(Logger.manager.loggerDict.values()):
            if not isinstance(logger, Logger):
                continue
            # Can you believe this actually works?  Python, what a country!!!
            logger.__class__ = logger_cls
