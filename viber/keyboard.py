from viber import ViberObject
from viber.enums import InputFieldState, FavoritesMetadataType, KeyboardType
from viber.error import ApiVersionError
from viber.utils.helpers import get_enum, get_hex


class FavoritesMetadata(ViberObject):
    """
    This object represents Favorites Metadata which let the user save your content (gif, link, video) to the user's favorite extension. Later, when the user enters the favorites extended keyboard and sends an item, the original Carousel content (rich message) will be sent.

    Attributes:
        type (:obj:`FavoritesMetadataType`): The type of content you serve.
        url (:obj:`str`): Accessible url of content.
        title (:obj:`str`): Optional. Title for your content.
        thumbnail (:obj:`str`): Optional. Accessible thumbnail url for your content (PNG, JPEG).
        domain (:obj:`str`): Optional. The top domain of your content url.
        width (:obj:`int`): Optional. Width of your thumbnail image in pixels.
        height (:obj:`int`): Optional. Height of your thumbnail image in pixels.
        min_api_version (:obj:`int`): Optional. Minimal api version.
        alternative_url (:obj:`str`): Optional. Alternative url for clients with apiVersion < min_api_version, this will be sent by bot to client, then the client has to send it back.
        alternative_text (:obj:`str`): Optional. Alternative title for the url for clients with apiVersion < min_api_version, this will be sent by bot to client, then the client has to send it back
    """
    def __init__(self,
                 type,
                 url,
                 title=None,
                 thumbnail=None,
                 domain=None,
                 width=None,
                 height=None,
                 min_api_version=None,
                 alternative_url=None,
                 alternative_text=None):

        self.type = self._set_enum(type, FavoritesMetadataType, 'type')
        self.url = url
        self.title = title
        self.thumbnail = thumbnail
        self.domain = domain
        self.width = width
        self.height = height
        self.min_api_version = min_api_version
        if self.min_api_version is None and (alternative_url or alternative_text):
            raise TypeError("alternative_url or alternative_text can be set only in min_api_version specified")
        self.alternative_url = alternative_url
        self.alternative_text = alternative_text

    def to_dict(self):
        data = dict()
        data['type'] = self.type.value
        data['url'] = self.url

        if self.title:
            data['title'] = self.title
        if self.thumbnail:
            data['thumbnail'] = self.thumbnail
        if self.domain:
            data['domain'] = self.domain
        if self.width:
            data['width'] = self.width
        if self.height:
            data['height'] = self.height
        if self.min_api_version:
            data['minApiVersion'] = self.min_api_version
        if self.alternative_url:
            data['alternativeUrl'] = self.alternative_url
        if self.alternative_text:
            data['alternativeText'] = self.alternative_text
        return data


