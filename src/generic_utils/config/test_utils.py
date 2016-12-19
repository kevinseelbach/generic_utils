"""Utilities for dealing with config within tests
"""
from mock import patch

from generic_utils import loggingtools
from generic_utils.config import config
from generic_utils.contextlib_ex import ExplicitContextDecorator

LOG = loggingtools.getLogger()


class OverrideConfig(ExplicitContextDecorator):
    """Decorator/Context Manager which provides the ability to override the configuration during the scope of the
    decorator/context.
    """
    config_kwargs = None
    old_func = None
    patched_func = None

    def __init__(self, **config_kwargs):
        self.config_kwargs = config_kwargs

    def __enter__(self):
        def cb_get_raw_value_patch(key):
            """Implementation of _get_raw_value which returns the requested config from the provided overrided kwargs
            otherwise it falls back to the core underlying configuration
            """
            try:
                return_val = self.config_kwargs[key]
                LOG.debug("Config key '%s' was overridden", key)
                return return_val
            except KeyError:
                LOG.debug("Key '%s' not in overrided config so requesting from base config", key)
                return self.old_func(key)

        self.old_func = config._get_raw_value  # pylint: disable=protected-access

        self.patched_func = patch.object(config, "_get_raw_value", side_effect=cb_get_raw_value_patch)
        self.patched_func.start()

        super(OverrideConfig, self).__enter__()

    def __exit__(self, *exc_info):
        self.old_func = None
        self.patched_func.stop()
        self.patched_func = None
        super(OverrideConfig, self).__exit__(*exc_info)

#: Alias to a more common naming pattern for decorators/context managers
override_config = OverrideConfig  # pylint: disable=invalid-name
