import calendar
import datetime
import os
import re
import hashlib


VERSION_PATTERN_PREFIX = "__version_"
VERSION_PATTERN = ''.join([VERSION_PATTERN_PREFIX, "%s__"])
VERSION_MAJOR_ATTRIBUTE = VERSION_PATTERN % "major"
VERSION_YEAR_ATTRIBUTE = VERSION_PATTERN % "year"
VERSION_WEEK_ATTRIBUTE = VERSION_PATTERN % "week"
VERSION_PATCH_ATTRIBUTE = VERSION_PATTERN % "patch"
VERSION_BUILD_ATTRIBUTE = VERSION_PATTERN % "build"

# Per http://docs.python.org/2/library/datetime.html#datetime.date.weekday
WEDNESDAY = 2
THURSDAY = WEDNESDAY + 1

FULL_VERSION_PATTERN = "%d.%02d.%02d"


def _optional(ptrn):
    return r"(?:" + ptrn + r")?"

# To make it easier to read, the full reg exp is broken up by component and then just appended together
VERSION_RE = "".join([
    r"(?P<major>\d+?)",
    _optional(r"\.(?P<year>\d+?)"),
    _optional(r"\.(?P<week>\d+?)"),
    _optional(r"\.(?P<patch>\d+?)"),
    _optional(_optional(r" - Build (?P<build>\d+?)") + "|" + _optional(r"-(?P<build_v2>\d+?)")),
    r"$"
])
del _optional

# A list of the possible regex named groups in the VERSION_RE which represent the build number
BUILD_VAL_NAMES = ["build", "build_v2"]

try:
    # Since this module is used within the mercurial extensions, we don't have access to all of python-utils, so we
    # need to guard importing of the logger
    from loggingtools import getLogger
    log = getLogger()
except ImportError:
    log = None


class Version(object):

    def __init__(self, major, year=None, week=None, patch=None, build=None):
        if isinstance(major, basestring) and year is None:
            ver = Version.from_string(major)
            if ver is None:
                raise ValueError("'%s' is not a valid version string" % major)
            major = ver.major
            year = ver.year
            week = ver.week
            patch = ver.patch
            build = ver.build
        self.major = major or 0
        self.year = year or 0
        self.week = week or 0
        self.patch = patch or 0
        self.build = build

    def __repr__(self):
        return "Major : %s; Year : %s; Week : %s; Patch : %s; Build : %s" % \
               (self.major, self.year, self.week, self.patch, self.build)

    def __str__(self):
        return self.__unicode__()

    def __cmp__(self, other):
        if isinstance(other, basestring):
            other = Version(other)

        return cmp((self.major, self.year, self.week, self.patch, self.build or 0),
                   (other.major, other.year, other.week, other.patch, other.build or 0))

    def __unicode__(self):
        version_string = self.to_version_string()
        return "%s - Build %s" % (version_string, self.build) if self.build else version_string

    def to_version_string(self, always_include_patch=False, always_include_build=False):
        """
        Returns a string representation of the version.
        :param always_include_patch: Always include patch in the version string, even if it is 0.  Default is False.
        :type always_include_patch: bool
        :param always_include_build: Always include build (-<build>) in the version string.  Default is False.
        :type always_include_build: bool
        :return: The string version of the Version object.
        :rtype: basestring
        """
        full_version = FULL_VERSION_PATTERN % (self.major, self.year, self.week)
        if always_include_patch or self.patch > 0:
            full_version = '%s.%d' % (full_version, self.patch)
        if always_include_build:
            try:
                full_version = '%s-%d' % (full_version, self.build)
            except TypeError:
                if log:
                    log.debug("Tried to get full version with build, but build was not set.")
                full_version = self.to_version_string(always_include_patch, always_include_build=False)

        return full_version

    @property
    def next_release(self):
        return self.get_future_version(release=1)

    def get_future_version(self, major=0, release=0, patch=0):
        num_weeks = 52 if not self._is_long_year(self.year + 2000) else 53

        year, week = divmod(self.week + release, num_weeks)

        if week == 0:
            week = num_weeks
            year -= 1

        return Version(
            self.major + major,
            self.year + year,
            week,
            0 if major or release else self.patch + patch
        )

    @classmethod
    def from_string(cls, version_string):
        """Parses `version_string` to create a `Version` object

        :param version_string: The string to be parsed to generate a `Version` object from
        :return: A `Version` instance which represents the provided `version_string`, or None if the `version_string`
                is not a valid version string
        :rtype: Version
        """
        match = re.match(VERSION_RE, version_string.strip())

        if not match:
            return None

        build_val = reduce(
            lambda x, y: x or y,
            [match.group(name) and int(match.group(name)) for name in BUILD_VAL_NAMES])

        return Version(
            match.group("major") and int(match.group("major")),
            match.group("year") and int(match.group("year")),
            match.group("week") and int(match.group("week")),
            match.group("patch") and int(match.group("patch")),
            build_val
        )

    @classmethod
    def _is_long_year(cls, year):
        """Returns whether or not the provided year has 53 work weeks(long) or not(short)
        """
        first_day_of_year = datetime.date(year, 1, 1)
        weekday = first_day_of_year.weekday()

        return weekday == WEDNESDAY if calendar.isleap(year) else weekday == THURSDAY


