import logging

from viber.event import Event
from viber.ext.handler import Handler
from viber.utils.promise import Promise


class ConversationHandler(Handler):
    END = -1

    def __init__(self,
                 entry_points,
                 states,
                 fallbacks,
                 allow_reentry=False,
                 run_async_timeout=None,
                 timed_out_behavior=None,
                 per_user=True,
                 per_message=False,
                 conversation_timeout=None):

        self.entry_points = entry_points
        self.states = states
        self.fallbacks = fallbacks

        self.allow_reentry = allow_reentry
        self.run_async_timeout = run_async_timeout
        self.timed_out_behavior = timed_out_behavior
        self.per_user = per_user
        self.per_message = per_message
        self.conversation_timeout = conversation_timeout

        self.timeout_jobs = dict()
        self.conversations = dict()
        self.current_conversation = None
        self.current_handler = None

        self.logger = logging.getLogger(__name__)

        all_handlers = list()
        all_handlers.extend(entry_points)
        all_handlers.extend(fallbacks)

        for state_handlers in states.values():
            all_handlers.extend(state_handlers)

    def _get_key(self, event):
        user_id = event.user_id

        key = list()

        if self.per_user and user_id is not None:
            key.append(user_id)

        if self.per_message:
            key.append(event.message_token)

        return tuple(key)

    def check_event(self, event):
        if not isinstance(event, Event) or self.per_message and not event.message_token:
            return False

        key = self._get_key(event)
        state = self.conversations.get(key)

        # Resolve promises
        if isinstance(state, tuple) and len(state) is 2 and isinstance(state[1], Promise):
            self.logger.debug('waiting for promise...')

            old_state, new_state = state
            error = False
            try:
                res = new_state.result(timeout=self.run_async_timeout)
            except Exception as exc:
                self.logger.exception("Promise function raised exception")
                self.logger.exception("{}".format(exc))
                error = True

            if not error and new_state.done.is_set():
                self.event_state(res, key)
                state = self.conversations.get(key)

            else:
                for candidate in (self.timed_out_behavior or []):
                    if candidate.check_event(event):
                        # Save the current user and the selected handler for check_event
                        self.current_conversation = key
                        self.current_handler = candidate

                        return True

                else:
                    return False

        self.logger.debug('selecting conversation %s with state %s' % (str(key), str(state)))

        handler = None

        # Search entry points for a match
        if state is None or self.allow_reentry:
            for entry_point in self.entry_points:
                if entry_point.check_event(event):
                    handler = entry_point
                    break

            else:
                if state is None:
                    return False

        # Get the handler list for current state, if we didn't find one yet and we're still here
        if state is not None and not handler:
            handlers = self.states.get(state)

            for candidate in (handlers or []):
                if candidate.check_event(event):
                    handler = candidate
                    break

            # Find a fallback handler if all other handlers fail
            else:
                for fallback in self.fallbacks:
                    if fallback.check_event(event):
                        handler = fallback
                        break

                else:
                    return False

        # Save the current user and the selected handler for check_event
        self.current_conversation = key
        self.current_handler = handler

        return True

    def handle_event(self, event, dispatcher):
        new_state = self.current_handler.handle_event(event, dispatcher)
        timeout_job = self.timeout_jobs.pop(self.current_conversation, None)

        if timeout_job is not None:
            timeout_job.schedule_removal()
        if self.conversation_timeout and new_state != self.END:
            self.timeout_jobs[self.current_conversation] = dispatcher.job_queue.run_once(
                self._trigger_timeout, self.conversation_timeout,
                context=self.current_conversation
            )

        self.event_state(new_state, self.current_conversation)

    def event_state(self, new_state, key):
        if new_state == self.END:
            if key in self.conversations:
                del self.conversations[key]
            else:
                pass

        elif isinstance(new_state, Promise):
            self.conversations[key] = (self.conversations.get(key), new_state)

        elif new_state is not None:
            self.conversations[key] = new_state

    def _trigger_timeout(self, bot, job):
        del self.timeout_jobs[job.context]
        self.event_state(self.END, job.context)
