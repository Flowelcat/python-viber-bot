"""This module contains the class Updater, which tries to make creating viber bots intuitive."""

import logging
import os
import ssl
import subprocess
from signal import SIGINT, SIGTERM, SIGABRT, signal
from threading import Thread, current_thread, Lock, Event
from time import sleep

from queue import Queue
from telegram.utils.helpers import get_signal_name

from viber.bot import Bot
from viber.enums import EventType
from viber.error import ViberError, RetryAfter, TimedOut, InvalidToken
from viber.ext.dispatcher import Dispatcher
from viber.ext.jobqueue import JobQueue
from viber.utils.helpers import get_enum
from viber.utils.request import Request
from viber.utils.webhookhandler import WebhookServer, WebhookHandler


class Updater(object):
    """
    This class, which employs the :class:`viber.ext.Dispatcher`, provides a frontend to
    :class:`viber.Bot` to the programmer, so they can focus on coding the bot. Its purpose is to
    receive the updates from Viber and to deliver them to said dispatcher. It also runs in a
    separate thread, so the user can interact with the bot, for example on the command line. The
    dispatcher supports handlers for different kinds of data: Events from Viber, basic text
    commands and even arbitrary types. The updater can be started as a webhook to receive events.
    This is achieved using the WebhookServer and WebhookHandler classes.


    Attributes:
        bot (:class:`viber.Bot`): The bot used with this Updater.
        user_sig_handler (:obj:`signal`): signals the updater will respond to.
        event_queue (:obj:`Queue`): Queue for the events.
        job_queue (:class:`viber.ext.JobQueue`): Jobqueue for the updater.
        dispatcher (:class:`viber.ext.Dispatcher`): Dispatcher that handles the updates and dispatches them to the
            handlers.
        running (:obj:`bool`): Indicates if the updater is running.

    Args:
        token (:obj:`str`, optional): The bot's token.
        name (:obj:`str`, optional): The name of the bot.
        avatar (:obj:`str`, optional): Avatar of the bot.
        base_url (:obj:`str`, optional): Base_url for the bot.
        workers (:obj:`int`, optional): Amount of threads in the thread pool for functions
            decorated with ``@run_async``.
        bot (:class:`viber.Bot`, optional): A pre-initialized bot instance. If a pre-initialized
            bot is used, it is the user's responsibility to create it using a `Request`
            instance with a large enough connection pool.
        user_sig_handler (:obj:`function`, optional): Takes ``signum, frame`` as positional
            arguments. This will be called when a signal is received, defaults are (SIGINT,
            SIGTERM, SIGABRT) setable with :attr:`idle`.
        request_kwargs (:obj:`dict`, optional): Keyword args to control the creation of a
            `viber.utils.request.Request` object (ignored if `bot` argument is used). The
            request_kwargs are very useful for the advanced users who would like to control the
            default timeouts and/or control the proxy used for http communication.

    Note:
        You must supply either a :attr:`bot` or a :attr:`token` arguments.

    Raises:
        ValueError: If both :attr:`bot` and :attr:`token` are passed or none of them.

    """

    def __init__(self,
                 token=None,
                 name=None,
                 avatar=None,
                 base_url=None,
                 workers=4,
                 bot=None,
                 user_sig_handler=None,
                 request_kwargs=None):

        if bot is None and token is None:
            raise ValueError('`token` or `bot` must be passed')
        if bot and token:
            raise ValueError('`token` and `bot` are mutually exclusive')

        con_pool_size = workers + 3

        if bot is not None:
            self.bot = bot
            if bot.request.con_pool_size < con_pool_size:
                self.logger.warning(
                    'Connection pool of Request object is smaller than optimal value (%s)',
                    con_pool_size)
        else:
            if request_kwargs is None:
                request_kwargs = {}
            if 'con_pool_size' not in request_kwargs:
                request_kwargs['con_pool_size'] = con_pool_size
            self._request = Request(token=token, **request_kwargs)
            self.bot = Bot(token, name, avatar, base_url, request=self._request)

        self.user_sig_handler = user_sig_handler
        self.event_queue = Queue()
        self.job_queue = JobQueue(self.bot)
        self.logger = logging.getLogger(__name__)
        self.__exception_event = Event()
        self.dispatcher = Dispatcher(self.bot,
                                     self.event_queue,
                                     job_queue=self.job_queue,
                                     workers=workers,
                                     exception_event=self.__exception_event)

        self.running = False
        self.is_idle = False
        self.__lock = Lock()
        self.__threads = []

    def _init_thread(self, target, name, *args, **kwargs):
        thr = Thread(target=self._thread_wrapper, name=name, args=(target,) + args, kwargs=kwargs)
        thr.start()
        self.__threads.append(thr)

    def _thread_wrapper(self, target, *args, **kwargs):
        thr_name = current_thread().name
        self.logger.debug('{0} - started'.format(thr_name))
        try:
            target(*args, **kwargs)
        except Exception:
            self.__exception_event.set()
            self.logger.exception('unhandled exception in %s', thr_name)
            raise
        self.logger.debug('{0} - ended'.format(thr_name))

    def start_webhook(self,
                      listen='127.0.0.1',
                      port=80,
                      url_path='',
                      cert=None,
                      key=None,
                      webhook_url=None,
                      event_types=None):
        """
        Starts a small http server to listen for events via webhook. If cert
        and key are not provided, the webhook will be started directly on
        http://listen:port/url_path, so SSL can be handled by another
        application. Else, the webhook will be started on
        https://listen:port/url_path

        Args:
            listen (:obj:`str`, optional): IP-Address to listen on. Default ``127.0.0.1``.
            port (:obj:`int`, optional): Port the bot should be listening on. Default ``80``.
            url_path (:obj:`str`, optional): Path inside url.
            cert (:obj:`str`, optional): Path to the SSL certificate file.
            key (:obj:`str`, optional): Path to the SSL key file.
            webhook_url (:obj:`str`, optional): Explicitly specify the webhook url. Useful behind
                NAT, reverse proxy, etc. Default is derived from `listen`, `port` & `url_path`.
            event_types (List[:obj:`str`], optional): Passed to :attr:`viber.Bot.set_webhook`.

        Returns:
            :obj:`Queue`: The update queue that can be filled from the main thread.
    """

        checked_event_types = []
        if event_types is not None:
            if isinstance(event_types, list):
                for event in event_types:
                    checked_event_types.append(get_enum(event, EventType, 'event_type'))

        with self.__lock:
            if not self.running:
                self.running = True

                self.job_queue.start()
                self._init_thread(self.dispatcher.start, "dispatcher"),
                self._init_thread(self._start_webhook, "updater", listen, port, url_path)

                use_ssl = cert is not None and key is not None
                if use_ssl:
                    self._check_ssl_cert(cert, key)

                    # DO NOT CHANGE: Only set webhook if SSL is handled by library
                    if not webhook_url:
                        webhook_url = self._gen_webhook_url(listen, port, url_path)

                self.bot.set_webhook(url=webhook_url, certificate=cert, event_types=checked_event_types)

                self.logger.info("Webhook binded to {}".format(webhook_url))

                # Return the update queue so the main thread can insert updates
                return self.event_queue

    def _start_webhook(self, listen, port, url_path):

        self.logger.debug('Updater thread started (webhook)')
        if not url_path.startswith('/'):
            url_path = '/{0}'.format(url_path)

        self.httpd = WebhookServer((listen, port), WebhookHandler, self.event_queue, url_path, self.bot)

        self.httpd.serve_forever(poll_interval=1)

    @staticmethod
    def _gen_webhook_url(listen, port, url_path):
        return 'https://{listen}:{port}{path}'.format(listen=listen, port=port, path=url_path)

    def _check_ssl_cert(self, cert, key):
        # Check SSL-Certificate with openssl, if possible
        try:
            exit_code = subprocess.call(
                ["openssl", "x509", "-text", "-noout", "-in", cert],
                stdout=open(os.devnull, 'wb'),
                stderr=subprocess.STDOUT)
        except OSError:
            exit_code = 0
        if exit_code == 0:
            try:
                self.httpd.socket = ssl.wrap_socket(
                    self.httpd.socket, certfile=cert, keyfile=key, server_side=True)
            except ssl.SSLError as error:
                self.logger.exception('Failed to init SSL socket')
                raise ViberError(str(error))
        else:
            raise ViberError('SSL Certificate invalid')

    def stop(self):
        """Stops the webhook thread, the dispatcher and the job queue."""

        self.job_queue.stop()
        with self.__lock:
            if self.running or self.dispatcher.has_running_threads:
                self.logger.debug('Stopping Updater and Dispatcher...')

                self.running = False

                self._stop_httpd()
                self._stop_dispatcher()
                self._join_threads()

    def _stop_httpd(self):
        if self.httpd:
            self.logger.debug('Waiting for current webhook connection to be '
                              'closed...')
            self.httpd.shutdown()
            self.httpd = None

    def _stop_dispatcher(self):
        self.logger.debug('Requesting Dispatcher to stop...')
        self.dispatcher.stop()

    def _join_threads(self):
        for thr in self.__threads:
            self.logger.debug('Waiting for {0} thread to end'.format(thr.name))
            thr.join()
            self.logger.debug('{0} thread has ended'.format(thr.name))
        self.__threads = []

    def _network_loop_retry(self, action_cb, description, interval):
        """Perform a loop calling `action_cb`, retrying after network errors.

        Stop condition for loop: `self.running` evaluates False or return value of `action_cb`
        evaluates False.

        Args:
            action_cb (:obj:`callable`): Network oriented callback function to call.
            onerr_cb (:obj:`callable`): Callback to call when ViberError is caught. Receives the
                exception object as a parameter.
            description (:obj:`str`): Description text to use for logs and exception raised.
            interval (:obj:`float` | :obj:`int`): Interval to sleep between each call to
                `action_cb`.

        """
        self.logger.debug('Start network loop retry %s', description)
        cur_interval = interval

        while self.running:
            try:
                if not action_cb():
                    break
            except RetryAfter as e:
                self.logger.info('%s', e)
                cur_interval = 0.5 + e.retry_after
            except TimedOut as toe:
                self.logger.debug('Timed out %s: %s', description, toe)
                # If failure is due to timeout, we should retry asap.
                cur_interval = 0
            except InvalidToken as pex:
                self.logger.error('Invalid token; aborting')
                raise pex
            else:
                cur_interval = interval

            if cur_interval:
                sleep(cur_interval)

    def signal_handler(self, signum, frame):
        self.is_idle = False
        if self.running:
            self.logger.info('Received signal {} ({}), stopping...'.format(
                signum, get_signal_name(signum)))
            self.stop()
            if self.user_sig_handler:
                self.user_sig_handler(signum, frame)
        else:
            self.logger.warning('Exiting immediately!')
            import os
            os._exit(1)

    def idle(self, stop_signals=(SIGINT, SIGTERM, SIGABRT)):
        """Blocks until one of the signals are received and stops the updater.

        Args:
            stop_signals (:obj:`iterable`): Iterable containing signals from the signal module that
                should be subscribed to. Updater.stop() will be called on receiving one of those
                signals. Defaults to (``SIGINT``, ``SIGTERM``, ``SIGABRT``).

        """
        for sig in stop_signals:
            signal(sig, self.signal_handler)

        self.is_idle = True

        while self.is_idle:
            sleep(1)
