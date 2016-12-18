"""Tests for python utils
"""
from . import settings
from generic_utils.config import config, PythonModuleConfig

python_utils_test_config = PythonModuleConfig(settings)  # pylint: disable=invalid-name
config.add_provider(python_utils_test_config)
