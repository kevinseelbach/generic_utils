"""Module which provides various utilities for wrapping and dealing with the Nose functionality
"""
from nose.plugins import attrib

from generic_utils.decorator_tools import decorator


def nose_attr_decorator(attr_key, attr_func=None, allow_multiple_values=True):
    """Method which generates a decorator which just specializes the nose Attr decorator.  The returned decorator from
    this function can be used to decorate test methods which the appropriate speciailized nose attrib based on the
     provided parameters

    :param attr_key: The key to use for any Attributes set via the decorator generated from this method.
    :param attr_func: If this is provided, then it is a func which takes *args and **kwargs to determine the value to
        be set to the named attribute when the generated decorator is invoked.  If this is not provided then the values
        provided in *args are used.
    :param allow_multiple_values: Whether or not to allow the attribute to have multiple values for the same key.  If
        this is `True`, then if multiple instances of the returned decorator are used on the same method then all
        values will be set to the attribute.  If this is `False` then only the one that is set first will be used.
        The default is `True`.
    :return: A func which is a generated decorator which acts as a specialized nose attrib decorator with pre-filled
        values.
    """
    @decorator
    def wrapper(func, *args, **kwargs):
        """Decorator wrapper method which decorates `func`"""
        if attr_func:
            values = attr_func(*args, **kwargs)
        else:
            values = args

        return get_attrib_decorated_func(func, attr_key,
                                         values=values,
                                         allow_multiple_values=allow_multiple_values)
    return wrapper


def get_attrib_decorated_func(func, attr_key, values=None, allow_multiple_values=True):
    """Returns a nose `attr` wrapped version of `func` as a helper for providing nose attr derived decorators more
    easily.

    :param func: The function to wrap with the nose `attr` decorator
    :param attr_key: The attr key to use for setting of attr values against the func
    :param values: The value(s) to set to the specified key.  This can be a single value or an iterable
    :param allow_multiple_values: Whether or not to allow the attribute to have multiple values for the same key.  If
        this is `True`, then if multiple instances of the returned decorator are used on the same method then all
        values will be set to the attribute.  If this is `False` then only the one that is set first will be used.
        The default is `True`.
    :return: A nose `attr` wrapped version of the provided `func`
    :rtype: func
    """
    current_values = attrib.get_method_attr(func, None, attr_key)

    if current_values and not allow_multiple_values:
        # Attribute is already set, so no need to further decorate
        return func
    final_values = list(values)

    if current_values:
        final_values.extend(list(current_values))

    attrs = {
        attr_key: tuple(final_values)
    }

    attr_wrapped = attrib.attr(**attrs)
    return attr_wrapped(func)


def specialize_attr_decorator(attr_decorator, *curried_args):
    """Helper method for generating a specialized attr_decorator pegged with specific values to be passed down to it
    to set for the attrib

    :param attr_decorator: The attr decorator to specialize
    :return: A decorator which is capable of being used with or without arguments which then applies the named category
        to the underlying decorated method
    """
    @decorator
    def _wrapper(func=None):
        """Decorator wrapper method which allows for being called with args (e.g. decorator() vs just decorator) or as
        an arg-less decorator"""
        return attr_decorator(*curried_args)(func)
    return _wrapper
