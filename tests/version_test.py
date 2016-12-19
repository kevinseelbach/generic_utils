# future/compat
from builtins import range
from builtins import str
from builtins import zip

# stdlib
import hashlib
import inspect
import os
import pickle
import random
from unittest import TestCase

from generic_utils import loggingtools
from generic_utils import versioninfo
from generic_utils.versioninfo import GuidMixin
from generic_utils.versioninfo import Version

log = loggingtools.getLogger()


class TestVersion(TestCase):

    def setUp(self):
        self.v = versioninfo.get_module_version('tests.test_version_module.without_build_info')

    def test_version_info(self):
        self.assertIsNotNone(self.v)
        self.assertEqual(self.v.major, 4)
        self.assertEqual(self.v.year, 5)
        self.assertEqual(self.v.week, 6)
        self.assertEqual(self.v.patch, 7)
        self.assertEqual(self.v.__unicode__(), "4.05.06.7")
        self.assertEqual(self.v.build, None,
                         "build_number should be None as this module doesn't have a build.py")

    def test_version_info_with_build(self):
        v = versioninfo.get_module_version('tests.test_version_module.with_build_info')

        self.assertEqual(v.major, 0)
        self.assertEqual(v.year, 1)
        self.assertEqual(v.week, 2)
        self.assertEqual(v.patch, 0)
        self.assertEqual(v.__unicode__(), "0.01.02 - Build 99")
        self.assertEqual(v.build, 99)

    def test_future_version(self):
        # Set release_day_of_week explicitly to Tuesday
        v = Version(major=0, year=13, week=47, patch=5)
        # Default call should return the current version
        self.assertVersionsEqual(v.get_future_version(), v)
        self.assertVersionsEqual(v.get_future_version(major=1),
                                 Version(major=1, year=13, week=47, patch=0))
        self.assertVersionsEqual(v.get_future_version(release=1),
                                 Version(major=0, year=13, week=48, patch=0))
        self.assertVersionsEqual(v.get_future_version(patch=1),
                                 Version(major=0, year=13, week=47, patch=6))

    def test_future_version_on_52_week_rollover(self):
        """Validates that on a year where the final release_day_of_week falls on the 52nd week that when we increment
        passed 52 the year rolls over as expected.  2012 is one of those years, so we explicitly set our version to
        that year
        """
        v = Version(major=0, year=12, week=51, patch=5)
        self.assertVersionsEqual(v.get_future_version(release=1),
                                 Version(major=0, year=12, week=52, patch=0))
        self.assertVersionsEqual(v.get_future_version(release=2),
                                 Version(major=0, year=13, week=0o1, patch=0))

    def test_future_version_on_53_week_rollover(self):
        """Validates that on a year where the final release_day_of_week falls on the 53rd week that when we increment
        passed 53 the year rolls over as expected.  2013 is one of those years, so we explicitly set our version to
        that year
        """
        v = Version(major=0, year=15, week=52, patch=5)
        self.assertVersionsEqual(v.get_future_version(release=1),
                                 Version(major=0, year=15, week=53, patch=0))
        self.assertVersionsEqual(v.get_future_version(release=2),
                                 Version(major=0, year=16, week=0o1, patch=0))

    def test_version_compare(self):
        """Validates that all comparisons for a Version work as expected.  This includes a Version to Version comparison
        as well as Version to Version String comparisons
        """
        FIXED_VAL = 6
        VERSION_COMPONENTS = ["major", "year", "week", "patch", "build"]

        def randomize_attrs(version, names):
            """Creates a copy of `version` with attributes in `names` set to random values"""
            local_version = pickle.loads(pickle.dumps(version))
            for name in names:
                val = random.randint(0, 20)
                setattr(local_version, name, val)
            return local_version

        for i in range(len(VERSION_COMPONENTS)):
            tested_comp = VERSION_COMPONENTS[i]
            log.debug("Testing version component '%s'", tested_comp)
            fuzzy_comps = VERSION_COMPONENTS[i+1:]
            fixed_kwargs = {}
            fixed_kwargs.update(dict(list(zip(VERSION_COMPONENTS, [FIXED_VAL] * len(VERSION_COMPONENTS)))))
            a = Version(**fixed_kwargs)
            b = Version(**fixed_kwargs)

            # Validate equality
            self.assertTrue(a == b)

            # Run tests where a is modified to either be less than or greater than b
            TEST_CASES = [
                ("Only change attribute under test", a, b),

                ("Randomize least significant attributes",
                 randomize_attrs(a, fuzzy_comps), randomize_attrs(b, fuzzy_comps))
            ]
            for case_name, a, b, in TEST_CASES:
                log.debug("Executing test case '%s'", case_name)
                setattr(a, tested_comp, FIXED_VAL - 1)
                self.assertVersionsLessThan(a, b)

                setattr(a, tested_comp, FIXED_VAL + 1)
                self.assertVersionsGreaterThan(a, b)

    def test_next_release(self):
        self.assertVersionsEqual(self.v.next_release, Version(4, 5, 7, 0))

    def test_get_version_info(self):
        vs = versioninfo.get_version_info([
            'tests.test_version_module.with_build_info',
            'a'
        ])

        self.assertIsNotNone(vs[0])
        self.assertIsNone(vs[1])

    def test_version_info_by_filepath(self):
        base_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
        base_dir = os.path.join(base_dir, "test_version_module")
        v = versioninfo.get_module_version_by_filepath("with_build_info",
                                                       base_dir)
        self.assertVersionsEqual(v, Version(major=0, year=1, week=2, patch=0, build=99))

    def test_version_string_parsing(self):
        """Validates that the string parsing capability is working correctly via the `from_string` method of Version
        """
        TEST_CASES = (
            ["1", Version(1)],
            ["0.14", Version(0, 14)],
            ["0.14.03", Version(0, 14, 3)],
            ["0.14.10.4", Version(0, 14, 10, 4)],
            [" 0.14.10.4  ", Version(0, 14, 10, 4)],  # Make sure whitespace is not an issue
            ["0.14.00.4", Version(0, 14, 0, 4)],
            ["0.14.09.1 - Build 1234", Version(0, 14, 9, 1, 1234)],
            ["0.14.09 - Build 1234", Version(0, 14, 9, 0, 1234)],
            # Validate build version short form format
            ["0.14.09-1234", Version(0, 14, 9, 0, 1234)],
            ["0.14.09.1-1234", Version(0, 14, 9, 1, 1234)],
        )

        for case in TEST_CASES:
            log.debug("Testing string '%s' against version %s", case[0], case[1])
            ver = Version.from_string(case[0])
            self.assertVersionsEqual(ver, case[1])

    def test_version_init_from_string(self):
        """Validates that creating a Version object with the first parameter as a string acts as a casting operation
        similar to int("9") == 9
        """
        self.assertVersionsEqual(Version(0, 1, 2, 3, 4), Version("0.01.02.3 - Build 4"))

    def test_version_string_parsing_value_error(self):
        """Validates that if an unparseable string is provided as an init parameter to a Version that an appropriate
        ValueError is thrown
        """
        with self.assertRaises(ValueError):
            Version("this is sooooo bogus")

    def test_version_to_string_options(self):
        """
        Validates that always_include_patch and always_include_build are working properly in to_version_string
        """
        TEST_CASES = (
            [Version(0, 14, 9, 0, 1234), False, False, "0.14.09"],
            [Version(0, 14, 9, 0, 1234), True, False, "0.14.09.0"],
            [Version(0, 14, 9, 0, 1234), True, True, "0.14.09.0-1234"],
            [Version(0, 14, 9, 0, 1234), False, True, "0.14.09-1234"],
            [Version(0, 14, 9, 1, 1234), False, False, "0.14.09.1"],
            [Version(0, 14, 9, 1, 1234), True, False, "0.14.09.1"],
            [Version(0, 14, 9, 1, 1234), True, True, "0.14.09.1-1234"],
            [Version(0, 14, 9, 1, 1234), False, True, "0.14.09.1-1234"],
            # Test for "build is not set" but was explicitly requested.
            [Version(0, 14, 9, 1), False, True, "0.14.09.1"],
        )

        for test in TEST_CASES:
            version_string = test[0].to_version_string(always_include_patch=test[1], always_include_build=test[2])
            self.assertEqual(test[3], version_string)

    def assertVersionsEqual(self, v1, v2):
        log.debug("Asserting equality of versions %s and %s", v1, v2)
        self.assertEqual(v1, v2)

    def assertVersionsLessThan(self, a, b):
        for b_prime in [b, str(b)]:
            log.debug("Checking %s is less than %s", repr(a), repr(b_prime))
            self.assertFalse(a == b_prime)
            self.assertTrue(a < b_prime)
            self.assertFalse(a > b_prime)
            self.assertTrue(b > a)
            self.assertFalse(b < a)

    def assertVersionsGreaterThan(self, a, b):
        for b_prime in [b, str(b)]:
            log.debug("Checking %s is greater than %s", repr(a), repr(b_prime))
            self.assertFalse(a == b_prime)
            self.assertTrue(a > b_prime)
            self.assertFalse(a < b_prime)
            self.assertTrue(b < a)
            self.assertFalse(b > a)


