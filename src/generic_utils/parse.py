from __future__ import absolute_import
import collections


def split_by_size(s, size, return_remainder=False):
    """
    Splits by incremental indexes.
    So if indexes is [1,2,3] and s is 'abcdefg', the result will be a tuple ('a', 'bc', 'def', 'g')
    :param size: sizes to split on.
    :param return_remainder: True|False for whether or not to return the remainder string (could be '')
    :return: split tuple
    """
    if not isinstance(size, collections.Iterable):
        # if size is 2, [2, 4, 6, 8, 10...]
        non_iter_size = size
        size = [non_iter_size for i in range(len(s)/non_iter_size)]

    retval = ()
    for i in size:
        t = s[:i]
        s = s[i:]
        retval = retval + (t,)

    if return_remainder:
        retval = retval + (s,)

    return retval


def versiontuple(version_string):
    """Takes a string and attempts to return a tuple of the split version numbers
    :param version_string: Version e.g. '1.6.2'
    :type version_string: str.
    :raises: ValueError, TypeError
    :return: version tuple e.g. (1, 6, 2)
    :rtype: tuple
    """
    return tuple(map(int, (version_string.split("."))))