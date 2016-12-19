"""
Functions which support creating dicts (mappings) with interesting structures and simplify getting or setting
 values which may be nested deeply within the object.
"""
from __future__ import absolute_import

# stdlib
import collections


def query_json_struct_from_path(json_struct, path):
    """
    Query the json structure given the path expression
    :param json_struct: A json structure / dictionary
    :param path: The path to use to locate the data value being requested
    :return:
    """
    if json_struct is None:
        return None
    assert isinstance(json_struct, collections.Mapping)
    if path is None or not (isinstance(path, str) or isinstance(path, str)):
        return None
    else:
        return path_query(json_struct, path.split('.'))


def path_query(json_struct, path_elts, default_val=None):
    """
    QUery the json structure given an array of path elements
    :param json_struct: A json structure / dictionary
    :param path_elts: The elements in the path to follow
    :param default_val: The value to return in=f there is no value at the given path
    :return:
    """
    if not json_struct or not isinstance(json_struct, collections.Mapping):
        return default_val
    elif not path_elts:
        return default_val
    elif len(path_elts) == 1:
        return json_struct.get(path_elts[0], default_val)
    else:  # len(path_elts) > 1
        next_step = json_struct.get(path_elts[0], None)
        return path_query(next_step, path_elts[1:])


def increment_json_value_from_path(json_struct, path, value):
    """
    Increment the numeric value for the path, creating the path if necessary
    :param json_struct: The json object to increment
    :param path: The path to the selected numeric value
    :param value: The value to add, use negative values to subtrreact
    :return:
    """
    if json_struct is None:
        json_struct = {}
    assert isinstance(json_struct, collections.Mapping)

    default_val = 0
    path_elts = path.split('.')
    previous_val = path_query(json_struct, path_elts, default_val=default_val)
    new_val = previous_val + value
    return update_json_struct_add(json_struct, path_elts, new_val)


def multi_update_json_struct(json_struct, new_attr_vals, delete_data=False):
    """
    This function will do multiple calls to update_json_struct_from_path on the same json record
    :param json_struct: The input json record
    :param new_attr_vals: A dictionary containing, for each update, an entry with the key as a path
        expression to the field being updated and the value being the new value for the field
    :param delete_data: True if you want to remove the information from the json as opposed to adding it
    :return: The updated json record
    """
    if new_attr_vals:
        try:
            for key, val in new_attr_vals.items():
                json_struct = update_json_struct_from_path(json_struct, key, val, delete_data=delete_data)
        except AttributeError:
            pass
    return json_struct


def update_json_struct_from_path(json_struct, path, value, delete_data=False):
    """
    Update the json struct element at path, as directed
    :param json_struct: The json struct to update
    :param path: The path to the element, as a path string, e.g. 'a.b.c'
    :param value: The value you want to add/delete
    :param delete_data: True if you want to delete the value, False if you want to add it
    :return:
    """
    if json_struct is None:
        json_struct = {}
    assert isinstance(json_struct, collections.Mapping)

    if path is None:
        # No place to update this value, so ignore
        return json_struct

    path_elts = path.split('.')
    if not delete_data:
        return update_json_struct_add(json_struct, path_elts, value) if path else json_struct
    else:
        return update_json_struct_delete(json_struct, path_elts, value) if path else json_struct


def make_json_struct(path_elts, value):
    """
    Make a new json structure with a single path, with its endpoint set to value
    :param path_elts: The elements of the path to traverse in the json struct
        to reach the value
    :param value: The value to set at the end of hte path
    :return: The created json struct
    """
    new_struct = dict()
    if not path_elts or len(path_elts) == 0:
        new_struct = None
    elif len(path_elts) == 1:
        new_struct[path_elts[0]] = value
    else:
        new_struct[path_elts[0]] = make_json_struct(path_elts[1:], value)
    return new_struct


def update_json_struct_add(json_struct, path_elts, value):
    """
    Update the json struct element at path, as directed
    :param json_struct: The json struct to update
    :param path_elts: The path to the element, as a path string, e.g. 'a.b.c'
    :param value: The value you want to add/delete
    :return:
    """
    if json_struct is None:
        json_struct = {}
    assert isinstance(json_struct, collections.Mapping)

    if not path_elts or len(path_elts) == 0:
        updated = json_struct

    elif json_struct == {}:
        updated = make_json_struct(path_elts, value)

    else:
        key = path_elts[0]
        val = json_struct.get(key, None)
        updated = dict(json_struct)

        if len(path_elts) == 1:
            # if both the value to be updated, and the new value are lists, the extend the existing list.
            if key in updated and isinstance(value, list) and isinstance(updated[key], list):
                updated[key].extend(value)
                # Need to remove duplicates
                updated[key] = list(set(updated[key]))
            else:
                updated[key] = value
        else:
            rest_of_path = path_elts[1:]
            if not val or not isinstance(val, collections.Mapping):
                updated[key] = make_json_struct(rest_of_path, value)
            else:
                updated[key] = update_json_struct_add(val, rest_of_path, value)

    return updated


def update_json_struct_delete(json_struct, path_elts, value):
    """
    Update the json struct element at path, as directed
    :param json_struct: The json struct to update
    :param path_elts: The path to the element, as a path string, e.g. 'a.b.c'
    :param value: The value you want to add/delete
    :return:
    """
    if json_struct is None or json_struct == {}:
        return json_struct

    if not path_elts or len(path_elts) == 0:
        return json_struct

    else:
        key = path_elts[0]
        val = json_struct.get(key, None)
        updated = dict(json_struct)

        if len(path_elts) == 1:
            # if both the value to be updated, and the input value are lists,
            # then remove the input elements from the existing list.
            original = updated[key]
            if not value or original == value:
                # Just clear out the field
                updated.pop(key, None)
                if updated == {}:
                    updated = None  # Need to be able to clear out keys all the way up the path
            elif key in updated and isinstance(value, list) and isinstance(updated[key], list):
                # Remove the items from the input list from the json struct
                updated[key] = [x for x in original if x not in value]
        else:
            rest_of_path = path_elts[1:]
            if val and isinstance(val, collections.Mapping):
                new_k = update_json_struct_delete(val, rest_of_path, value)
                if new_k:
                    updated[key] = update_json_struct_delete(val, rest_of_path, value)
                else:
                    updated.pop(key, None)

    return updated
