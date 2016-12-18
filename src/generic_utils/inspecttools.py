import inspect


def get_calling_frame():
    """Returns the frame of the caller of the caller of this method(AKA 2 frames up from this method, 1 frame up from
    the caller of this method)
    """
    stack = inspect.stack()
    return stack[2]


def get_frame_module(frame):
    """
    Returns the module for a frame

    :return:
    """
    return inspect.getmodule(frame)


def is_module_frame(frame):
    """
    Returns whether or not the provided `frame` represents code at the module level or not
    """
    return frame.f_code.co_name == "<module>"


def getmembers_ex(obj, predicate=None, handle_exceptions=True):
    """Similar to `inspect.getmembers` with the difference being that if `handle_exceptions` is True, then if getting
    a member of `obj` results in an exception then instead of completely failing this will return the exception as
    the value of the property which will allow for retrieval of all other members.

    Return all members of an obj as (name, value) pairs sorted by name.
    Optionally, only return members that satisfy a given predicate."""
    results = []
    for key in dir(obj):
        try:
            value = getattr(obj, key)
        except AttributeError:
            continue
        except Exception as exc:
            if not handle_exceptions:
                raise
            value = exc
        if not predicate or predicate(value):
            results.append((key, value))
    results.sort()
    return results


def get_function_arg_value(arg_name, func, args, kwargs):
    """Returns the value of a named function argument `arg_name` for function `func` given a set of varargs `args` and
        kwargs `kwargs` so that even if the value is passed into the function by position or by name this will return
        the value intended for `arg_name`.

        This is most useful for decorators which don't know the details of the function arguments and just want to
        operate on the set of function arguments generically.

        If the value could not be determined from the provided information then a `ValueError` is raised

    :param arg_name: The name of the argument to `func` which to return the value for whether or not it is provided as
        a named parameter or a positional argument.
    :type arg_name: str
    :param func: The function that the provided args and kwargs are specific invocation instances of for the function
    :type func: func
    :param args: A varargs for a specific invocation of `func` to use for determining the value of `arg_name` from
    :type args: []
    :param kwargs: A kwarg for a specific invocation of `func` to use for determining the value of `arg_name` from
    :type kwargs:
    :return: The value of the requested argument if it could be determined.
    :raises: ValueError
    """
    try:
        return kwargs[arg_name]
    except (KeyError, TypeError):
        funcargs = inspect.getargspec(func).args
        try:
            arg_idx = funcargs.index(arg_name)
            return args[arg_idx]
        except (ValueError, IndexError):
            raise ValueError("Value does not exist for arg '%s' for func %s with args %s and kwargs %s" %
                             (arg_name, func, args, kwargs))
