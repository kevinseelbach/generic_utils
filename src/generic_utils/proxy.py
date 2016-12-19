# future/compat
from builtins import str


class Proxy(object):
    """
    Proxies an object and allows for injecting behavior into the representation of the object without modifying the
    underlying object.

    When creating an instance of this object you can provide the following:

    Positional Arguments

        1 - The object to proxy

    Arguments:

        'property_map' - A dict where the key is the name of a attribute to expose on the proxy and the value is
                                the attribute of the proxied object to proxy any requests for that attribute to.  For
                                instance, {"x": "y"} would proxy any requests for attribute proxy.x to object.y

    """
    __slots__ = ["_obj", "__weakref__"]
    property_map = None

    def __init__(self, obj, property_map=None):
        object.__setattr__(self, "property_map", property_map)
        object.__setattr__(self, "_obj", obj)

    def __getattr__(self, item):
        if item in ["__getstate__", "__setstate__", "__reduce_ex__", "__reduce__"]:
            return object.__getattribute__(self, item)
        item = object.__getattribute__(self, "_get_attr_name")(item)
        attr = getattr(object.__getattribute__(self, "_obj"), item)

        return attr

    def __getattribute__(self, name):
        if name in ["__getstate__", "__setstate__", "__reduce_ex__", "__reduce__"]:
            return object.__getattribute__(self, name)
        name = object.__getattribute__(self, "_get_attr_name")(name)
        attr = getattr(object.__getattribute__(self, "_obj"), name)

        return attr

    def __delattr__(self, name):
        name = object.__getattribute__(self, "_get_attr_name")(name)
        delattr(object.__getattribute__(self, "_obj"), name)

    def __setattr__(self, name, value):
        name = object.__getattribute__(self, "_get_attr_name")(name)
        setattr(object.__getattribute__(self, "_obj"), name, value)

    def __bool__(self):
        return bool(object.__getattribute__(self, "_obj"))

    def __str__(self):
        return str(object.__getattribute__(self, "_obj"))

    def __repr__(self):
        return repr(object.__getattribute__(self, "_obj"))

    def __reduce_ex__(self, *args, **kwargs):
        clazz = object.__getattribute__(self, "__class__")
        return (
            object.__getattribute__(self, "__class__").__base_class__,
            (
                object.__getattribute__(self, "_obj"),
                object.__getattribute__(self, "property_map")
            )
        )

    #
    # factories
    #
    _special_names = [
        '__abs__', '__add__', '__and__', '__call__', '__cmp__', '__coerce__',
        '__contains__', '__delitem__', '__delslice__', '__div__', '__divmod__',
        '__eq__', '__float__', '__floordiv__', '__ge__', '__getitem__',
        '__getslice__', '__gt__', '__hash__', '__hex__', '__iadd__', '__iand__',
        '__idiv__', '__idivmod__', '__ifloordiv__', '__ilshift__', '__imod__',
        '__imul__', '__int__', '__invert__', '__ior__', '__ipow__', '__irshift__',
        '__isub__', '__iter__', '__itruediv__', '__ixor__', '__le__', '__len__',
        '__long__', '__lshift__', '__lt__', '__mod__', '__mul__', '__ne__',
        '__neg__', '__oct__', '__or__', '__pos__', '__pow__', '__radd__',
        '__rand__', '__rdiv__', '__rdivmod__',
        '__repr__', '__reversed__', '__rfloorfiv__', '__rlshift__', '__rmod__',
        '__rmul__', '__ror__', '__rpow__', '__rrshift__', '__rshift__', '__rsub__',
        '__rtruediv__', '__rxor__', '__setitem__', '__setslice__', '__sub__',
        '__truediv__', '__xor__', 'next',
    ]

    @classmethod
    def _create_class_proxy(cls, theclass):
        """creates a proxy for the given class"""

        def make_method(name):
            def method(self, *args, **kw):
                return getattr(object.__getattribute__(self, "_obj"), name)(*args, **kw)
            return method

        namespace = {}
        for name in cls._special_names:
            if hasattr(theclass, name):
                namespace[name] = make_method(name)
        new_class = type("%s(%s)" % (cls.__name__, theclass.__name__), (cls,), namespace)
        new_class.__base_class__ = cls
        return new_class

    def __new__(cls, obj, *args, **kwargs):
        """
        creates an proxy instance referencing `obj`. (obj, *args, **kwargs) are
        passed to this class' __init__, so deriving classes can define an
        __init__ method of their own.
        note: _class_proxy_cache is unique per deriving class (each deriving
        class must hold its own cache)
        """
        try:
            cache = cls.__dict__["_class_proxy_cache"]
        except KeyError:
            cls._class_proxy_cache = cache = {}
        try:
            theclass = cache[obj.__class__]
        except KeyError:
            cache[obj.__class__] = theclass = cls._create_class_proxy(obj.__class__)
        ins = object.__new__(theclass)
        theclass.__init__(ins, obj, *args, **kwargs)
        return ins

    def _get_attr_name(self, item):
        """Returns the name to use for accessing a attribute in the proxied object
        """
        try:
            property_map = object.__getattribute__(self, "property_map")
            if property_map and item in property_map:
                item = property_map[item]
        except AttributeError:
            pass

        return item

