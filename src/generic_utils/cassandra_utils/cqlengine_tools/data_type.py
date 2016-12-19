"""
Module which defines custom Cassandra data types or extensions to core Cassandra data types.
"""
# future/compat
from past.builtins import basestring

# stdlib
import pickle

from cassandra.cqlengine import ValidationError
from cassandra.cqlengine import columns
from cassandra.cqltypes import DateType  # pylint: disable=no-name-in-module
from cassandra.protocol import ResultMessage  # pylint: disable=no-name-in-module

from generic_utils import loggingtools
from generic_utils.datetimetools import utc
from generic_utils.json_tools import serialization

log = loggingtools.getLogger()

# ID for the DateType within the Cassandra protocol
DATETYPE_TYPE_CODE = 0x000B


class TimezoneAwareDateType(DateType):
    """Custom DateType subclass which returns timezone aware datetime results as the core `DateType` returns naive
    datetime objects based on UTC timestamps.  Note that the class MUST have the name "DateType" as that is what
    Cassandra keys off of to do the type mapping.

    To register this DateType with the Cassandra python driver it just needs to be defined as there is an undocumented
    feature of the Cassandra python driver that DateType subclasses leverage a MetaClass which registers the defined
    class against the class name.  Note this method/hack is described in the Cassandra Driver bug
    https://datastax-oss.atlassian.net/browse/PYTHON-145 which is a bug against the fact that datetime's are naive.
    """

    @staticmethod
    def deserialize(byts, protocol_version):
        """Deserialize raw Cass bytes into a python representation
        """
        naive_datetime = DateType.deserialize(byts, protocol_version)
        return naive_datetime.replace(tzinfo=utc)

    @classmethod
    def set_as_default_datetype(cls):
        """Sets the TimezoneAwareDataType as the default data type for the python Cassandra driver to use for
        timestamp data types when communicating with Cassandra
        """
        override_core_response_datatype(DATETYPE_TYPE_CODE, cls)


def override_core_response_datatype(type_code, clazz):
    """Overrides GLOBALLY the DataType class that the Cassandra driver uses to handle responses of type `type_code`.

    :param type_code: The type code within the Cassandra response protocol to assign `clazz` to
    :param clazz: The class to use when a value of type `type_code` is retrieved via the Cassandra protocol
    :return: The previous class that was assigned to `type_code`
    """
    current_clazz = get_response_datatype(type_code)
    try:
        ResultMessage.type_codes[type_code] = clazz
    except AttributeError:
        # backwards compat.
        ResultMessage._type_codes[type_code] = clazz  # pylint: disable=protected-access
    log.debug("Overrode core response type code %s with class %s", type_code, clazz)
    return current_clazz


def get_response_datatype(type_code):
    """Retrieve the current DataType class which is currently assigned for handling of data returned from Cassandra of
    type `type_code`

    :param type_code: The type code within the Cassandra response protocol to retrieve the current assigned DataType for
    :return: The DataType class which is currently assigned for handling of data returned from Cassandra
        of type `type_code`
    """
    try:
        return ResultMessage.type_codes[type_code]
    except AttributeError:
        # backwards compat
        return ResultMessage._type_codes[type_code]  # pylint: disable=protected-access


class ObjectType(columns.Column):
    """Cassandra data type which stores any raw python object in a compatible serialized form and restores it from
    Cassandra.  This will attempt to use JSON serialization but if that fails then it will use Pickle
    """
    db_type = 'text'

    PACKET_FORMAT = "::{serializer}::{serialized_data}"
    JSON_SERIALIZER = "json"
    PICKLE_SERIALIZER = "pickle"

    def to_database(self, value):
        """Convert `value` to a database representation

        :param value: The value to store
        :type value: object
        :return: Representation of `value` which can be stored to cassandra
        :rtype: str
        """
        try:
            log.debug("Attempting to serialize as JSON")
            json_str = serialization.dumps(value)
            str_value = self.PACKET_FORMAT.format(serializer=self.JSON_SERIALIZER,
                                                  serialized_data=json_str)
        except TypeError:
            try:
                log.debug("JSON serialization failed, so attempting pickle")
                pickle_str = pickle.dumps(value)
                str_value = self.PACKET_FORMAT.format(serializer=self.PICKLE_SERIALIZER,
                                                      serialized_data=pickle_str)
            except TypeError:
                log.debug("Pickle serialization failed, so throwing a validation error")
                raise ValidationError("{} cant be serialized via the supported serializers".format(value))
        return str_value

    def to_python(self, value):
        """Convert the stored `value` to a python representation
        """
        if isinstance(value, (str, basestring)) and value.startswith("::"):
            _, serializer, data = value.split("::", 2)
            if serializer == self.JSON_SERIALIZER:
                value = serialization.loads(data)
            elif serializer == self.PICKLE_SERIALIZER:
                value = pickle.loads(data)
            else:
                raise ValidationError("{} is invalid as the serializer {} is unknown".format(value, serializer))

        return value
