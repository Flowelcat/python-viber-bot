import datetime
import logging
import time
import weakref
from numbers import Number
from queue import PriorityQueue, Empty
from threading import Lock, Event, Thread


class Days(object):
    MON, TUE, WED, THU, FRI, SAT, SUN = range(7)
    EVERY_DAY = tuple(range(7))


class JobQueue(object):
    def __init__(self, bot):
        self._queue = PriorityQueue()
        self.bot = bot
        self.logger = logging.getLogger(self.__class__.__name__)
        self.__start_lock = Lock()
        self.__next_peek_lock = Lock()  # to protect self._next_peek & self.__tick
        self.__tick = Event()
        self.__thread = None
        self._next_peek = None
        self._running = False

    def _put(self, job, next_t=None, last_t=None):
        if next_t is None:
            next_t = job.interval
            if next_t is None:
                raise ValueError('next_t is None')

        if isinstance(next_t, datetime.datetime):
            next_t = (next_t - datetime.datetime.now()).total_seconds()

        elif isinstance(next_t, datetime.time):
            next_datetime = datetime.datetime.combine(datetime.date.today(), next_t)

            if datetime.datetime.now().time() > next_t:
                next_datetime += datetime.timedelta(days=1)

            next_t = (next_datetime - datetime.datetime.now()).total_seconds()

        elif isinstance(next_t, datetime.timedelta):
            next_t = next_t.total_seconds()

        next_t += last_t or time.time()

        self.logger.debug('Putting job %s with t=%f', job.name, next_t)

        self._queue.put((next_t, job))

        # Wake up the loop if this job should be executed next
        self._set_next_peek(next_t)

    def run_once(self, callback, when, context=None, name=None):
        job = Job(callback, repeat=False, context=context, name=name, job_queue=self)
        self._put(job, next_t=when)
        return job

    def run_repeating(self, callback, interval, first=None, context=None, name=None):
        job = Job(callback,
                  interval=interval,
                  repeat=True,
                  context=context,
                  name=name,
                  job_queue=self)
        self._put(job, next_t=first)
        return job

    def run_daily(self, callback, time, days=Days.EVERY_DAY, context=None, name=None):
        job = Job(callback,
                  interval=datetime.timedelta(days=1),
                  repeat=True,
                  days=days,
                  context=context,
                  name=name,
                  job_queue=self)
        self._put(job, next_t=time)
        return job

    def _set_next_peek(self, t):
        # """
        # Set next peek if not defined or `t` is before next peek.
        # In case the next peek was set, also trigger the `self.__tick` event.
        # """
        with self.__next_peek_lock:
            if not self._next_peek or self._next_peek > t:
                self._next_peek = t
                self.__tick.set()

    def tick(self):
        now = time.time()

        self.logger.debug('Ticking jobs with t=%f', now)

        while True:
            try:
                t, job = self._queue.get(False)
            except Empty:
                break

            self.logger.debug('Peeked at %s with t=%f', job.name, t)

            if t > now:
                # We can get here in two conditions:
                # 1. At the second or later pass of the while loop, after we've already
                #    processed the job(s) we were supposed to at this time.
                # 2. At the first iteration of the loop only if `self.put()` had triggered
                #    `self.__tick` because `self._next_peek` wasn't set
                self.logger.debug("Next task isn't due yet. Finished!")
                self._queue.put((t, job))
                self._set_next_peek(t)
                break

            if job.removed:
                self.logger.debug('Removing job %s', job.name)
                continue

            if job.enabled:
                try:
                    current_week_day = datetime.datetime.now().weekday()
                    if any(day == current_week_day for day in job.days):
                        self.logger.debug('Running job %s', job.name)
                        job.run(self.bot)

                except Exception:
                    self.logger.exception('An uncaught error was raised while executing job %s',
                                          job.name)
            else:
                self.logger.debug('Skipping disabled job %s', job.name)

            if job.repeat and not job.removed:
                self._put(job, last_t=t)
            else:
                self.logger.debug('Dropping non-repeating or removed job %s', job.name)

    def start(self):
        """Starts the job_queue thread."""
        self.__start_lock.acquire()

        if not self._running:
            self._running = True
            self.__start_lock.release()
            self.__thread = Thread(target=self._main_loop, name="job_queue")
            self.__thread.start()
            self.logger.debug('%s thread started', self.__class__.__name__)
        else:
            self.__start_lock.release()

    def _main_loop(self):
        while self._running:
            # self._next_peek may be (re)scheduled during self.tick() or self.put()
            with self.__next_peek_lock:
                tmout = self._next_peek - time.time() if self._next_peek else None
                self._next_peek = None
                self.__tick.clear()

            self.__tick.wait(tmout)

            # If we were woken up by self.stop(), just bail out
            if not self._running:
                break

            self.tick()

        self.logger.debug('%s thread stopped', self.__class__.__name__)

    def stop(self):
        with self.__start_lock:
            self._running = False

        self.__tick.set()
        if self.__thread is not None:
            self.__thread.join()

    def jobs(self):
        with self._queue.mutex:
            return tuple(job[1] for job in self._queue.queue if job)

    def get_jobs_by_name(self, name):
        with self._queue.mutex:
            return tuple(job[1] for job in self._queue.queue if job and job[1].name == name)


