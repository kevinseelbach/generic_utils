from . import django_rest_framework
from . import django


def apply_augmentations(linter):
    django_rest_framework.apply_augmentations(linter)
    django.apply_augmentations(linter)
