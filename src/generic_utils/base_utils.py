"""Module which provides some base level python utilities such as the ability to make any arbitrary class Immutable
through the ImmutableMixin
"""
# stdlib
import threading

_immutable_delay_locals = threading.local()  # pylint: disable=invalid-name


def _get_current_scoped_queue():
    """
    :return: A list which can have ImmutableMixin objects appended to it to have them automatically flipped over
                to being immutable.  If this returns None then that means there is not currently a manager handling
                delayed immutability and therefore there is not a queue in scope to append to.
    """
    if not hasattr(_immutable_delay_locals, "backlog"):
        return None
    backlog_stack = _immutable_delay_locals.__getattribute__("backlog")

    try:
        return backlog_stack[-1]
    except IndexError:
        return None


def _is_immutability_delayed():
    """
    :return: Whether or not immutability delay is currently enabled for the current scope of execution.
    """
    queue = _get_current_scoped_queue()
    return queue is not None


def _create_scoped_queue():
    """Creates a scope on the queue for tracking the stack of immutability delays to ensure we don't remove the delay
    until all layered calls to delay immutability have run their course and expired.
    """
    try:
        backlog_stack = _immutable_delay_locals.__getattribute__("backlog")
    except AttributeError:
        backlog_stack = []
        _immutable_delay_locals.__setattr__("backlog", backlog_stack)
    new_queue = []
    backlog_stack.append(new_queue)
    return new_queue


def _pop_scoped_queue():
    """Removes an item off the scope queue
    """
    if _is_immutability_delayed():
        backlog_stack = _immutable_delay_locals.__getattribute__("backlog")

        return backlog_stack.pop()

    return None


class ImmutableDelay(object):
    """
    Context Manager for delaying immutability of objects that use the ImmutableMixin.  This allows for delayed
    construction of objects before closing them out.

    Example:

    >>> with ImmutableDelay():
    >>>   immutable_object = ImmutableMixin()
    >>>   # I can mutate the object!
    >>>   immutable_object.some_prop = "bleh"
    >>> # This will throw a TypeError now since we are now longer in the ImmutableDelay context
    >>> immutable_object.some_prop = "bleh"
    """
    def __enter__(self):
        _create_scoped_queue()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        queue = _pop_scoped_queue()
        for item in queue:
            try:
                item.make_immutable()
            except AttributeError:
                pass


class ImmutableObjectException(TypeError):
    """Exception raised if a change is attempted to an Immutable object
    """
    message = "Change attempted to an Immutable Object"


class ImmutableMixin(object):
    """Mixin which can be applied to any arbitrary class to make it immutable through the standard attribute access
    means.  This does not guarantee complete immutability but instead makes it sufficiently difficult for someone
    to change the state of the affected class that only those who are motivated will be able to mutate the object.
    """
    __immutable__ = False

    def __init__(self, *args, **kwargs):
        if _is_immutability_delayed():
            _get_current_scoped_queue().append(self)
        else:
            self.make_immutable()
        super(ImmutableMixin, self).__init__(*args, **kwargs)

    def __setattr__(self, key, value):
        if self.is_immutable():
            raise ImmutableObjectException()
        return super(ImmutableMixin, self).__setattr__(key, value)

    def __delattr__(self, item):
        if self.is_immutable():
            raise ImmutableObjectException()
        return super(ImmutableMixin, self).__delattr__(item)

    def make_immutable(self):
        """
        Puts the current object into an immutable state which guards against state changes to the object
        """
        self.__dict__["__immutable__"] = True

    def is_immutable(self):
        """
        :return: Whether or not the current object is in the immutable state
        :rtype: bool
        """
        return self.__dict__.get("__immutable__", False)
