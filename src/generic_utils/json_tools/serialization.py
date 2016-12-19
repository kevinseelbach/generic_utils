"""Base implementation of JSON serialization which provides bidirectional serialization from python to json and back to
python.  This is interesting because some of the data types in python are not directly supported in JSON so while you
can generate a JSON representation there is no going back.
"""
# stdlib
import datetime
import json

from generic_utils.classtools import get_class_from_fqn
from generic_utils.classtools import get_classfqn
from generic_utils.datetimetools import utc

OBJ_TYPE_KEY = "__type__"
OBJ_VALUE_KEY = "__value__"


class JSONEncoder(json.JSONEncoder):
    """JSON Encoder which encodes objects in a way that, while not representable as accurate JSON objects, can be
    decoded back to python
    """
    def default(self, obj):  # pylint: disable=method-hidden
        """Default encoding
        """
        if isinstance(obj, (datetime.datetime, datetime.date)):
            # Currently this forces UTC and does not retain the original timezone through the serialization.
            # This should be fine for right now as everything should be stored in UTC anyway, but this could be a
            # problem in some cases at which point we need to address it
            if isinstance(obj, datetime.datetime):
                if not obj.tzinfo:
                    obj = obj.replace(tzinfo=utc)
                obj = obj.astimezone(tz=utc)
            return {
                OBJ_TYPE_KEY: get_classfqn(obj),
                OBJ_VALUE_KEY: obj.strftime("%Y-%m-%dT%H:%M:%S.%f%z")
            }

        try:
            return super(JSONEncoder, self).default(obj)
        except TypeError:
            if hasattr(obj, "__getstate__"):
                obj_value = obj.__getstate__()
                print("Object-value = %r" % obj_value)
            else:
                obj_value = obj.__dict__
            return {
                OBJ_TYPE_KEY: get_classfqn(obj),
                OBJ_VALUE_KEY: obj_value
            }


def dumps(obj, *args, **kwargs):
    """Wrapper around json.dumps which leverages the sane JSON encoder.  Args and kwargs passed into this are just
    fed down into `json.dumps` so see the args for that for details
    :param obj: The object to serialize
    :return: JSON representation of 'obj'
    :rtype: str
    """
    kwargs["cls"] = JSONEncoder
    return json.dumps(obj, *args, **kwargs)


def loads(s, *args, **kwargs):  # pylint: disable=invalid-name
    """Wrapper around the core json.loads which supports object serialization and deserialization through json as
    the protocol.  Given a `s` which was generated from the `dumps` method in this module this will return the
    appropriate python representation
    """
    kwargs["object_hook"] = get_object_hook(kwargs.get("object_hook", None))
    return json.loads(s, *args, **kwargs)


def get_object_hook(override_hook=None):
    """Method which returns an 'object_hook' method suitable as an 'object_hook' kwarg for json.loads for loading
    a json representation generated from the JSONEncoder in this module.
    """
    def _object_hook(obj):
        """Actual object hook implementation which gives `override_hook` a shot at converting the obj, and then
        checks to see if the `obj` represents a complex object and if so attempts to convert it to the native
        python representation
        """
        if override_hook:
            obj = override_hook(obj)
        if OBJ_TYPE_KEY in obj:
            clazz = get_class_from_fqn(obj[OBJ_TYPE_KEY])
            """:type:type"""
            if issubclass(clazz, datetime.datetime):
                return datetime.datetime.strptime(obj[OBJ_VALUE_KEY], r"%Y-%m-%dT%H:%M:%S.%f+0000").replace(tzinfo=utc)
            elif issubclass(clazz, datetime.date):
                return datetime.datetime.strptime(obj[OBJ_VALUE_KEY], r"%Y-%m-%dT%H:%M:%S.%f").date()
            obj_state = obj[OBJ_VALUE_KEY]
            obj = clazz.__new__(clazz)
            if hasattr(obj, "__setstate__"):
                obj.__setstate__(obj_state)
            else:
                obj.__dict__ = obj_state

        return obj
    return _object_hook
