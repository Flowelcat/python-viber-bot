from viber import ViberObject
from viber.error import ApiVersionError
from viber.message import Location

from viber.enums import *
from viber.utils.helpers import get_enum, get_hex


class InternalBrowser(ViberObject):
    """
    This object represents internal browser for the keyboard.

    Note:
        This object is api level 3

    Attributes:
        action_button (:obj:`InternalBrowserActionButton` | :obj:`str`): Optional. Action button in internal's browser navigation bar.
        action_predefined_url (:obj:`str`): Optional. If action_button is 'send' or 'forward' then the value from this property will be used to be sent as message, otherwise ignored.
        title_type (:obj:`InternalBrowserTitleType` | :obj:`str`): Optional. Type of title for internal browser if has no custom_title field.
        custom_title (:obj:`str`): Optional. Custom text for internal's browser title, title_type will be ignored in case this key is presented.
        mode (:obj:`InternalBrowserMode` | :obj:`str`): Optional. Indicates that browser should be opened in a full screen or in partial size (50% of screen height). Full screen mode can be with orientation lock (both orientations supported, only landscape or only portrait).
        footer_type (:obj:`InternalBrowserFooterType` | :obj:`str`): Optional. Should the browser's footer will be displayed.
        action_reply_data (:obj:`str`): Optional. Custom reply data for 'send-to-bot' action_button that will be resent in msgInfo.
        min_api_version (:obj:`int`): Optional.  Minimal api version.

    """
    def __init__(self, action_button=None,
                 action_predefined_url=None,
                 title_type=None,
                 custom_title=None,
                 mode=None,
                 footer_type=None,
                 action_reply_data=None,
                 min_api_version=6):

        if min_api_version < 3:
            raise ApiVersionError("internal browser is api level 3")

        self.action_button = get_enum(action_button, InternalBrowserActionButton, 'action_button')
        self.title_type = get_enum(title_type, InternalBrowserTitleType, 'title_type')
        self.mode = get_enum(mode, InternalBrowserMode, 'mode')
        self.footer_type = get_enum(footer_type, InternalBrowserFooterType, 'footer_type')

        self.action_predefined_url = action_predefined_url
        self.custom_title = custom_title
        if action_reply_data and min_api_version < 6:
            raise ApiVersionError("action_reply_data is api level 6")
        self.action_reply_data = action_reply_data

    def to_dict(self):
        data = dict()
        if self.action_button:
            data['ActionButton'] = self.action_button
        if self.title_type:
            data['TitleType'] = self.title_type
        if self.mode:
            data['Mode'] = self.mode
        if self.footer_type:
            data['FooterType'] = self.footer_type
        if self.action_predefined_url:
            data['ActionPredefinedURL'] = self.action_predefined_url
        if self.custom_title:
            data['CustomTitle'] = self.custom_title
        if self.action_reply_data:
            data['ActionReplyData'] = self.action_reply_data

        return data


class Map(Location):
    """
    This object represents map for the keyboard.

    Note:
        This object is api level 6

    Attributes:
        lat (:obj:`float`): Optional. Location latitude.
        lon (:obj:`float`): Optional. Location longitude.
    """
    def to_dict(self):
        data = dict()
        data['Latitude'] = self.lat
        data['Longitude'] = self.lon
        return data


class Frame(ViberObject):
    """
    This object represents frame for the keyboard.

    Note:
        This object is api level 6

    Attributes:
        border_width (:obj:`int`): Optional. Width of border.
        border_color (:obj:`str`): Optional. Color of border in HEX format.
        corner_radius (:obj:`int`): Optional. The border will be drawn with rounded corners.
    """
    def __init__(self,
                 border_width=1,
                 border_color='#000000',
                 corner_radius=0):
        if border_width < 0 or border_width > 10:
            TypeError("border_width must be int in range 0-10")
        if corner_radius < 0 or corner_radius > 10:
            TypeError("corner_radius must be int in range 0-10")

        self.border_width = border_width
        self.corner_radius = corner_radius
        self.border_color = self._get_hex(border_color, 'border_color')

    def to_dict(self):
        data = dict()
        data['BorderWidth'] = self.border_width
        data['BorderColor'] = self.border_color
        data['CornerRadius'] = self.corner_radius
        return data


