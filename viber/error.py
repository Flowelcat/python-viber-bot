class ViberError(Exception):
    pass


class InvalidToken(ViberError):
    def __init__(self):
        super(InvalidToken, self).__init__('Invalid token')


class NetworkError(ViberError):
    pass

class ApiVersionError(ViberError):
    pass

class BadRequest(NetworkError):
    pass


class TimedOut(NetworkError):

    def __init__(self):
        super(TimedOut, self).__init__('Timed out')

class InvalidWebhookUrl(NetworkError):
    pass

class Unauthorized(ViberError):
    pass

class RetryAfter(ViberError):
    def __init__(self, retry_after):
        super(RetryAfter,
              self).__init__('Flood control exceeded. Retry in {} seconds'.format(retry_after))
        self.retry_after = float(retry_after)
