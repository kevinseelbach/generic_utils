"""Tools for dealing with JSON
"""
# stdlib
import datetime
import json


class JSONEncoder(json.JSONEncoder):
    """Standard sane JSONEncoder that can be used for json serialization instead of the default one shipped with python
    """
    def default(self, obj):  # pylint: disable=method-hidden
        """Default encoding
        """
        if isinstance(obj, (datetime.datetime, datetime.date)):
            return obj.isoformat()
        return super(JSONEncoder, self).default(obj)


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
    """Wrapper around json.loads which augments the out of the box capability to add some additional decoding abilities.

    Currently this is just an empty wrapper/hook to provide a logical pairing with the `dumps` method in this module
    which may evolve over time
    """
    json.loads(s, *args, **kwargs)
