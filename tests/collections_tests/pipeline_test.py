"""Tests for generic_utils.collections.pipeline"""
from unittest import TestCase
from nose.tools import nottest

from generic_utils.collections.pipeline import Pipeline
from generic_utils.collections.exceptions import InvalidStageException, PipelineSuccessExit, PipelineErrorExit

from generic_utils import loggingtools


LOG = loggingtools.getLogger()

# pylint: disable=invalid-name
a = lambda x: x + 1
b = lambda x: x + 2 if x else 100
c = lambda x: x + 3
d = lambda x: x + 4
# pylint: enable=invalid-name


STAGE_A_ADD_VAL = 1  # Used in tests that should run to full completion
STAGE_B_ADD_VAL = 2.3
STAGE_C_ADD_VAL = 1
EXIT_PIPELINE_VAL = STAGE_B_ADD_VAL  # Exit when result is default.
STAGE_B_CONTINUE_VAL = STAGE_A_ADD_VAL + STAGE_B_ADD_VAL
FULL_PIPELINE_RESULT_VAL = STAGE_B_CONTINUE_VAL + 1


def stage_a(run_to_completion=False):
    return STAGE_A_ADD_VAL if run_to_completion is True else 0


def stage_b(val):
    return val + STAGE_B_ADD_VAL if val is not None else STAGE_B_ADD_VAL


def stage_c(val):
    return val + STAGE_C_ADD_VAL




@nottest
def test_transition_filter(self, stage_func, intermediate_result):
    LOG.debug("Transition filter called on Pipeline=%r with stage_func=%r and intermediate_result=%r",
              self, stage_func, intermediate_result)
    return intermediate_result

DEFAULT_TRANS_FILTER_RESULT = FULL_PIPELINE_RESULT_VAL


def do_nothing(previous_result):
    assert type(previous_result) is int, "Integer is expected as input."


class PipelineTestCase(TestCase):
    def setUp(self):
        self.pipeline = Pipeline(a, b, c)

    def test_pipeline(self):
        self.assertEqual(self.pipeline.start(1), 7)

    def test_with_starting_stage(self):
        new_pipeline = self.pipeline.with_starting_stage(b)
        self.assertEqual(new_pipeline(1), 6)

    def test_start_stage_not_in_pipeline(self):
        """Tests Pipeline's with_starting_stage function where the starting
        stage is not defined in the pipeline. In this case, pipeline should raise InvalidStageException.
        """
        self.assertRaises(InvalidStageException, self.pipeline.with_starting_stage, d)

    def test_empty_stage_return_value(self):
        pipeline = Pipeline(a, do_nothing, b)
        self.assertEqual(pipeline.start(1), 100)

    def test_get_next_stage(self):
        """Validate behavior of _get_next_stage method.
        """
        EXPECTATION_MAP = {
            None: a,
            a: b,
            b: c,
            c: None,
            d: InvalidStageException
        }
        for stage_func, expectation in EXPECTATION_MAP.iteritems():
            if expectation is InvalidStageException:
                with self.assertRaises(expectation):
                    self.pipeline._get_next_stage(stage_func)
            else:
                self.assertEqual(self.pipeline._get_next_stage(stage_func), expectation)

    def test_success_exit(self):
        """Validate Pipeline can be exited gracefully in a success state.
        """
        EXPECTED_EXIT_TRANSFORM_RESULT = int(STAGE_B_ADD_VAL)

        def test_filter(pipeline_self, stage_func, intermediate_result):
            if stage_func == stage_b and intermediate_result == STAGE_B_ADD_VAL:
                intermediate_result = int(intermediate_result)  # conversion of the result.
                raise PipelineSuccessExit(pipeline_self, intermediate_result)
            elif stage_func == stage_b and intermediate_result == STAGE_B_CONTINUE_VAL:
                LOG.debug("Continuing pipeline from stage_b with result = %s", intermediate_result)
                return intermediate_result
            elif stage_func == stage_c and intermediate_result != FULL_PIPELINE_RESULT_VAL:
                self.fail("stage_c completed but result is not what expected %s %s" % (intermediate_result,
                                                                                       FULL_PIPELINE_RESULT_VAL))
            else:
                LOG.debug("stage_func %r completed with intermediate_result=%s" % (stage_func, intermediate_result))
                return intermediate_result

        self._do_exit_condition_tests(test_filter, EXPECTED_EXIT_TRANSFORM_RESULT)
        self._do_exit_condition_tests(test_filter, FULL_PIPELINE_RESULT_VAL, True)

    def test_error_exit(self):
        """Validate error condition exits work as expected."""
        EXIT_RESULT = 4

        def test_filter(pipeline_self, stage_func, intermediate_result):
            if stage_func == stage_b and intermediate_result == STAGE_B_ADD_VAL:
                ### Transformation of result.
                intermediate_result = EXIT_RESULT
                raise PipelineErrorExit(pipeline_self, intermediate_result)
            elif stage_func == stage_c:
                ### Pipelines should never call transition with their final stage.
                self.fail("Filter should have raised PipelineErrorExit and this should not get called.")
            else:
                return intermediate_result

        err_exit = None
        try:
            self._do_exit_condition_tests(test_filter, EXIT_RESULT)
        except PipelineErrorExit as err_exit:
            LOG.debug("Raised PipelineErrorExit as expected")

        self.assertEqual(EXIT_RESULT, err_exit.intermediate_result)
        ### Validate the transition filter does not get called after the final stage.
        self._do_exit_condition_tests(test_filter, FULL_PIPELINE_RESULT_VAL, True)

    def test_transition_filter(self):
        """Validate transition filter only affects the pipeline instance on which it is called."""
        # Original pipeline result is 4.3 + 1 after stage 1 + 1 after stage 2 (not executed after stage 3)
        AFTER_RESULT_TOTAL = 6.3

        def trans_filter(pipeline_self, stage_func, intermediate_result):
            LOG.debug("Replacement transition filter called on Pipeline=%r with stage_func=%r and "
                      "intermediate_result=%r", pipeline_self, stage_func, intermediate_result)
            return intermediate_result + 1

        new_pipeline = Pipeline(stage_a, stage_b, stage_c, transition_filters=trans_filter)

        self.assertIn(trans_filter, new_pipeline._transition_filters)
        self.assertEqual(new_pipeline.start(True), AFTER_RESULT_TOTAL)

        def second_filter(pipeline_self, stage_func, intermediate_result):
            LOG.debug("Replacement transition filter called on Pipeline=%r with stage_func=%r and "
                      "intermediate_result=%r", pipeline_self, stage_func, intermediate_result)
            return intermediate_result + 1

        new_pipeline = Pipeline(stage_a, stage_b, stage_c, transition_filters=[trans_filter, second_filter])
        ### Increase expected result (1*n, n=number of steps - 1)
        self.assertEqual(new_pipeline.start(True), AFTER_RESULT_TOTAL + 2, "multiple trans filters should get executed")

    def _do_exit_condition_tests(self, trans_filter, expected_result, *pipeline_callargs):
        """Run the pipeline and validate filter works as expected.
        """
        ### SETUP
        test_pipeline = Pipeline(stage_a, stage_b, stage_c, transition_filters=trans_filter)
        pipeline_result = test_pipeline.start(*pipeline_callargs)
        self.assertEqual(pipeline_result, expected_result)


