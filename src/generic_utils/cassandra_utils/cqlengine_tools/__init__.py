"""Tools and utils for dealing with CQLEngine which is an ORM for Cassandra
"""
try:
    from cassandra import cqlengine
except ImportError:
    raise ImportError("CQLEngine is required for using the cqlengine_tools package.  Make sure this dependency is "
                      "available by adding the python-utils 'cassandra' feature as a dependency.")

from .data_type import TimezoneAwareDateType

TimezoneAwareDateType.set_as_default_datetype()
