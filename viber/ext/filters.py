import re

from viber.message import MessageType


class BaseFilter(object):
    name = None

    def __call__(self, message):
        return self.filter(message)

    def __and__(self, other):
        return MergedFilter(self, and_filter=other)

    def __or__(self, other):
        return MergedFilter(self, or_filter=other)

    def __invert__(self):
        return InvertedFilter(self)

    def __repr__(self):
        # We do this here instead of in a __init__ so filter don't have to call __init__ or super()
        if self.name is None:
            self.name = self.__class__.__name__
        return self.name

    def filter(self, message):

        raise NotImplementedError


class InvertedFilter(BaseFilter):

    def __init__(self, f):
        self.f = f

    def filter(self, message):
        return not self.f(message)

    def __repr__(self):
        return "<inverted {}>".format(self.f)


class MergedFilter(BaseFilter):
    def __init__(self, base_filter, and_filter=None, or_filter=None):
        self.base_filter = base_filter
        self.and_filter = and_filter
        self.or_filter = or_filter

    def filter(self, message):
        if self.and_filter:
            return self.base_filter(message) and self.and_filter(message)
        elif self.or_filter:
            return self.base_filter(message) or self.or_filter(message)

    def __repr__(self):
        return "<{} {} {}>".format(self.base_filter, "and" if self.and_filter else "or",
                                   self.and_filter or self.or_filter)


class Filters(object):

    class _All(BaseFilter):
        name = 'Filters.all'

        def filter(self, message):
            return True

    all = _All()
    """:obj:`Filter`: All Messages."""

    class _Text(BaseFilter):
        name = 'Filters.text'

        def filter(self, message):
            return bool(message.text and not message.text.startswith('/'))

    text = _Text()
    """:obj:`Filter`: Text Messages."""

    class _Command(BaseFilter):
        name = 'Filters.command'

        def filter(self, message):
            return bool(message.text and message.text.startswith('/'))

    command = _Command()
    """:obj:`Filter`: Messages starting with ``/``."""

    class regex(BaseFilter):
        def __init__(self, pattern):
            self.pattern = re.compile(pattern)
            self.name = 'Filters.regex({})'.format(self.pattern)

        # TODO: Once the callback revamp (#1026) is done, the regex filter should be able to pass
        # the matched groups and groupdict to the context object.

        def filter(self, message):
            if message.text:
                return bool(self.pattern.search(message.text))
            return False

    class _File(BaseFilter):
        name = 'Filters.file'

        def filter(self, message):
            return message.type is MessageType.file

    file = _File()

    class _Picture(BaseFilter):
        name = 'Filters.picture'

        def filter(self, message):
            return message.type is MessageType.picture

    picture = _Picture()

    class _Sticker(BaseFilter):
        name = 'Filters.sticker'

        def filter(self, message):
            return message.type is MessageType.sticker

    sticker = _Sticker()

    class _Video(BaseFilter):
        name = 'Filters.video'

        def filter(self, message):
            return message.type is MessageType.video

    video = _Video()

    class _Contact(BaseFilter):
        name = 'Filters.contact'

        def filter(self, message):
            return message.type is MessageType.contact

    contact = _Contact()

    class _Location(BaseFilter):
        name = 'Filters.location'

        def filter(self, message):
            return message.type == MessageType.location

    location = _Location()

    class _Url(BaseFilter):
        name = 'Filters.url'

        def filter(self, message):
            return message.type == MessageType.url

    ulr = _Url()