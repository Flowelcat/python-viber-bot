"""This module contains an object that represents a Viber Contact."""

from viber import ViberObject


class Contact(ViberObject):
    """This object represents a phone contact.

       Attributes:
           name (:obj:`str`): Contact's name.
           phone_number (:obj:`str`): Contact's phone number.

       Args:
           phone_number (:obj:`str`): Contact's phone number.
           name (:obj:`str`): Contact's name.

       """
    def __init__(self, name, phone_number):
        self.name = name
        self.phone_number = phone_number

        self._id_attrs = (self.phone_number,)

    @classmethod
    def from_dict(cls, data, bot):
        if not data:
            return None

        return cls(**data)
