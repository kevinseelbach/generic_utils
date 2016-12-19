"""Tests for python utils
"""
from generic_utils.config import PythonModuleConfig
from generic_utils.config import config

from . import settings

python_utils_test_config = PythonModuleConfig(settings)  # pylint: disable=invalid-name
config.add_provider(python_utils_test_config)