def get_version_info(module_names):
    """
    Returns a list of VersionInfo objects corresponding to the list of module names.
    :param module_names: List of module names
    :return:
    """
    version_infos = []
    for m in module_names:
        try:
            version_infos.append(get_module_version(m))
        except ImportError:
            version_infos.append(None)

    return version_infos


def get_module_version(module_name):
    """Returns a `Version` representation of the version of the requested python module.

    Note this only works for modules which conform to the versioning pattern

    :param module_name: The name of a module within the python path that you want the version of
    :return: A `Version` representation of the version of the requested `module_name`
    :rtype: Version
    """
    try:
        version_module = __import__('.'.join([module_name, "__version__"]), fromlist=["*"])
    except:
        if log:
            log.error('failed to import __version__ for module %s.' % module_name)
        return None

    module_name = module_name

    if not hasattr(version_module, VERSION_MAJOR_ATTRIBUTE) or \
            not hasattr(version_module, VERSION_YEAR_ATTRIBUTE) or \
            not hasattr(version_module, VERSION_WEEK_ATTRIBUTE):
        raise ImportError('version information not found in %s.' % module_name)

    major = getattr(version_module, VERSION_MAJOR_ATTRIBUTE)
    year = getattr(version_module, VERSION_YEAR_ATTRIBUTE)
    week = getattr(version_module, VERSION_WEEK_ATTRIBUTE)
    patch = getattr(version_module, VERSION_PATCH_ATTRIBUTE, 0)
    if patch < 0:
        patch = 0
    build = getattr(version_module, VERSION_BUILD_ATTRIBUTE, None)

    return Version(major, year, week, patch, build)


def get_module_version_by_filepath(module_name, base_dir=None):
    """Returns a `Version` representation of the version of the requested python module.

    Obtains version info by opening (NOT importing) the file:
    <base_dir>/<module_name>/__version__.py

    :param module_name: Name of the module you want the version of.
    :param base_dir: Base directory to attempt to find the module in.
    :return: Version
    """

    base_dir = base_dir or os.getcwd()
    init_filename = os.path.join(base_dir, module_name, "__version__.py")
    values = {
        "patch": None,
        "build": None
    }

    with open(init_filename, "r") as init_file:
        for line in init_file.readlines():
            line = line.strip('\n')
            if line.find(VERSION_PATTERN_PREFIX) == 0:
                name, val = line.split("=")
                trash, field = name.strip('_ ').split('_')
                values[field] = int(val)

    return Version(**values)


# pylint: disable=abstract-class-not-used
class GuidMixin(object):
    """Extend classes with a guid concept for uniqueness.
    """
    hashing_fnc = hashlib.sha256
    GUID_INPUTS_SEPARATOR = "~"
    GUID_INPUTS_ESCAPE = r'\{sep}\{sep}'.format(sep=GUID_INPUTS_SEPARATOR)
    _guid = None

    @property
    def guid(self):
        """
        Unique hash for this object.
        :return:
        """
        return self._generate_guid()

    def _generate_guid(self):
        """
        Generate a unique hash to identify this object
        :return: Hash value
        :rtype: str
        """
        guid = self.hashing_fnc()

        try:
            inputs_to_guid = self._get_guid_inputs()
        except NotImplementedError:
            log.debug("Attempted to generate guid for instance of %s, but _get_guid_inputs is not implemented.")
            raise ValueError("Unabled to generate GUID")

        inputs = [input_value.replace(self.GUID_INPUTS_SEPARATOR, self.GUID_INPUTS_ESCAPE)
                  for input_value in inputs_to_guid]
        guid.update(self.GUID_INPUTS_SEPARATOR.join(inputs))

        return guid.hexdigest()

    def _get_guid_inputs(self):
        """
        Generate a list of strings inputs that will be fed into the GUID generation.
        :return: Inputs for GUID generation
        :rtype: list of str
        """
        raise NotImplementedError()
