from nose.plugins.attrib import get_method_attr

from generic_utils.test import JIRA_ATTR_NAME
from generic_utils.test import TestCase
from generic_utils.test import bad_data
from generic_utils.test import data
from generic_utils.test import jira
from generic_utils.test import test_generator


class AttrTestCase(TestCase):
    TEST_ATTR = None

    def _get_attr(self, method, attr=None):
        attr = attr or self.TEST_ATTR
        return get_method_attr(method, self.__class__, attr, None)


class TestMethodDecoratorTestCase(AttrTestCase):
    TEST_ATTR = JIRA_ATTR_NAME

    @jira()
    def test_jira_decorator_no_issue(self):
        """Validates that applying no Jira ticket on a method is exposed correctly as a nose attribute
        """
        jira_attr = self._get_attr(self.test_jira_decorator_no_issue)
        self.assertListEqual(list(jira_attr), [])

    @jira("DJUTILS-3")
    def test_jira_decorator_single_issue(self):
        """Validates that applying a single Jira ticket on a method is exposed correctly as a nose attribute
        """
        jira_attr = self._get_attr(self.test_jira_decorator_single_issue)
        self.assertListEqual(list(jira_attr), ["DJUTILS-3"])

    @jira("DJUTILS-3", "BOGUS-1")
    def test_jira_decorator_multiple_issues(self):
        """Validates that applying multiple Jira tickets on a method is exposed correctly as a nose attribute
        """
        jira_attr = self._get_attr(self.test_jira_decorator_multiple_issues)
        self.assertListEqual(list(jira_attr), ["DJUTILS-3", "BOGUS-1"])

    @jira("DJUTILS-10", resolved=False)
    def test_jira_decorator_resolved_flag(self):
        """Validates that when using the resolved keyword when a test fails that is treated as a success
        """
        self.fail("Since the test is flagged as resolved=False, the final result of the test should be treated as a "
                  "success and this failure will not bubble up.  If you see this message in a test result, then the "
                  "'resolved' kwarg is not working as expected.")

generator_with_func_count = 0  # pylint: disable=invalid-name

class TestGeneratorDecoratorTestCase(TestCase):
    """
    Test case which validates that the `test_generator` decorator properly generates new tests on a TestCase
    """

    def _generator_func(test_func):  # pylint: disable=no-self-argument
        def _test_outer_wrapper(val, expect_fail):
            def _test_inner_wrapper(self):
                try:
                    test_func(self, val)
                    if expect_fail:
                        raise AssertionError("Test should have failed with value %s" % val)
                except:  # pylint: disable=bare-except
                    if not expect_fail:
                        raise
            return _test_inner_wrapper
        DATA_CASES = [
            (0, False),
            (1, False),
            (2, True)
        ]
        for val, expect_fail in DATA_CASES:
            yield _test_outer_wrapper(val, expect_fail), (val, expect_fail)

    @test_generator(_generator_func)
    def test_generator_with_func(self, val):
        self._test_generated_val(val)

    @data(0, 1)
    @bad_data(2, 3)
    def test_data_driven(self, val):
        self._test_generated_val(val)

    @bad_data(2, 3)
    @bad_data((4,), (5,), unpack=True)
    def test_data_driven_expected_failure(self, val):
        self._test_generated_val(val)

    def _test_generated_val(self, val):
        global generator_with_func_count  # pylint: disable=global-statement, invalid-name
        generator_with_func_count += 1  # Log that this was called

        self.assertTrue(val < 2)

    def test_z_validate_generator_behavior(self):
        """Validates that the generator tests were created as expected in the previous tests of this test case.  This
        is named intentionally to be last in alphabetical order as it needs to run after all of the other tests to
        validate the appropriate number of tests were generated and executed.
        """
        self.assertEqual(generator_with_func_count, 11)
