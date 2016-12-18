"""Utility library for python based applications which provides common utilities, libraries, etc for making
writing python programs a bit easier.
"""
# from generic_utils.debug_utils import enable_thread_dump_signal

# Const for using in default assignments for keyword args.  This is useful in cases where you want to assign a default
# value to a keyword arg which must be computed dynamically and None is a valid value for the argument.  For example:
# def my_func(cool_prop=NOTSET):
#   if cool_prop is NOTSET:
#     cool_prop = calculate_value()
NOTSET = "__NOTSET__"


def has_value(val):
    """Helper alias for checking whether or not a value actually has a value set or not when the variable leverages
    the `NOTSET` global above.  This prevents having to do checking of values with a double negative like:

    >>> if val is not NOTSET

    and instead you can write the following which is much easier to read and doesn't make your head explode:

    >>> if has_value(val)
    """
    return val is not NOTSET
