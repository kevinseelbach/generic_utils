from pylint.checkers.base import DocStringChecker
from pylint_django.utils import node_is_subclass
from pylint_plugin_utils import suppress_message


def is_class(class_name):
    """Shortcut for node_is_subclass."""
    return lambda node: node_is_subclass(node, class_name)


def apply_augmentations(linter):
    # Turn off docstrings on Django Admin classes
    suppress_message(linter, DocStringChecker.visit_classdef, 'C0111', is_class("django.contrib.admin.options.ModelAdmin"))
