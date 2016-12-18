"""Tests for `mapping_utils`"""
from unittest import TestCase
from generic_utils import json_utils as ju

UPDATE = 'update'
PATH = 'path'
VALUE = 'new_value'
EXPECTED = 'expected'


class UpdateJsonTestCase(TestCase):
    def setUp(self):
        pass

    def test_path_query(self):
        self.assertIsNone(ju.path_query(None, None))
        self.assertIsNone(ju.path_query(None, ['a']))
        try:
            self.assertIsNone(ju.path_query('abcde', ['a']))
        except AssertionError:
            pass
        self.assertIsNone(ju.path_query({'a': 1}, None))
        self.assertIsNone(ju.path_query({'a': 1}, []))
        self.assertIsNone(ju.path_query({'a': 1}, None))
        self.assertEquals(ju.path_query({'a': 1}, 'a'), 1)
        self.assertEquals(ju.path_query({'a': {'b': 2}}, ['a']), {'b': 2})
        self.assertEquals(ju.path_query({'a': {'b': 2}}, ['a', 'b']), 2)
        self.assertIsNone(ju.path_query({'a': {'b': 2}}, ['a', 'b', 'c']))

    def test_increment_json_value_from_path(self):
        # increment_json_value_from_path(json_struct, path, value)
        json_struct = {}
        json_struct = ju.increment_json_value_from_path(json_struct, 'a.b', 2)
        self.assertEqual(json_struct, {'a': {'b': 2}})
        json_struct = ju.increment_json_value_from_path(json_struct, 'a.b', 4)
        self.assertEqual(json_struct, {'a': {'b': 6}})
        json_struct = ju.increment_json_value_from_path(json_struct, 'a.b', -5)
        self.assertEqual(json_struct, {'a': {'b': 1}})

    def test_query_json_struct_from_path(self):
        self.assertEquals(ju.query_json_struct_from_path({'a': {'b': 2}}, 'a.b'), 2)

    def test_make_json_struct(self):
        self.assertIsNone(ju.make_json_struct(None, 'foo'))
        self.assertEquals(ju.make_json_struct(['a'], 'foo'), {'a': 'foo'})
        self.assertEquals(ju.make_json_struct(['a', 'b', 'c'], 'foo'), {'a': {'b': {'c': 'foo'}}})

    def test_update_json_struct_add(self):
        """
        Test the different ways you can add new things to a json struct
        :return:
        """
        json_struct = dict()
        self.assertEquals(ju.update_json_struct_add(json_struct, None, 'foo'), json_struct)
        self.assertEquals(ju.update_json_struct_add(json_struct, ['a'], 'foo'), {'a': 'foo'})
        self.assertEquals(ju.update_json_struct_add(json_struct, ['a', 'b', 'c'], 'foo'), {'a': {'b': {'c': 'foo'}}})

        json_struct = {'a': None}
        self.assertEquals(ju.update_json_struct_add(json_struct, None, 'foo'), json_struct)
        self.assertEquals(ju.update_json_struct_add(json_struct, ['a'], 'foo'), {'a': 'foo'})
        self.assertEquals(ju.update_json_struct_add(json_struct, ['a', 'b', 'c'], 'foo'), {'a': {'b': {'c': 'foo'}}})

        json_struct = {'a': {'b': None}}
        self.assertEquals(ju.update_json_struct_add(json_struct, None, 'foo'), json_struct)
        self.assertEquals(ju.update_json_struct_add(json_struct, ['a', 'b'], 'foo'), {'a': {'b': 'foo'}})
        self.assertEquals(ju.update_json_struct_add(json_struct, ['a', 'b', 'c'], 'foo'), {'a': {'b': {'c': 'foo'}}})

        json_struct = {'a': {'b': 'something else'}}
        self.assertEquals(ju.update_json_struct_add(json_struct, None, 'foo'), json_struct)
        self.assertEquals(ju.update_json_struct_add(json_struct, ['a', 'b'], 'foo'), {'a': {'b': 'foo'}})
        self.assertEquals(ju.update_json_struct_add(json_struct, ['a', 'b', 'c'], 'foo'), {'a': {'b': {'c': 'foo'}}})

        json_struct = {'a': {'b': ['something else']}, 'x': {'y': "this should stay around"}}
        self.assertEquals(ju.update_json_struct_add(json_struct, None, 'foo'), json_struct)
        self.assertEquals(ju.update_json_struct_add(json_struct, ['a', 'b'], 'foo'),
                          {'a': {'b': 'foo'}, 'x': {'y': "this should stay around"}})
        self.assertEquals(ju.update_json_struct_add(json_struct, ['a', 'b', 'c'], 'foo'),
                          {'a': {'b': {'c': 'foo'}}, 'x': {'y': "this should stay around"}})

        json_struct = {'a': [1]}
        self.assertEquals(ju.update_json_struct_add(json_struct, ['a'], [2, 3]), {'a': [1, 2, 3]})
        self.assertEquals(ju.update_json_struct_add(json_struct, ['a'], [2, 3]), {'a': [1, 2, 3]})

    def test_update_json_struct_from_path(self):
        """
        Test adding information to a json struct
        :return:
        """
        json_struct = {'a': {'b': ['something else']},
                       'x': {'y': "this should stay around"}}

        test_1 = ju.update_json_struct_from_path(json_struct, None, 'foo')
        self.assertEqual(test_1, json_struct)

        test_2 = ju.update_json_struct_from_path(json_struct, 'a', 'foo')
        self.assertEqual(test_2, {'a': 'foo', 'x': {'y': "this should stay around"}})

        test_3 = ju.update_json_struct_from_path(json_struct, 'a.b.c', 'foo')
        self.assertEqual(test_3, {'a': {'b': {'c': 'foo'}}, 'x': {'y': "this should stay around"}})

        test_4 = ju.update_json_struct_from_path(json_struct, 'a.b', ['a', 'b'])
        mylist = test_4['a']['b']
        self.assertEqual(set(mylist), {'something else', 'a', 'b'})
        # {'a': {'b': ['something else', 'a', 'b']}, 'x': {'y': "this should stay around"}})

        test_5 = ju.update_json_struct_from_path(json_struct, 'a.b', 'b')
        self.assertEqual(test_5, {'a': {'b': 'b'}, 'x': {'y': "this should stay around"}})

    def test_update_json_struct_delete(self):
        """
        Test deleting information from a json struct
        :return:
        """
        json_struct = {'a': {'b': ['something else', 'a', 'b']},
                       'x': {'y': "this should stay around",
                             'z': "this should go away"}}
        test_1 = ju.update_json_struct_from_path(json_struct, None, 'foo', delete_data=True)
        self.assertEqual(test_1, json_struct)

        test_2 = ju.update_json_struct_from_path(json_struct, 'a.b', None, delete_data=True)
        self.assertEqual(test_2, {'x': {'y': "this should stay around", 'z': "this should go away"}})

        test_3 = ju.update_json_struct_from_path(json_struct, 'x.z', None, delete_data=True)
        self.assertEqual(test_3, {'a': {'b': ['something else', 'a', 'b']},
                                  'x': {'y': "this should stay around"}})
