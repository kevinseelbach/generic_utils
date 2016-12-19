"""Tests for generic_utils.test.mock.tools"""
# stdlib
from functools import reduce
from unittest import TestCase

import mock
from mock import patch

from generic_utils import loggingtools
from generic_utils.test.mock.tools import patch_urlopen_with_file
from generic_utils.test.mock.tools import spy_object

try:
    import urllib.request
    urllib2 = urllib.request
except ImportError:     # python 2
    import urllib2



LOG = loggingtools.getLogger()


class MyTestObject(object):

    def __init__(self, propa, propb, *args, **kwargs):
        self.propa = propa
        self.propb = propb
        self.args = args
        self.kwargs = kwargs

    def add(self, *args):
        operands = [self.propa, self.propb]
        operands.extend(args)
        return reduce(lambda a, b: a + b, operands)

    @property
    def propc(self):
        return self.propa + self.propb


class SpyObjectTestCase(TestCase):
    def test_init_spying(self):
        with spy_object(MyTestObject, "__init__") as init_spy:
            instance = MyTestObject(1, 2, 3, some_kwarg="bleh")
            init_spy.assert_called_with(instance, 1, 2, 3, some_kwarg="bleh")
            self.assertTrue(isinstance(instance, MyTestObject))
            self.assertEqual(instance.propa, 1)
            self.assertEqual(instance.propb, 2)
            self.assertEqual(instance.args, (3,))
            self.assertEqual(instance.kwargs, {"some_kwarg": "bleh"})

    def test_method_spying(self):
        with spy_object(MyTestObject, "add") as add_spy:
            instance = MyTestObject(1, 2)
            self.assertEqual(instance.add(3, 4), 1 + 2 + 3 + 4)
            add_spy.assert_called_with(instance, 3, 4)

    def test_spy_with_cbs(self):
        """Validates that if a callback is provided to a spy that it is invoked as expected
        """
        ADD_ARGS = (3, 4)
        EXPECTED_RESULT = 1 + 2 + 3 + 4

        cb_param_dict = {}
        cb_post_param_dict = {}

        def cb_add(self, *args):
            cb_param_dict["self"] = self
            cb_param_dict["args"] = args

        def cb_post_add(return_val, args, kwargs):
            cb_post_param_dict["return_val"] = return_val
            cb_post_param_dict["args"] = args
            cb_post_param_dict["kwargs"] = kwargs

        with spy_object(MyTestObject, "add", cb_func=cb_add, cb_post_func=cb_post_add) as add_spy:
            instance = MyTestObject(1, 2)
            # Validate that even with the callback in place, the underlying spied object does its job
            self.assertEqual(instance.add(*ADD_ARGS), EXPECTED_RESULT)
            add_spy.assert_called_with(instance, *ADD_ARGS)

        # Validate that our cb method was invoked as expected
        self.assertEqual(cb_param_dict["self"], instance)
        self.assertEqual(cb_param_dict["args"], ADD_ARGS)

        # Validate that our post cb method was invoked as expected
        self.assertEqual(cb_post_param_dict["return_val"], EXPECTED_RESULT)
        self.assertEqual(cb_post_param_dict["args"], tuple([instance] + list(ADD_ARGS)))
        self.assertEqual(cb_post_param_dict["kwargs"], {})

    def test_property_spying(self):
        # Not currently supporting property spying as there are some subtleties that need to be worked out.  Waiting for
        # a real need on this
        with self.assertRaises(NotImplementedError):
            with spy_object(MyTestObject, "propc") as propc_spy:
                instance = MyTestObject(1, 2)
                self.assertEqual(instance.propc, 1 + 2)
                propc_spy.assert_called_with()


class PatchUrlopenWithFileTestCase(TestCase):
    """Tests for PatchUrlopenWithFile context manager."""
    test_file_content = "this is a test."

    def test_patch_urlopen_with_file(self):
        """Validate that using the patch_urlopen_with_file context manager works as expected
        """
        with patch('io.open', mock.mock_open(read_data=self.test_file_content), create=True) as mocked_open:
            with patch_urlopen_with_file("dummy_filename"):
                LOG.debug("urlopen={0}.{1}".format(urllib2.urlopen.__module__, urllib2.urlopen.func_name))
                response = urllib2.urlopen("http://example.com")
                self.assertEqual(response.read(), self.test_file_content)
                mocked_open.assert_called_with("dummy_filename", "r")
