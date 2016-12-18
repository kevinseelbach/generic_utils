from pylint.checkers.base import DocStringChecker
from pylint.checkers.design_analysis import MisdesignChecker
from pylint.checkers.classes import ClassChecker
from pylint.checkers.newstyle import NewStyleConflictChecker
from astroid.nodes import Class
from pylint_plugin_utils import suppress_message
from pylint_django.utils import node_is_subclass


def is_class(class_name):
    """Shortcut for node_is_subclass."""
    return lambda node: node_is_subclass(node, class_name)


def is_model_meta_subclass(node):
    """Checks that node is derivative of Meta class."""
    if node.name != 'Meta' or not isinstance(node.parent, Class):
        return False

    parents = ('rest_framework.views.APIView',
               'django_filters.filterset.FilterSet',
               'rest_framework.serializers.ModelSerializer')
    return any([node_is_subclass(node.parent, parent) for parent in parents])


def apply_augmentations(linter):

    # Suppress the no __init__ method message
    for clazz in ["django_filters.filterset.FilterSet"]:
        suppress_message(linter, ClassChecker.visit_classdef, 'W0232', is_class(clazz))

    suppress_message(linter, DocStringChecker.visit_classdef, 'C0111', is_class('django_filters.filterset.FilterSet'))

    # Meta
    suppress_message(linter, DocStringChecker.visit_classdef, 'C0111', is_model_meta_subclass)
    suppress_message(linter, NewStyleConflictChecker.visit_classdef, 'C1001', is_model_meta_subclass)
    suppress_message(linter, ClassChecker.visit_classdef, 'W0232', is_model_meta_subclass)
    suppress_message(linter, MisdesignChecker.leave_classdef, 'R0903', is_model_meta_subclass)
