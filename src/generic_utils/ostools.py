import os
from generic_utils import loggingtools
from contextlib import contextmanager

log = loggingtools.getLogger(__name__)


@contextmanager
def environment_var(key, val):
    """
    Context manager which sets the value of an environment variable within the context and restores it when the context
    is complete.

    This currently does not yield anything.

    :param key: The environment variable key to set
    :param val: The value to set to the environment variable
    """
    try:
        old_val = os.environ[key]
    except KeyError:
        old_val = None

    log.debug("Setting environment variable '%s' to value '%s'", key, val)
    os.environ[key] = val
    try:
        yield
    finally:
        if old_val is None:
            del os.environ[key]
            log.debug("Removed environment variable '%s'", key)
        else:
            os.environ[key] = old_val
            log.debug("Reset environment variable '%s' back to '%s'", key, old_val)

