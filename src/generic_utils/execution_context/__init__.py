"""Classes to define ExecutionContext concepts which contain any special configuration / context data needed at runtime
"""
import copy
import threading

from generic_utils import loggingtools, NOTSET
from generic_utils.contextlib_ex import ExplicitContextDecorator
from generic_utils.exceptions import GenUtilsValueError, GenUtilsTypeError, GenUtilsAttributeError
from generic_utils.execution_context.exceptions import ExecutionContextValueDoesNotExist, \
    ExecutionContextStackEmptyError
from generic_utils.typetools import as_iterable

LOG = loggingtools.getLogger()


class BaseExecutionContext(object):
    """Defines an API for storing / getting values into an "ExecutionContext" which may be stored in various backends
    """
    def __init__(self, initial_context=None):  # pylint: disable=unused-argument
        """
        :param initial_context: Optional argument to initialize context with another context's data
          or a dict of key/value pairs
        :type initial_context: dict | BaseExecutionContext
        :return:
        :rtype:
        """
        pass

    def clear(self):
        """Clears the data on the instance"""
        pass

    def remove(self, key):
        """Removes the key from the instance.
        :param key:
        :type key:
        :return:
        :rtype:
        """
        pass

    def set(self, key, val):
        """Sets key/value pair on this ExecutionContext instance
        :param key:
        :type key:
        :param val:
        :type val:
        :return:
        :rtype:
        """
        pass

    def get(self, key, default=NOTSET):
        """Get key from this instance. Raises ExecutionContextValueDoesNotExist if not present
        :param key:
        :type key:
        :param default: Optionally pass a default value and do not raise Exception if key is not present.
        :type default:
        :return:
        :raises: ExecutionContextValueDoesNotExist
        :rtype:
        """
        pass

    def bulk_set(self, key_value_dict):
        """A method to update this instances data in bulk.
        :param key_value_dict:
        :type key_value_dict: dict
        :return:
        :rtype:
        """
        pass

    def __str__(self):
        """
        :return:
        :rtype: unicode
        """
        return "%s" % self.__class__.__name__

    def __getstate__(self):
        """Subclasses must implement to enable serializing instances
        :return:
        :rtype:
        """
        pass

    def __setstate__(self, state):
        """Subclasses should implement to enable restoring instance from serialized data
        :type state: dict
        :return:
        :rtype:
        """
        pass

    def __deepcopy__(self, memo):
        """Base deep copy implementation that populates the `memo` argument with the copy. Is called by copy.deepcopy()
        :return: A deep clone of the original object
        :rtype: BaseExecutionContext
        """
        LOG.debug("Begin copying object of type=%s", self.__class__)
        cls = self.__class__
        result = cls.__new__(cls)
        memo[id(self)] = result
        for key, value in self.__dict__.iteritems():
            setattr(result, key, copy.deepcopy(value, memo))
        LOG.debug("Successful deep copy, returning instance copy.")
        return result


class ThreadLocalExecutionContext(BaseExecutionContext):
    """An ExecutionContext backed by thread local storage

    :type _thread_local: None | thread._local
    """
    _thread_local = None

    def __init__(self, initial_context=None):
        """Set any initial context data.
        :param initial_context:
        :type initial_context:
        """
        self._thread_local = threading.local()
        super(ThreadLocalExecutionContext, self).__init__(initial_context)
        if initial_context is not None and isinstance(initial_context, dict):
            # noinspection PyArgumentList
            self.bulk_set(**initial_context)
        elif initial_context:
            raise TypeError("ThreadLocalExecutionContext received incorrect type=%s for _initial_context" %
                            type(initial_context))

    def __getstate__(self):
        """
        :return:
        :rtype: dict
        """
        return dict(self._thread_local.__dict__)

    def __setstate__(self, state):
        """
        :type state: dict
        :return:
        :rtype: None
        """
        self._thread_local = threading.local()
        self._thread_local.__dict__.update(state)

    def clear(self):
        """Clears all set values for the context
        :return:
        :rtype:
        """
        self._thread_local.__dict__.clear()

    def remove(self, key):
        """Remove key from the ExecutionContext storage
        :param key:
        :type key:
        :return:
        :rtype: None
        """
        try:
            self._thread_local.__delattr__(key)
        except AttributeError:
            raise GenUtilsAttributeError(attribute_name=key)

    def set(self, key, val):
        """
        :param key:
        :type key:
        :param val:
        :type val: T
        :return:
        :rtype: None
        """
        LOG.debug("Setting thread local %s=%s", key, val)
        setattr(self._thread_local, key, val)

    def get(self, key, default=NOTSET):
        """
        :param key:
        :type key:
        :param default:
        :type default:
        :return:
        :raises: ExecutionContextValueDoesNotExist
        :rtype:
        """
        try:
            return getattr(self._thread_local, key)
        except AttributeError:
            if default == NOTSET:
                raise ExecutionContextValueDoesNotExist(key=key)
            else:
                LOG.debug("User requested key=%s with default=%s, value was not found - returning default.",
                          key, default)
                return default

    def bulk_set(self, **kwargs):
        """Bulk updates the thread_local's dict
        :param kwargs:
        :type kwargs: dict
        :return:
        :rtype:
        """
        self._thread_local.__dict__.update(**kwargs)