class GuidMixinTestCases(TestCase):
    """Test cases for the GuidMixin"""

    # pylint: disable=abstract-method
    class DummyClassNoInputs(GuidMixin):
        """Dummy Class for housing the Mixin that has NO _get_guid_inputs override (required)"""

    class DummyClass(DummyClassNoInputs):
        """Dummy Class that properly overrides _get_guid_inputs"""

        def _get_guid_inputs(self):
            """Basic input construction"""
            return ["some input", "another input", "another!input~with~~special||chars:::::"]

    def test_bad_class(self):
        """Validate that classes not implementing _get_guid_inputs will throw exception"""

        clazz = self.DummyClassNoInputs()

        self.assertRaises(NotImplementedError, clazz._get_guid_inputs)
        self.assertRaises(ValueError, clazz._generate_guid)

    def test_basic_guid(self):
        """Validate that a basic guid is generated correctly (includes testing for hashing func change)"""

        clazz = self.DummyClass()

        guid_tests = [
            # Hashing method (none default in the mixin to hashlib.sha256, expected hash
            (None, "46e513c2ef7ac301ef10356597dec3b69e28b51d36926521aaa4757944ef6ad2"),
            (hashlib.md5, "40180face84a1b522e8b857bb8ca2b62"),
            (hashlib.sha1, "f2a30846213a4bbfafd39f032ce1331f1ddd1b15"),
        ]

        for hashing_method, expected_hash in guid_tests:
            clazz.hashing_fnc = hashing_method or clazz.hashing_fnc

            self.assertEqual(clazz.guid, expected_hash)
