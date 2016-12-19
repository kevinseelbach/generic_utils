# stdlib
import datetime
import logging

from freezegun import freeze_time

from generic_utils import loggingtools
from generic_utils.datetimetools import utcnow
from generic_utils.loggingtools.loggingconfig import InMemoryLogLevelProvider
from generic_utils.loggingtools.loggingconfig import LevelOverride
from generic_utils.loggingtools.loggingconfig import LogLevelProviderCollection
from generic_utils.test import TestCase

LOG = loggingtools.getLogger()


class LevelOverrideComparisonTestCases(TestCase):

    def test_greater_than(self):
        ### SETUP
        expired_time = utcnow() - datetime.timedelta(hours=1)
        TEST_CASES = [
            # Each tuple contains a left and a right component for which left should be greater than right
            (LevelOverride(logging.DEBUG), LevelOverride(logging.INFO)),
            (LevelOverride(logging.INFO), LevelOverride(logging.DEBUG, expired_time))
        ]

        ### EXECUTION
        for left, right in TEST_CASES:
            self.assertTrue(left > right, "%r should be > %r" % (left.level, right.level))
            self.assertTrue(left != right)
            self.assertFalse(left == right)
            self.assertFalse(left < right)

    def test_equality(self):
        ### SETUP
        expired_time = utcnow() - datetime.timedelta(hours=1)
        TEST_CASES = [
            # Each tuple contains a left and a right component for which left should be equal to right
            (LevelOverride(logging.DEBUG), LevelOverride(logging.DEBUG)),
            (
                LevelOverride(logging.INFO, expired_time),
                LevelOverride(logging.DEBUG, expired_time)
            )
        ]

        ### EXECUTION
        for left, right in TEST_CASES:
            self.assertTrue(left == right)
            self.assertTrue(left >= right)
            self.assertTrue(left <= right)
            self.assertFalse(left != right)
            self.assertFalse(left > right)
            self.assertFalse(left < right)


class LogLevelProviderTestCases(TestCase):
    """Test cases which validate the behavior of the base LogLevelProvider class as well as the InMemoryLogLevelProvider
    subclass
    """

    def setUp(self):
        self.log_name = LOG.name
        self.initial_level = LOG.level
        # Create a new level to make sure we don't clash based on environment conf
        self.override_level = self.initial_level + 1

    def test_basic_override(self):
        ### SETUP
        provider = InMemoryLogLevelProvider()

        ### EXECUTION
        self.assertEqual(provider.get_log_level(self.log_name), self.initial_level)
        provider.apply_overrides({self.log_name: LevelOverride(self.override_level)})

        ### VALIDATION
        self.assertTrue(provider.is_overridden(self.log_name))
        self.assertEqual(provider.get_log_level(self.log_name), self.override_level)

    def test_override_expiration(self):
        """Validates that an applied override is properly expired
        """
        ### SETUP
        provider = InMemoryLogLevelProvider()
        now = utcnow()
        expiration_date = now + datetime.timedelta(hours=1)

        ### EXECUTION
        provider.apply_overrides({self.log_name: LevelOverride(self.override_level, expiration_date)})
        self.assertEqual(provider.get_log_level(self.log_name), self.override_level, "Override should be valid still")

        with freeze_time(expiration_date + datetime.timedelta(seconds=1)):
            self.assertFalse(provider.is_overridden(self.log_name))
            self.assertEqual(provider.get_log_level(self.log_name), self.initial_level, "Override should have expired")

    def test_remove_overrides(self):
        """Validates that removing overrides on the InMemoryLogLevelProvider works as expected
        """
        ### SETUP
        provider = InMemoryLogLevelProvider()
        provider.apply_overrides({self.log_name: LevelOverride(self.override_level)})
        self.assertTrue(provider.is_overridden(self.log_name))

        ### EXECUTION
        provider.remove_overrides(self.log_name, "bogus.log")

        ### VALIDATION
        self.assertFalse(provider.is_overridden(self.log_name))
        self.assertEqual(provider.get_log_level(self.log_name), self.initial_level)


class LogLevelProviderCollectionTestCase(TestCase):
    """Validates the behavior of the LogLevelProviderCollection
    """

    def setUp(self):
        self.log_name = LOG.name
        self.initial_level = LOG.level
        # Create a new level to make sure we don't clash based on environment conf
        self.override_level = self.initial_level + 1

    def test_basic_functionality(self):
        ### SETUP
        provider1 = InMemoryLogLevelProvider()
        provider2 = InMemoryLogLevelProvider()
        prov_coll = LogLevelProviderCollection(provider1, provider2)

        ### EXECUTION/VALIDATION
        self.assertFalse(prov_coll.is_overridden(self.log_name))

        LOG.debug("Applying override at child provider of collection")
        provider2.apply_overrides({self.log_name: LevelOverride(logging.DEBUG)})
        self.assertTrue(prov_coll.is_overridden(self.log_name))
        self.assertEqual(prov_coll.get_log_level(self.log_name), logging.DEBUG)

    def test_initial_override(self):
        """Validates that the override capability works as expected if a log level was overridden to begin with
        instead of getting updated after the collection was first created.
        """
        ### SETUP
        provider1 = InMemoryLogLevelProvider()
        provider2 = InMemoryLogLevelProvider()
        # Start off with an initial override
        provider2.apply_overrides({self.log_name: LevelOverride(logging.DEBUG)})
        prov_coll = LogLevelProviderCollection(provider1, provider2)

        ### EXECUTION/VALIDATION
        self.assertTrue(prov_coll.is_overridden(self.log_name))
