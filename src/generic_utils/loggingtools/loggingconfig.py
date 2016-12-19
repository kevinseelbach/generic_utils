"""Module which provides tools for dealing with logging configuration, primarily with providing log configuration at
runtime from any provider backend.
"""
# stdlib
import logging
import threading
from collections import namedtuple

from generic_utils import NOTSET
from generic_utils.classtools import get_instance_from_fqn
from generic_utils.config import config
from generic_utils.datetimetools import utcnow
from generic_utils.mixins import comparable
from generic_utils.typetools import as_iterable

from . import getLogger

LOG = getLogger()


class LevelOverride(comparable.ComparableMixin):
    """Definition of a level override which can be applied to a log level dynamically to override the log level for a
    logger within a given scope/time frame.
    """
    __slots__ = ["_level", "expiration_date"]

    def __init__(self, level, expiration_date=None):
        """
        :param level: The log level to use in the override
        :type level: int
        :param expiration_date: The datetime that the override should expire. If this is None or not set then the
            override does not expire.
        :type expiration_date: datetime.datetime
        """
        self._level = level
        if expiration_date and not expiration_date.tzinfo:
            raise ValueError("'expiration_date' must be timezone aware")
        self.expiration_date = expiration_date

    def is_expired(self):
        """
        :return: whether or not the override has expired and is therefore no longer valid.
        :rtype: bool
        """
        if self.expiration_date:
            now = utcnow()
            return now > self.expiration_date
        return False

    @property
    def level(self):
        """
        :return: The logging level assigned to the override
        :rtype: int
        """
        if self.is_expired():
            return logging.NOTSET
        return self._level

    def _cmpkey(self):
        """Logging constants are in reverse order, i.e. 10-Debug, 20-info, etc. Do some basic math to make this work
        with Comparable ordering mixin.

        Comparisons, such as "greater than", for a Level Override is determined not by level but by which is most
        specific and valid.  For instance a level override which is not expired will always be greater than one which
        is expired and an override with a lower log level will be greater than one with a bigger level because a lower
        level has higher override precedence than a higher log level since it is more permissive
        (e.g. Someone who wants "DEBUG" level wins over someone who wants "INFO" level).
        """
        # A level of NOTSET is ignored and the operand is disqualified from comparisons unless both are NOTSET in which
        # case they are considered equal
        base_level = self.level
        if base_level is logging.NOTSET:
            return -100
        else:
            return -1 * base_level


