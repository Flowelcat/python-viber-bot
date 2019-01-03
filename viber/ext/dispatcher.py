import logging
import weakref
from functools import wraps
from threading import Event, Thread, current_thread, Lock, BoundedSemaphore
from collections import defaultdict
from queue import Empty, Queue
from time import sleep
from uuid import uuid4

from viber.error import ViberError
from viber.ext.handler import Handler
from viber.utils.promise import Promise

DEFAULT_GROUP = 0


def run_async(func):
    """
    Function decorator that will run the function in a new thread.

    Will run :attr:`viber.ext.Dispatcher.run_async`.

    Using this decorator is only possible when only a single Dispatcher exist in the system.

    Note: Use this decorator to run handlers asynchronously.

    """

    @wraps(func)
    def async_func(*args, **kwargs):
        return Dispatcher.get_instance().run_async(func, *args, **kwargs)

    return async_func


class DispatcherHandlerStop(Exception):
    """Raise this in handler to prevent execution any other handler (even in different group)."""
    pass


class Dispatcher(object):
    """
    This class dispatches all kinds of updates to its registered handlers.

    Attributes:
        bot (:class:`viber.Bot`): The bot object that should be passed to the handlers.
        event_queue (:obj:`Queue`): The synchronized queue that will contain the events.
        job_queue (:class:`viber.ext.JobQueue`): Optional. The :class:`viber.ext.JobQueue`
            instance to pass onto handler callbacks.
        workers (:obj:`int`): Number of maximum concurrent worker threads for the ``@run_async``
            decorator.

    Args:
        bot (:class:`viber.Bot`): The bot object that should be passed to the handlers.
        event_queue (:obj:`Queue`): The synchronized queue that will contain the updates.
        job_queue (:class:`viber.ext.JobQueue`, optional): The :class:`viber.ext.JobQueue`
                instance to pass onto handler callbacks.
        workers (:obj:`int`, optional): Number of maximum concurrent worker threads for the
            ``@run_async`` decorator. defaults to 4.

    """

    __singleton_lock = Lock()
    __singleton_semaphore = BoundedSemaphore()
    __singleton = None
    logger = logging.getLogger(__name__)

    def __init__(self, bot, event_queue, workers=4, process_silent_events=False, exception_event=None, job_queue=None):
        self.event_queue = event_queue
        self.job_queue = job_queue
        self.bot = bot
        self.workers = workers
        self.process_silent_events = process_silent_events

        self.handlers = {}
        """Dict[:obj:`int`, List[:class:`viber.ext.Handler`]]: Holds the handlers per group."""
        self.error_handlers = []
        """List[:obj:`callable`]: A list of errorHandlers."""
        self.groups = []
        """List[:obj:`int`]: A list with all groups."""
        self.user_data = defaultdict(dict)
        """:obj:`dict`: A dictionary handlers can use to store data for the user."""
        self.chat_data = defaultdict(dict)
        self.running = False
        """:obj:`bool`: Indicates if this dispatcher is running."""

        self.__stop_event = Event()
        self.__exception_event = exception_event or Event()
        self.__async_queue = Queue()
        self.__async_threads = set()

    @classmethod
    def _set_singleton(cls, val):
        cls.logger.debug('Setting singleton dispatcher as %s', val)
        cls.__singleton = weakref.ref(val) if val else None

    @classmethod
    def get_instance(cls):
        """
        Get the singleton instance of this class.

        Returns:
            :class:`viber.ext.Dispatcher`

        Raises:
            RuntimeError

        """
        if cls.__singleton is not None:
            return cls.__singleton()  # pylint: disable=not-callable
        else:
            raise RuntimeError('{} not initialized or multiple instances exist'.format(
                cls.__name__))

    def run_async(self, func, *args, **kwargs):
        """Queue a function (with given args/kwargs) to be run asynchronously.

        Args:
            func (:obj:`callable`): The function to run in the thread.
            *args (:obj:`tuple`, optional): Arguments to `func`.
            **kwargs (:obj:`dict`, optional): Keyword arguments to `func`.

        Returns:
            Promise

        """
        # TODO: handle exception in async threads
        #       set a threading.Event to notify caller thread
        promise = Promise(func, args, kwargs)
        self.__async_queue.put(promise)
        return promise

    def add_handler(self, handler, group=DEFAULT_GROUP):
        """
        Register a handler.

        TL;DR: Order and priority counts. 0 or 1 handlers per group will be used.

        A handler must be an instance of a subclass of :class:`viber.ext.Handler`. All handlers
        are organized in groups with a numeric value. The default group is 0. All groups will be
        evaluated for handling an event, but only 0 or 1 handler per group will be used. If
        :class:`viber.ext.DispatcherHandlerStop` is raised from one of the handlers, no further
        handlers (regardless of the group) will be called.

        The priority/order of handlers is determined as follows:

          * Priority of the group (lower group number == higher priority)
          * The first handler in a group which should handle an event (see
            :attr:`viber.ext.Handler.check_update`) will be used. Other handlers from the
            group will not be used. The order in which handlers were added to the group defines the
            priority.

        Args:
            handler (:class:`viber.ext.Handler`): A Handler instance.
            group (:obj:`int`, optional): The group identifier. Default is 0.

                """
        if not isinstance(handler, Handler):
            raise TypeError('handler is not an instance of {0}'.format(Handler.__name__))
        if not isinstance(group, int):
            raise TypeError('group is not int')

        if group not in self.handlers:
            self.handlers[group] = list()
            self.groups.append(group)
            self.groups = sorted(self.groups)

        self.handlers[group].append(handler)

    def remove_handler(self, handler, group=DEFAULT_GROUP):
        """Remove a handler from the specified group.

        Args:
            handler (:class:`viber.ext.Handler`): A Handler instance.
            group (:obj:`object`, optional): The group identifier. Default is 0.

        """
        if handler in self.handlers[group]:
            self.handlers[group].remove(handler)
            if not self.handlers[group]:
                del self.handlers[group]
                self.groups.remove(group)

    def add_error_handler(self, callback):
        """Registers an error handler in the Dispatcher.

        Args:
            callback (:obj:`callable`): A function that takes ``Bot, Event, ViberError`` as
                arguments.

        """
        self.error_handlers.append(callback)

    def remove_error_handler(self, callback):
        """Removes an error handler.

        Args:
            callback (:obj:`callable`): The error handler to remove.

        """
        if callback in self.error_handlers:
            self.error_handlers.remove(callback)

    @property
    def has_running_threads(self):
        return self.running or bool(self.__async_threads)

    def start(self, ready=None):
        """Thread target of thread 'dispatcher'.

        Runs in background and processes the event queue.

        Args:
            ready (:obj:`threading.Event`, optional): If specified, the event will be set once the
                dispatcher is ready.

        """

        if self.running:
            self.logger.warning('already running')
            if ready is not None:
                ready.set()
            return

        if self.__exception_event.is_set():
            msg = 'reusing dispatcher after exception event is forbidden'
            self.logger.error(msg)
            raise ViberError(msg)

        self._init_async_threads(uuid4(), self.workers)
        self.running = True
        self.logger.debug('Dispatcher started')

        if ready is not None:
            ready.set()

        while 1:
            try:
                # Pop event from event queue.
                event = self.event_queue.get(True, 1)
            except Empty:
                if self.__stop_event.is_set():
                    self.logger.debug('orderly stopping')
                    break
                elif self.__exception_event.is_set():
                    self.logger.critical('stopping due to exception in another thread')
                    break
                continue

            self.logger.debug('Processing Event: %s' % event)
            if not event.silent or (event.silent and self.process_silent_events):
                self.process_event(event)

        self.running = False
        self.logger.debug('Dispatcher thread stopped')

    def _pooled(self):
        thr_name = current_thread().getName()
        while 1:
            promise = self.__async_queue.get()

            # If unpacking fails, the thread pool is being closed from Updater._join_async_threads
            if not isinstance(promise, Promise):
                self.logger.debug("Closing run_async thread %s/%d", thr_name,
                                  len(self.__async_threads))
                break

            promise.run()
            if isinstance(promise.exception, DispatcherHandlerStop):
                self.logger.warning(
                    'DispatcherHandlerStop is not supported with async functions; func: %s',
                    promise.pooled_function.__name__)

    def _init_async_threads(self, base_name, workers):
        base_name = '{}_'.format(base_name) if base_name else ''

        for i in range(workers):
            thread = Thread(target=self._pooled, name='{}{}'.format(base_name, i))
            self.__async_threads.add(thread)
            thread.start()

    def stop(self):
        """Stops the thread."""
        if self.running:
            self.__stop_event.set()
            while self.running:
                sleep(0.1)
            self.__stop_event.clear()

        # async threads must be join()ed only after the dispatcher thread was joined,
        # otherwise we can still have new async threads dispatched
        threads = list(self.__async_threads)
        total = len(threads)

        # Stop all threads in the thread pool by put()ting one non-tuple per thread
        for i in range(total):
            self.__async_queue.put(None)

        for i, thr in enumerate(threads):
            self.logger.debug('Waiting for async thread {0}/{1} to end'.format(i + 1, total))
            thr.join()
            self.__async_threads.remove(thr)
            self.logger.debug('async thread {0}/{1} has ended'.format(i + 1, total))

    def process_event(self, event):
        """
        Processes a single event.

        Args:
            event (:obj:`str` | :class:`viber.Event` | :class:`viber.ViberError`):
                The event to process.

        """
        # An error happened while polling
        if isinstance(event, ViberError):
            try:
                self.dispatch_error(None, event)
            except Exception:
                self.logger.exception('An uncaught error was raised while handling the error')
            return

        for group in self.groups:
            try:
                for handler in (x for x in self.handlers[group] if x.check_event(event)):
                    handler.handle_event(event, self)
                    break

            # Stop processing with any other handler.
            except DispatcherHandlerStop:
                self.logger.debug('Stopping further handlers due to DispatcherHandlerStop')
                break

            # Dispatch any error.
            except ViberError as ve:
                self.logger.warning('A ViberError was raised while processing the Event')

                try:
                    self.dispatch_error(event, ve)
                except DispatcherHandlerStop:
                    self.logger.debug('Error handler stopped further handlers')
                    break
                except Exception:
                    self.logger.exception('An uncaught error was raised while handling the error')

            # Errors should not stop the thread.
            except Exception:
                self.logger.exception('An uncaught error was raised while processing the event')

    def dispatch_error(self, event, error):
        """
        Dispatches an error.

        Args:
            event (:obj:`str` | :class:`viber.Event` | None): The event that caused the error
            error (:class:`viber.ViberError`): The Viber error that was raised.

        """
        if self.error_handlers:
            for callback in self.error_handlers:
                callback(self.bot, event, error)

        else:
            self.logger.exception(
                'No error handlers are registered, logging exception.', exc_info=error)
