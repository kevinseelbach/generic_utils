"""Utilities for working with dictionaries
"""
from .typetools import is_iterable


def lower_keys(input_val, recursive=False):
    """Convert all keys in dict to lowercase.

    WARNING: This implementation assumes any dictionary keys are strings. Don't use this if the input value contains
        keys of any other type.
    :param input_val: Unknown input value , if it is a dict, convert keys to lowercase.
    :type input_val: T
    :param recursive: whether to also force any keys inside nested dictionaries to lowercase
    :type recursive: bool
    :return:
    :rtype:
    """
    if isinstance(input_val, dict):
        if recursive:
            return {key.lower(): lower_keys(value, recursive) for key, value in input_val.iteritems()}
        else:
            return {key.lower(): value for key, value in input_val.iteritems()}
    elif is_iterable(input_val):
        return [lower_keys(v, recursive) for v in input_val]
    else:
        return input_val
