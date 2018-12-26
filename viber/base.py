import json
from abc import ABCMeta
from future.utils import string_types


class ViberObject(object):
    """Base class for most telegram objects."""

    __metaclass__ = ABCMeta
    _id_attrs = ()

    def __str__(self):
        return str(self.to_dict())

    def __getitem__(self, item):
        return self.__dict__[item]

    @classmethod
    def from_dict(cls, data, bot):
        if not data:
            return None

        data = data.copy()

        return data

    def to_json(self):
        """
        Returns:
            :obj:`str`

        """

        return json.dumps(self.to_dict())

    def to_dict(self):
        data = dict()

        for key in iter(self.__dict__):
            if key in ('bot',
                       '_id_attrs'):
                continue

            value = self.__dict__[key]
            if value is not None:
                if hasattr(value, 'to_dict'):
                    data[key] = value.to_dict()
                else:
                    data[key] = value

        return data

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self._id_attrs == other._id_attrs
        return super(ViberObject, self).__eq__(other)  # pylint: disable=no-member

    def __hash__(self):
        if self._id_attrs:
            return hash((self.__class__, self._id_attrs))  # pylint: disable=no-member
        return super(ViberObject, self).__hash__()