class LogLevelProvider(object):
    """Class which provides configuration of log levels for loggers
    """
    #: datetime of the last time this provider's config was updated
    last_update = None

    #: Dict of (str, LevelOverride)
    _overrides = {}

    _modification_lock = None

    #: Dirty bit on the provider
    _is_dirty = False

    def __init__(self):
        self._overrides = {}
        self.last_update = utcnow()
        self._modification_lock = threading.Lock()

    def get_overrides(self):
        """
        :return: The current log level overrides that this config provider declares.  This should be a dict where the
            key is the logger name and the value is the log level to set to the logger.
        :rtype: dict of (str, LevelOverride)
        """
        if self._is_update_available():
            self._is_dirty = False
            self._overrides = self._get_updated_config()
            self.last_update = utcnow()
        return self._overrides

    def is_overridden(self, logger_name):
        """Returns whether or not the logging level has been overridden for logger `logger_name` through this manager

        :param logger_name: The name of the logger to determine if it is overridden or not through this provider
        :type logger_name: str
        :return: Whether or not the logging level has been overridden for logger `logger_name` through this manager
        :rtype: bool
        """
        return self._get_override(self.get_overrides(), logger_name) is not None

    def get_log_level(self, logger_name, only_overriden=False):
        """Returns the log level for the requested logger `logger_name`.  Note that this is not the effective level
        but instead is the log level assigned to the requested logger through this configuration.  If the level is
        not overridden then this will return the level that is assigned to the actual underlying logger.

        :param logger_name: The name of the logger to get the log level for.
        :type logger_name: str
        :param only_overriden: Whether or not to only return the log level if it is overridden.  If this is True than
            if the log level for the requested logger is not overridden then log level NOTSET will be returned.
        :type only_overriden: bool
        :return: The log level for the requested logger.
        :rtype: int
        """
        override = self._get_override(self.get_overrides(), logger_name)
        if override:
            return override.level
        if only_overriden:
            return logging.NOTSET
        logger = logging.getLogger(logger_name)
        return logger.level

    def get_original_log_level(self, logger_name):  # pylint: disable=no-self-use
        """Returns the original log level that was set to `logger_name` before any overrides, whether or not an
        override ever occurred for the logger.

        :param logger_name: THe name of the logger to get the original log level for
        :type logger_name: str
        :return: The original log level for the requested logger
        :rtype: int
        """
        logger = logging.getLogger(logger_name)
        try:
            return logger.configured_level  # pylint: disable=maybe-no-member
        except AttributeError:
            return logger.level

    def _get_override(self, overrides, logger_name):
        """Returns any override for the requested logger for the provided `overrides`, or None if one does not exist.
        This method performs any necessary validation of the override to determine if it is valid for the requested
        logger.

        :param overrides: The overrides dict to use to lookup the logger_name
        :type overrides: dict of (str, LevelOverride)
        :param logger_name: The name of the logger to get the override for
        :type logger_name: str
        :return: A valid LevelOverride for the requested logger that is available within `overrides`
        :rtype: LevelOverride or None
        """
        try:
            override = overrides[logger_name]
        except (TypeError, KeyError):
            return None

        return override if self._is_valid_override(override) else None

    def _is_valid_override(self, override):  # pylint: disable=no-self-use
        """Returns whether or not the provided `override` is valid or not

        :param override: A LevelOverride to validate
        :type override: LevelOverride
        :return: Whether or not the provided `override` is valid or not
        :rtype: bool
        """
        if not override:
            return False

        return not override.is_expired()

    def _is_update_available(self):
        """
        :return: Whether or not there is a log level update available
        :rtype: bool
        """
        return self._is_dirty

    def _get_updated_config(self):
        """Internal method which refreshes the log level overrides via whatever provider mechanism

        :rtype: dict of (str, LevelOverride)
        """
        return self._overrides


ProviderMetaData = namedtuple("ProviderMetaData", ["last_update_datetime"])


class LogLevelProviderCollection(LogLevelProvider):
    """LogLevelProvider which exposes a collection of log level providers as a single provider such that it is made
    up of the union of all of the log levels of the contained providers.
    """
    #: Dict of `ProviderMetaData' objects the key is a hashable provider instance and value is a ProviderMetaData:
    providers = {}

    def __init__(self, *providers):
        self.providers = {}
        """ :type : dict of (LogLevelProvider, ProviderMetaData) """
        self.add_providers(*providers)
        super(LogLevelProviderCollection, self).__init__()

    def add_providers(self, *providers):
        """Adds providers to the collection to be used in determining the overrides of the overall collection

        :param providers: Providers to add to the collection
        :type providers: Iterable of LogLevelProvider
        """
        if providers:
            for provider in providers:
                self.providers[provider] = ProviderMetaData(None)
            self._is_dirty = True

    def remove_providers(self):
        """Removes all providers assigned to this collection
        """
        self.providers = {}
        self._is_dirty = True

    def remove_provider(self, provider):
        """Removes a provider which was registered with this collection

        :param provider: The provider to remove from this collection
        :type provider: LogLevelProvider
        """
        try:
            del self.providers[provider]
            self._is_dirty = True
        except KeyError:
            pass

    def _is_provider_update_avail(self, provider):
        """
        :type provider: LogLevelProvider
        """
        # pylint: disable=protected-access
        if provider._is_update_available():
            return True
        last_known_update = self.providers[provider].last_update_datetime
        return bool(not last_known_update or last_known_update < provider.last_update)

    def _is_update_available(self):
        if super(LogLevelProviderCollection, self)._is_update_available():
            return True

        return any((self._is_provider_update_avail(provider) for provider in self.providers))

    def _get_updated_config(self):
        overrides = {}
        for provider in self.providers:
            prov_overrides = provider.get_overrides()
            self._refresh_last_update_datetime(provider)
            if not prov_overrides:
                continue
            for logger_name, override in prov_overrides.items():
                if logger_name not in overrides or override > overrides[logger_name]:
                    overrides[logger_name] = override

        return overrides

    def _refresh_last_update_datetime(self, provider):
        """Updates the last_update_datetime for a provider that we are maintaining within this collection

        :type provider: LogLevelProvider
        """
        # pylint: disable=protected-access
        self.providers[provider] = self.providers[provider]._replace(last_update_datetime=utcnow())


