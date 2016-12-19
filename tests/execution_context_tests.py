"""Tests for ExecutionContext concepts"""
from generic_utils import NOTSET
from generic_utils import loggingtools
from generic_utils.datetimetools import utcnow
from generic_utils.exceptions import GenUtilsAttributeError
from generic_utils.exceptions import GenUtilsTypeError
from generic_utils.exceptions import GenUtilsValueError
from generic_utils.execution_context import BaseExecutionContext
from generic_utils.execution_context import ExecutionContextStack
from generic_utils.execution_context import ExecutionContextStackEmptyError
from generic_utils.execution_context import ThreadLocalExecutionContext
from generic_utils.execution_context import as_execution_context
from generic_utils.execution_context import execution_context_stack
from generic_utils.execution_context.exceptions import ExecutionContextValueDoesNotExist
from generic_utils.json_tools.serialization import dumps
from generic_utils.json_tools.serialization import loads
from generic_utils.test import TestCase

LOG = loggingtools.getLogger()


class DummyExecutionContext(BaseExecutionContext):
    __storage = None

    def __init__(self, initial_context=None):
        """
        :param initial_context:
        :type initial_context:
        :return:
        :rtype:
        """
        self.__storage = {}
        if initial_context:
            self.__storage.update(initial_context)
        super(DummyExecutionContext, self).__init__(initial_context)

    def get(self, key, default=NOTSET):
        """Get value from local dict
        """
        try:
            return self.__storage[key]
        except KeyError:
            if default == NOTSET:
                raise ExecutionContextValueDoesNotExist(key=key)
            else:
                return default

    def set(self, key, val):
        """Set dict value"""
        self.__storage[key] = val


