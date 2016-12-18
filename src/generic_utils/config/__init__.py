"""
Generic configuration interface and module which allows for exposing environment/application configuration through a
generic uniformly available interface
"""
import inspect

import os
import importlib
from generic_utils import loggingtools, NOTSET
import ast
from generic_utils.base_utils import ImmutableMixin, ImmutableDelay
from generic_utils.classtools import get_classfqn
from generic_utils.contextlib_ex import ContextDecorator, ExplicitContextDecorator
from ..typetools import is_iterable, parse_bool

log = loggingtools.getLogger()


def get_config_value(property_name, default=None, secure=False, val_type=None):
    """
    Returns the value for the provided configuration property if it is defined through the available configuration
    systems otherwise `default` is returned.
    :param property_name: The name of the configuration property to retrieve.
    :param default: The default value to return if the configuration property is not available
    :param secure: Whether or not the property is considered a secure property and thus the value should be protected
                    when logging or any other type of reporting.
    :param val_type: The data type to cast the value to.  This can be a single value or an iterable of types to attempt
                        to cast the value to in the order they are provided.  If this is not provided and a value is
                        provided for `default` then the type of that value will be used.
    :return: The value of the configuration property `property_name`.
    """
    # pylint: disable=too-many-branches
    if property_name in os.environ:
        val = os.environ[property_name]
        location = "ENVIRONMENT"
    else:
        val = default
        location = "DEFAULT"

    if val_type is None and default is not None:
        target_type = type(default)
        log.debug("Assuming target type to be %s", target_type)
        val_type = [target_type]

    if not is_iterable(val_type):
        val_type = [val_type]
    # pylint: disable=too-many-nested-blocks
    for cast_option in val_type:
        try:
            if not isinstance(val, cast_option):
                if cast_option is dict:
                    val = ast.literal_eval(val)
                elif cast_option is tuple or cast_option is list:
                    if isinstance(val, basestring):
                        val = val.strip()
                    if val:
                        if isinstance(val, basestring):
                            val = val.split(",")
                            val = [item.strip() for item in val]
                    else:
                        val = []

                    if cast_option is tuple:
                        val = tuple(val)  # pylint: disable=redefined-variable-type
                elif cast_option is bool and isinstance(val, basestring):
                    val = parse_bool(val)
                else:
                    val = cast_option(val)

            if isinstance(val, cast_option):
                break
        except (TypeError, ValueError):
            pass
        log.debug("Could not cast value '%s' to type %s", "*********" if secure else val, cast_option)

    log.info("loaded '%s' from %s; value = '%s' and is type %s",
             property_name, location, "*********" if secure else val, type(val))
    return val


class ConfigKeyError(KeyError):
    """Exception which is raised if a requested config key does not exist for a given Config
    """
    missing_key = None
    config = None
    message = "Key {missing_key} does not exist within config {config_name}"

    def __init__(self, config_obj, missing_key):
        self.missing_key = missing_key
        self.config = config_obj
        message = self.message.format(missing_key=missing_key, config_name=config_obj.name)
        super(ConfigKeyError, self).__init__(message)


