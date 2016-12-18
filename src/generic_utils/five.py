"""Additional 2/3 compatibility helpers"""
import six
import codecs


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
else:
    def bytes_if_py2(val):
        """Convert str to bytes if running under Python 2."""
        return val

    def u(x):
        return x

    def b(x):
        return codecs.latin_1_encode(x)[0]