class MediaPlayer(ViberObject):
    """
    This object represents media_player for the keyboard.

    Note:
        This object is api level 6

    Attributes:
        title (:obj:`str`): Optional. Media player's title (first line).
        subtitle (:obj:`str`): Optional. Media player's subtitle (second line).
        thumbnail_url (:obj:`str`): Optional. The URL for player's thumbnail (background).
        loop (:obj:`bool`): Optional. Whether the media player should be looped forever or not.
    """
    def __init__(self,
                 title=None,
                 subtitle=None,
                 thumbnail_url=None,
                 loop=False):
        self.title = title
        self.subtitle = subtitle
        self.thumbnail_url = thumbnail_url
        self.loop = loop

    def to_dict(self):
        data = dict()
        if self.title:
            data["Title"] = self.title
        if self.subtitle:
            data["Subtitle"] = self.subtitle
        if self.thumbnail_url:
            data["ThumbnailURL"] = self.thumbnail_url

        data["Loop"] = self.loop
        return data


class KeyboardButton(ViberObject):
    def __init__(self, action_body,
                 text=None,
                 action_type=ButtonActionType.reply,
                 image=None,
                 bg_media=None,
                 bg_color=None,
                 min_api_version=6,
                 columns=6,
                 rows=1,
                 silent=None,
                 bg_media_type=None,
                 bg_media_scale_type=None,
                 image_scale_type=None,
                 bg_loop=True,
                 text_v_align=VerticalAlign.middle,
                 text_h_align=HorizontalAlign.center,
                 text_paddings=None,
                 text_opacity=100,
                 text_size=TextSize.regular,
                 open_url_type=OpenURLType.internal,
                 open_url_media_type=OpenURLMediaType.not_media,
                 text_bg_gradient_color=None,
                 text_should_fit=None,
                 internal_browser=None,
                 map=None,
                 frame=None,
                 media_player=None):
        """
        This object represents one button of the keyboard. For enums String can be
        used instead of enum objects to specify value.

        Note:
            The :attr:`silent` is supported on devices running Viber version 6.7 and above.
            The api level 3 is supported on devices running Viber version 7.6 and above.

        Attributes:
            action_body (:obj:`str`): Text for reply and none ActionType, or URL for open-url.
            text (:obj:`str`): Optional. Text to be displayed on the button. Can contain some HTML tags.
            action_type (:obj:`ActionType` | :obj:`str`): Optional. Type of action pressing the button will perform.
            image (:obj:`str`): Optional. URL of image to place on top of background (if any). Can be a partially transparent image that will allow showing some of the background. Will be placed with aspect to fill logic.
            bg_media (:obj:`str`): Optional. URL for background media content (picture or gif). Will be placed with aspect to fill logic.
            bg_color (:obj:`str`): Optional. Background color of button in HEX format.
            min_api_version (:obj:`int`): Optional. Minimal api version.
            columns (:obj:`int`): Optional. Button width in columns.
            rows (:obj:`int`): Optional. Button height in rows.
            silent (:obj:`bool`): Optional. Determine whether the user action is presented in the conversation.
            bg_media_type (:obj:`MediaType` | :obj:`str`): Optional. Type of the background media.
            bg_media_scale_type (:obj:`ScaleType` | :obj:`str`): Optional. Options for scaling the bounds of the background to the bounds of this view.
            image_scale_type (:obj:`ScaleType` | :obj:`str`): Optional. Options for scaling the bounds of an image to the bounds of this view.
            bg_loop (:obj:`bool`): Optional. When 'True' - animated background media (gif) will loop continuously. When 'False' - animated background media will play once and stop.
            text_v_align (:obj:`VerticalAlign` | :obj:`str`): Optional. Vertical alignment of the text.
            text_h_align (:obj:`HorizontalAlign` | :obj:`str`): Optional. Horizontal align of the text.
            text_paddings (:obj:`list`): Optional. Custom paddings for the text in points. The value is an array of Integers [top, left, bottom, right.
            text_opacity (:obj:`int`): Optional. Text opacity.
            text_size (:obj:`TextSize` | :obj:`str`): Optional. Text size out of 3 available options.
            open_url_type (:obj:`OpenURLType` | :obj:`str`): Optional. Determine the open-url action result, in app or external browser.
            open_url_media_type (:obj:`OpenURLMediaType` | :obj:`str`): Optional. Determine the url media type. 'not-media' - force browser usage. 'video' - will be opened via media player. 'gif' - client will play the gif in full screen mode. 'picture' - client will open the picture in full screen mode.
            text_bg_gradient_color (:obj:`str`): Optional. Background gradient to use under text in HEX format, works only when text_v_align is equal to 'top' or 'bottom'.
            text_should_fit (:obj:`bool`): Optional. If true the size of text will decreased to fit (minimum size is 12).
            internal_browser (:obj:`InternalBrowser`): Optional. Internal browser configuration for 'open-url' action_type with 'internal' open_url_type.
            map (:obj:`Map`): Optional. Map configuration for 'open-map' action_type with internal open_url_type.
            frame (:obj:`Frame`): Optional. Draw frame above the background on the button, the size will be equal the size of the button.
            media_player (:obj:`MediaPlayer`): Optional. Specifies media player options. Will be ignored if open_url_media_type is not 'video' or 'audio'.

        """

        # Required
        self.action_type = get_enum(action_type, ButtonActionType, 'action_type')
        self.action_body = action_body
        # Optionals
        if action_type is ButtonActionType.reply and not text and not image and not bg_media and not bg_color:
            TypeError("With action reply must button must have one of the following: text, image, bg_media, bg_color")

        self.min_api_version = min_api_version
        self.text = text
        self.image = image
        self.bg_media = bg_media
        self.bg_loop = bg_loop
        self.silent = silent
        if text_should_fit and min_api_version < 6:
            raise ApiVersionError("text_should_fit is api level 6")

        self.text_should_fit = text_should_fit

        self.bg_color = get_hex(bg_color, 'bg_color')

        if columns:
            if not isinstance(columns, int) or not (1 <= columns <= 6):
                TypeError("columns must be int in range 1-6")
        self.columns = columns

        if rows:
            if not isinstance(rows, int) or not (1 <= columns <= 2):
                TypeError("rows must be int in range 1-2")
        self.rows = rows

        self.bg_media_type = get_enum(bg_media_type, MediaType, 'bg_media_type')
        self.bg_media_scale_type = get_enum(bg_media_scale_type, ScaleType, 'bg_media_scale_type')
        self.image_scale_type = get_enum(image_scale_type, ScaleType, 'image_scale_type')
        self.text_h_align = get_enum(text_h_align, HorizontalAlign, 'text_h_align')
        self.text_v_align = get_enum(text_v_align, VerticalAlign, 'text_v_align')
        self.text_size = get_enum(text_size, TextSize, 'text_size')
        self.open_url_type = get_enum(open_url_type, OpenURLType, 'open_url_type')
        self.open_url_media_type = get_enum(open_url_media_type, OpenURLMediaType, 'open_url_media_type')

        if self.bg_media_scale_type and min_api_version < 6:
            raise ApiVersionError("bg_media_scale_type is api level 6")
        if self.image_scale_type and min_api_version < 6:
            raise ApiVersionError("image_scale_type is api level 6")

        if text_paddings:
            if min_api_version < 4:
                raise ApiVersionError("text_paddings is api level 4")
            if isinstance(text_paddings, list) and len(text_paddings) == 4 and all([1 <= x <= 12 for x in text_paddings]):
                self.text_paddings = text_paddings
            else:
                raise TypeError("text_paddings must be list which contains 4 in values in range 0-12")
        else:
            self.text_paddings = None

        if not (0 <= text_opacity <= 100):
            raise TypeError("text_opacity must be in in range 0-100")

        self.text_opacity = text_opacity

        if text_bg_gradient_color:
            if text_v_align is VerticalAlign.top or text_v_align is VerticalAlign.bottom:
                self.text_bg_gradient_color = get_hex(text_bg_gradient_color, 'text_bg_gradient_color')
            else:
                raise TypeError("text_bg_gradient_color can be set only if text_v_align is 'top' or 'bottom'")
        else:
            self.text_bg_gradient_color = None

        if internal_browser:
            if min_api_version < 3:
                raise ApiVersionError("internal_browser is api level 3")

            if self.action_type is ButtonActionType.open_url and self.open_url_type is OpenURLType.internal and isinstance(internal_browser, InternalBrowser):
                self.internal_browser = internal_browser
            else:
                raise TypeError("internal_browser must be InternalBrowser instance and can be set only if action_type is 'open-url' and open_url_type is 'internal'")
        else:
            self.internal_browser = None

        if map:
            if min_api_version < 6:
                raise ApiVersionError("map is api level 6")

            if self.action_type is ButtonActionType.location_picker and self.open_url_type is OpenURLType.internal and isinstance(map, Map):
                self.map = map
            else:
                raise TypeError("map must be Map instance and can be set only if action_type is 'location-picker' and open_url_type is 'internal'")
        else:
            self.map = None

        if frame:
            if min_api_version < 6:
                raise ApiVersionError("frame is api level 6")

            if isinstance(frame, Frame):
                self.frame = frame
            else:
                raise TypeError("frame must be Frame instance")
        else:
            self.frame = None

        if media_player:
            if min_api_version < 6:
                raise ApiVersionError("media_player is api level 6")

            if self.open_url_media_type is OpenURLMediaType.video and isinstance(media_player, MediaPlayer):
                self.media_player = media_player
            else:
                raise TypeError("media_player must be MediaPlayer instance and can be set only if open_url_media_type is 'video'")
        else:
            self.media_player = None

    def to_dict(self):
        data = dict()
        data['ActionType'] = self.action_type.value
        data['ActionBody'] = self.action_body

        data['Columns'] = self.columns
        data['Rows'] = self.rows

        data['BgLoop'] = self.bg_loop
        data['TextVAlign'] = self.text_v_align.value
        data['TextHAlign'] = self.text_h_align.value
        data['TextPaddings'] = self.text_paddings
        data['TextOpacity'] = self.text_opacity
        data['TextSize'] = self.text_size.value
        data['OpenURLType'] = self.open_url_type.value
        data['OpenURLMediaType'] = self.open_url_media_type.value
        data['TextShouldFit'] = self.text_should_fit

        if self.silent is not None:
            data['silent'] = self.silent
        if self.min_api_version:
            data['minApiVersion'] = self.min_api_version
        if self.text:
            data['Text'] = self.text
        if self.image:
            data['Image'] = self.image
        if self.bg_media:
            data['BgMedia'] = self.bg_media
        if self.bg_color:
            data['BgColor'] = self.bg_color
        if self.bg_media_type:
            data['BgMediaType'] = self.bg_media_type.value
        if self.bg_media_scale_type:
            data['BgMediaScaleType'] = self.bg_media_scale_type.value
        if self.image_scale_type:
            data['ImageScaleType'] = self.image_scale_type.value
        if self.text_bg_gradient_color:
            data['TextBgGradientColor'] = self.text_bg_gradient_color
        if self.internal_browser:
            data['InternalBrowser'] = self.internal_browser.to_dict()
        if self.map:
            data['Map'] = self.map.to_dict()
        if self.frame:
            data['Frame'] = self.frame.to_dict()
        if self.media_player:
            data['MediaPlayer'] = self.media_player.to_dict()

        return data
