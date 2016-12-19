"""Tools for working with iterators"""
# future/compat
from builtins import next
from builtins import object
from builtins import range
from builtins import zip

# stdlib
from inspect import getmembers

from generic_utils import loggingtools
from generic_utils.exceptions import GenUtilsTypeError

LOG = loggingtools.getLogger()


class IteratorProxy(object):
    """A proxy object to support iterating over a set of data and applying transform function `transform_func`
        over each row of data, with enhanced support for continuing iteration over nested IteratorProxy objects.

    E.g. If you have a list of items which you wish to process and produce more than one item for each item in the
        top-level of data, you could do something like below. This is useful for processing level from databases which
        may have one or more related items for the uppermost level of data.

    >>> input_data = [1,10,20]
    >>> def _outer_transform(item):
    ...     items = [item, item + 1]
    ...     return IteratorProxy(items, lambda a: a + 1)
    ...
    >>> proxy = IteratorProxy(input_data, _outer_transform)
    >>> list(proxy)
    [2, 3, 11, 12, 21, 22]

    """
    _proxied_data = None
    _dataiterator_stack = None
    item_processor = None

    def __init__(self, data, item_processor=None):
        """
        :param data:
        :type data: collections.Iterable
        :param item_processor: An optional transform_func which will be applied to each row of `data` before yielding
          the row
        :type item_processor: callable | None
        """
        self._proxied_data = data
        if item_processor and not callable(item_processor):
            raise GenUtilsTypeError(type_name=type(item_processor), argument='item_processor')
        self.item_processor = item_processor

    def __iter__(self):
        """Set the dataiterator stack
        :return:
        :rtype:
        """
        LOG.debug("iter called on %r", self)
        self._dataiterator_stack = [iter(self._proxied_data)]
        return self

    def __next__(self):
        """
        :return:
        :rtype:
        """
        response = None

        while response is None:
            data_generator = self._dataiterator_stack[-1]
            try:
                response = next(data_generator)
                LOG.debug("Raw response = %r", response)
            except StopIteration:
                if len(self._dataiterator_stack) > 1:
                    self._dataiterator_stack.remove(data_generator)
                    LOG.debug("Removed %r from _dataiterator_stack", data_generator)
                    continue
                else:
                    LOG.debug("Raising StopIteration on %r", self)
                    raise

            if self.item_processor is not None and not isinstance(data_generator, IteratorProxy):
                # Do not call the transform on a response from an IteratorProxy
                response = self.item_processor(response)

            if isinstance(response, IteratorProxy):
                LOG.debug("Response is an IteratorProxy object, appending to DataIterator stack.")
                # Must call iter on the IteratorProxy object in order to set it up for calling next() method
                self._dataiterator_stack.append(iter(response))
                response = None

        return response


def reverse_enumerate(iterable):
    """
    The same as `enumerate` except in reverse order

    reverse_enumerate(iterable) -> iterator for index, value of iterable

    Return an enumerate object.  iterable must be another object that supports
    iteration.  The enumerate object yields pairs containing a count and a value yielded by the iterable argument.
    reverse_enumerate is useful for obtaining an indexed list in reverse order:
        (len(seq) - 1, seq[-1]), (len(seq) - 2, seq[-2]), (len(seq) - 3, seq[-3]), ...
    """
    return zip(range(len(iterable)-1, -1, -1), reversed(iterable))


def iiterex(iterable, callback=None, **kwargs):
    """
    Takes an iterable and allows the caller to short circuit or modify object details through the use of a general
      callback, or through declaritive attribute specific callbacks.
    :param iterable: The iterable object to be inspected.
    :param callback: Callback method for handling objects about to be yielded.  Callback must return True to
    yield the obj.
    :param kwargs: kwargs
    :return: iterable
    """
    for obj in iterable:
        do_yield = True
        if callback:
            if not callback(obj):
                continue

        declared_callbacks = [
            (kwargs["_".join([attr[0], 'callback'])], getattr(obj, attr[0]))
            for attr in getmembers(obj) if "_".join([attr[0], 'callback']) in kwargs
        ]

        for func, o in declared_callbacks:
            if not func(o):
                do_yield = False
                continue

        if do_yield:
            yield obj


def ibatch(iterable, chunk_size=1):
    """
    Takes an iterable and yields individuals while chunking for performance.
    :param iterable: The iterable object to be chunked.
    :param chunk_size: Number of items to chunk before yielding individuals.
    :return: iterable
    """
    chunk_count = 0
    while 1:
        start = chunk_size * chunk_count
        data = iterable[start:start + chunk_size]
        try:
            for i in range(chunk_size):
                yield data[i]
        except IndexError:
            return
        chunk_count += 1
        #     do_yield = True
        #     obj = data[i]
        #     if callback:
        #         if not callback(obj):
        #             continue
        #
        #     declared_callbacks = [
        #         (kwargs["_".join([attr[0], 'callback'])], getattr(obj, attr[0]))
        #         for attr in getmembers(obj) if "_".join([attr[0], 'callback']) in kwargs]
        #
        #     for func, o in declared_callbacks:
        #         if not func(o):
        #             do_yield = False
        #             continue
        #
        #     if do_yield:
        #         yield obj


def first_non_none(*arg):
    """
    :param arg: A list of arguments.
    :return: Returns the first non-None value in the given arguments or None if no non-None arguments are given.
    """
    return next((x for x in arg if x is not None), None)

def index_of(iterable, predicate, first_only=True):
    """Returns the index(s) of the elements of iterable which match the `predicate` function.  If no elements exist
    in the iterable which the predicate matches then a ValueError is raised.

    By default only the first matching index is returned as a single integer, however if `first_only` is `False` then
    the return will be a list with all indices that predicate matches.

    :param iterable: An iterable to iterate through and attempt to find elements which predicate matches.
    :type iterable: Iterable
    :param predicate: A function which takes a single argument and returns True if it is a match or False otherwise
    :type predicate: func
    :param first_only: Whether or not only the first matching index should be returned or not.  If this is True then
        the return value is a single integer, otherwise a list is returned with all of the indices that are matched
        by `predicate`
    :type first_only: bool
    :return: The indices of elements within `iterable` which `predicate` matches.
    :rtype: int or [int]
    """
    matches = [] if not first_only else None
    for idx, element in enumerate(iterable):
        if predicate(element):
            if first_only:
                return idx
            else:
                matches.append(idx)

    if not matches:
        raise ValueError()
    return matches
