"""
ElasticsearchTestCaseMixin module.
"""
from os import environ
from unittest import SkipTest
from elasticsearch import Elasticsearch

from generic_utils import loggingtools
from generic_utils.test import TestCaseMixinMetaClass
from generic_utils.test.category_decorators import integration_test


LOG = loggingtools.getLogger()


def get_es_instance(**kwargs):
    """Return an instance of Elasticsearch based on configured environment variables

    *** WARNING - This has not been tested to work against a REAL elasticsearch cluster. Added because open-sourced
        python-utils had a lingering import from proprietary project.
    :param kwargs: Additional valid kwargs for Elasticsearch client.
    :type kwargs: dict
    :return:
    :rtype: Elasticsearch
    """
    es_hosts = environ.get('ELASTICSEARCH_HOSTS', [])
    es_hosts = list(es_hosts) if not isinstance(es_hosts, list) else es_hosts
    return Elasticsearch(hosts=es_hosts, **kwargs)


@integration_test
class ElasticsearchTestCaseMixin(object):
    """
    Base Elasticsearch test class. It handles setup and teardown and set up Elasticsearch connection.
    """
    __metaclass__ = TestCaseMixinMetaClass

    index_name = "for-testing-only"

    es_client = None

    def _custom_setup(self): # pylint: disable=invalid-name
        """Perform test setup behaviors through the generic_utils setup hook which does not require the
        underlying TestCase method to call super when overriding setUp which could be a source of errors
        """
        self.validate_es_client()
        self.es_client.indices.create(self.index_name)

    def _custom_teardown(self):  # pylint: disable=invalid-name
        """Perform test tearDown behaviors through the generic utils setup hook which does not require the
        underlying TestCase method to call super when overriding tearDown which could be a source of errors
        """
        if self.es_client:
            self.es_client.indices.delete(self.index_name)
            self.es_client = None

    def validate_es_client(self):
        """Skip tests if ELASTICSEARCH_HOSTS is not set."""
        try:
            self.es_client = get_es_instance()
        except Exception:
            LOG.debug("Elasticsearch is not available.  Raising SkipTest")
            self.es_client = None
        if not self.es_client:
            raise SkipTest("Elasticsearch is not configured.")
