from __future__ import absolute_import

# future/compat
import six

# stdlib
import collections


def is_iterable(obj, exclude_string=True):
    """Returns whether or not the provided `obj` is iterable in the list sense and not in the string sense

    :param obj: The object to test for whether it is iterable or not
    :param exclude_string: Whether or not to exclude the string type as iterable.  The default is True.
    :return: Whether or not the provided `obj` is iterable
    :rtype: bool
    """
    if exclude_string and isinstance(obj, six.string_types):
        return False

    return isinstance(obj, collections.Iterable)


def as_iterable(obj, exclude_string=True, iter_type=list):
    """Returns `obj` as something that can be iterated over if it is not already iterable.  This is useful in
    scenarios such as instead of doing::

        x = "test"
        if not is_iterable(x):
            x = [x]
        for val in x:
            pass

    We can now do::

        for val in as_iterable(x):
            pass


    :param obj: The object to return as an iterable if it is not already iterable.  If this is None, then an empty
        iterable is returned.
    :param exclude_string: Whether or not to exclude the string type as iterable.  The default is True
    :param iter_type: If `obj` is not already iterable, then this is the iterable type to return with `obj` as an
        element.  This defaults to `list` and should be a type/function which can take a list of `obj` as a parameter
        and return an iterable.
    :return: Iterable representation of `obj`.
    """
    if obj is None:
        return iter_type()
    if is_iterable(obj, exclude_string):
        return obj
    return iter_type([obj])


def parse_bool(bool_str):
    """Parses a string `bool_str` and returns the bool interpretation of the string value.  This introspects the value
    of the string and if the value is interpretable as a `True` value then `True` is returned, else `False`.

    :param bool_str: A String to parse to determine if it represents a `True` or `False` bool value.
    :return: Bool interpretation of `bool_str`
    :rtype: bool
    """
    try:
        if bool_str and isinstance(bool_str, six.string_types):
            return bool_str.upper() in ["TRUE", "YES", "1", "T"]
    except TypeError:
        pass

    return False