class ExecutionContextStack(BaseExecutionContext):
    """Handles getting / setting values from a set of ExecutionContext backends.
    """
    _thread_local = None

    def __init__(self, initial_context=None):
        """Sets initial context and thread local
        :param initial_context:
        :type initial_context:
        :return:
        :rtype:
        """
        self._thread_local = threading.local()
        super(ExecutionContextStack, self).__init__(initial_context)
        LOG.debug("_on_init handling _initial_context=%r passed to ExecutionContextStack", initial_context)
        if initial_context is not None:
            if isinstance(initial_context, ExecutionContextStack):
                self.extend(initial_context)
            elif isinstance(initial_context, BaseExecutionContext):
                self.push(initial_context)
            elif isinstance(initial_context, dict):
                self.bulk_set(initial_context)
            else:
                raise TypeError("Received unexpected type=%s for argument `initial_context`." % type(initial_context))

    def __len__(self):
        """Return the length of the current_stack (number of BaseExecutionContext subclass instances on current stack)
        :return:
        :rtype: int
        """
        return len(self.current_stack)

    def __getstate__(self):
        """
        :return:
        :rtype:
        """
        return copy.deepcopy(self._thread_local.__dict__)

    def __setstate__(self, state):
        """
        :type state: dict
        :return:
        :rtype:
        """
        self._thread_local = threading.local()
        self._thread_local.__dict__.update(state)

    @property
    def current_stack(self):
        """
        :return: Current stack stored in thread_local
        :rtype: [BaseExecutionContext]
        """
        try:
            return self._thread_local.execution_context_stack
        except AttributeError:
            LOG.debug("execution_context_stack not found in thread_local, setting to list with "
                      "ThreadLocalExecutionContext().")
            self._thread_local.execution_context_stack = []
            return self._thread_local.execution_context_stack

    @current_stack.setter
    def current_stack(self, stack):
        """Set the current stack stored in thread_local
        :param stack:
        :type stack: [BaseExecutionContext]
        :return:
        :rtype: None
        """
        LOG.debug("Replacing current stack with stack %r", stack)
        self._thread_local.execution_context_stack = stack
        LOG.debug("Successfully set current_stack=%r", stack)

    def get(self, key, default=NOTSET):
        """
        :param default:
        :type default:
        :param key:
        :type key:
        :param default: If set to a value other than NOTSET, will return default value even if the attribute does not
          exist in any ExecutionContext instances on the stack , otherwise, raises Exception if final value is NOTSET.
        :type default:
        :return:
        :raises: ExecutionContextValueDoesNotExist
        :rtype:
        """
        LOG.debug("Attempting to get value for key=%s from ExecutionContextStack.", key)
        index = 0
        for execution_ctx in reversed(self.current_stack):
            try:
                result = execution_ctx.get(key)
                LOG.debug("Got result=%s from ExecutionContext=%s with index=%s for key=%s", result, execution_ctx,
                          index, key)
                return result
            except ExecutionContextValueDoesNotExist:
                index += 1
                continue

        LOG.debug("Could not get value for key=%s from current stack, checked %s ExecutionContexts", key, index + 1)

        if default == NOTSET:
            raise ExecutionContextValueDoesNotExist(key=key)
        else:
            LOG.debug("Could not get value for key=%s from ExecutionContextStack, returning default=%s", key, default)
            return default

    def set(self, key, value):
        """Sets a value for ExecutionContext into first available BaseExecutionContext subclass of `type`,
            starting from the right.
        :param key:
        :type key:
        :param value:
        :type value:
        :return:
        :rtype: None
        :raises:
        """
        LOG.debug("Begin setting %s=%s for context at top of stack", key, value)
        try:
            target_context = self.peek()
        except ExecutionContextStackEmptyError:
            LOG.debug("Stack is empty, adding ThreadLocalExecutionContext to set key %s", key)
            target_context = ThreadLocalExecutionContext()
            self.push(target_context)
            LOG.debug("Appended new ThreadLocalExecutionContext to empty stack to set %s=%s", key, value)
        target_context.set(key, value)
        LOG.debug("Successfully set %s=%s at top of stack", key, value)

    def bulk_set(self, key_value_dict):
        """Bulk sets key_value_dict on stack , creating a new ThreadLocalExecutionContext instance if stack is empty.
        :param key_value_dict:
        :type key_value_dict: dict
        :return:
        :rtype: None
        """
        try:
            stack_top = self.peek()
        except ExecutionContextStackEmptyError:
            stack_top = ThreadLocalExecutionContext()
            self.push(stack_top)
        stack_top.bulk_set(key_value_dict)

    def remove(self, key):
        """Remove key `key` from execution_context at top of stack.
        :param key:
        :type key:
        :raises: ExecutionContextStackEmptyError
        :return:
        :rtype: None
        """
        LOG.debug("Attempting to remove key=%r from current stack", key)
        context = self.peek()
        if context:
            context.remove(key)
            LOG.debug("Removed key=%s from last context.", key)

    def push(self, execution_context):
        """Append an ExecutionContext instance to the top of stack.
        :param execution_context:
        :type execution_context: T<=BaseExecutionContext
        :rtype: None
        """
        if not isinstance(execution_context, BaseExecutionContext):
            raise GenUtilsTypeError(argument='execution_context', type_name=type(execution_context))

        if execution_context in self.current_stack:
            raise GenUtilsValueError(value_name='execution_context')
        self.current_stack.append(execution_context)

    def pop(self, index=None):
        """Pops execution_context at `index` from current execution context stack
        :param index:
        :type index: int
        :return: the popped item.
        :rtype: BaseExecutionContext
        """
        LOG.debug("Begin popping execution_ctx at index=%s", index)
        execution_ctx = self.current_stack.pop(index) if index is not None else self.current_stack.pop()
        LOG.debug("Successfully popped execution_ctx=%r at index=%s from stack.", execution_ctx, index)
        return execution_ctx

    def extend(self, execution_contexts):
        """
        :param execution_contexts:
        :type execution_contexts: [BaseExecutionContext]
        :return:
        :rtype:
        """
        if isinstance(execution_contexts, ExecutionContextStack):
            execution_contexts = execution_contexts.current_stack
        else:
            execution_contexts = as_iterable(execution_contexts)
        for context in execution_contexts:
            if not isinstance(context, BaseExecutionContext):
                raise GenUtilsTypeError(message="Received invalid type=%s for argument=execution_contexts" % type(context))
            self.push(context)

    def peek(self):
        """Returns context at top of stack
        :return:
        :rtype: BaseExecutionContext
        """
        try:
            return self.current_stack[-1]
        except IndexError:
            raise ExecutionContextStackEmptyError("Stack is empty, can not peek.")

    def is_empty(self):
        """Is the stack empty
        :return:
        :rtype: bool
        """
        return len(self) == 0

    def pop_to_item(self, exec_context, raise_exception=True):
        """Removes all items above `exec_context` in current stack,
          raising exception if exec_context is not in current_stack and raise_exception is True

        :param exec_context:
        :type exec_context: BaseExecutionContext
        :param raise_exception: Whether to raise an exception if the exec_context is not found.
        :type raise_exception: bool
        :return:
        :rtype: [BaseExecutionContext]
        :raises:GenUtilsValueError
        """
        if raise_exception is True and exec_context not in self.current_stack:
            raise GenUtilsValueError("ExecutionContext=%r is not in the current_stack, can not continue." % exec_context)

        popped_items = []
        while self.current_stack[-1] != exec_context:
            popped_items.append(self.pop())
        return popped_items

    def clear(self):
        """Clears the stack of any values.
        :return:
        :rtype:
        """
        self.current_stack = []
        LOG.debug("Cleared current execution stack")

    def clone(self):
        """Returns a deepcopy of the ExecutionContextStack which is safe to modify and store.
        :return:
        :rtype:
        """
        return copy.deepcopy(self)


