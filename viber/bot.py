"""This module contains an object that represents a Viber Bot."""
import functools
import logging

from viber import User
from viber.base import ViberObject
from viber.enums import MessageType, EventType
from viber.error import InvalidToken
from viber.message import Message, Contact, Location
from viber.utils.helpers import get_enum
from viber.utils.request import Request


def log(func):
    logger = logging.getLogger(func.__module__)

    @functools.wraps(func)
    def decorator(self, *args, **kwargs):
        logger.debug('Entering: %s', func.__name__)
        result = func(self, *args, **kwargs)
        logger.debug(result)
        logger.debug('Exiting: %s', func.__name__)
        return result

    return decorator


def info(func):
    @functools.wraps(func)
    def decorator(self, *args, **kwargs):
        if not self.info:
            self.get_account_info()

        result = func(self, *args, **kwargs)
        return result

    return decorator


def message(func):
    @functools.wraps(func)
    def decorator(self, *args, **kwargs):
        url, payload = func(self, *args, **kwargs)

        result = self._request.post(url, payload, timeout=kwargs.get('timeout'))

        if result is True:
            return result

        mes = Message(payload['type'])
        for key in payload:
            if hasattr(mes, key):
                setattr(mes, key, payload[key])

        return mes

    return decorator


class Bot(ViberObject):
    """
    This object represents a Viber Bot.

    Args:
       token (:obj:`str`): Bot's unique authentication.
       name (:obj:`str`, optional): Bot's name.
       avatar (:obj:`str`, optional): Bot's avatar url.
       base_url (:obj:`str`, optional): Viber Bot API service URL.
    """

    def __init__(self, token, name=None, avatar=None, base_url=None, request=None):

        self.token = self._validate_token(token)
        self.name = name
        self.avatar = avatar

        if base_url is None:
            self.base_url = 'https://chatapi.viber.com/pa'

        self.info = None
        self._request = request or Request(self.token)
        self.logger = logging.getLogger(__name__)

    @property
    def request(self):
        return self._request

    @staticmethod
    def _validate_token(token):
        """A very basic validation on token."""
        if len(token) != 50:
            raise InvalidToken()

        token_parts = token.split('-')
        if len(token_parts) != 3:
            raise InvalidToken()
        else:
            left, center, right = token_parts
            if len(left) != 16 or len(center) != 16 or len(right) != 16:
                raise InvalidToken()

        return token

    @property
    @info
    def id(self):
        """:obj:`int`: Unique identifier for this bot."""

        return self.info['id']

    @property
    @info
    def chat_hostname(self):
        """:obj:`int`: Chat hostname for this bot."""

        return self.info['chat_hostname']

    @property
    @info
    def bot_name(self):
        """:obj:`str`: Name for this bot."""

        return self.info['name']

    @property
    @info
    def uri(self):
        """:obj:`str`: Uri for this bot."""

        return self.info['uri']

    @property
    @info
    def icon(self):
        """:obj:`str`: URL for icon for this bot."""

        return self.info['icon']

    @property
    @info
    def background(self):
        """:obj:`str`: URL for background for this bot."""

        return self.info['background']

    @property
    @info
    def category(self):
        """:obj:`str`: Category for this bot."""

        return self.info['category']

    @property
    @info
    def subcategory(self):
        """:obj:`str`: Subcategory for this bot."""

        return self.info['subcategory']

    @property
    @info
    def location(self):
        """:obj:`viber.Location`: Location for this bot."""

        return Location.from_dict(self.info['location'], self)

    @property
    @info
    def country(self):
        """:obj:`str`: Country code for this bot."""

        return self.info['country']

    @property
    @info
    def webhook(self):
        """:obj:`str`: Webhook url for this bot."""

        return self.info['webhook']

    @property
    @info
    def event_types(self):
        """:obj:`list of viber.enums.EventType`: Event types for this bot."""

        return [get_enum(event, EventType, 'event_type') for event in self.info['event_types']]

    @property
    @info
    def members(self):
        """:obj:`list of viber.User`: Member of this bot."""

        return [User.from_dict(user, self) for user in self.info['members']]

    @property
    @info
    def subscribers_count(self):
        """:obj:`int`: Number of subscribers of this bot."""

        return self.info['subscribers_count']

    def get_account_info(self, timeout=None):
        """
        A simple method for testing your bot's auth token. Requires no parameters.

        Args:
            timeout (:obj:`int` | :obj:`float`, optional): If this value is specified, use it as
                the read timeout from the server (instead of the one specified during creation of
                the connection pool).

        Returns:
            :obj:`dict`: A dict of parameters representing that bot if the
            credentials are valid, :obj:`None` otherwise.

        Raises:
            :class:`viber.ViberError`

        """
        url = '{0}/get_account_info'.format(self.base_url)
        result = self._request.post(url, {}, timeout=timeout)
        self.info = result
        return result

    def set_webhook(self, url, event_types=None, send_name=True, send_photo=True, timeout=10, **kwargs):
        """
        Use this method to specify a url and receive incoming events via an outgoing webhook.
        Whenever there is an event for the bot, we will send an HTTPS POST request to the
        specified url, containing a JSON-serialized Event. In case of an unsuccessful request,
        we will give up after a reasonable amount of attempts.

        If you'd like to make sure that the Webhook request comes from Viber, we recommend
        using a secret path in the URL, e.g. https://www.example.com/<token>. Since nobody else
        knows your bot's token, you can be pretty sure it's us.

        Note:
            The certificate argument should be a file from disk ``open(filename, 'rb')``.

        Args:
            url (:obj:`str`): HTTPS url to send updates to. Use an empty string to remove webhook
                integration.
            event_types (List[:class:`vbier.enums.EventType`], optional): List the types of events you want your
                bot to receive. See :class:`viber.enums.EventType` for a complete list of available event types. Specify an
                empty list to receive all updates regardless of type (default). If not specified,
                the previous setting will be used. Please note that this parameter doesn't affect
                events created before the call to the set_webhook, so unwanted events may be
                received for a short period of time.
            send_name (:obj:`bool`): Indicates whether or not the bot should receive the user name.
            send_photo (:obj:`bool`): Indicates whether or not the bot should receive the user photo.
            timeout (:obj:`int` | :obj:`float`, optional): If this value is specified, use it as
                the read timeout from the server (instead of the one specified during creation of
                the connection pool).
            **kwargs (:obj:`dict`): Arbitrary keyword arguments.

        Note:
            1. You will not be able to receive updates using get_events for as long as an outgoing
               webhook is set up.
            2. You can't use self-signed certificate

        Returns:
            :obj:`bool` On success, ``True`` is returned.

        Raises:
            :class:`viber.ViberError`

        """

        if not event_types:
            event_types = [et for et in EventType]

        _url = '{0}/set_webhook'.format(self.base_url)
        payload = {'url': url,
                   'event_types': [et.value for et in event_types],
                   send_name: send_name,
                   send_photo: send_photo}

        payload.update(kwargs)
        result = self._request.post(_url, payload, timeout=timeout)
        return result

    def delete_webhook(self, timeout=None, **kwargs):
        """
        Use this method to remove webhook integration. Requires no parameters.

        Args:
            timeout (:obj:`int` | :obj:`float`, optional): If this value is specified, use it as
                the read timeout from the server (instead of the one specified during creation of
                the connection pool).
            **kwargs (:obj:`dict`): Arbitrary keyword arguments.

        Returns:
            :obj:`bool` On success, ``True`` is returned.

        Raises:
            :class:`viber.ViberError`

        """

        url = '{0}/set_webhook'.format(self.base_url)
        payload = {'url': ""}

        payload.update(kwargs)
        result = self._request.post(url, payload, timeout=timeout)
        return result

    @message
    def send_message(self, user_id, text, tracking_data=None, keyboard=None, min_api_version=None, timeout=None, **kwargs):
        """Use this method to send text messages.
        Message and Keyboard can contain placeholders if list of user_ids used.
        | `replace_me_with_receiver_id` - will be replaced by the receiver ID
        | `replace_me_with_url_encoded_receiver_id` - will be replaced by the URL encoded receiver ID
        | `replace_me_with_user_name` - will be replaced by the receiver user name

        Args:
            user_id (:obj:`str`, List[:obj:`str`] ): Unique identifier for the target user.
            text (:obj:`str`, optional): Text of the messsage.
            tracking_data (:obj:`str`, optional): Allow the account to track messages and user's replies.
                Sent tracking_data value will be passed back with user's reply. Max 4000 characters. Also found as
                :attr:`viber.constants.MAX_TRACKING_DATA_LENGTH`.
            keyboard (:obj:`Keyboard`, optional): Keyboard to be sent.
            min_api_version (:obj:`int`, optional): Minimal api version.
            timeout (:obj:`int` | :obj:`float`, optional): If this value is specified, use it as
                the read timeout from the server (instead of the one specified during creation of
                the connection pool).
            **kwargs (:obj:`dict`): Arbitrary keyword arguments.

        Returns:
            :class:`viber.Message`: On success, the sent message is returned.

        Raises:
            :class:`viber.ViberError`
        """

        url = '{0}/send_message'.format(self.base_url)
        payload = {
            "type": MessageType.text.value,
            "text": text
        }
        if isinstance(user_id, list):
            payload['broadcast_list'] = user_id
        else:
            payload['receiver'] = user_id

        if self.name or self.avatar:
            payload['sender'] = {}
            if self.name:
                payload['name'] = self.name
            if self.avatar:
                payload['avatar'] = self.avatar

        if min_api_version:
            payload["min_api_version"] = min_api_version
        if tracking_data:
            payload["tracking_data"] = tracking_data
        if keyboard:
            payload["keyboard"] = keyboard.to_dict()

        payload.update(kwargs)
        return url, payload

    @message
    def send_picture(self, user_id, media, description=None, thumbnail=None, tracking_data=None, keyboard=None,
                     min_api_version=None, timeout=None, **kwargs):
        """Use this method to send picture messages.

        Message and Keyboard can contain placeholders if
        list of user_ids used.
        | `replace_me_with_receiver_id` - will be replaced by the receiver ID
        | `replace_me_with_url_encoded_receiver_id` - will be replaced by the URL encoded receiver ID
        | `replace_me_with_user_name` - will be replaced by the receiver user name


        Args:
            user_id (:obj:`str`): Unique identifier for the target user.
            media (:obj:`str`): Url of the JPEG image, max size is 1MB. Also found as
                :attr:`viber.constants.MAX_PICTURE_SIZE`.
            description (:obj:`str`, optional): Description of the picture to be sent. Max 120 characters.
                Also found as :attr:`viber.constants.MAX_PICTURE_DESCRIPTION_LENGTH`.
            thumbnail (:obj:`str`, optional): Url of the thumbnail JPEG image, max size is 100KB. Also found as
                :attr:`viber.constants.MAX_THUMBNAIL_SIZE`.
            tracking_data (:obj:`str`, optional): Allow the account to track messages and user's replies.
                Sent tracking_data value will be passed back with user's reply. Max 4000 characters. Also found as
                :attr:`viber.constants.MAX_TRACKING_DATA_LENGTH`.

            keyboard (:obj:`Keyboard`, optional): Keyboard to be sent.
            min_api_version (:obj:`int`, optional): Minimal api version.
            timeout (:obj:`int` | :obj:`float`, optional): If this value is specified, use it as
                the read timeout from the server (instead of the one specified during creation of
                the connection pool).
            **kwargs (:obj:`dict`): Arbitrary keyword arguments.

        Returns:
            :class:`viber.Message`: On success, the sent message is returned.

        Raises:
            :class:`viber.ViberError`
        """
        url = '{0}/send_message'.format(self.base_url)
        payload = {
            "type": MessageType.picture.value,
            "media": media,
        }
        if isinstance(user_id, list):
            payload['broadcast_list'] = user_id
        else:
            payload['receiver'] = user_id

        if self.name or self.avatar:
            payload['sender'] = {}
            if self.name:
                payload['name'] = self.name
            if self.avatar:
                payload['avatar'] = self.avatar

        if min_api_version:
            payload["min_api_version"] = min_api_version
        if thumbnail:
            payload["thumbnail"] = thumbnail
        if description:
            payload["text"] = description

        if tracking_data:
            payload["tracking_data"] = tracking_data
        if keyboard:
            payload["keyboard"] = keyboard.to_dict()

        payload.update(kwargs)
        return url, payload

    @message
    def send_video(self, user_id, media, size, duration=None, thumbnail=None, tracking_data=None, keyboard=None,
                   min_api_version=None, timeout=None, **kwargs):
        """Use this method to send video messages.
        Message and Keyboard can contain placeholders if list of user_ids used.
        | `replace_me_with_receiver_id` - will be replaced by the receiver ID
        | `replace_me_with_url_encoded_receiver_id` - will be replaced by the URL encoded receiver ID
        | `replace_me_with_user_name` - will be replaced by the receiver user name


        Args:
            user_id (:obj:`str`): Unique identifier for the target user.
            media (:obj:`str`): Url of the video(MP4, H264), max size is 50MB. Also found as
                :attr:`viber.constants.MAX_VIDEO_SIZE`.
            size (:obj:`int`): Size of the video in bytes.
            duration (:obj:`int`, optional): Video duration in seconds; will be displayed to the receiver, max 180 seconds.
                Also found as :attr:`viber.constants.MAX_VIDEO_DURATION`.
            thumbnail (:obj:`str`, optional): Url of the thumbnail JPEG image, max size is 100KB. Also found as
                :attr:`viber.constants.MAX_THUMBNAIL_SIZE`.

            tracking_data (:obj:`str`, optional): Allow the account to track messages and user's replies.
                Sent tracking_data value will be passed back with user's reply. Max 4000 characters. Also found as
                :attr:`viber.constants.MAX_TRACKING_DATA_LENGTH`.
            keyboard (:obj:`Keyboard`, optional): Keyboard to be sent.
            min_api_version (:obj:`int`, optional): Minimal api version.
            timeout (:obj:`int` | :obj:`float`, optional): If this value is specified, use it as
                the read timeout from the server (instead of the one specified during creation of
                the connection pool).
            **kwargs (:obj:`dict`): Arbitrary keyword arguments.

        Returns:
            :class:`viber.Message`: On success, the sent message is returned.

        Raises:
            :class:`viber.ViberError`
        """
        url = '{0}/send_message'.format(self.base_url)
        payload = {
            "type": MessageType.video.value,
            "media": media,
            "size": size,
        }
        if isinstance(user_id, list):
            payload['broadcast_list'] = user_id
        else:
            payload['receiver'] = user_id

        if self.name or self.avatar:
            payload['sender'] = {}
            if self.name:
                payload['name'] = self.name
            if self.avatar:
                payload['avatar'] = self.avatar

        if min_api_version:
            payload["min_api_version"] = min_api_version
        if thumbnail:
            payload["thumbnail"] = thumbnail
        if duration:
            payload["duration"] = duration

        if tracking_data:
            payload["tracking_data"] = tracking_data
        if keyboard:
            payload["keyboard"] = keyboard.to_dict()

        payload.update(kwargs)
        return url, payload

    @message
    def send_file(self, user_id, media, size, file_name, tracking_data=None, keyboard=None, min_api_version=None,
                  timeout=None, **kwargs):
        """Use this method to send file messages.

        Message and Keyboard can contain placeholders if list of user_ids used.
        | `replace_me_with_receiver_id` - will be replaced by the receiver ID
        | `replace_me_with_url_encoded_receiver_id` - will be replaced by the URL encoded receiver ID
        | `replace_me_with_user_name` - will be replaced by the receiver user name


        Args:
            user_id (:obj:`str`): Unique identifier for the target user.
            media (:obj:`str`): Url of the video(MP4, H264), max size is 50MB. Also found as
                :attr:`viber.constants.MAX_FILE_SIZE`.
            size (:obj:`int`): Size of the video in bytes.
            file_name (:obj:`str`):  File name should include extension.
                Sending a file without extension or with the wrong extension might cause the client to be unable to open the file.
                Max 256 characters (including file extension)
                Also found as :attr:`viber.constants.MAX_FILE_NAME_LENGTH`.

            tracking_data (:obj:`str`, optional): Allow the account to track messages and user's replies.
                Sent tracking_data value will be passed back with user's reply. Max 4000 characters. Also found as
                :attr:`viber.constants.MAX_TRACKING_DATA_LENGTH`.
            keyboard (:obj:`Keyboard`, optional): Keyboard to be sent.
            min_api_version (:obj:`int`, optional): Minimal api version.
            timeout (:obj:`int` | :obj:`float`, optional): If this value is specified, use it as
                the read timeout from the server (instead of the one specified during creation of
                the connection pool).
            **kwargs (:obj:`dict`): Arbitrary keyword arguments.

        Returns:
            :class:`viber.Message`: On success, the sent message is returned.

        Raises:
            :class:`viber.ViberError`
        """
        url = '{0}/send_message'.format(self.base_url)
        payload = {
            "type": MessageType.file.value,
            "media": media,
            "size": size,
            "file_name": file_name,
        }
        if isinstance(user_id, list):
            payload['broadcast_list'] = user_id
        else:
            payload['receiver'] = user_id

        if self.name or self.avatar:
            payload['sender'] = {}
            if self.name:
                payload['name'] = self.name
            if self.avatar:
                payload['avatar'] = self.avatar

        if min_api_version:
            payload["min_api_version"] = min_api_version
        if tracking_data:
            payload["tracking_data"] = tracking_data
        if keyboard:
            payload["keyboard"] = keyboard.to_dict()

        payload.update(kwargs)
        return url, payload

    @message
    def send_contact(self, user_id, contact=None, name=None, phone_number=None, tracking_data=None, keyboard=None,
                     min_api_version=None, timeout=None, **kwargs):
        """Use this method to send contact messages.

        Message and Keyboard can contain placeholders if list of user_ids used.
        | `replace_me_with_receiver_id` - will be replaced by the receiver ID
        | `replace_me_with_url_encoded_receiver_id` - will be replaced by the URL encoded receiver ID
        | `replace_me_with_user_name` - will be replaced by the receiver user name


        Args:
            user_id (:obj:`str`): Unique identifier for the target user.
            contact (:obj:`Contact`): Contact to be sent.
            name (:obj:`str`): Name of the contact if contact is None
            phone_number (:obj:`str`): phone number of the contact if contact is None
            tracking_data (:obj:`str`, optional): Allow the account to track messages and user's replies.
                Sent tracking_data value will be passed back with user's reply. Max 4000 characters. Also found as
                :attr:`viber.constants.MAX_TRACKING_DATA_LENGTH`.
            keyboard (:obj:`Keyboard`, optional): Keyboard to be sent.
            min_api_version (:obj:`int`, optional): Minimal api version.
            timeout (:obj:`int` | :obj:`float`, optional): If this value is specified, use it as
                the read timeout from the server (instead of the one specified during creation of
                the connection pool).
            **kwargs (:obj:`dict`): Arbitrary keyword arguments.

        Returns:
            :class:`viber.Message`: On success, the sent message is returned.

        Raises:
            :class:`viber.ViberError`
        """

        if contact is None and (name is None or phone_number is None):
            TypeError("Must be contact or name with phone_number")
        elif contact and (name or phone_number):
            TypeError("Contact and name with phone_number are mutually exclusive")
        elif contact is None and name and phone_number:
            contact = Contact(name, phone_number)

        url = '{0}/send_message'.format(self.base_url)
        payload = {
            "type": MessageType.contact.value,
            "contact": contact.to_dict(),
        }
        if isinstance(user_id, list):
            payload['broadcast_list'] = user_id
        else:
            payload['receiver'] = user_id

        if self.name or self.avatar:
            payload['sender'] = {}
            if self.name:
                payload['name'] = self.name
            if self.avatar:
                payload['avatar'] = self.avatar

        if min_api_version:
            payload["min_api_version"] = min_api_version
        if tracking_data:
            payload["tracking_data"] = tracking_data
        if keyboard:
            payload["keyboard"] = keyboard.to_dict()

        payload.update(kwargs)
        return url, payload

    @message
    def send_location(self, user_id, location=None, lat=None, lon=None, tracking_data=None, keyboard=None,
                      min_api_version=None, timeout=None, **kwargs):
        """Use this method to send location messages.

        Message and Keyboard can contain placeholders if list of user_ids used.
        | `replace_me_with_receiver_id` - will be replaced by the receiver ID
        | `replace_me_with_url_encoded_receiver_id` - will be replaced by the URL encoded receiver ID
        | `replace_me_with_user_name` - will be replaced by the receiver user name


        Args:
            user_id (:obj:`str`): Unique identifier for the target user.
            location (:obj:`Location`): Location to be sent.
            lat (:obj:`str`): Latitude of the location if location is None
            lon (:obj:`str`): Longitude of the location if location is None

            tracking_data (:obj:`str`, optional): Allow the account to track messages and user's replies.
                Sent tracking_data value will be passed back with user's reply. Max 4000 characters. Also found as
                :attr:`viber.constants.MAX_TRACKING_DATA_LENGTH`.
            keyboard (:obj:`Keyboard`, optional): Keyboard to be sent.
            min_api_version (:obj:`int`, optional): Minimal api version.
            timeout (:obj:`int` | :obj:`float`, optional): If this value is specified, use it as
                the read timeout from the server (instead of the one specified during creation of
                the connection pool).
            **kwargs (:obj:`dict`): Arbitrary keyword arguments.

        Returns:
            :class:`viber.Message`: On success, the sent message is returned.

        Raises:
            :class:`viber.ViberError`
        """

        if location is None and (lat is None or lon is None):
            TypeError("Must be location or lat with lon")
        elif location and (lat or lon):
            TypeError("Location and lat with lon are mutually exclusive")
        elif location is None and lat and lon:
            location = Location(lat, lon)

        url = '{0}/send_message'.format(self.base_url)
        payload = {
            "type": MessageType.location.value,
            "location": location.to_dict(),

        }
        if isinstance(user_id, list):
            payload['broadcast_list'] = user_id
        else:
            payload['receiver'] = user_id

        if self.name or self.avatar:
            payload['sender'] = {}
            if self.name:
                payload['name'] = self.name
            if self.avatar:
                payload['avatar'] = self.avatar

        if min_api_version:
            payload["min_api_version"] = min_api_version
        if tracking_data:
            payload["tracking_data"] = tracking_data
        if keyboard:
            payload["keyboard"] = keyboard.to_dict()

        payload.update(kwargs)
        return url, payload

    @message
    def send_url(self, user_id, url_address, tracking_data=None, keyboard=None, min_api_version=None, timeout=None, **kwargs):
        """Use this method to send url messages.

        Message and Keyboard can contain placeholders if list of user_ids used.
        | `replace_me_with_receiver_id` - will be replaced by the receiver ID
        | `replace_me_with_url_encoded_receiver_id` - will be replaced by the URL encoded receiver ID
        | `replace_me_with_user_name` - will be replaced by the receiver user name


        Args:
            user_id (:obj:`str`): Unique identifier for the target user.
            url_address (:obj:`str`): URL to be sent. Max 2000 characters.  Also found as
                :attr:`viber.constants.MAX_URL_LENGTH`.

            tracking_data (:obj:`str`, optional): Allow the account to track messages and user's replies.
                Sent tracking_data value will be passed back with user's reply. Max 4000 characters. Also found as
                :attr:`viber.constants.MAX_TRACKING_DATA_LENGTH`.
            keyboard (:obj:`Keyboard`, optional): Keyboard to be sent.
            min_api_version (:obj:`int`, optional): Minimal api version.
            timeout (:obj:`int` | :obj:`float`, optional): If this value is specified, use it as
                the read timeout from the server (instead of the one specified during creation of
                the connection pool).
            **kwargs (:obj:`dict`): Arbitrary keyword arguments.

        Returns:
            :class:`viber.Message`: On success, the sent message is returned.

        Raises:
            :class:`viber.ViberError`
        """

        url = '{0}/send_message'.format(self.base_url)
        payload = {
            "type": MessageType.url.value,
            "media": url_address,
        }
        if isinstance(user_id, list):
            payload['broadcast_list'] = user_id
        else:
            payload['receiver'] = user_id

        if self.name or self.avatar:
            payload['sender'] = {}
            if self.name:
                payload['name'] = self.name
            if self.avatar:
                payload['avatar'] = self.avatar

        if min_api_version:
            payload["min_api_version"] = min_api_version
        if tracking_data:
            payload["tracking_data"] = tracking_data
        if keyboard:
            payload["keyboard"] = keyboard.to_dict()

        payload.update(kwargs)
        return url, payload

    @message
    def send_sticker(self, user_id, sticker_id, tracking_data=None, keyboard=None, min_api_version=None, timeout=None, **kwargs):
        """Use this method to send sticker messages.

        Message and Keyboard can contain placeholders if list of user_ids used.
        | `replace_me_with_receiver_id` - will be replaced by the receiver ID
        | `replace_me_with_url_encoded_receiver_id` - will be replaced by the URL encoded receiver ID
        | `replace_me_with_user_name` - will be replaced by the receiver user name


        Args:
            user_id (:obj:`str`): Unique identifier for the target user.
            sticker_id (:obj:`int`): Unique Viber sticker ID. For examples visit https://viber.github.io/docs/tools/sticker-ids/ page.

            tracking_data (:obj:`str`, optional): Allow the account to track messages and user's replies.
                Sent tracking_data value will be passed back with user's reply. Max 4000 characters. Also found as
                :attr:`viber.constants.MAX_TRACKING_DATA_LENGTH`.
            keyboard (:obj:`Keyboard`, optional): Keyboard to be sent.
            min_api_version (:obj:`int`, optional): Minimal api version.
            timeout (:obj:`int` | :obj:`float`, optional): If this value is specified, use it as
                the read timeout from the server (instead of the one specified during creation of
                the connection pool).
            **kwargs (:obj:`dict`): Arbitrary keyword arguments.

        Returns:
            :class:`viber.Message`: On success, the sent message is returned.

        Raises:
            :class:`viber.ViberError`
        """

        url = '{0}/send_message'.format(self.base_url)
        payload = {
            "type": MessageType.sticker.value,
            "sticker_id": sticker_id,
        }
        if isinstance(user_id, list):
            payload['broadcast_list'] = user_id
        else:
            payload['receiver'] = user_id

        if self.name or self.avatar:
            payload['sender'] = {}
            if self.name:
                payload['name'] = self.name
            if self.avatar:
                payload['avatar'] = self.avatar

        if min_api_version:
            payload["min_api_version"] = min_api_version
        if tracking_data:
            payload["tracking_data"] = tracking_data
        if keyboard:
            payload["keyboard"] = keyboard.to_dict()

        payload.update(kwargs)
        return url, payload

    @message
    def send_carousel(self, user_id, rich_media, tracking_data=None, keyboard=None, min_api_version=None, timeout=None, **kwargs):
        """Use this method to send url messages.

        Message and Keyboard can contain placeholders if list of user_ids used.
        | `replace_me_with_receiver_id` - will be replaced by the receiver ID
        | `replace_me_with_url_encoded_receiver_id` - will be replaced by the URL encoded receiver ID
        | `replace_me_with_user_name` - will be replaced by the receiver user name


        Note:
            Carousel Content Message is supported on devices running Viber version 6.7 and above.

        Args:
            user_id (:obj:`str`): Unique identifier for the target user.
            rich_media (:obj:`Keyboard`): Keyboard with type rich_media.
            min_api_version (:obj:`int`): Minimal api version.

            tracking_data (:obj:`str`, optional): Allow the account to track messages and user's replies.
                Sent tracking_data value will be passed back with user's reply. Max 4000 characters. Also found as
                :attr:`viber.constants.MAX_TRACKING_DATA_LENGTH`.
            keyboard (:obj:`Keyboard`, optional): Keyboard to be sent.
            min_api_version (:obj:`int`, optional): Minimal api version.
            timeout (:obj:`int` | :obj:`float`, optional): If this value is specified, use it as
                the read timeout from the server (instead of the one specified during creation of
                the connection pool).
            **kwargs (:obj:`dict`): Arbitrary keyword arguments.

        Returns:
            :class:`viber.Message`: On success, the sent message is returned.

        Raises:
            :class:`viber.ViberError`
        """

        url = '{0}/send_message'.format(self.base_url)
        payload = {
            "type": MessageType.rich_media.value,
            "rich_media": rich_media.to_dict(),
        }
        if isinstance(user_id, list):
            payload['broadcast_list'] = user_id
        else:
            payload['receiver'] = user_id

        if self.name or self.avatar:
            payload['sender'] = {}
            if self.name:
                payload['name'] = self.name
            if self.avatar:
                payload['avatar'] = self.avatar

        if min_api_version:
            payload["min_api_version"] = min_api_version
        if tracking_data:
            payload["tracking_data"] = tracking_data
        if keyboard:
            payload["keyboard"] = keyboard.to_dict()

        payload.update(kwargs)
        return url, payload