class Keyboard(ViberObject):
    """
    This object represents a custom keyboard for send_message action.

    Attributes:
        type (:obj:`KeyboardType` | :obj:`str`): Keyboard type.
        buttons (:obj:`list`): Array containing all keyboard buttons by order.
        bg_color (:obj:`str`): Optional. Background color of the keyboard in HEX format.
        min_api_version (:obj:`int`): Optional. Minimal api version.
        default_height (:obj:`bool`): Optional. When True - the keyboard will always be displayed with the same height as the native keyboard.When False - short keyboards will be displayed with the minimal possible height. Maximal height will be native keyboard height.
        custom_default_height (:obj:`int`): Optional. How much percent of free screen space in chat should be taken by keyboard. The final height will be not less than height of system keyboard.
        height_scale (:obj:`int`): Optional. Allow use custom aspect ratio for Carousel content blocks. Scales the height of the default square block (which is defined on client side) to the given value in percents. It means blocks can become not square and it can be used to create Carousel content with correct custom aspect ratio. This is applied to all blocks in the Carousel content
        buttons_group_columns (:obj:`int`): Optional. Represents size of block for grouping buttons during layout.
        buttons_group_rows (:obj:`int`): Optional. Represents size of block for grouping buttons during layout.
        input_field_state (:obj:`InputFieldState` | :obj:`str`): Optional. Customize the keyboard input field.
        favorites_metadata (:obj:`FavoritesMetadata`): Optional. Object, which describes Carousel content to be saved via favorites bot, if saving is available.
    """
    def __init__(self,
                 keyboard_type=KeyboardType.keyboard,
                 buttons=None,
                 bg_color=None,
                 min_api_version=6,
                 default_height=None,
                 custom_default_height=None,
                 height_scale=None,
                 buttons_group_columns=None,
                 buttons_group_rows=None,
                 input_field_state=None,
                 favorites_metadata=None
                 ):

        # Required
        if buttons:
            self.buttons = buttons
        else:
            self.buttons = []

        # Optionals
        self.keyboard_type = get_enum(keyboard_type, KeyboardType, 'keyboard_type')
        self.min_api_version = min_api_version
        self.bg_color = get_hex(bg_color, 'bg_color')
        self.default_height = default_height
        if custom_default_height:
            if min_api_version < 3:
                raise ApiVersionError("custom_default_height is api level 3")
            if isinstance(custom_default_height, int) and 40 <= custom_default_height <= 70:
                self.custom_default_height = custom_default_height
            else:
                raise TypeError("custom_default_height must be int in range 40-70")
        else:
            self.custom_default_height = None

        if height_scale:
            if min_api_version < 3:
                raise ApiVersionError("height_scale is api level 3")
            if not (20 <= height_scale <= 100):
                raise TypeError("height_scale must be int in range 20-100")

        self.height_scale = height_scale

        if buttons_group_columns:
            if min_api_version < 4:
                raise ApiVersionError("buttons_group_columns is api level 4")
            if not (1 <= buttons_group_columns <= 6):
                raise TypeError("buttons_group_columns must be int in range 1-6")

        self.buttons_group_columns = buttons_group_columns

        if buttons_group_rows:
            if min_api_version < 4:
                raise ApiVersionError("buttons_group_rows is api level 4")
            if 1 <= buttons_group_rows <= 7:
                self.buttons_group_rows = buttons_group_rows
            else:
                raise TypeError("buttons_group_rows must be int in range 1-7")
        else:
            self.buttons_group_rows = None

        if input_field_state:
            if min_api_version < 4:
                raise ApiVersionError("input_field_state is api level 4")

        self.input_field_state = get_enum(input_field_state, InputFieldState, 'input_field_state')

        if favorites_metadata:
            if min_api_version < 6:
                raise ApiVersionError("favorites_metadata is api level 6")
            if isinstance(favorites_metadata, FavoritesMetadata):
                self.favorites_metadata = favorites_metadata
            else:
                raise TypeError("favorites_metadata must be FavoritesMetadata instance")
        else:
            self.favorites_metadata = None

    def to_dict(self):
        data = dict()
        data['Type'] = self.keyboard_type.value
        if self.bg_color:
            data['BgColor'] = self.bg_color

        if self.default_height:
            data['DefaultHeight'] = self.default_height
        if self.min_api_version:
            data['minApiVersion'] = self.min_api_version
        if self.height_scale:
            data['HeightScale'] = self.height_scale
        if self.buttons_group_columns:
            data['ButtonsGroupColumns'] = self.buttons_group_columns
        if self.input_field_state:
            data['InputFieldState'] = self.input_field_state.value

        if self.buttons_group_rows:
            data['ButtonsGroupRows'] = self.buttons_group_rows
        if self.favorites_metadata:
            data['FavoritesMetadata'] = self.favorites_metadata
        if self.custom_default_height:
            data['CustomDefaultHeight'] = self.custom_default_height

        if len(self.buttons) == 0:
            TypeError("Must be at least one button")

        r = []
        for button in self.buttons:
            r.append(button.to_dict())
        data['Buttons'] = r
        return data

    def add_button(self, button):
        self.buttons.append(button)