#
#
# ------ example ------
# >>> p = Proxy(6)
# >>> p
# 6
# >>> type(p)
# <class '__main__.Proxy(int)'>
# >>> p + 2
# 8
# >>> p2 = Proxy([1,2,3])
# >>> p2
# [1, 2, 3]
# >>> dir(p2)
# ['__add__', '__class__', '__contains__', '__delattr__', '__delitem__ #...
# '__getslice__', '__gt__', '__hash__', '__iadd__', '__imul__', '__ini #...
# educe__', '__reduce_ex__', '__repr__', '__reversed__', '__rmul__', ' #...
# 'index', 'insert', 'pop', 'remove', 'reverse', 'sort']
# >>> isinstance(p2, list)
# True
# >>> p2.append(8)
# >>> p2.append(2)
# >>> p2.append(5)
# >>> p2
# [1, 2, 3, 8, 2, 5]
# >>> p2.sort()
# >>> p2
# [1, 2, 2, 3, 5, 8]
# >>> p2[2]
# 2
# >>> p2[-1]
# 8
# >>> type(p2)
# <class '__main__.Proxy(list)'>
# >>> p2.__class__
# <type 'list'>
#
# ----- exceptions -----
# Proxying user-types should work perfectly well. But proxying builtin objects,
# like ints, floats, lists, etc., has some limitation and inconsistencies,
# imposed by the interpreter:
#
# >>> p = Proxy(6)
# >>> p + p
# Traceback (most recent call last):
#   File "<stdin>", line 1, in ?
# TypeError: unsupported operand type(s) for +: 'Proxy(int)' and 'Proxy(int)'
#
#
# >>> Proxy([1,2,3]) + [4,5]
# [1, 2, 3, 4, 5]
# >>> Proxy([1,2,3]) + Proxy([4,5])
# >>> p = Proxy([1,2,3])
# >>> p.extend(Proxy([4,5]))
# >>> p
# [1, 2, 3, 4, 5]
# >>> p + Proxy([6, 7])
# Traceback (most recent call last):
#   File "<stdin>", line 1, in ?
#   File "Proxy.py", line 49, in method
#     return getattr(object.__getattribute__(self, "_obj"), name)(*args, **kw)
# TypeError: can only concatenate list (not "Proxy(list)") to list
#
#
# Also note that the methods of a proxied type return "real objects", not
# proxies. So,
#
# >>> p = Proxy(3)
# >>> type(p)
# <class '__main__.Proxy(int)'>
# >>> p + 1
# 4
# >>> type(_)
# <type 'int'>
# >>> p += 1
# >>> p
# 4
# >>> type(p)
# <type 'int'>
#
# In this case, 'p' was reassigned a real integer, and the proxy was
# garbage-collected. What you might want to do is
#
# >>> p = Proxy(3)
# >>> p = Proxy(p + 1)
# >>> p
# 4
# >>> type(p)
# <class '__main__.Proxy(int)'>