class ExecutionContextTestCase(TestCase):
    """Validates behavior of ExecutionContextStack and ThreadLocalExecutionContext classes"""
    def _custom_setup(self):
        """Always clear current stack before tests.
        """
        execution_context_stack.clear()
        super(ExecutionContextTestCase, self)._custom_setup()

    def test_set(self):
        """Validate setting a value sets value to first execution context matching type from right to left.
        """
        TEST_KEY = 'test key'  # pylint: disable=invalid-name
        TEST_VALUE = 'test value'  # pylint: disable=invalid-name

        dummy_ctx = DummyExecutionContext()
        execution_context_stack.push(dummy_ctx)

        with self.assertRaises(ExecutionContextValueDoesNotExist):
            execution_context_stack.get(TEST_KEY)

        execution_context_stack.set(TEST_KEY, TEST_VALUE)
        self.assertEqual(execution_context_stack.get(TEST_KEY), TEST_VALUE)
        execution_context_stack.pop()
        with self.assertRaises(ExecutionContextValueDoesNotExist):
            execution_context_stack.get(TEST_KEY)

    def test_clear_isempty(self):
        """Validate clear works as expected
        """
        execution_context_stack.set("a", "b")
        self.assertFalse(execution_context_stack.is_empty())
        execution_context_stack.clear()
        self.assertTrue(execution_context_stack.is_empty())

    def test_remove(self):
        """Validate remove works as expected.
        """
        test_key = "Test remove key"
        with self.assertRaises(ExecutionContextValueDoesNotExist):
            # Validate key not present in stack.
            execution_context_stack.get(test_key)
        execution_context_stack.set(test_key, 1)
        # Validate key can be retrieved
        self.assertEqual(execution_context_stack.get(test_key), 1)

        # VALIDATION
        execution_context_stack.remove(test_key)
        with self.assertRaises(ExecutionContextValueDoesNotExist):
            execution_context_stack.get(test_key)
        # Should raise if not present.
        with self.assertRaises(GenUtilsAttributeError):
            execution_context_stack.remove(test_key)

    def test_push_invalid(self):
        """Validate behavior of push method on ExecutionContextStack if called with context already in stack"""
        local_context = ThreadLocalExecutionContext()

        execution_context_stack.push(local_context)

        with self.assertRaises(GenUtilsValueError):
            execution_context_stack.push(local_context)

    def test_extend_invalid(self):
        """Validate behavior of extend method on ExecutionContextStack when called with invalid type arguments.
        """
        execution_contexts = [ThreadLocalExecutionContext(), {}]
        with self.assertRaises(GenUtilsTypeError):
            execution_context_stack.extend(execution_contexts)

    def test_peek(self):
        """Validate peek method
        """
        top_context = ThreadLocalExecutionContext()
        with self.assertRaises(ExecutionContextStackEmptyError):
            execution_context_stack.peek()

        execution_context_stack.push(top_context)
        self.assertEqual(execution_context_stack.peek(), top_context)
        execution_context_stack.pop()

    def test_pop_to_item(self):
        """Validate behavior of pop to item
        """
        keep_context = ThreadLocalExecutionContext()
        top_context = ThreadLocalExecutionContext()
        exec_contexts = [keep_context, top_context]

        with self.assertRaises(GenUtilsValueError):
            execution_context_stack.pop_to_item(keep_context)

        execution_context_stack.extend(exec_contexts)
        execution_context_stack.pop_to_item(keep_context)

        self.assertNotIn(top_context, execution_context_stack.current_stack)
        self.assertIn(keep_context, execution_context_stack.current_stack)

    def test_to_from_dict(self):
        """Validate to/from dict on ThreadLocalExecutionContext works as expected"""
        TEST_KEY = "test key"  # pylint: disable=invalid-name
        TEST_VALUE = "test value"  # pylint: disable=invalid-name
        TEST_DATETIME_KEY = "test_datetime_key"
        TEST_DATETIME_VALUE = utcnow()

        execution_context = ThreadLocalExecutionContext()
        execution_context.set(TEST_KEY, TEST_VALUE)
        execution_context.set(TEST_DATETIME_KEY, TEST_DATETIME_VALUE)

        exec_context_dict = dumps(execution_context)
        LOG.debug("Got exec_context_dict = %r", exec_context_dict)
        restored_exec_context = loads(exec_context_dict)
        self.assertEqual(restored_exec_context.get(TEST_KEY), TEST_VALUE)
        self.assertEqual(restored_exec_context.get(TEST_DATETIME_KEY), TEST_DATETIME_VALUE,
                         "Datetime should be serialized / deserialized properly.")

    def test_get(self):
        """Validate when a key is requested, the stack is traveled right to left and first value is returned"""
        ### SETUP
        test_key = 'TEST_KEY'
        test_value_left = 'TEST VALUE left'
        test_key_only_left = 'TEST_KEY_ONLY_LEFT'
        test_value_only_left = 'TEST VALUE only left'
        test_value_right = 'TEST VALUE right'

        test_exec_context_left = ThreadLocalExecutionContext()
        test_exec_context_right = ThreadLocalExecutionContext()

        test_exec_context_left.set(test_key, test_value_left)
        test_exec_context_left.set(test_key_only_left, test_value_only_left)
        test_exec_context_right.set(test_key, test_value_right)

        execution_context_stack.push(test_exec_context_left)
        execution_context_stack.push(test_exec_context_right)

        self.assertEqual(execution_context_stack.get(test_key), test_value_right)
        self.assertEqual(execution_context_stack.get(test_key_only_left), test_value_only_left)
        self.assertIsNone(execution_context_stack.get('nonexistent', default=None),
                          "Should return None if default explicitly set to None")
        with self.assertRaises(ExecutionContextValueDoesNotExist):
            # If default is NOTSET, raise Exception
            execution_context_stack.get('nonexistent')

    def test_getstate_setstate(self):
        """Validate behavior of ExecutionContextStack when using the getstate/setstate magicmethods.
        """
        test_first_key = "test_first_key"
        test_first_val = "test_first_value"
        execution_context_stack.set(test_first_key, test_first_val)

        local_exec_stack = ExecutionContextStack()
        with self.assertRaises(ExecutionContextValueDoesNotExist):
            # Validate that the value is local to the execution_context_stack
            local_exec_stack.get(test_first_key)

        context_a_key = 'test_key_context_a'
        context_b_key = 'test_key_context_b'
        context_a = ThreadLocalExecutionContext()
        context_a.set(context_a_key, "context_a")
        context_b = ThreadLocalExecutionContext()
        context_b.set(context_b_key, "context_b")

        local_exec_stack.extend([context_a, context_b])
        self.assertIsNotNone(local_exec_stack.get(context_a_key))

        for key in (context_a_key, context_b_key):
            with self.assertRaises(ExecutionContextValueDoesNotExist):
                execution_context_stack.get(key)

        context_json = dumps(local_exec_stack)
        del local_exec_stack

        LOG.debug("Context JSON = %s", context_json)
        restored_stack = loads(context_json)

        begin_stack_length = len(execution_context_stack)

        with as_execution_context(restored_stack):   # test pushing this stack onto global stack temporarily
            self.assertEqual(execution_context_stack.get(context_a_key), "context_a")
            self.assertEqual(execution_context_stack.get(context_b_key), "context_b")
            self.assertEqual(execution_context_stack.get(test_first_key), test_first_val)
        end_stack_length = len(execution_context_stack)
        self.assertEqual(begin_stack_length, end_stack_length)
        for key in (context_a_key, context_b_key):
            with self.assertRaises(ExecutionContextValueDoesNotExist):
                execution_context_stack.get(key)

        with self.assertRaises(ExecutionContextValueDoesNotExist):
            execution_context_stack.get(context_b_key)

        self.assertEqual(execution_context_stack.get(test_first_key), test_first_val)

    def test_as_exec_context_removes(self):
        """Validate decorator removes any context added while inside the context manager/decorator
        """
        # SETUP
        execution_context_stack.clear()
        self.assertTrue(execution_context_stack.is_empty())

        with as_execution_context():
            execution_context_stack.push(ThreadLocalExecutionContext())

        self.assertTrue(execution_context_stack.is_empty())

    # TODO: Improve as_execution_context to support yielding/returning a frozen "execution context stack" so
    #     that below test cases can pass - where using as_execution_context in a nested manner as shown below to set
    #     values does not modify values which have already been set in the outer stack.
    #
    # def test_nested_execution_context(self):
    #     """
    #     """
    #     with as_execution_context() as ctx:
    #         test_val = "outer value"
    #         test_key = "test_nested_key"
    #         ctx.set(test_key, test_val)
    #
    #         def nested_context_validations(expected_value):
    #             self.assertEqual(ctx.get(test_key), test_val, "Outer context value should not change")
    #             self.assertEqual(execution_context_stack.get(test_key), expected_value,
    #                              "Stack should return top value for key")
    #
    #         with as_execution_context():
    #             execution_context_stack.set(test_key, "inner_value")
    #             nested_context_validations("inner_value")
