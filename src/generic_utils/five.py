"""Additional 2/3 compatibility helpers"""
# future/compat
import six

# stdlib
import codecs
import functools
import unittest

if six.PY2:
    def bytes_if_py2(val):
        """Convert str to bytes if running under Python 2."""
        if isinstance(val, unicode):
            return val.encode()
        return val

    def b(x):
        return x

    def u(x):
        return codecs.unicode_escape_decode(x)[0]

    expectedFailure = unittest.expectedFailure
else:
    # Python > 2.7 imports
    from unittest.case import _AssertRaisesContext

    def bytes_if_py2(val):
        """Convert str to bytes if running under Python 2."""
        return val

    def u(x):
        return x

    def b(x):
        return codecs.latin_1_encode(x)[0]

    def expectedFailure(func):
        """Pythons > 2.7 implement expectedFailure by setting `func.__unittest_expecting_failure__ = True`
            re-implementing wrapper here to do the assertRaises() behavior
        """
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            context = _AssertRaisesContext(Exception, func)
            with context:
                func(*args, **kwargs)
        return wrapper
