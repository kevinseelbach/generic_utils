"""Various core python logging handlers
"""
from __future__ import absolute_import
# stdlib
import codecs
from logging import StreamHandler as py_StreamHandler
from logging import FileHandler
from logging import Formatter
from logging.handlers import RotatingFileHandler


class NoBufferingFileHandlerMixin(object):
    """Log File handler mixin which has file buffering turned off so that logs go immediately to disk
    """

    def _open(self):
        assert isinstance(self, FileHandler)
        if self.encoding is None:
            stream = open(self.baseFilename, self.mode, buffering=0)
        else:
            stream = codecs.open(self.baseFilename, self.mode, self.encoding, buffering=0)
        return stream


class NoBufferingRotatingFileHandler(NoBufferingFileHandlerMixin, RotatingFileHandler):
    """A RotatingFileHandler which does not buffer
    """
    pass


class NoBufferingFileHandler(NoBufferingFileHandlerMixin, FileHandler):
    """A FileHandler which does not buffer
    """
    pass


class StreamHandler(py_StreamHandler):
    """Log handler which formats log messages as unicode
    """
    def __init__(self):
        super(StreamHandler, self).__init__()
        # set the default formatter to use a unicode string
        self.setFormatter(Formatter(u"%s"))
