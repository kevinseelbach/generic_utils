"""Tests for generic_utils.hashlib_tools
"""
# future/compat
import six

# stdlib
import hashlib
import os
import unittest

from generic_utils.hashlib_tools import get_chunked_hash


class HashlibToolsTestCase(unittest.TestCase):
    """TestCase for HashlibTools"""

    def test_get_chunked_hash(self):
        """Validate get_chunked_hash works as expected
        """
        # noinspection PyCallingNonCallable
        test_output = six.StringIO()
        # An odd number of bytes to validate that the result hashes the remainder of len(data) /chunk_size
        test_data = os.urandom(150000)
        # Hack for Python 3, StringIO expects string not bytes
        if not six.PY2:
            test_data = six.text_type(test_data)

        test_output.write(test_data)
        hasher = hashlib.sha256()
        test_data_encoded = test_data

        if not six.PY2:
            test_data_encoded = test_data_encoded.encode('utf-8')

        hasher.update(test_data_encoded)
        expected_hash = hasher.hexdigest()
        actual_hash = get_chunked_hash(test_output)
        self.assertEqual(expected_hash, actual_hash)
