"""
Introduces a 'comparable' mixin which can be used to quickly add support for Py2/3 compatible object comparison
"""
# pylint: disable=missing-docstring
COMPARABLE_INSTANCE_COMP_KEY_ATTR = '_cmpkey'


class ComparableMixin(object):
    """Mostly pulled from http://python3porting.com/preparing.html#comparatively-tricky

    """

    def _cmpkey(self):
        """
        :return:
        :rtype: primitive data that may be used by the mixin to apply the sort functionality
        """
        pass

    def _compare(self, other, method):
        try:
            return method(getattr(self, COMPARABLE_INSTANCE_COMP_KEY_ATTR)(),
                          getattr(other, COMPARABLE_INSTANCE_COMP_KEY_ATTR)())
        except (AttributeError, TypeError):
            # _cmpkey not implemented, or return different type,
            # so I can't compare with "other".
            return NotImplemented

    def __lt__(self, other):
        return self._compare(other, lambda _self, other: _self < other)

    def __le__(self, other):
        return self._compare(other, lambda _self, other: _self <= other)

    def __eq__(self, other):
        return self._compare(other, lambda _self, other: _self == other)

    def __ge__(self, other):
        return self._compare(other, lambda _self, other: _self >= other)

    def __gt__(self, other):
        return self._compare(other, lambda _self, other: _self > other)

    def __ne__(self, other):
        return self._compare(other, lambda _self, other: _self != other)
