"""Functions to assist programming various things with classes."""
import inspect
from importlib import import_module

from . import loggingtools

LOG = loggingtools.getLogger()


def get_classfqn(obj):
    """
    Returns the fully qualified class name for the provided `obj`
    :param obj: Either a Class or an object instance that you want the fully qualified class name for
    :type obj: object|Class
    :return: The fully qualified class name for `obj`
    :rtype: str
    """
    if obj is None:
        raise ValueError("Must provide an object")

    if inspect.isclass(obj):
        clazz = obj
    else:
        clazz = obj.__class__

    return "%s.%s" % (clazz.__module__, clazz.__name__)


def get_class_from_fqn(class_fqn):
    """Attempts to import a class based on the input classname string.
        If the class is not importable, raises ImportError.

        The FQN may be relative IF the caller is located within the same module as the FQN target (like Django FKs)

        WARNING: This is aliased below to `get_from_fqn` as it does not do anything special for classes and can
        be used currently to get any importable attribute from a fqn. If you change the internal logic to check types,
        make sure you implement `get_from_fqn` with the original functionality.

    :param class_fqn: a fully qualified class name
    :type class_fqn: str|unicode
    :return: the class
    :rtype: T
    :raises: ImportError
    """

    try:
        mod_name, class_name = class_fqn.rsplit('.', 1)
        LOG.debug("Mod name = %s , class_name = %s", mod_name, class_name)
        if not mod_name:
            raise ValueError("Mod name must be blank string for a relative import with dot prefix, "
                             "falling through to inspect block.")
    except ValueError:
        current_stack = inspect.stack()
        frm = current_stack[1]
        mod = inspect.getmodule(frm[0])
        mod_name = mod.__name__
        class_name = class_fqn[1:] if class_fqn.startswith('.') else class_fqn
        LOG.debug("Attempting to get_class_from_fqn using inspected module %s cls=%s", mod.__name__, class_name)
    module_ = import_module(mod_name)
    return getattr(module_, class_name)

get_from_fqn = get_class_from_fqn  # pylint: disable=invalid-name


def get_instance_from_fqn(class_fqn, *args, **kwargs):
    """Given a fqn, get a class and return a new instance.
       class_fqn should be importable path to the class.
    :param class_fqn: fully qualified class name / import path.
    :type class_fqn: str|unicode
    :param args: any args that should be passed into the class at __init__
    :type args:
    :param kwargs: any kwargs that should be passed into class at __init__
    :type kwargs:
    :return: the instance
    :rtype: object
    :raises: ImportError
    """
    clazz = get_class_from_fqn(class_fqn)
    return clazz(*args, **kwargs)

def get_class_attributes(clazz, include_base_attrs=True, include_private=False):
    """Retrieves a dict which contains all of the class attributes of `clazz` as the key in the dict and the current
    value of the attribute as the value in the dict.

    This only retrieves value attributes and not functions or properties since those are only useful for a class
    instance.

    :param clazz: The class to retrieve the attributes for
    :type clazz: type
    :param include_base_attrs: Whether or not to include the attributes of any base class.
    :type include_base_attrs: bool
    :param include_private: Whether or not to include private attributes (e.g. leading with "_")
    :type include_private: bool
    :return: A dict which contains all of the attributes and values of the provided class with the key as the name of
        the attribute and the value containing the current value of the attribute for the class.
    :rtype: dict of (str, ?)
    """
    return_dict = {}

    def _is_private(attr_name):
        """Whether or not attr_name is a private named attribute based on the defined criteria of "private"
        :rtype: bool
        """
        if not include_private and attr_name.startswith("_"):
            return True
        elif attr_name.startswith("__"):
            return True
        return False

    # Process the class hierarchy in reverse mro order so that the final attribute values reflect how they would be
    # resolved if actually requested.
    mro_list = reversed(inspect.getmro(clazz)) if include_base_attrs else (clazz,)
    LOG.debug("Retrieving class attributes for class %r using mro %r", clazz, mro_list)
    for mro_clazz in mro_list:
        # Exclude functions/methods as well as properties(aka getsetdescriptors/datadescriptors) since props require
        # a class instance
        clazz_atrs = inspect.getmembers(mro_clazz,
                                        lambda x: not (inspect.isroutine(x) or
                                                       inspect.isgetsetdescriptor(x) or
                                                       inspect.isdatadescriptor(x)))

        for attr_name, obj in clazz_atrs:
            if _is_private(attr_name):
                continue
            return_dict[attr_name] = obj

    return return_dict


class cached_property(object):  # pylint: disable=invalid-name
    """Property descriptor that caches the return value
    of the get function.

    *Examples*

    .. code-block:: python

        @cached_property
        def connection(self):
            return Connection()

        @connection.setter  # Prepares stored value
        def connection(self, value):
            if value is None:
                raise TypeError('Connection must be a connection')
            return value

        @connection.deleter
        def connection(self, value):
            # Additional action to do at del(self.attr)
            if value is not None:
                print('Connection {0!r} deleted'.format(value)


    ***NOTE***
    This is pulled from kombu version 3.0.24 with a new BSD license from module kombu.utils.cached_property
    """

    def __init__(self, fget=None, fset=None, fdel=None, doc=None):
        self.__get = fget
        self.__set = fset
        self.__del = fdel
        self.__doc__ = doc or fget.__doc__
        self.__name__ = fget.__name__
        self.__module__ = fget.__module__

    def __get__(self, obj, _type=None):
        if obj is None:
            return self
        try:
            return obj.__dict__[self.__name__]
        except KeyError:
            value = obj.__dict__[self.__name__] = self.__get(obj)
            return value

    def __set__(self, obj, value):
        if obj is None:
            return self
        if self.__set is not None:
            value = self.__set(obj, value)
        obj.__dict__[self.__name__] = value

    def __delete__(self, obj):
        if obj is None:
            return self
        try:
            value = obj.__dict__.pop(self.__name__)
        except KeyError:
            pass
        else:
            if self.__del is not None:
                self.__del(obj, value)

    def setter(self, fset):  # pylint: disable=missing-docstring
        return self.__class__(self.__get, fset, self.__del)

    def deleter(self, fdel):  # pylint: disable=missing-docstring
        return self.__class__(self.__get, self.__set, fdel)
