import logging
from threading import Event


logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class Promise(object):
    def __init__(self, pooled_function, args, kwargs):
        self.pooled_function = pooled_function
        self.args = args
        self.kwargs = kwargs
        self.done = Event()
        self._result = None
        self._exception = None

    def run(self):
        try:
            self._result = self.pooled_function(*self.args, **self.kwargs)

        except Exception as exc:
            logger.exception('An uncaught error was raised while running the promise')
            self._exception = exc

        finally:
            self.done.set()

    def __call__(self):
        self.run()

    def result(self, timeout=None):
        self.done.wait(timeout=timeout)
        if self._exception is not None:
            raise self._exception  # pylint: disable=raising-bad-type
        return self._result

    @property
    def exception(self):
        return self._exception