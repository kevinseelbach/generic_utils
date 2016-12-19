"""Various tools for working with the Cassandra schema
"""
# future/compat
from past.builtins import basestring

# stdlib
import inspect
from importlib import import_module

from cassandra import AlreadyExists
from cassandra.cqlengine import connection as cql_connection
from cassandra.cqlengine import management
from cassandra.cqlengine.connection import get_cluster
from cassandra.cqlengine.models import Model as cqlengine_Model

from generic_utils import loggingtools
from generic_utils.cassandra_utils.cqlengine_tools.connection import setup_connection_from_config
from generic_utils.typetools import as_iterable

log = loggingtools.getLogger()

CQL_MODULE_NAME = "cql_models"


def sync_db(packages=None, modules=None, *keyspaces):
    """Syncs all cassandra models defined in `cql_models` modules within the provided python 'packages' and/or in the
    explicitly provided `modules` which contain CQLEngine models.

    :param packages: The packages to look for Cassandra models in.
    :type packages: list of str or list of object
    :param modules: Additional modules to discover models from.  This should be a list of strings and/or modules
    :param keyspaces: List of keyspaces to only sync models for.  If this is not provided then all keyspaces are
        sync'ed.
    :return: Whether or not the Cassandra DB was sync'ed
    :rtype: bool
    """
    models_dict = discover_models_from_packages(packages) if packages else {}
    if modules:
        for module in modules:
            models_dict.update(discover_models_from_module(module))
    if not setup_connection_from_config():
        log.warn("Cassandra DB could not be sync'ed because it is not configured.  In most cases this should not cause "
                 "the application to fail, however certain functionality will not be available")
        return False
    for keyspace in models_dict:
        if keyspaces and keyspace not in keyspaces:
            log.debug("Skipping models in keyspace %s", keyspace)
            continue
        if not does_keyspace_exist(keyspace):
            log.debug("Creating keyspace %s", keyspace)
            try:
                # Hardcoding strategy_class and replication_factor for now as a result of a change in cqlengine 0.21.0
                # But will need to expose these as a config option outside of this method at some point
                management.create_keyspace_simple(keyspace, replication_factor=3)
                log.info("Created keyspace %s", keyspace)
            except AlreadyExists:
                log.debug("Keyspace %s already exists", keyspace)
        for model in models_dict[keyspace]:
            log.info("Syncing Cassandra table %s in keyspace %s", model.column_family_name(), keyspace)
            management.sync_table(model)
    return True


def does_keyspace_exist(keyspace):  # pylint: disable=unused-argument
    """Returns whether or not a keyspace `keyspace` exists within the Cassandra cluster

    :param keyspace: The keyspace to validate whether it exists or not.
    :return: Whether or not the requested keyspace exists.
    :rtype: bool
    """
    cluster = get_cluster()
    return keyspace in cluster.metadata.keyspaces


def discover_models_from_packages(packages):
    """
    Discovers CQL Engine models that are defined in set of python packages within a cql_models module.  The list of
    packages is provided in the `apps` parameter

    :param packages: The list of packages to discover CQLEngine models from.  This should be a list of strings or
        object references to packages.
    :type packages: list of str or list of object

    :return: A dictionary which contains all of the discovered CQL Engine model classes keyed by the keyspace defined
        on the class.  A key of None indicates the default keyspace.
    :rtype: dict of (str, cqlengine.Model)
    """
    models = {}
    packages = as_iterable(packages)
    log.debug("Attempting to discover models from packages %s", packages)
    for pkg in packages:
        module_name = ".".join([pkg, CQL_MODULE_NAME])
        try:
            module = import_module(module_name)
            log.debug("Cassandra models module defined for package %s", pkg)
            new_models = discover_models_from_module(module)
            for keyspace, ks_models in list(new_models.items()):
                keyspace_models = models.setdefault(keyspace, [])
                keyspace_models.extend(ks_models)
        except ImportError:
            log.debug("No Cassandra models module defined for package %s", pkg)
            continue

    return models


def discover_models_from_module(module, include_abstract=False):
    """Discovers Cassandra models within the python module `module`.

    :param module: The python module to introspect for Cassandra model class definitions
    :param bool include_abstract: Whether or not to include abstract Cassandra models in the discovery or not.  Default
        is `False`
    :return: A dict of the discovered models within the `module`.  The key of the dict is the keyspace of the models and
        the value is a list of the model Class
    :rtype: dict of (str, type)
    """
    models = {}
    if not module:
        return models
    if isinstance(module, basestring):
        module = import_module(module)

    for attr in dir(module):
        val = getattr(module, attr)
        is_class = inspect.isclass(val)
        log.debug("Property %s - %s : %s - %s",
                  attr, type(val), is_class, is_class and issubclass(val, cqlengine_Model))
        if inspect.isclass(val) and issubclass(val, cqlengine_Model):
            log.debug("Found CQL Model class %s", val.__name__)

            if not include_abstract and getattr(val, "__abstract__", False):
                log.debug("Model is abstract and we are not including abstract models")
                continue

            keyspace = val._get_keyspace()  # pylint: disable=protected-access
            log.debug("Discovered model class %s for keyspace %s", val.__name__, keyspace)
            keyspace_models = models.setdefault(keyspace, [])
            keyspace_models.append(val)

    return models


def truncate_table(model):
    """Truncates the data for the table represented by `model`

    :param model: The model to truncate the data of the underlying table
    """
    # don't try to delete non existant tables
    meta = cql_connection.get_cluster().metadata

    ks_name = model._get_keyspace()  # pylint: disable=protected-access
    raw_cf_name = model.column_family_name(include_keyspace=False)

    try:
        # Make sure the underlying table exists before trying to truncate
        if meta.keyspaces[ks_name].tables[raw_cf_name]:
            cql_connection.execute('TRUNCATE {};'.format(model.column_family_name(include_keyspace=True)))
    except KeyError:
        pass


def create_keyspace(keyspace, strategy_class=None, replication_factor=None):
    """Creates the requested keyspace in Cassandra

    :param keyspace: The keyspace to create in cassandra
    :type keyspace: str
    :param strategy_class: The replication strategy to use for the keyspace.  If this is not provided than the value is
        pulled from configuration or if not configured then 'SimpleStrategy' is used
    :type strategy_class: str
    :param replication_factor: The replication factor to use for the keyspace.  If this is not provided than the value
        is pulled from configuration or if not configured then 3 is used
    :type replication_factor: int
    :return: Whether or not the requested keyspace was created (True) or if it already existed (False)
    """
    if not does_keyspace_exist(keyspace):
        strategy_class = strategy_class or "SimpleStrategy"
        replication_factor = replication_factor or 3
        log.debug("Creating keyspace %s", keyspace)
        try:
            # Hardcoding strategy_class and replication_factor for now as a result of a change in cqlengine 0.21.0
            # But will need to expose these as a config option outside of this method at some point
            management.create_keyspace_simple(keyspace, replication_factor=replication_factor)
            log.info("Created keyspace %s", keyspace)
            return True
        except AlreadyExists:
            log.debug("Keyspace %s already exists", keyspace)
    return False


def create_keyspace_from_model(model):
    """Ensures that a keyspace from the provided `model` exists.  True is returned if the keyspace was created as a
    result of this call, otherwise False is returned if it already exists.

    :param model: The model to create the keyspace for
    :type model: Model
    :return: Whether or not the keyspace was created as a result of this call
    :rtype: bool
    """
    keyspace = model._get_keyspace()  # pylint: disable=protected-access
    return create_keyspace(keyspace)
