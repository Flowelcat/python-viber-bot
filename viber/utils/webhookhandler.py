import hashlib
import hmac
import json
import logging
from threading import Lock

from future.utils import bytes_to_native_str

from viber.event import Event

try:
    import BaseHTTPServer
except ImportError:
    import http.server as BaseHTTPServer


class _InvalidPost(Exception):

    def __init__(self, http_code):
        self.http_code = http_code
        super(_InvalidPost, self).__init__()


class WebhookServer(BaseHTTPServer.HTTPServer, object):

    def __init__(self, server_address, RequestHandlerClass, event_queue, webhook_path, bot):
        super(WebhookServer, self).__init__(server_address, RequestHandlerClass)
        self.logger = logging.getLogger(__name__)
        self.event_queue = event_queue
        self.webhook_path = webhook_path
        self.bot = bot
        self.is_running = False
        self.server_lock = Lock()
        self.shutdown_lock = Lock()

    def serve_forever(self, poll_interval=0.5):
        with self.server_lock:
            self.is_running = True
            self.logger.debug('Webhook Server started.')
            super(WebhookServer, self).serve_forever(poll_interval)
            self.logger.debug('Webhook Server stopped.')

    def shutdown(self):
        with self.shutdown_lock:
            if not self.is_running:
                self.logger.warning('Webhook Server already stopped.')
                return
            else:
                super(WebhookServer, self).shutdown()
                self.is_running = False

    def handle_error(self, request, client_address):
        """Handle an error gracefully."""
        self.logger.debug('Exception happened during processing of request from %s',
                          client_address, exc_info=True)


class WebhookHandler(BaseHTTPServer.BaseHTTPRequestHandler, object):
    server_version = 'WebhookHandler/1.0'

    def __init__(self, request, client_address, server):
        self.logger = logging.getLogger(__name__)
        super(WebhookHandler, self).__init__(request, client_address, server)

    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        self.send_response(200)
        self.end_headers()

    def do_POST(self):
        self.logger.debug('Webhook triggered')
        try:
            clen = self._get_content_len()
            buf = self.rfile.read(clen)
            self._validate_post(buf)
        except _InvalidPost as e:
            self.send_error(e.http_code)
            self.end_headers()
        else:
            json_string = bytes_to_native_str(buf)

            self.send_response(200)
            self.end_headers()

            self.logger.debug('Webhook received data: ' + json_string)

            event = Event.from_dict(json.loads(json_string), self.server.bot)

            self.logger.debug('Received Update with message_token %d on Webhook' % event.message_token)
            self.server.event_queue.put(event)

    def _calculate_message_signature(self, message):
        return hmac.new(bytes(self.server.bot.token.encode('ascii')), msg=message, digestmod=hashlib.sha256).hexdigest()

    def verify_signature(self, request_data, signature):
        return signature == self._calculate_message_signature(request_data)


    def _validate_post(self, data):
        if not (self.verify_signature(data, self.path.replace('/?sig=', "")) and 'content-type' in self.headers and self.headers['content-type'] == 'application/json;charset=UTF-8'):
            raise _InvalidPost(403)

    def _get_content_len(self):
        clen = self.headers.get('content-length')
        if clen is None:
            raise _InvalidPost(411)
        try:
            clen = int(clen)
        except ValueError:
            raise _InvalidPost(403)
        if clen < 0:
            raise _InvalidPost(403)
        return clen

    def log_message(self, format, *args):
        """Log an arbitrary message.

        This is used by all other logging functions.

        It overrides ``BaseHTTPRequestHandler.log_message``, which logs to ``sys.stderr``.

        The first argument, FORMAT, is a format string for the message to be logged.  If the format
        string contains any % escapes requiring parameters, they should be specified as subsequent
        arguments (it's just like printf!).

        The client ip is prefixed to every message.

        """
        self.logger.debug("%s - - %s" % (self.address_string(), format % args))
