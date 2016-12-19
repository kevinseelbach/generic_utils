# stdlib
from unittest import TestCase

from generic_utils import loggingtools
from generic_utils.datetimetools import utcnow
from generic_utils.json_tools import serialization
from generic_utils.test.datetime_utils import EST

log = loggingtools.getLogger()


class MySerializationObject(object):
    some_prop = None

    def __init__(self, some_prop):
        self.some_prop = some_prop

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__


class BidirectionalSerializationTestCase(TestCase):
    """Test case which validates that python objects can be serialized through JSON and deserialized back to the
    original python objects
    """

    def test_core_types(self):
        """Validates core python to json types survive the round trip serialization/deserialization
        """
        ### SETUP
        orig_obj = {
            "str": "This is a string",
            "int": 1,
            "bool": True,
            "dict": {
                "val": "yup"
            },
            "list": [1, 2, 3]
        }

        ### EXECUTION
        json_rep = serialization.dumps(orig_obj)
        log.debug("Json rep %s", json_rep)
        deserialized = serialization.loads(json_rep)

        ### VALIDATION
        self.assertEqual(orig_obj, deserialized)

    def test_date_types(self):
        """Validates datetime types survive round trip
        """
        ### SETUP
        orig_obj = {
            "datetime": utcnow(),
            # Validate that correct time value survives serialization for a non-utc datetime;  Note that while the
            # absolute datetime relative to UTC will be maintained, the tzinfo is currently lost such that this fails:
            # self.assertEqual(deserialized["eastern_datetime"].tzinfo, orig_obj["eastern_datetime"].tzinfo)
            "eastern_datetime": utcnow().astimezone(EST()),
            "date": utcnow().date()
        }

        ### EXECUTION
        json_rep = serialization.dumps(orig_obj)
        log.debug("Json rep %s", json_rep)
        deserialized = serialization.loads(json_rep)

        ### VALIDATION
        self.assertEqual(orig_obj, deserialized)

    def test_arbitrary_class(self):
        """Validates that an arbitrary class can be serialized/deserialized
        """
        ### SETUP
        obj_instance = MySerializationObject("dont care")

        ### EXECUTION
        json_rep = serialization.dumps(obj_instance)
        log.debug("JSON rep '%s'", json_rep)
        deserialized = serialization.loads(json_rep)

        ### VALIDATION
        self.assertEqual(obj_instance, deserialized)
