"""Exceptions for collections
"""
class PipelineException(Exception):
    """Basic exception class for Pipelines
    """
    pass


class PipelineExit(PipelineException):
    """Base exception for pipeline exits"""
    intermediate_result = None
    message = "Pipeline was exited for unspecified reason. pipeline={pipeline}"
    pipeline = None

    def __init__(self, pipeline, intermediate_result):
        """

        :param pipeline:
        :type pipeline: generic_utils.collections.pipeline.Pipeline
        :return:
        :rtype: None
        """
        self.pipeline = pipeline
        self.intermediate_result = intermediate_result
        self.message = self.message.format(pipeline=pipeline)
        super(PipelineExit, self).__init__(self.message)


class PipelineSuccessExit(PipelineExit):
    """Raised in order to signal Pipeline should be exited gracefully (success)
    """
    message = "Intermediate Pipeline stage signaled pipeline should be exited successfully pipeline=" \
              "{pipeline}"


class PipelineErrorExit(PipelineExit):
    """Raised in order to signal Pipeline should be exited ungracefully due to an error condition
    """
    message = "Intermediate Pipeline stage signaled pipeline should not continue due to error condition. pipeline=" \
              "{pipeline}"


class InvalidStageException(PipelineException):
    """Raise when start stage is not in the pipeline."""
    def __init__(self, stage):
        self.stage = stage
        super(InvalidStageException, self).__init__('%r is not defined in the pipeline.' % self.stage,
                                                    self.stage)
