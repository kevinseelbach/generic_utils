"""Exceptions for collections
"""
from generic_utils import exceptions


class PipelineException(exceptions.GenUtilsException):
    """Basic exception class for Pipelines which inherits the default message formatting helpers
    """
    pass


class PipelineExit(PipelineException):
    """Raised to indicate a Pipeline should exit - children implement successful / error exit exception types.
    """
    message = "Pipeline was exited for unspecified reason. pipeline={pipeline}"
    pipeline = None


class PipelineSuccessExit(PipelineExit):
    """Raised to indicate a Pipeline should exit gracefully
    """
    message = "Intermediate stage signaled Pipeline should exit successfully - pipeline={pipeline}, " \
              "result={intermediate_result}"
    pipeline = None
    # Note that intermediate result is used for signaling as well as message formatting here.
    intermediate_result = None


class PipelineErrorExit(PipelineExit):
    """Raised in order to signal Pipeline should be exited ungracefully due to an error condition
    """
    message = "Intermediate stage signaled Pipeline should not continue due to error condition - pipeline={pipeline}," \
              " result={intermediate_result}"
    pipeline = None
    intermediate_result = None  # same comment as above exception type applies


class InvalidStageException(PipelineException):
    """Raise when start stage is not in the pipeline."""
    message = 'Stage={stage} is not defined in the pipeline.'
    stage = None