execution_context_stack = ExecutionContextStack()  # pylint: disable=invalid-name


class AsExecutionContext(ExplicitContextDecorator):
    """Supports injecting ExecutionContext data to be restored on the ExecutionContextStack when
    entering/exiting a decorator or context manager.
    """
    _entry_point = None
    _execution_contexts = None

    def __init__(self, execution_contexts=None):
        """
        :param execution_contexts: list of execution contexts to push to stack while inside
          decorator / context_manager.
        :type execution_contexts: [BaseExecutionContext]
        :return:
        :rtype:
        """
        self._execution_contexts = execution_contexts

    def __enter__(self):
        """
        :return:
        :rtype:
        """
        try:
            # Entry point refs original execution context
            self._entry_point = execution_context_stack.peek()
        except ExecutionContextStackEmptyError:
            LOG.debug("Stack is empty, marking entry_point to None.")
            self._entry_point = None

        if self._execution_contexts is not None:
            LOG.debug("Attempting to add execution_contexts=%r to current stack", self._execution_contexts)
            if isinstance(self._execution_contexts, (ExecutionContextStack, list)):
                execution_context_stack.extend(self._execution_contexts)
            elif isinstance(self._execution_contexts, BaseExecutionContext):
                execution_context_stack.push(self._execution_contexts)
            else:
                raise TypeError(
                    message="Received unexpected type=%s for `execution_contexts`" % type(self._execution_contexts))
        else:
            execution_context_stack.push(ThreadLocalExecutionContext())

    def __exit__(self, *exc_info):
        """
        :param exc_info:
        :type exc_info:
        :return:
        :rtype:
        """
        if self._entry_point is not None:
            LOG.debug("Restoring stack by removing items after entry_index = %r", self._entry_point)
            execution_context_stack.pop_to_item(self._entry_point, raise_exception=True)
        else:
            LOG.debug("Restoring stack by removing all items since it was empty when we entered as_execution_context.")
            execution_context_stack.clear()
        LOG.debug("Restored original stack successfully.")
        self._execution_contexts = None
        self._entry_point = None


as_execution_context = AsExecutionContext  # pylint: disable=invalid-name
