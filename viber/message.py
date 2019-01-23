from viber.base import ViberObject
from viber.files.contact import Contact
from viber.files.picture import Picture
from viber.files.file import File
from viber.enums import MessageType
from viber.files.location import Location
from viber.utils.helpers import get_enum


class Message(ViberObject):
    def __init__(self,
                 type,
                 text=None,
                 picture=None,
                 thumbnail=None,
                 file=None,
                 duration=None,
                 location=None,
                 contact=None,
                 tracking_data=None,
                 sticker_id=None,
                 reciever=None,
                 bot=None):

        self.type = get_enum(type, MessageType, 'message_type')
        self.text = text
        self.picture = picture
        self.thumbnail = thumbnail
        self.location = location
        self.contact = contact
        self.tracking_data = tracking_data
        self.file = file
        self.duration = duration
        self.sticker_id = sticker_id
        self.reciever = reciever
        self.bot = bot

    @classmethod
    def from_dict(cls, data, bot):
        if not data:
            return None

        data = super(Message, cls).from_dict(data, bot)

        data['type'] = get_enum(data.get('type'), MessageType, 'message_type')
        if data['type'] is MessageType.picture:
            data['picture'] = Picture.from_url(data['media'], bot)
            data['thumbnail'] = Picture.from_url(data['thumbnail'], bot)
        if data['type'] is MessageType.file:
            data['file'] = File.from_url(data['media'], bot, data['file_name'], data['size'])

        if 'file_name' in data:
            del data['file_name']
        if 'size' in data:
            del data['size']
        if 'media' in data:
            del data['media']

        # data['text'] = data.get('text')
        # data['media'] = data.get('media')

        # data['tracking_data'] = data.get('tracking_data')
        # data['file_name'] = data.get('file_name')
        # data['file_size'] = data.get('file_size')
        # data['size'] = data.get('size')
        # data['duration'] = data.get('duration')
        # data['sticker_id'] = data.get('sticker_id')
        # data['thumbnail'] = data.get('thumbnail')

        data['contact'] = Contact.from_dict(data.get('contact'), bot)
        data['location'] = Location.from_dict(data.get('location'), bot)

        return cls(bot=bot, **data)
