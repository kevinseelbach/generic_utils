"""Settings required for driving the python utils test suite
"""
STATSD_CLIENT_TYPE = "TESTCASE"

# Just adding something in here to verify config exceptions are suppressed
SAFE_EXCEPTION_CLASSES = ["generic_utils.exceptions.GenUtilsValueError"]

try:
    from .local_settings import *
except ImportError:
    pass
