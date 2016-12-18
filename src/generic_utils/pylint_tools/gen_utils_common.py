"""Tools to improve pylint introspection"""
import os
import re
# These imports are *sort-of* dangerous in that python-utils does not declare a dependency on any of these, but since
# this specific package and modules are only meant to be run within pylint we are assuming that the pylint environment
# is setup as expected which includes pylint_django and pylint_plugin_utils.  The more appropriate way to do this is
# to create a whole new pylint plugin python package, but the need is not quite there yet.
from astroid import MANAGER
from astroid.builder import AstroidBuilder
from astroid import nodes, InferenceError
from pylint.checkers.typecheck import TypeChecker
from pylint_django.utils import node_is_subclass
from pylint_plugin_utils import augment_visit
from . import augmentations


def _add_module_transform(package_name, *class_names):
    transforms_dir = os.path.join(os.path.dirname(__file__), 'transforms')
    fake_module_path = os.path.join(transforms_dir, '%s.py' % re.sub(r'\.', '_', package_name))

    with open(fake_module_path) as modulefile:
        fake_module = modulefile.read()

    fake = AstroidBuilder(MANAGER).string_build(fake_module)

    def set_fake_locals(module):
        if module.name != package_name:
            return
        for class_name in class_names:
            module.locals[class_name] = fake.locals[class_name]

    MANAGER.register_transform(nodes.Module, set_fake_locals)


def factory_dynamic_attributes(chain, node):
    """A pylint augmentation method which augments a TypeCheck visit on Factory subclasses so that if a getattr
    attempt is made on a Factory then this will actually determine the target class that the factory is for and
    validate the getattr against that whereas by default Pylint would not know about the Metaclass behavior of the
    Factoryboy Factory and would complain with a no-member error.

    The only limitation of this implementation right now is that this suppresses a type check error, but it DOES NOT
    provide type inferring of the requested attribute, which means that if for instance the requested attr is a function
    pylint will not be able to do any additional checking on the usage of the method.  This would normally be done as a
    transform hook, however it appears that at that point in time the whole class hierarchy is not loaded yet so there
    is not a way to do a is_subclass check at that time.  Since this Factory based augementation requires that check
    we have to do it down here.
    """
    children = list(node.get_children())
    for child in children:
        try:
            inferred = child.infered()
        except InferenceError:
            pass
        else:
            for cls in inferred:

                if node_is_subclass(cls, 'factory.base.FactoryMetaClass') or \
                        node_is_subclass(cls, 'factory.base.Factory'):
                    attempted_attr = node.attrname
                    try:
                        # TODO: Broken but not sure how to fix.
                        factory_for_class = cls.getattr("FACTORY_FOR")[0].infered()[0]
                        factory_for_class.getattr(attempted_attr)
                        return
                    except:
                        # Fall through to the chain and let them handle the issue as we can't
                        pass
    chain()


_add_module_transform('django.db.models.fields.files', 'FileField', 'ImageField')


def register(linter):
    """Hook for doing various registrations with pylint for additional functionality."""
    augment_visit(linter, TypeChecker.visit_attribute, factory_dynamic_attributes)
    augmentations.apply_augmentations(linter)

