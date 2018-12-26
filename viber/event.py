"""This module contains an object that represents a Viber Update."""

from viber.base import ViberObject
from viber.enums import EventType
from viber.message import Message
from viber.user import User
from viber.utils.helpers import get_enum, from_timestamp


class Event(ViberObject):
    """This object represents an incoming event.

    Note:
        At most one of the optional parameters can be present in any given event.

    Attributes:
        event (:class:`viber.enums.EventType`): The event's unique identifier.
        message_token (:obj:`str`): Optional. Unique identifier of the event.
        timestamp (:obj:`datetime.datetime`): Optional. Time when message was created.
        chat_hostname (:class:`str`): Optional. Chat hostname
        silent (:obj:`bool`): Optional. Is message silent.
        user_id (:class:`str`): Optional. User unique identifier.
        desc (:obj:`str`): Optional. Description for falture events.
        user (:class:`viber.User`): Optional. User instance for subscribed and conversation_started event.
        type (:obj:`str`): Optional. Type for conversation_started event.
        context (:obj:`str`): Optional. Context for conversation_started event.
        subscribed (:obj:`bool`): Optional. Is user subscribed for conversation_started event.
        message (:obj:`viber.Message`): Optional. Message attached to event.
        sender (:obj:`viber.User`): Optional. User who send the message.

    Args:
        event (:class:`viber.enums.EventType`): The event's unique identifier.
        message_token (:obj:`str`, optional): Unique identifier of the event.
        timestamp (:obj:`datetime.datetime`, optional): Time when message was created.
        chat_hostname (:class:`str`, optional): Chat hostname
        silent (:obj:`bool`, optional): Is message silent.
        user_id (:class:`str`, optional): User unique identifier.
        desc (:obj:`str`, optional): Description for falture events.
        user (:class:`viber.User`, optional): User instance for subscribed and conversation_started event.
        type (:obj:`str`, optional): Type for conversation_started event.
        context (:obj:`str`, optional): Context for conversation_started event.
        subscribed (:obj:`bool`, optional): Is user subscribed for conversation_started event.
        message (:obj:`viber.Message`, optional): Message attached to event.
        sender (:obj:`viber.User`, optional): User who send the message.
        """

    def __init__(self,
                 event,
                 message_token,
                 timestamp,
                 chat_hostname=None,
                 silent=None,
                 user_id=None,
                 desc=None,
                 user=None,
                 type=None,
                 context=None,
                 subscribed=None,
                 message=None,
                 sender=None):

        self.event = event
        self.timestamp = timestamp
        self.message_token = message_token

        self.chat_hostname = chat_hostname
        self.silent = silent
        self.user_id = user_id
        self.desc = desc
        self.user = user
        self.type = type
        self.context = context
        self.subscribed = subscribed
        self.message = message
        self.sender = sender

    @classmethod
    def from_dict(cls, data, bot):
        if not data:
            return None

        data = super(Event, cls).from_dict(data, bot)

        data['event'] = get_enum(data.get('event'), EventType, 'event_type')
        data['timestamp'] = from_timestamp(data['timestamp'])
        data['desc'] = data.get('desc')
        data['user'] = User.from_dict(data.get('user'), bot)
        data['type'] = data.get('type')
        data['context'] = data.get('context')
        data['subscribed'] = data.get('subscribed')
        data['sender'] = User.from_dict(data.get('sender'), bot)
        data['message'] = Message.from_dict(data.get('message'), bot)
        data['user_id'] = data.get('user_id')

        if not data['user_id']:
            if data['user']:
                data['user_id'] = data['user'].id
            elif data['sender']:
                data['user_id'] = data['sender'].id

        return cls(**data)
