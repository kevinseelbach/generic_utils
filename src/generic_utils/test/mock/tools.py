"""Tools for simplifying mocking of objects
"""
# stdlib
import io

from mock import patch

from generic_utils import loggingtools
from generic_utils.contextlib_ex import ContextDecorator
from generic_utils.contextlib_ex import ExplicitContextDecorator
from generic_utils.contextlib_ex import ExplicitContextManagerMixin

LOG = loggingtools.getLogger()

# future/compat
try:
    from urllib import request
    urlopen = request.urlopen
except ImportError:
    import urllib2
    urlopen = urllib2.urlopen


_URLOPEN_PATCH_TARGET = "{0}.urlopen".format(urlopen.__module__)


class SpyObjectResult(object):
    def __init__(self, result_value):
        self.result_value = result_value

    @property
    def value(self):
        return self.result_value


class SpyObject(ExplicitContextManagerMixin, ContextDecorator):
    """ContextManager/Decorator which simplifies using Mock objects to spy on the usage of an object without actually
    modifying the behavior.  For instance, you may want to validate that a method is called a certain number of times
    or with certain objects while still having the underlying method perform it's operations and then after the test is
    complete assert on the number of calls, etc.

    This is similar to the Mock patch.object method which takes an object instance and the name of a method to patch.

    The context manager yields a Mock object which wraps the target method and can be used to assert the call behavior
    on it.
    """
    target_obj = None
    target_method = None
    mock_kwargs = None
    cb_func = None
    cb_post_func = None
    _patched_object = None

    illegal_kwargs = {"autospec", "side_effect"}

    def __init__(self, obj, method_name, mock_kwargs=None, cb_func=None, cb_post_func=None):
        """
        :param obj: The object with a method that you wish to spy on.  This is similar to the
        :param method_name: The name of the method to spy on
        :param mock_kwargs: A dict which contains kwargs to pass on to the underlying patch.object method should you
            want to add additional mocking functionality.  You cannot provide values for the "autospec" or
            "side_effect" kwargs
        :param cb_func: An optional function to call whenever the spied method is called.  This function will be called
            before the spied method with the exact parameters of the spied method.  The return value of cb_func is
            ignored.
        :param cb_post_func: An optional function to call after the spied method is called.  This function will be
            called with the following args ::

                return_value - The value returned by the target method
                args - The vargs that were provided to the target method
                kwargs - The kwargs that were provided to the target method

            Any return value will be ignored.
        """
        self.target_obj = obj
        self.target_method = method_name
        self.mock_kwargs = mock_kwargs or {}
        self.cb_func = cb_func
        self.cb_post_func = cb_post_func
        self._patched_object = None
        for illegal_kwarg in self.illegal_kwargs:
            if illegal_kwarg in self.mock_kwargs:
                LOG.warn("Illegal kwarg %s provided as input to spy_object and it will be ignored", illegal_kwarg)
                del self.mock_kwargs[illegal_kwarg]

    def __enter__(self):
        wrapped_method = getattr(self.target_obj, self.target_method)
        if self.cb_func or self.cb_post_func:
            cb_func = self.cb_func
            cb_post_func = self.cb_post_func

            def cb_wedge(*args, **kwargs):
                """Function which wedges a call to the provided cb_func in front of the actual underlying method
                """
                if cb_func:
                    cb_func(*args, **kwargs)
                result = wrapped_method(*args, **kwargs)
                if cb_post_func:
                    new_result = cb_post_func(result, args, kwargs)
                    if isinstance(new_result, SpyObjectResult):
                        result = new_result.value
                return result
            side_effect = cb_wedge
        else:
            side_effect = wrapped_method
        is_property = isinstance(wrapped_method, property)
        mock_kwargs = self.mock_kwargs

        self._patched_object = patch.object(self.target_obj, self.target_method, autospec=True, **mock_kwargs)

        mocked_method = self._patched_object.start()
        if is_property:
            self._safe_debug_log("Spying on property %s of object %r", self.target_method, self.target_obj)
            mocked_method.__get__ = wrapped_method.__get__
            raise NotImplementedError("Property spying is not currently supported.")
        else:
            self._safe_debug_log("Spying on method %s of object %r", self.target_method, self.target_obj)
            mocked_method.side_effect = side_effect
        return mocked_method

    def __exit__(self, *exc_info):
        if self._patched_object:
            self._patched_object.stop()
            self._safe_debug_log("Spying stopped on method %s of object %s", self.target_method, self.target_obj)
            self._patched_object = None

    @staticmethod
    def _safe_debug_log(msg, *args):
        """Logs `msg` at debug level and if there is an exception related to formatting the data the log silently fails
        This is because some of the underlying formatted data may not have a proper str method and instead of complete
        failure for a debug log we just want to miss out on the log message.
        """
        try:
            LOG.debug(msg, *args)
        except (TypeError, AttributeError):
            # Some objects dont know how to str themselves, so no point in puking on a debug message
            pass

# alias to make it more friendly for consumers as a decorator/context manager
spy_object = SpyObject  # pylint: disable=invalid-name


class PatchFilelikeResponse(ExplicitContextDecorator):
    """Mock a function which expects a file-like response object, using a file's contents as the replacement."""
    patch_method = None
    open_file = None

    _patch_module = None
    _target_method = None
    _filename = None

    def __init__(self, filename, patch_module, target_method=None):
        """


        :param filename:
        :type filename: str
        :param patch_module:
        :type patch_module: module or str
        :param target_method:
        :type target_method:
        """
        self._filename = filename
        self._patch_module = patch_module
        self._target_method = target_method

    def __enter__(self):
        """Start patch."""
        LOG.debug("Patching urllopen with target patch=%r", self._patch_module)
        if isinstance(self._patch_module, str):
            self.patch_method = patch(self._patch_module)
        else:
            self.patch_method = patch.object(self._patch_module, self._target_method)

        self.open_file = io.open(self._filename, 'r')
        mock_method = self.patch_method.start()
        mock_method.return_value = self.open_file

    def __exit__(self, *exc_info):
        """Exit context manager, stop patch and close file."""
        try:
            if self.patch_method:
                self.patch_method.stop()
        finally:
            self.open_file.close()

patch_filelike_response = PatchFilelikeResponse  # pylint: disable=invalid-name


class PatchUrlopenWithFile(PatchFilelikeResponse):
    """Patch the response to urlopen with contents of a file."""

    def __init__(self, filename):
        """
        :param str filename: file to open and inject to urlopen response.
        """
        super(PatchUrlopenWithFile, self).__init__(filename, _URLOPEN_PATCH_TARGET, None)

patch_urlopen_with_file = PatchUrlopenWithFile  # pylint: disable=invalid-name
