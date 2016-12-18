"""Utilities for dealing with Cassandra
"""
try:
    import cassandra
except ImportError:
    raise ImportError("The python Cassandra driver is required for using the cassandra_utils package.  Make sure this "
                      "dependency is available by adding the python-utils 'cassandra' feature as a dependency.")
