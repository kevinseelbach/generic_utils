"""Custom exceptions for ExecutionContext package
"""

from generic_utils.exceptions import GenUtilsKeyError, GenUtilsRuntimeError, GenUtilsException


class ExecutionContextStackEmptyError(GenUtilsException):
    """Raised when stack is empty and blocks proper execution
    """
    pass


class ExecutionContextValueDoesNotExist(GenUtilsKeyError):
    """Raised when attempting to get a value that does not exist in a backend"""
    message = "Could not get key={key} from ExecutionContext."
    key = None


class ExecutionContextRuntimeError(GenUtilsRuntimeError):
    """Raised when ExecutionContextStack can not recover from an unknown problem."""
    message = "ExecutionContextStack could not complete operation due to reason={reason}."
    reason = None
