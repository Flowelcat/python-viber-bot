import json
import logging
import socket
import sys

import certifi
import urllib3
from urllib3 import Timeout
from urllib3.connection import HTTPConnection

from viber.error import TimedOut, NetworkError, ViberError, InvalidToken, Unauthorized, BadRequest, InvalidWebhookUrl

USER_AGENT = 'Python Viber Bot'


class Request(object):
    def __init__(self, token, con_pool_size=1, connect_timeout=5., read_timeout=5.):
        self.token = token
        self._connect_timeout = connect_timeout

        sockopts = HTTPConnection.default_socket_options + [
            (socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)]

        # TODO: Support other platforms like mac and windows.
        if 'linux' in sys.platform:
            sockopts.append((socket.IPPROTO_TCP,
                             socket.TCP_KEEPIDLE, 120))  # pylint: disable=no-member
            sockopts.append((socket.IPPROTO_TCP,
                             socket.TCP_KEEPINTVL, 30))  # pylint: disable=no-member
            sockopts.append((socket.IPPROTO_TCP,
                             socket.TCP_KEEPCNT, 8))  # pylint: disable=no-member

        self._con_pool_size = con_pool_size

        kwargs = dict(
            maxsize=con_pool_size,
            cert_reqs='CERT_REQUIRED',
            ca_certs=certifi.where(),
            socket_options=sockopts,
            timeout=urllib3.Timeout(
                connect=self._connect_timeout, read=read_timeout, total=None))

        mgr = urllib3.PoolManager(**kwargs)

        self._con_pool = mgr

    @property
    def con_pool_size(self):
        """The size of the connection pool used."""
        return self._con_pool_size

    def stop(self):
        self._con_pool.clear()

    def _parse(self, json_data):
        try:
            decoded_s = json_data.decode('utf-8')
            data = json.loads(decoded_s)
        except UnicodeDecodeError:
            logging.getLogger(__name__).debug('Logging raw invalid UTF-8 response:\n%r', json_data)
            raise ViberError('Server response could not be decoded using UTF-8')
        except ValueError:
            raise ViberError('Invalid server response')

        return data

    def _request_wrapper(self, *args, **kwargs):
        if 'headers' not in kwargs:
            kwargs['headers'] = {}

        kwargs['headers']['connection'] = 'keep-alive'
        kwargs['headers']['X-Viber-Auth-Token'] = self.token
        # Also set our user agent
        kwargs['headers']['user-agent'] = USER_AGENT

        try:
            resp = self._con_pool.request(*args, **kwargs)
        except urllib3.exceptions.TimeoutError:
            raise TimedOut()
        except urllib3.exceptions.HTTPError as error:
            # HTTPError must come last as its the base urllib3 exception class
            # TODO: do something smart here; for now just raise NetworkError
            raise NetworkError('urllib3 HTTPError {0}'.format(error))

        try:
            data = self._parse(resp.data)
        except ValueError:
            message = 'Unknown HTTPError'

        if 200 <= resp.status <= 299:
            # 200-299 range are HTTP success statuses
            if isinstance(data, dict):
                response_status = data['status']
                if response_status == 0:
                    return data
                elif response_status == 1:
                    raise InvalidWebhookUrl(data['status_message'])
                else:
                    raise NetworkError(data or message)
            else:
                return data

        if resp.status in (401, 403):
            raise Unauthorized(data)
        elif resp.status == 400:
            raise BadRequest(data)
        elif resp.status == 404:
            raise InvalidToken()
        elif resp.status == 502:
            raise NetworkError('Bad Gateway')
        else:
            raise NetworkError('{0} ({1})'.format(data, resp.status))

    def post(self, url, data, timeout=None):
        urlopen_kwargs = {}

        if timeout is not None:
            urlopen_kwargs['timeout'] = Timeout(read=timeout, connect=self._connect_timeout)

        result = self._request_wrapper('POST', url,
                                       body=json.dumps(data).encode('utf-8'),
                                       headers={'Content-Type': 'application/json'})

        return result

    def retrieve(self, url, timeout=None, **params):
        """Retrieve the contents of a file by its URL.

        Args:
            url (:obj:`str`): The web location we want to retrieve.
            timeout (:obj:`int` | :obj:`float`): If this value is specified, use it as the read
                timeout from the server (instead of the one specified during creation of the
                connection pool).

        """
        urlopen_kwargs = {}
        if timeout is not None:
            urlopen_kwargs['timeout'] = Timeout(read=timeout, connect=self._connect_timeout)
        urlopen_kwargs.update({'fields': params})

        return self._request_wrapper('GET', url, **urlopen_kwargs)