class InMemoryLogLevelProvider(LogLevelProvider):
    """A log level provider which is maintained completely in memory and is therefore read/write
    """

    def __init__(self, initial_overrides=None):
        super(InMemoryLogLevelProvider, self).__init__()
        if initial_overrides:
            self.apply_overrides(initial_overrides)

    def remove_all_overrides(self):
        """Removes all applied overrides
        """
        self.remove_overrides(list(self._overrides.keys()))
        LOG.debug("All overrides removed")

    def remove_overrides(self, *logger_names):
        """Removes applied log level overrides that have been set for the provided `logger_names`.  If no override has
        occurred for a requested logger than this is a no-op

        :param logger_names: The logger names of the loggers to remove any overrides from
        :type logger_names:
        :return:
        :rtype:
        """
        change_made = False
        try:
            self._modification_lock.acquire(True)

            # Make a local copy for thread safety
            local_overrides = dict(self.get_overrides())
            for logger_name in logger_names:
                if logger_name not in local_overrides:
                    continue
                override_details = local_overrides[logger_name]
                del local_overrides[logger_name]
                change_made = True
                logger = logging.getLogger(logger_name)
                LOG.debug("Removed level override of %s to return to level %s for logger %s",
                          logging.getLevelName(override_details.level), logging.getLevelName(logger.level), logger_name)

            self._overrides = local_overrides
            if change_made:
                self._is_dirty = True
        finally:
            self._modification_lock.release()

    def apply_overrides(self, overrides_dict, expiration_date=NOTSET):
        """Applies log level overrides which are specified via `overrides_dict`

        :param overrides_dict: A set of logger names and the log level to use to override the respective loggers.  The
            key of the dictionary is the full logger name and the value is the log level to use for the logger
        :type overrides_dict: dict of (str, LevelOverride) or dict of (str, int)
        :param expiration_date: The datetime that the provided overrides expire.  If this is None, then there is no
            expiration for the override.  Any expiration dates's specified for a specific logger within
            `overrides_dict` will supercede this value.
        """
        change_made = False
        try:
            self._modification_lock.acquire()
            current_overrides = self.get_overrides()
            new_overrides = {}
            for logger_name, level_override in overrides_dict.items():
                if isinstance(level_override, int):
                    # Convert a raw level to a LevelOverride as a convenience
                    level_override = LevelOverride(level_override)
                current_override = self._get_override(current_overrides, logger_name)
                if self._is_valid_override(current_override) and level_override.level == current_override.level:
                    continue  # Nothing new
                new_overrides[logger_name] = level_override

            for logger_name, level_override in new_overrides.items():
                if level_override.expiration_date is NOTSET:
                    level_override.expiration_date = expiration_date

                self._overrides[logger_name] = level_override
                change_made = True
                LOG.debug("Overriding logger %s with level %s", logger_name, logging.getLevelName(level_override.level))
        finally:
            if change_made:
                self._is_dirty = True
            self._modification_lock.release()


class LoggingLevelManager(LogLevelProviderCollection):
    """Manager which aggregates all of the LogLevelProviders within a system and provides a single interface for
    retrieving log levels from which could be dynamically derived based on the applied providers
    """
    PROVIDER_CLASSES_CONF_KEY = "LOGGING_LEVEL_MANAGER_PROVIDER_CLASSES"

    @classmethod
    def from_config(cls, conf):
        """Creates a new LoggingLevelManager from a config instance

        :param conf: The configuration to pull configuration from for creation of the logging level manager
        :type conf: generic_utils.config.Config
        :return: A new LoggingLevelManager created based on the configuration provided within the current config
        :rtype: LoggingLevelManager
        """
        new_self = cls()
        provider_classes = conf.get_conf_value(cls.PROVIDER_CLASSES_CONF_KEY, None)
        if provider_classes:
            prov_instances = [get_instance_from_fqn(prov_classname) for prov_classname in as_iterable(provider_classes)]
            new_self.add_providers(*prov_instances)
        return new_self


#: Singleton logging level manager to use for retrieval of logging level overrides
logging_level_manager = LoggingLevelManager.from_config(config)  # pylint: disable=invalid-name
