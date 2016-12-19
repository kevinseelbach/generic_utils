# future/compat
from future.utils import with_metaclass

# stdlib
import inspect


class MetaClass(type):
    def __new__(self, classname, classbases, classdict):
        try:
            frame = inspect.currentframe()
            frame = frame.f_back
            if classname in frame.f_locals:
                old_class = frame.f_locals.get(classname)
                for name, func in list(classdict.items()):
                    if inspect.isfunction(func):
                        setattr(old_class, name, func)
                return old_class
            return type.__new__(self, classname, classbases, classdict)
        finally:
            del frame


class MetaObject(with_metaclass(MetaClass, object)):
    pass
