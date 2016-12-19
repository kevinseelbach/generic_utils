"""Core base exceptions as well as standard exceptions that are generally applicable
"""
from __future__ import absolute_import

from generic_utils.classtools import get_class_attributes


class GenUtilsException(Exception):
    """
    A base exception class which provides a few benefits over the core Exception:

    1> Message helpers
    2> A convenient way to catch exceptions raised by this library
    3> A base set of core exceptions

    In general when defining your own exception all you need to do is subclass this exception class or a subclass of
    it, define a special `message` class attribute with a message specific to your exception if needed, and then
    define any class attributes which should be assigned to an instance of your exception for either message generation
    or for more detail for a caller.  For instance:

    >>> class MyException(GenUtilsException):
    >>>     message = "This is my exception and your name is {name}"
    >>>     name = None
    >>>
    >>> my_exception = MyException(name="Ted")
    >>> assert my_exception.name == "Ted"
    >>> assert my_exception.message = "This is my exception and your name is Ted"

    """
    message = None

    def __init__(self, message=None, *args, **kwargs):
        self._set_kwargs(kwargs)
        self.message = self._format_message(message, args)
        super(GenUtilsException, self).__init__(self.message)

    def _format_message(self, message, args):
        """Formats the message of the exception
        """
        if message is None:
            if args:
                message = args[0]
            else:
                message = self.message

        # Get class defined attributes and values
        attrs = get_class_attributes(self.__class__, include_base_attrs=True, include_private=False)
        attrs.update(self.__dict__)
        return message.format(**attrs) if message else None

    def _set_kwargs(self, kwargs):
        """Sets the values of the kwargs of the init of the exception as attributes on the exception instance
        """
        for key, val in kwargs.items():
            try:
                if key.startswith("_"):
                    raise IllegalArgumentException("Illegal argument {argument_name}.  Cannot provide private "
                                                   "properties as kwargs", argument_name=key)
                attr_val = getattr(self, key)

                if callable(attr_val):
                    raise IllegalArgumentException("Illegal argument {argument_name}.  Cannot provide a kwarg that "
                                                   "is a method on the exception", argument_name=key)
            except AttributeError:
                raise IllegalArgumentException("Cannot provide kwarg '{argument_name}' that is not a declared "
                                               "property on the exception", argument_name=key)

            setattr(self, key, val)


class GenUtilsValueError(GenUtilsException, ValueError):
    """Base ValueError raised if a value is illegal or not allowed
    """
    value_name = None
    message = "Invalid value provided for {value_name}"


class GenUtilsTypeError(GenUtilsException, TypeError):
    """Base TypeError raised if a argument is of incorrect type."""
    message = "Received value of incorrect type={type_name} for argument={argument}"
    argument = None
    type_name = None


class GenUtilsAttributeError(GenUtilsException, AttributeError):
    """Base AttributeError raised if there was a problem accessing an attribute
    """
    attribute_name = None
    message = "Unable to access attribute {attribute_name}"


class GenUtilsKeyError(GenUtilsException, KeyError):
    """Base KeyError raised if there was a problem getting key from a dictionary"""
    message = "Unable to access value for key={key}"
    key = None


class GenUtilsRuntimeError(GenUtilsException, RuntimeError):
    """Base RuntimeError raised for reasons that don't fit into other exceptions."""
    message = "Errors during processing={errors}."
    errors = None


class GenUtilsIndexError(GenUtilsException, IndexError):
    """Base IndexError raised when a sequence is out of range"""
    message = "Unable to access index={index}."
    index = None


class IllegalArgumentException(GenUtilsValueError):
    """Raised if an argument provided to a method or class is not allowed
    """
    argument_name = None
    message = "The provided argument {argument_name} is not allowed"


class RequiredArgumentException(GenUtilsValueError):
    """Raised if an argument provided to a method or class is required and it is not provided
    """
    message = "The provided argument {argument_name} is required"
