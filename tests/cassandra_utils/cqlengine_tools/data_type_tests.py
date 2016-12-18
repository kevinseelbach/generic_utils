from cassandra.cqlengine import models, columns
from generic_utils.cassandra_utils.cqlengine_tools.data_type import override_core_response_datatype, \
    DATETYPE_TYPE_CODE, TimezoneAwareDateType
from generic_utils.cassandra_utils.cqlengine_tools.test_utils import CassandraTestCaseMixin
from generic_utils.datetimetools import utcnow
from generic_utils.test import TestCase


class DummyModel(models.Model):
    test_datetime = columns.DateTime(primary_key=True)


class TimezoneAwareDataTypeTestCase(CassandraTestCaseMixin, TestCase):
    """Validates the behaviors of the TimezoneAwareDataType
    """
    test_models = [DummyModel]

    def setUp(self):
        self.current_handler_clazz = override_core_response_datatype(DATETYPE_TYPE_CODE, TimezoneAwareDateType)

    def tearDown(self):
        override_core_response_datatype(DATETYPE_TYPE_CODE, self.current_handler_clazz)

    def core_type_override_test(self):
        """Validates that the TimezoneAwareDataType override works as expected when enabled
        """
        ### SETUP
        some_date = utcnow().replace(microsecond=0)  # Not testing Cassandra's granularity on time, so set ms to 0
        test_model = DummyModel(test_datetime=some_date)
        test_model.save()

        ### EXECUTION
        retrieved_model = DummyModel.objects.all()[0]

        ### VALIDATION
        self.assertEqual(retrieved_model.test_datetime.tzinfo, some_date.tzinfo)
        # The date coming from Cassandra is always going to be UTC, so `some_date` must be UTC
        self.assertEqual(retrieved_model.test_datetime, some_date)
