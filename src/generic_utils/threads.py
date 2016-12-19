"""Helpers for programs that use threading
"""
# stdlib
import copy
import threading


class CopyableLocal(threading.local):
    """A subclass of threading.local which provides additional features for deepcopy.
    """

    def __deepcopy__(self, memodict=None):
        """Base deep copy implementation that populates the `memo` argument with the copy. Is called by copy.deepcopy()
                :return: A deep clone of the original object
                :rtype: BaseExecutionContext
                """
        if memodict is None:
            memodict = {}
        cls = self.__class__
        result = cls.__new__(cls)
        memodict[id(self)] = result
        for key, value in self.__dict__.items():
            setattr(result, key, copy.deepcopy(value, memodict))
        return result


copyable_local = CopyableLocal  # pylint: disable=invalid-name
