"""This module contains an object that represents a Viber Location."""

from viber import ViberObject


class Location(ViberObject):
    """This object represents a point on the map.

      Attributes:
          lat (:obj:`float`): Latitude as defined by sender.
          lon (:obj:`float`): Longitude as defined by sender.

      Args:
          lat (:obj:`float`): Latitude as defined by sender.
          lon (:obj:`float`): Longitude as defined by sender.

      """

    def __init__(self, lat, lon):
        self.lat = lat
        self.lon = lon

    @classmethod
    def from_dict(cls, data, bot):
        if not data:
            return None

        return cls(**data)
