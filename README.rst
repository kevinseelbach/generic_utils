========
Overview
========

.. start-badges

.. list-table::
    :stub-columns: 1

    * - package
      - |version|


.. |version| image:: https://img.shields.io/pypi/v/generic_utils.svg?style=flat
    :alt: PyPI Package latest release
    :target: https://pypi.python.org/pypi/generic_utils

.. end-badges

A set of generic utility classes and helper functions for Python  development.

generic_utils is a set of generic Python utilities which currently target
Python 2.7.X environments with no other required dependencies.  The code
targets both general production code as well as test utilities to facilitate
easier test generation, management and complexity.

This library is not currently intended to be generally useful to the community at
large as there is work to be done to provide greater Python support as well as
general documentation and upkeep, but has been used successfully in production
environments within the prescribed environments.



Installation
============

::

    pip install generic_utils


Development
===========


Install requirements into a local virtualenv::

    virtualenv env
    env/bin/pip install -e ".[html,cassandra,celery_test,test_utils]"


This project requires available cassandra and redis hosts in order to run the full test-suite.

Redis Setup::

    docker run -d --name test-redis -p 6379:6379 -v /path/to/storage/redis:/data redis

Connect to the container::

    $ docker exec -i -t test-redis /bin/bash
    $ root@7a3377df67f0:/data# redis-cli
    127.0.0.1:6379> SET __THIS_IS_A_TEST_INSTANCE__ True
    OK
    127.0.0.1:6379> exit

Cassandra Setup::

    $ docker run --name test-cassandra -d -p 9042:9042 -p 7000:7000 -v /path/to/storage/cassandra:/var/lib/cassandra cassandra:3.0

Connect to the container::

    $ docker exec -i -t test-cassandra /bin/bash

Open cqlsh and create the python_utils_test keyspace::

    $ cqlsh
    > CREATE KEYSPACE python_utils_test WITH REPLICATION = { 'class' : 'SimpleStrategy', 'replication_factor' : 1} AND DURABLE_WRITES = true;


Configure Cassandra cluster in `tests/local_settings.py` (not in version-control). Replace the values with appropriate
values for your environment::

    CQLENGINE = {
        "TEST_CLUSTER": {
            ConfigKey.CONTACT_POINTS: get_config_value("TEST_CASSANDRA_CONTACT_POINTS", default=["localhost"]),
            ConfigKey.KEYSPACE: get_config_value("TEST_CASSANDRA_KEYSPACE", "python_utils_test"),
            ConfigKey.PORT: get_config_value("TEST_CASSANDRA_PORT", default=9042),
            ConfigKey.USERNAME: get_config_value("TEST_CASSANDRA_USERNAME", default=""),
            ConfigKey.PASSWORD: get_config_value("TEST_CASSANDRA_PASSWORD", default=""),
            ConfigKey.DEFAULT_TIMEOUT: EXPLICTLY_NOT_10_SECONDS_TIMEOUT
        }
    }

Run the test suite::

    nosetests tests



Note, to combine the coverage data from all the tox environments run:

.. list-table::
    :widths: 10 90
    :stub-columns: 1

    - - Windows
      - ::

            set PYTEST_ADDOPTS=--cov-append
            tox

    - - Other
      - ::

            PYTEST_ADDOPTS=--cov-append tox
