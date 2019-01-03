"""This module contains the UnsubscribedHandler class."""
from viber.event import Event, EventType
from viber.ext.handler import Handler


class UnsubscribedHandler(Handler):

    def __init__(self,
                 callback,
                 pass_event_queue=False,
                 pass_job_queue=False,
                 pass_user_data=False):

        super(UnsubscribedHandler, self).__init__(
            callback,
            pass_event_queue=pass_event_queue,
            pass_job_queue=pass_job_queue,
            pass_user_data=pass_user_data)

    def check_event(self, event):
        if isinstance(event, Event) and event.event == EventType.unsubscribed:
            return True
        else:
            return False

    def handle_event(self, request, dispatcher):
        optional_args = self.collect_optional_args(dispatcher, request)

        return self.callback(dispatcher.bot, request, **optional_args)
