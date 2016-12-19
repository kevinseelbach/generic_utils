"""Generic pipeline."""
# stdlib
from builtins import object
from builtins import range

from generic_utils import loggingtools
from generic_utils.collections.exceptions import InvalidStageException
from generic_utils.collections.exceptions import PipelineErrorExit
from generic_utils.collections.exceptions import PipelineException
from generic_utils.collections.exceptions import PipelineSuccessExit
from generic_utils.typetools import as_iterable

LOG = loggingtools.getLogger()


class Pipeline(object):
    """This is a generic implementation of chaining a series of functions and dispatch as a unit.
    It's similar to Python's 'pipe' (i.e. a() | b() | c()). But in addition to that we are also
    passing in the result of previous function, if any, to the next function defined in the pipeline.
    """
    _transition_filters = None

    def __init__(self, *stage_functions, **kwargs):
        """
        Constructor.
        :param stage_functions: A series of functions to be dispatched in sequence.
        :type stage_functions: Tuple.
        :param transition_filter: callable to use to determine whether to proceed to the next stage, or possibly
            transform the intermediate result before calling the next stage.
        :type transition_filter: function
        """
        transition_filters = as_iterable(kwargs.get('transition_filters'))
        for trans_filter in transition_filters:
            if trans_filter and not callable(trans_filter):
                raise PipelineException("Invalid type passed to Pipeline as transition_filters argument, "
                                        "transition_filter must be callable")

        self._transition_filters = transition_filters
        self._stage_functions = list(stage_functions)

    def __call__(self, *args, **kwargs):
        return self.start(*args, **kwargs)

    def __len__(self):
        return len(self._stage_functions)

    def start(self, *args, **kwargs):
        """
        Pipeline execution. Result of the previous function, if any, should be passed into the
        next function in the pipeline.

        Child class inherited from this class should overwrite `start()` rather than `__call__`. `__call__` is now
        the magic wrapper.

        :param args:
        :param kwargs:
        :return: The result of the last function in the pipeline.
        """
        intermediate_result = None
        num_of_stage_funcs = len(self)
        for idx in range(num_of_stage_funcs):
            func = self._stage_functions[idx]
            if idx == 0:
                intermediate_result = func(*args, **kwargs)
            else:
                intermediate_result = func(intermediate_result)

            if idx < num_of_stage_funcs - 1:
                try:
                    should_continue, intermediate_result = self._execute_transition_filters(func, intermediate_result)
                except PipelineErrorExit as error_exit:
                    LOG.debug("Exiting pipeline early due to transition function raising Error=%r", error_exit)
                    raise

                if should_continue is not True:
                    break
            else:
                break

        return intermediate_result

    def with_starting_stage(self, start_from_stage):
        """
        Truncated pipeline from a specific stage.
        :param start_from_stage: Start stage.
        :return: A new instance of Pipeline.
        :raises: InvalidStageException
        """
        func_index = self._get_stage_index(start_from_stage)
        return self.__class__(*self._stage_functions[func_index:],
                              transition_filters=self._transition_filters)

    def _get_stage_index(self, func):
        """

        :param func:
        :type func: callable, which is a stage in the Pipeline
        :return:
        :rtype: int
        :raises: InvalidStageException
        """
        try:
            return self._stage_functions.index(func)
        except ValueError:
            raise InvalidStageException(func)

    def _get_next_stage(self, func=None):
        """Given a stage `func`, gets the next stage or returns None.

            If the argument passed is not a valid stage, this method will bubble the `InvalidStageException`
            raised by `_get_stage_index` up to callers.
            If the argument passed is the final stage, returns None.
        :param func:
        :type func: callable , which is a stage within this Pipeline instance.
        :return:
        :rtype: callable|None
        :raises: InvalidStageException
        """
        func_idx = self._get_stage_index(func) + 1 if func else 0
        try:
            return self._stage_functions[func_idx]
        except IndexError:
            # Returning None indicates there is not another stage. This is safe because we have already checked
            # that the `func` argument is a valid stage inside the `_get_stage_index` method
            return None

    def _execute_transition_filters(self, stage_func, intermediate_result):
        """Run between stages.

        :param stage_func: Callable, the previous pipeline stage which returned intermediate_result
        :type stage_func: function
        :param intermediate_result:
        :type intermediate_result: T
        :return: tuple with (continue, intermediate_result)
        :rtype: bool,T
        """
        for trans_filter in self._transition_filters:
            try:
                intermediate_result = trans_filter(self, stage_func, intermediate_result)
            except PipelineSuccessExit as exit_signal:
                LOG.debug(exit_signal.message)
                intermediate_result = exit_signal.intermediate_result
                LOG.debug("transition filter %r signaled Pipeline=%r should exit with success after stage %r",
                          trans_filter, self, stage_func)
                return False, intermediate_result
            except PipelineErrorExit as exit_signal:
                LOG.warn(exit_signal.message)
                LOG.debug("transition filter %r signaled Pipeline=%r should exit with error after stage %r",
                          trans_filter, self, stage_func)
                ### Re raise the error so the pipeline can record this failure.
                raise
        return True, intermediate_result