class Job(object):

    def __init__(self,
                 callback,
                 interval=None,
                 repeat=True,
                 context=None,
                 days=Days.EVERY_DAY,
                 name=None,
                 job_queue=None):

        self.callback = callback
        self.context = context
        self.name = name or callback.__name__

        self._repeat = repeat
        self._interval = None
        self.interval = interval
        self.repeat = repeat

        self._days = None
        self.days = days

        self._job_queue = weakref.proxy(job_queue) if job_queue is not None else None

        self._remove = Event()
        self._enabled = Event()
        self._enabled.set()

    def run(self, bot):
        self.callback(bot, self)

    def schedule_removal(self):
        self._remove.set()

    @property
    def removed(self):
        return self._remove.is_set()

    @property
    def enabled(self):
        return self._enabled.is_set()

    @enabled.setter
    def enabled(self, status):
        if status:
            self._enabled.set()
        else:
            self._enabled.clear()

    @property
    def interval(self):
        return self._interval

    @interval.setter
    def interval(self, interval):
        if interval is None and self.repeat:
            raise ValueError("The 'interval' can not be 'None' when 'repeat' is set to 'True'")

        if not (interval is None or isinstance(interval, (Number, datetime.timedelta))):
            raise ValueError("The 'interval' must be of type 'datetime.timedelta',"
                             " 'int' or 'float'")

        self._interval = interval

    @property
    def interval_seconds(self):
        interval = self.interval
        if isinstance(interval, datetime.timedelta):
            return interval.total_seconds()
        else:
            return interval

    @property
    def repeat(self):
        return self._repeat

    @repeat.setter
    def repeat(self, repeat):
        if self.interval is None and repeat:
            raise ValueError("'repeat' can not be set to 'True' when no 'interval' is set")
        self._repeat = repeat

    @property
    def days(self):
        return self._days

    @days.setter
    def days(self, days):
        if not isinstance(days, tuple):
            raise ValueError("The 'days' argument should be of type 'tuple'")

        if not all(isinstance(day, int) for day in days):
            raise ValueError("The elements of the 'days' argument should be of type 'int'")

        if not all(0 <= day <= 6 for day in days):
            raise ValueError("The elements of the 'days' argument should be from 0 up to and "
                             "including 6")

        self._days = days

    @property
    def job_queue(self):
        return self._job_queue

    @job_queue.setter
    def job_queue(self, job_queue):
        # Property setter for backward compatibility with JobQueue.put()
        if not self._job_queue:
            self._job_queue = weakref.proxy(job_queue)
        else:
            raise RuntimeError("The 'job_queue' attribute can only be set once.")

    def __lt__(self, other):
        return False
