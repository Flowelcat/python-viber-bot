"""This module contains an object that represents a Viber User."""
from viber.base import ViberObject
from viber.enums import UserRole
from viber.utils.helpers import get_enum


class User(ViberObject):
    """This object represents a Viber user.

    Attributes:
        id (:obj:`int`): Unique identifier for this user.
        name (:obj:`bool`): Optional. User's name.
        avatar (:obj:`str`): Optional. User's avatar URL.
        country (:obj:`str`): Optional. User's country code.
        language (:obj:`str`): Optional. User's language code..
        role (:class:`viber.enums.UserRole`): Optional. User's role in bot, present when getting members of bot.
        api_version (:obj:`str`): Optional. Minimal api version.
        bot (:class:`viber.Bot`): Optional. The Bot to use for instance methods.

    Args:
        id (:obj:`int`): Unique identifier for this user.
        bot (:class:`viber.Bot`, optional): The Bot to use for instance methods.

    """

    def __init__(self, id, name=None, avatar=None, country=None, language=None, role=None, api_version=None, bot=None):
        """
        userdoct
        """
        self.id = id
        self.name = name
        self.avatar = avatar
        self.country = country
        self.language = language
        self.role = role
        self.api_version = api_version
        self.bot = bot

    @classmethod
    def from_dict(cls, data, bot):
        if not data:
            return None

        data = super(User, cls).from_dict(data, bot)
        data['role'] = get_enum(data.get('role'), UserRole, 'user_role')
        return cls(bot=bot, **data)
