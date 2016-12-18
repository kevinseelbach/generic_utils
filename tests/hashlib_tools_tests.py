"""Tests for generic_utils.hashlib_tools
"""
import hashlib
import os
from generic_utils.hashlib_tools import get_chunked_hash

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

from unittest import TestCase


class HashlibToolsTestCase(TestCase):
    """TestCase for HashlibTools"""

    def test_get_chunked_hash(self):
        """Validate get_chunked_hash works as expected
        """
        test_output = StringIO()
        # An odd number of bytes to validate that the result hashes the remainder of len(data) /chunk_size
        test_data = os.urandom(150000)
        test_output.write(test_data)
        hasher = hashlib.sha256()
        hasher.update(test_data)
        expected_hash = hasher.hexdigest()
        actual_hash = get_chunked_hash(test_output)
        self.assertEqual(expected_hash, actual_hash)