class Config(object):
    """Generic interface for retrieving configuration from
    """
    _config_dict = {}
    _config_providers = []

    #: The name assigned to this config object for logging and other display purposes
    _name = None

    def __init__(self, name=None, initial_config=None, *providers):
        self._name = name
        self._config_dict = dict(initial_config) if initial_config else {}
        self._config_providers = []
        for provider in providers:
            self.add_provider(provider)
        super(Config, self).__init__()

    def add_provider(self, provider):
        """Adds a config provider to the current config object to provide additional sources of config information

        :param provider: The provider to add to the current config
        :type provider: Config
        """
        log.info("Config provider %s added to Config %s", provider.name, self.name)
        self._config_providers.append(provider)

    def get_conf_value(self, key, default_value=NOTSET, value_type_func=None):
        """Retrieves the requested config `key` from the configuration

        :param key: The configuration value to retrieve
        :type key: str
        :param default_value: The default value to return if the provided key doesn't exist.  If this is not set
          and the requested key does not exist then a `ConfigKeyError` is raised
        :type default_value: value_type
        :param value_type_func: Function which will convert the underlying raw config value to the expected type for the
            requested config value.
        :type value_type_func: func
        :return: The request config value, or KeyError if it does not exist
        :raises: ConfigKeyError
        """
        # Currently do not support nested keys (e.g. "a.b.c")
        try:
            return_val = self._get_raw_value(key)
        except ConfigKeyError:
            if default_value is not NOTSET:
                log.debug("Config value for key %s not found.  Using default value", key)
                return_val = default_value
            else:
                raise ConfigKeyError(self, key)

        if value_type_func:
            return_val = value_type_func(return_val)
        return return_val

    @property
    def name(self):
        """
        :return: The name for this config which is suitable for display/identification
        :rtype: str
        """
        return self._name if self._name else get_classfqn(self)

    @property
    def is_readonly(self):  # pylint: disable=no-self-use
        """
        :return: Whether or not this configuration is readonly or not
        :rtype: bool
        """
        return False

    def __getitem__(self, item):
        return self.get_conf_value(item)

    def __setitem__(self, key, value):
        setattr(self, key, value)

    def __setattr__(self, key, value):
        try:
            super(Config, self).__setattr__(key, value)
        except AttributeError:
            self._config_dict[key] = value

    def __getattr__(self, item):
        # First try and see if the attribute is explicitly defined on the class, otherwise pull from config
        try:
            return super(Config, self).__getattribute__(item)
        except AttributeError:
            pass

        try:
            return self.get_conf_value(item)
        except KeyError:
            raise ConfigKeyError(self, item)

    def __contains__(self, item):
        if item in self._config_dict:
            return True

        for provider in self._config_providers:
            if item in provider:
                return True

        return False

    def _get_raw_value(self, key):
        """Return the raw config value for `key`.  If `key` does not exist than `ConfigKeyError` is raised

        :param key: The config key to get the raw value for
        :type key: str
        :return: The requested raw config value
        """
        return_val = NOTSET
        try:
            return_val = self._config_dict[key]
            log.debug("Found config value %s in current provider", key)
        except KeyError:
            for provider in self._config_providers:
                try:
                    return_val = provider[key]
                    log.debug("Found config value %s in child provider %s", key, str(provider))
                    break
                except KeyError:
                    pass
        if return_val is NOTSET:
            raise ConfigKeyError(self, key)
        return return_val


class ReadOnlyConfig(ImmutableMixin, Config):
    """Subclass of Config which is read-only and once created no values of the configuration can be changed
    """

    def __init__(self, name=None, initial_config=None, *providers):
        # Delay immutablility until our supers are created since they didn't sign up for this immutability stuff
        with ImmutableDelay():
            super(ReadOnlyConfig, self).__init__(name, initial_config, *providers)

    @property
    def is_readonly(self):
        """
        :return: Whether or not this configuration is readonly or not
        :rtype: bool
        """
        return True


class PythonModuleConfig(ReadOnlyConfig):
    """Config backed by a python module
    """

    NAME_FORMAT = "Python Module {module_fqn} Config"

    _module = None
    _module_fqn = None

    def __init__(self, module_fqn):
        """
        :param module_fqn: Either a module or a string which is the fqn to a module within the python path that should
            provide attributes that are exposed as config values through this config instance
        """
        self._module_fqn = module_fqn
        if not inspect.ismodule(self._module_fqn):
            self._module = importlib.import_module(self._module_fqn)
        else:
            self._module = self._module_fqn
            self._module_fqn = "{package}.{module_name}".format(package=self._module.__package__,
                                                                module_name=self._module.__name__)
        super(PythonModuleConfig, self).__init__(name=self.NAME_FORMAT.format(module_fqn=self._module_fqn))

    def get_conf_value(self, key):  # pylint: disable=arguments-differ
        try:
            return getattr(self._module, key)
        except AttributeError:
            raise ConfigKeyError(self, key)



# The global configuration instance for the environment
config = Config()  # pylint: disable=invalid-name


__all__ = ['config']
