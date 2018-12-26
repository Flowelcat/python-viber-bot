"""Constants in the Viber network.

Attributes:
    MAX_MESSAGE_LENGTH (:obj:`int`): 4096
    MAX_CAPTION_LENGTH (:obj:`int`): 200
    SUPPORTED_WEBHOOK_PORTS (List[:obj:`int`]): [443, 80, 88, 8443]
    MAX_FILESIZE_DOWNLOAD (:obj:`int`): In bytes (20MB)
    MAX_FILESIZE_UPLOAD (:obj:`int`): In bytes (50MB)
    MAX_MESSAGES_PER_SECOND_PER_CHAT (:obj:`int`): `1`. Telegram may allow short bursts that go
        over this limit, but eventually you'll begin receiving 429 errors.
    MAX_MESSAGES_PER_SECOND (:obj:`int`): 30
    MAX_MESSAGES_PER_MINUTE_PER_GROUP (:obj:`int`): 20
    MAX_INLINE_QUERY_RESULTS (:obj:`int`): 50

The following constant have been found by experimentation:

Attributes:
    MAX_MESSAGE_ENTITIES (:obj:`int`): 100 (Beyond this cap telegram will simply ignore further
        formatting styles)

"""

MAX_PICTURE_DESCRIPTION_LENGTH = 120
MAX_PICTURE_SIZE = int(1E6)  # (1MB)
MAX_THUMBNAIL_SIZE = int(1E5)  # (100KB)
MAX_TRACKING_DATA_LENGTH = 4000
MAX_VIDEO_SIZE = int(50E6)  # 50MB
MAX_FILE_SIZE = int(50E6)  # 50MB
MAX_VIDEO_DURATION = 180  # 180 seconds
MAX_FILE_NAME_LENGTH = 256
MAX_URL_LENGTH = 2000

# constants above this line are tested

# SUPPORTED_WEBHOOK_PORTS = [443, 80, 88, 8443]
# MAX_FILESIZE_DOWNLOAD = int(20E6)  # (20MB)
# MAX_FILESIZE_UPLOAD = int(50E6)  # (50MB)
# MAX_MESSAGES_PER_SECOND_PER_CHAT = 1
# MAX_MESSAGES_PER_SECOND = 30
# MAX_MESSAGES_PER_MINUTE_PER_GROUP = 20
# MAX_MESSAGE_ENTITIES = 100
# MAX_INLINE_QUERY_RESULTS = 50
