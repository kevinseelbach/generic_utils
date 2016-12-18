try:
    from django.db.models.fields.files import FieldFile, ImageFieldFile
except ImportError:
    from generic_utils import loggingtools

    log = loggingtools.getLogger()
    log.warn("Unable to load Django classes, therefore cannot properly inform pylint of some of Django's less obvious "
             "attributes and methods on some classes.  Pylint may be noisy as a result when running against a Django "
             "project")
    FieldFile = object
    ImageFieldFile = object


class FileField(FieldFile):
    pass


class ImageField(ImageFieldFile):
    pass
