import enum


class UserRole(enum.Enum):
    admin = 'admin'
    participant = 'participant'


class KeyboardType(enum.Enum):
    keyboard = 'keyboard'
    rich_media = 'rich_media'


class FavoritesMetadataType(enum.Enum):
    gif = 'gif'
    link = 'link'
    video = 'video'


class InputFieldState(enum.Enum):
    """
    'regular' - display regular size input field.
    'minimized' - display input field minimized by default.
    'hidden' - hide the input field.
    """
    regular = 'regular'
    minimized = 'minimized'
    hidden = 'hidden'


class ButtonActionType(enum.Enum):
    reply = 'reply'
    open_url = 'open-url'
    share_phone = 'share-phone'
    location_picker = 'location-picker'
    none = 'none'


class MessageType(enum.Enum):
    text = 'text'
    picture = 'picture'
    video = 'video'
    file = 'file'
    sticker = 'sticker'
    contact = 'contact'
    url = 'url'
    location = 'location'
    rich_media = 'rich_media'


class MediaType(enum.Enum):
    picture = 'picture'
    gif = 'gif'


class ScaleType(enum.Enum):
    crop = 'crop'
    fill = 'fill'
    fit = 'fit'


class VerticalAlign(enum.Enum):
    top = 'top'
    middle = 'middle'
    bottom = 'bottom'


class HorizontalAlign(enum.Enum):
    left = 'left'
    center = 'center'
    right = 'right'


class TextSize(enum.Enum):
    small = 'small'
    regular = 'regular'
    large = 'large'


class OpenURLType(enum.Enum):
    internal = 'internal'
    external = 'external'


class OpenURLMediaType(enum.Enum):
    not_media = 'not-media'
    video = 'video'
    gif = 'gif'
    picture = 'picture'


class InternalBrowserActionButton(enum.Enum):
    """
    'forward' - will open the forward via Viber screen and share current URL or predefined URL.
    'send' - sends the currently opened URL as an URL message.
    'open-externally' - opens external browser with the current URL.
    'send-to-bot' - (api level 6) sends reply data in msgInfo to bot in order to receive message.
    'none' - will not display any button
    """
    forward = 'forward'
    send = 'send'
    open_externally = 'open-externally'
    send_to_bot = 'send-to-bot'
    none = 'none'


class InternalBrowserTitleType(enum.Enum):
    """
    'default' - the content in the page's <OG:title> element or in <title> tag.
    'domain' - the top level domain.
    """
    domain = 'domain'
    default = 'default'


class InternalBrowserMode(enum.Enum):
    fullscreen = 'fullscreen'
    fullscreen_portrait = 'fullscreen-portrait'
    fullscreen_landscape = 'fullscreen-landscape'
    partial_size = 'partial-size'


class InternalBrowserFooterType(enum.Enum):
    """
    'default' - display footer.
    'hidden' - hide footer.
    """
    default = 'default'
    hidden = 'hidden'


class EventType(enum.Enum):
    webhook = 'webhook'
    subscribed = 'subscribed'
    unsubscribed = 'unsubscribed'
    delivered = 'delivered'
    seen = 'seen'
    failed = 'failed'
    conversation_started = 'conversation_started'
    message = 'message'
